import google.genai
import numpy as np # for embedding normalization

from shared_types import Article
import os
import json
# TODO: look into feather or parquet if speed becomes an issue

# import pandas as pd
# import polars as pl # speed baby!

MAX_TOKENS_PER_MINUTE = 1_000_000
MAX_REQUESTS_PER_MINUTE = 3_000_000

# tokens per request ~20k
  # each request has 10 chunks, each with ~2k tokens (cannot exceed 2048)
  
# any potential consequences of passing in a title and empty string to the embedding model
# could that meaningfully through things off? can probably just do a little check before embedding

def load_json(filepath: str) -> Article:
  try:
    with open(filepath, 'r') as file:
      article = json.load(file)
      return article
  except FileNotFoundError:
    print("Error finding file")
  except:
    print("Something went wrong when trying to load the JSON file!")

def main():
  base_filepath = os.path.join(os.getcwd(), 'sep', 'articles')
  test_file = 'sep-logic-and-games.json'
  test_filepath = os.path.join(base_filepath, test_file)
  article = load_json(test_filepath)
  
  # print(article)
  
  # retrieve documents (iterate through articles folder)
  # for each document, get the document's embeddings from the model
    # should think about rate-limiting & how to optimize 1M TPM
      # can generate multiple embeddings at once by passing in a list?
      # 2k tokens per input text, 20k per API call (i.e., 10 input texts)
      # 
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