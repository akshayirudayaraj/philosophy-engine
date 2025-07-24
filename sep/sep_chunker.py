from tokenizer import Tokenizer

from typing import cast
from collections import deque # for O(1) popping
from hashlib import sha256

from json_helper import JsonHelper
from shared_types import Article, Section, Chunk, Metadata
import os

TOKENIZER_MODEL_PATH = os.path.join('sep', 'gemma_tokenizer.model')

TOKEN_LIMIT_PER_STRING = 2048
TOKEN_BUFFER = 48 # trying to stay under 2k

# any potential consequences of passing in a title and empty string to the embedding model
# could that meaningfully through things off? can probably just do a little check before embedding

# idk if this is a correct usage of classmethod
# i guess i'm trying to get something close to a singleton...not really a static class
class ChunkTracker: 
  _num_chunks_over_2048 = 0
  _running_chunk_token_avg = 0
  _total_token_count = 0
  _num_processed_chunks = 0
  
  @classmethod
  def get_num_chunks_over_2048(cls):
    return cls._num_chunks_over_2048
  
  @classmethod
  def get_chunk_avg_length(cls):
    return cls._total_token_count / cls._num_processed_chunks
  
  @classmethod
  def update(cls, chunk_length: int):
    cls._total_token_count += chunk_length
    cls._num_processed_chunks += 1 
    
    if (chunk_length > 2048):
      cls._num_chunks_over_2048 += 1

def generate_id(article: Article, section: Section, text: str) -> str:
  NUM_CHARS_FOR_SHA = 20
  SHA_LENGTH = 10
  
  return "-".join([article['title'].lower().replace(" ", "-"),
                    section['header'][-1].lower().replace(" ", "-"),
                    sha256(text[-NUM_CHARS_FOR_SHA:].encode('utf-8')).hexdigest()[-SHA_LENGTH:]])

# TODO: optimize chunker so sentences don't get cut off
def chunk_article(article: Article, tokenizer: Tokenizer) -> list[Chunk]:
  chunk_metadata = Metadata( # TODO: after refactoring, this will become less of a mess
    organization="Stanford Encyclopedia of Philosophy",
    authors=article['authors'],
    editors=article['editors'],
    original_date=article['original_date'],
    revised_date=article['revision_date'],
    link=article['link'],
    bibliography=article['bibliography'],
  ) 
  
  article_chunks: list[Chunk] = []
  for section in article['content']:
    chunk_title = article['title'] + ", " + ", ".join(section['header'])
    title_size_tokens = tokenizer.count_tokens(chunk_title)
    
    max_tokens_to_take = TOKEN_LIMIT_PER_STRING - TOKEN_BUFFER - title_size_tokens
    
    section_tokens = tokenizer.encode(section['text'])
    
    section_tokens_dq = deque(section_tokens)
    
    section_chunks: list[Chunk] = []
    while (len(section_tokens_dq) > 0):
      available_tokens = min(max_tokens_to_take, len(section_tokens_dq))
      chunk_dq = [section_tokens_dq.popleft() for _ in range(available_tokens)]
      
      num_chunk_tokens = len(chunk_dq)
      ChunkTracker.update(num_chunk_tokens)
      
      chunk = list(chunk_dq)
      chunk_text_decoded = tokenizer.decode(chunk)
            
      section_chunks.append({
        'id': generate_id(article, section, chunk_text_decoded),
        'num_tokens': num_chunk_tokens,
        'content': chunk_text_decoded,
        'title': chunk_title,
        'text_metadata': chunk_metadata,
      })
    
    article_chunks.extend(section_chunks)
  
  return article_chunks

def main():
  base_filepath = os.path.join(os.getcwd(), 'sep')
  base_read_filepath = os.path.join(base_filepath, 'articles')
  write_base_filepath = os.path.join(base_filepath, 'chunked_articles')
  
  tokenizer = Tokenizer(TOKENIZER_MODEL_PATH)
  # test_file = 'sep-logic-and-games.json'
  
  for idx, file in enumerate(os.listdir(base_read_filepath), 1):
    print("Reading " + file)
    
    read_filepath = os.path.join(base_read_filepath, file)
    article = cast(Article, JsonHelper.load_file(read_filepath))
    
    article_chunks = chunk_article(article, tokenizer)
    
    
    for chunk in article_chunks:
      write_filepath = os.path.join(write_base_filepath, chunk['id'].replace('/', "-"))
      JsonHelper.write_dict_to_json(cast(dict, chunk), write_filepath)
    
    print("Wrote " + file)
    print(f'{idx}/1840') # 1840 and not 1852 because 12 SEP entries have been retired
  
  print(f"number of chunks over 2048 tokens: {ChunkTracker.get_num_chunks_over_2048()}")
  print(f"average chunk length: {ChunkTracker.get_chunk_avg_length()}")

if __name__ == '__main__':
  main()