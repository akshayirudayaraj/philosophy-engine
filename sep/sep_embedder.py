from google import genai
from google.genai import types

from typing import TypedDict

import numpy as np # for embedding normalization

from dotenv import load_dotenv
load_dotenv('./.env')

from shared_types import Article, Section
import os
import json
# TODO: look into feather or parquet if speed becomes an issue

# import pandas as pd
# import polars as pl # speed baby!

# MAX_TOKENS_PER_MINUTE = 1_000_000
MAX_REQUESTS_PER_MINUTE = 100_000

GEMINI_DEV_API_KEY = os.getenv('GOOGLE_GENAI_API_KEY')
CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
CLOUD_REGION = os.getenv('GOOGLE_CLOUD_LOCATION')

EMBEDDING_MODEL_ID = 'gemini-embedding-001'
DENSE_OUTPUT_DIMENSIONALITY = 1536
  # TODO: try the higher 3072 if the retrieval is confusing
TASK_TYPE = 'RETRIEVAL_DOCUMENT'

# tokens per request ~20k
  # each request has 10 chunks, each with ~2k tokens (cannot exceed 2048)
  
# any potential consequences of passing in a title and empty string to the embedding model
# could that meaningfully through things off? can probably just do a little check before embedding

class Metadata(TypedDict):
  organization: str
  authors: list[str]
  editors: list[str]
  original_date: str
  revised_date: str | None
  link: str

class Chunk(TypedDict):
  id: str
  content: str # must be under 1.95k tokens
  title: str # must be 0.05k - 0.98k tokens
  metadata: Metadata
  
# makes it easy for Pinecone ingestion (might have to change filedata)
class Embedding(TypedDict):
  id: str
  embeddings: list[float]
  metadata: Metadata

def chunk(article: Article) -> list[Chunk]:
  0

def embed(chunk: Chunk) -> Embedding:
  0

def load_json(filepath: str) -> Article:
  try:
    with open(filepath, 'r') as file:
      article = json.load(file)
      return article
  except:
    print("error loading json")

def main():
  base_filepath = os.path.join(os.getcwd(), 'sep', 'articles')
  test_file = 'sep-logic-and-games.json'
  test_filepath = os.path.join(base_filepath, test_file)
  article = load_json(test_filepath)
    
  test_chunk = article['content'][0]
  # print(len(test_chunk['text'].split(' ')))
  
  client = genai.Client(
    vertexai=True,
    project=CLOUD_PROJECT_ID,
    location=CLOUD_REGION,
  )
  
  # 3k RPM limit
  # response = client.models.count_tokens(
  #   model=EMBEDDING_MODEL_ID,
  #   contents=test_chunk['text'],
  # )
  
  embedding = client.models.embed_content(
    model=EMBEDDING_MODEL_ID,
    contents=[test_chunk['text']],
    config=types.EmbedContentConfig(
      title=",".join(test_chunk['header']),
      task_type=TASK_TYPE,
      output_dimensionality=DENSE_OUTPUT_DIMENSIONALITY,
      auto_truncate=False,
    )
  )
  
  print(embedding.embeddings[0].values) # can use 0 here for embeddings because only passing in one piece of content
  
  # retrieve documents (iterate through articles folder)
  # for each document, get the document's embeddings from the model
    # can pass in title (with section headers) into TextEmbeddingInput
      # that input then passed into the TextEmbeddingModel
      # maybe the title can be used for other metadata in the future
      # task type for this document embedding is RETRIEVAL_DOCUMENT
        # when the user gives a query, it'll be RETRIEVAL_QUERY
      # uses MRL (basically distillation?) to get similar performance embeddings
        # on smaller dimensionality (less compute) -> 768 or 1536
        # for these ones, i need to manually normalize

if __name__ == '__main__':
  main()