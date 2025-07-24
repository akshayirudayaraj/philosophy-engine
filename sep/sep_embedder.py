from typing import cast
from google import genai
from google.genai import types, Client

import numpy as np # for embedding normalization
import os
from shared_types import Chunk, Embedding, VectorMetadata
from json_helper import JsonHelper
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv('./.env')

CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
CLOUD_REGION = os.getenv('GOOGLE_CLOUD_LOCATION')
EMBEDDING_MODEL_ID = 'gemini-embedding-001'
DENSE_OUTPUT_DIMENSIONALITY = 1536
  # TODO: try the higher 3072 if the retrieval is confusing
TASK_TYPE = 'RETRIEVAL_DOCUMENT'
MAX_TOKENS_PER_MINUTE = 200_000 # via vertex API (https://cloud.google.com/vertex-ai/generative-ai/docs/quotas_)
  # at most i'm sending 2k in one request, so basically i should only send 100 requests or chunks/minute
  # i have 49k chunks so that's around 8 hours
  # secondary restriction is 30k RPM which is impossible to get with < 2k per chunk

# tokens per request ~20k
  # each request has 10 chunks, each with ~2k tokens (cannot exceed 2048)
  
def normalize(embeddings: list[float]) -> list[float]:
  vec = np.array(embeddings)
  norm = np.linalg.norm(vec)
  normalized_vectors = vec / norm
  normalized_vectors_list = normalized_vectors.tolist()
  return cast(list[float], normalized_vectors_list)

def embed(client: Client, chunk: Chunk) -> Embedding:
  title = chunk['title']
  text = chunk['content']
  
  embedding = client.models.embed_content(
    model=EMBEDDING_MODEL_ID,
    contents=text,
    config=types.EmbedContentConfig(
      title=title,
      task_type=TASK_TYPE,
      output_dimensionality=DENSE_OUTPUT_DIMENSIONALITY,
      auto_truncate=False,
    )
  )
  
  if embedding is None:
    raise ValueError("The embedding is empty!")
  elif embedding.embeddings is None:
    raise ValueError("There's no embedding list in the embedding object!")
  elif len(embedding.embeddings) > 1:
    raise ValueError("There shouldn't be more than one set of embeddings in the object!")
  elif (chunk_embedding_values := embedding.embeddings[0].values) is None: # yay python!
    raise ValueError("No embedding values!")
  
  normalized_embeddings = normalize(chunk_embedding_values) # manually needed for the 768 and 1536 dimensions
    
  vector_metadata: VectorMetadata = {
    **chunk['text_metadata'], # yay python!
    'num_tokens': chunk['num_tokens'],
  }
    
  return {
    'id': chunk['id'],
    'embeddings': normalized_embeddings,
    'metadata': vector_metadata,
  }

def main():
  client = genai.Client(
    vertexai=True,
    project=CLOUD_PROJECT_ID,
    location=CLOUD_REGION,
  )
  
  # test_read_filepath = os.path.join(os.getcwd(), 'sep', 'chunked_articles', '18th-century-german-philosophy-prior-to-kant-life-and-works-83b92c37c1.json')
  # test_chunk = cast(Chunk, JsonHelper.load_file(test_read_filepath))
    
  # embedding = embed(client, test_chunk)
    
  # test_write_filepath = os.path.join(os.getcwd(), 'sep', 'embeddings', embedding['id'])
  # JsonHelper.write_dict_to_json(cast(dict, embedding), test_write_filepath)
  
  base_filepath = os.path.join(os.getcwd(), 'sep')
  base_read_filepath = os.path.join(base_filepath, 'chunked_articles')
  base_write_filepath = os.path.join(base_filepath, 'embeddings')

  with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    
    for file in os.listdir(base_read_filepath):
      futures.append(executor.submit(
        read_embed_write,
        base_read_filepath=base_read_filepath,
        base_write_filepath=base_write_filepath,
        file=file,
        client=client,
      ))
      
    for future in as_completed(futures):
      try:
        result = future.result()
        print(result)
      except Exception as e:
        # print(e)
        print(future.exception())
        break
    
def read_embed_write(base_read_filepath: str, base_write_filepath: str, file: str, client: Client):
  read_filepath = os.path.join(base_read_filepath, file)
  chunk = cast(Chunk, JsonHelper.load_file(read_filepath))
  
  embedding = embed(client, chunk)
  
  write_filepath = os.path.join(base_write_filepath, embedding['id'].replace('/', '-'))
  JsonHelper.write_dict_to_json(cast(dict, embedding), write_filepath)

if __name__ == '__main__':
  main()