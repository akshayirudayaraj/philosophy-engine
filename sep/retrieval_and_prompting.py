from google import genai
from google.genai import Client, types
from typing import cast
from pinecone import Pinecone
from dotenv import load_dotenv
from bs4 import BeautifulSoup, Tag
import os
import numpy as np
from json_helper import JsonHelper
import requests

load_dotenv('./.env')

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_HOST_IDX = cast(str, os.getenv('PC_INDEX'))

CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
CLOUD_REGION = os.getenv('GOOGLE_CLOUD_LOCATION')
EMBEDDING_MODEL_ID = 'gemini-embedding-001'
DENSE_OUTPUT_DIMENSIONALITY = 1536
TASK_TYPE = 'RETRIEVAL_QUERY'

# LOTS of duplicate code from embedding file here
  # TODO: need to clean up a lot after i get MVP up
  
def normalize(embeddings: list[float]) -> list[float]:
  vec = np.array(embeddings)
  norm = np.linalg.norm(vec)
  normalized_vectors = vec / norm
  normalized_vectors_list = normalized_vectors.tolist()
  return cast(list[float], normalized_vectors_list)

def embed_query(client: Client, query: str) -> list[float]:  
  embedding = client.models.embed_content(
    model=EMBEDDING_MODEL_ID,
    contents=query,
    config=types.EmbedContentConfig(
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
  
  return cast(list[float], normalized_embeddings)

def query_pinecone(query_vector: list[float], index) -> dict:
  TOP_K = 10
  
  results = index.query(
    namespace='__default__',
    vector=query_vector,
    top_k=TOP_K,
    include_metadata=True,
    include_values=True
  )
  
  return results
  
def find_required(soup, **kwargs) -> Tag:
  tag = soup.find(**kwargs)
  if not isinstance(tag, Tag):
    raise ValueError("Unable to find tag! Something's wrong with the document you're searching.")
  else:
    return tag
  
def fetch_url(link: str) -> BeautifulSoup:
  page = requests.get(link)
  soup = BeautifulSoup(page.content, "lxml")
  return soup

def get_context(match: dict) -> tuple[str, str]:
  id = match['id']
  link = match['metadata']['link']
  
  title = scrape_title(link)
  
  id_without_sha = id[:-11]
  title_and_deepest_header = id_without_sha.split('-')
  
  deepest_header = consume_title(title, title_and_deepest_header)
  
  internal_json_title = "sep-" + title.lower().replace(' ', '-').replace('/', '-')
  article_text_and_headers = get_json_content(internal_json_title)
  
  content = find_header_text(article_text_and_headers, deepest_header)
  
  return title, content
  
def find_header_text(article_content: list[dict], header: str) -> str:
  print(header)
  for section in article_content:
    if (section['header'][-1].lower() == header):
      return section['text']
  
  # if can't find header, default is to get the context underneath the title
    # in my case, that's the last entry in the content list
  return article_content[-1]['text']
  
def get_json_content(json_title: str) -> list[dict]:
  search_directory = os.path.join(os.getcwd(), 'sep', 'articles')
  filepath = os.path.join(search_directory, json_title + '.json')
  article = JsonHelper.load_file(filepath)
  return article['content']
  
def scrape_title(link: str) -> str:
  soup = fetch_url(link)
  title = find_required(soup, name='h1').get_text()
  return title.lower()

def consume_title(title: str, title_and_deepest_header: list[str]) -> str:
  title_header_combined = " ".join(title_and_deepest_header)
  header = title_header_combined.removeprefix(title + ' ')
  return header
  
def construct_prompt(user_query: str, contextual_info: list[str]) -> str:
  return "hey chat"

def main():
  user_query = "Does free will exist?"
  
  client = genai.Client(
    vertexai=True,
    project=CLOUD_PROJECT_ID,
    location=CLOUD_REGION,
  )
  
  pc = Pinecone(api_key=PINECONE_API_KEY)
  index = pc.Index(host=PINECONE_HOST_IDX)
  
  query_vector = embed_query(client, user_query)
  
  results = query_pinecone(query_vector, index)
  
  for match in results['matches']:
    metadata = match['metadata']
    print(f'id: {match['id']}, link: {metadata['link']}')
    
  print(f'usage: {results['usage']}')
  
  contextual_info = [
    (lambda m: (get_context(m), print(get_context(match)))[0])(match)
    for match in results['matches']
    if print(f'\n\n id: {match['id']}') or True
  ]
  
  
  # prompt = construct_prompt(user_query, contextual_info)
  
  # response = OpenAI.prompt(prompt)
  
  # print(response) # the moment of truth!
  
if __name__ == '__main__':
  main()