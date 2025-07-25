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
import anthropic

load_dotenv('./.env')

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_HOST_IDX = cast(str, os.getenv('PC_INDEX'))

CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
CLOUD_REGION = os.getenv('GOOGLE_CLOUD_LOCATION')
EMBEDDING_MODEL_ID = 'gemini-embedding-001'
DENSE_OUTPUT_DIMENSIONALITY = 1536
TASK_TYPE = 'RETRIEVAL_QUERY'

ANTHROPIC_MODEL_ID = 'claude-3-5-haiku-latest' # 'claude-sonnet-4-latest'
MAX_WORD_RESPONSE_APPROX = 5000
WORD_TO_TOKEN_APPROX = 1.3
MAX_RESPONSE_TOKENS = int(MAX_WORD_RESPONSE_APPROX * WORD_TO_TOKEN_APPROX)

# LOTS of duplicate code from embedding file here
  # TODO: need to clean up a lot after i get MVP up
  
def normalize(embeddings: list[float]) -> list[float]:
  vec = np.array(embeddings)
  norm = np.linalg.norm(vec)
  normalized_vectors = vec / norm
  normalized_vectors_list = normalized_vectors.tolist()
  return cast(list[float], normalized_vectors_list)

def embed_query(embedding_client: Client, query: str) -> list[float]:  
  embedding = embedding_client.models.embed_content(
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

def get_context(match: dict) -> dict:
  id = match['id']
  link = match['metadata']['link']
  
  title = scrape_title(link)
  
  id_without_sha = id[:-11]
  title_and_deepest_header = id_without_sha.split('-')
  
  deepest_header = consume_title(title, title_and_deepest_header)
  
  internal_json_title = "sep-" + title.lower().replace(' ', '-').replace('/', '-')
  article_text_and_headers = get_json_content(internal_json_title)
  
  content = find_header_text(article_text_and_headers, deepest_header)
  
  return {
    'title': title,
    **content,
  }
  
def find_header_text(article_content: list[dict], header: str) -> dict[str, str]:
  print(header)
  for section in article_content:
    if (section['header'][-1].lower() == header):
      return {
        'header_tree': ", ".join(section['header']),
        'text': section['text'],
      }
  
  # if can't find header, default is to get the context underneath the title
    # in my case, that's the last entry in the content list
  under_title_context = article_content[-1]
  return {
    'header_tree': ", ".join(under_title_context['header']),
    'text': under_title_context['text'],
  }
  
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
  
def construct_prompt(user_query: str, contextual_info: list[dict]) -> dict[str, str]:
  system_prompt = """
  You are a scholar of philosophy and ethics. Your mission is to help young philosopers and ethicists
  think about very hard, nuanced questions. Because you are wise, you offer many potential answers to questions
  and spend time in deliberation before reaching a conclusion.
  """
  
  user_prompt = f"""
    <question>{user_query}</question>

    <context>
    {[
      f"""
      <article>
      Title: {context['title']}
      Headers: {context['header_tree']}
      Text: {context['text']}
      </article>
      """
      for context in contextual_info
    ]}
    </context>
    
    <task>
    Write an in-depth, well-structured essay addressing the user's question. Use the context provided to structure
    your argumentation and frequently cite the articles you use in your essay. Be even-keeled and academic, and question
    your own logic as you draft the essay. Reason thoughtfully, thinking about all possible answers to the question.
    
    Provide an overview of how to approach the question and potential answers to it. Be nuanced, careful, and precise
    as you write. Use the scholarly texts provided as much as possible to outline and justify your arguments.
    </task>
  """
  
  thinking_prompt = """
  
  """
  
  return {
    'system': system_prompt,
    'user': user_prompt,
    'thinking': thinking_prompt
  }

def main():
  user_query = "Does free will exist?"
  
  embedding_client = genai.Client(
    vertexai=True,
    project=CLOUD_PROJECT_ID,
    location=CLOUD_REGION,
  )
  
  pc = Pinecone(api_key=PINECONE_API_KEY)
  index = pc.Index(host=PINECONE_HOST_IDX)
  
  query_vector = embed_query(embedding_client, user_query)
  
  results = query_pinecone(query_vector, index)
  
  for match in results['matches']:
    metadata = match['metadata']
    print(f'id: {match['id']}, link: {metadata['link']}')
    
  print(f'usage: {results['usage']}')
  
  contextual_info = [
    get_context(match)
    for match in results['matches']
    if (print(get_context(match))) or True
  ]
  
  client = anthropic.Anthropic()
  
  prompt = construct_prompt(user_query, contextual_info)
  
  response = client.messages.create(
    model=ANTHROPIC_MODEL_ID,
    max_tokens=MAX_RESPONSE_TOKENS,
    # thinking={
    #   'type': 'disabled',
    #   'budget_tokens': THINKING_TOKEN_BUDGET,
    # },
    system=[
      {
        'type': 'text',
        'text': prompt['system'],
        'cache_control': {'type': 'ephemeral'} # min cacheable prompt length: 1024 tokens
      }
    ],
    messages=[
      {
        'role': 'user',
        'content': prompt['user']
      }
    ],
  )
  
  print(f'\n\n\nCLAUDE:\n{response.content[0]}')
  
if __name__ == '__main__':
  main()