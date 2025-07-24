import itertools
from typing import Generator, cast
from json_helper import JsonHelper
import os
from pinecone import Pinecone, Vector
from shared_types import Embedding

import logging
from dotenv import load_dotenv

import json

logging.basicConfig(
    filename='upsert_errors.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv('./.env')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PC_INDEX = cast(str, os.getenv('PC_INDEX'))
BATCH_SIZE = 150
MAX_VECTOR_SIZE_BYTES = 2_000_000

def fast_chunker(vectors: list[Embedding], batch_size=BATCH_SIZE) -> Generator[list[Embedding]]:
    it = iter(vectors)
    
    for _ in range(0, len(vectors), batch_size):
      yield list(itertools.islice(it, batch_size))
      
def estimate_size(vector: dict):
    return len(json.dumps(vector, ensure_ascii=False).encode('utf-8'))
  
def remove_non_ascii_fast(text):
  return text.encode('ascii', 'ignore').decode('ascii')

def process_vector_generator(vector: dict) -> Generator[Embedding]:
  yield process_and_clean_vector(vector)

def process_and_clean_vector(v: dict) -> Embedding:
  '''
  replaces `embeddings` field with values,
  removes `revised_date` from metadata if empty,
  reduces bibliography size so that the whole vector < 2MB (pinecone requirement),
  removes non-ASCII characters (like special quotes) from `id`
  '''
  
  v['values'] = cast(list[float], v.pop('embeddings'))
  if v['metadata'].get('revised_date') is None:
    del v['metadata']['revised_date']
    
  original_id = v['id']
  cleaned_id = remove_non_ascii_fast(v['id'])
  if cleaned_id != original_id:
    v['id'] = cleaned_id # only reassign if difference (since most ids don't need cleaning)
  
  PERCENT_TO_KEEP = 70
  while estimate_size(v) > MAX_VECTOR_SIZE_BYTES:
    biblio_len = len(v['metadata']['bibliography'])
    indices_to_keep = int((PERCENT_TO_KEEP/100) * biblio_len)
    
    if (biblio_len > indices_to_keep):
      v['metadata']['bibliography'] = v['metadata']['bibliography'][:indices_to_keep]
    else:
      del v['metadata']['bibliography']
      break
    
  # assumption: no size concerns (vector always under 2MB) if bibliography is removed
  
  return cast(Embedding, v)

def main():
  base_read_path = os.path.join(os.getcwd(), 'sep', 'embeddings')
  
  pc = Pinecone(PINECONE_API_KEY)
  index = pc.Index(host=PC_INDEX, 
                   pool_threads=10
                   )
  
  v1 = JsonHelper.load_file(os.path.join
                            (base_read_path,
                              '19th-century-romantic-aesthetics-romantic-poetry-and-romantic-irony-6f334221db.json'))
  v2 = JsonHelper.load_file(os.path.join(base_read_path,
                              '18th-century-german-aesthetics-gottsched-and-his-critics:-truth-and-imagination-dfa0af8ea5.json'))
  v3 = JsonHelper.load_file(os.path.join(base_read_path,
                              'wittgenstein’s-logical-atomism-m-452306a480.json'))
  
  print(estimate_size(v3))
  
  test_v = [v1, v2, v3]
  [process_and_clean_vector(d) for d in test_v]
    
  index.upsert(
    cast(list[Vector], test_v)
  )
  
  vectors = [
    process_and_clean_vector(JsonHelper.load_file(os.path.join(base_read_path, file)))
    for file in os.listdir(base_read_path)
  ]
  
  with index:
    futures = [
      index.upsert(cast(list[Vector], batch), async_req=True, show_progress=True)
      for batch in fast_chunker(vectors)  
    ]

    for future in futures: # using ignores here bc i'm following docs (future.get() should raise on error)
      try:
        print(future.get()) # type: ignore
      except Exception:
        logging.error(f"Error upserting {future.get()}") # type: ignore
  
if __name__ == '__main__':
  main()