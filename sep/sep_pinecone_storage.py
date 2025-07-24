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

def fast_chunker(vectors: list[Embedding], batch_size=BATCH_SIZE) -> Generator[list[Embedding]]:
    it = iter(vectors)
    
    for i in range(0, len(vectors), batch_size):
      yield list(itertools.islice(it, batch_size))

def main():
  base_read_path = os.path.join(os.getcwd(), 'sep', 'embeddings')
  
  pc = Pinecone(PINECONE_API_KEY)
  index = pc.Index(host=PC_INDEX, 
                   # pool_threads=10
                   )
  
  v1 = cast(Embedding,
                  JsonHelper.load_file(os.path.join(base_read_path,
                                                    '19th-century-romantic-aesthetics-romantic-poetry-and-romantic-irony-6f334221db.json')))
  v2 = cast(Embedding,
                  JsonHelper.load_file(os.path.join(base_read_path,
                                                    '18th-century-german-aesthetics-gottsched-and-his-critics:-truth-and-imagination-dfa0af8ea5.json')))
  
  test_v = [v1, v2]
  # [print(json.dumps(d, indent=4)) for d in test_v]
  
  for v in test_v:
    v['values'] = cast(list[float], v.pop('embeddings'))
    if v['metadata'].get('revised_date') is None:
      del v['metadata']['revised_date']
    
  index.upsert(
    cast(list[Vector], test_v)
  )
  
  # vectors = [
  #   cast(Embedding, JsonHelper.load_file(os.path.join(base_read_path, file)))
  #   for file in os.listdir(base_read_path)
  # ]
  
  # with index:
  #   futures = [
  #     index.upsert(cast(list[Vector], batch), async_req=True, show_progress=True)
  #     for batch in fast_chunker(vectors)  
  #   ]

  #   for future in futures: # using ignores here bc i'm following docs (future.get() should raise on error)
  #     try:
  #       future.get() # type: ignore
  #     except Exception:
  #       logging.error(f"Error upserting {future.get()}") # type: ignore
  

if __name__ == '__main__':
  main()