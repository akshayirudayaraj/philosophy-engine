from hashlib import sha256
from typing import Any
from collections import deque # for O(1) popping

from shared_types import Article, Section, Chunk

class ChunkTracker:
  _token_limit_per_chunk: int
  _num_chunks_over_limit = 0
  _running_chunk_token_avg = 0
  _total_token_count = 0
  _num_processed_chunks = 0
  
  def __init__(self, token_limit_per_chunk: int):
    self._token_limit_per_chunk = token_limit_per_chunk
    
  def get_num_processed_chunks(self):
    return self._num_processed_chunks
  
  def get_total_token_count(self):
    return self._total_token_count
  
  def get_num_chunks_over_limit(self):
    return self._num_chunks_over_limit
  
  def get_chunk_avg_length(self):
    return self._total_token_count / self._num_processed_chunks
  
  def update(self, chunk_length: int):
    self._total_token_count += chunk_length
    self._num_processed_chunks += 1 
    
    if (chunk_length > self._token_limit_per_chunk):
      self._num_chunks_over_limit += 1
        
class Chunker:
  _token_limit_per_chunk: int
  _tokenizer: Any
  _chunk_tracker: ChunkTracker
  TOKEN_BUFFER = 48
      
  def __init__(self, token_limit_per_chunk: int, tokenizer):
    self._token_limit_per_chunk = token_limit_per_chunk
    self._chunk_tracker = ChunkTracker(self._token_limit_per_chunk)
    self._tokenizer = tokenizer
    
  def generate_id(self, article: Article, section: Section, text: str) -> str:
    NUM_CHARS_FOR_SHA = 20
    SHA_LENGTH = 10
    
    return "-".join([article['title'].lower().replace(" ", "-"),
                      section['header'][-1].lower().replace(" ", "-"),
                      sha256(text[-NUM_CHARS_FOR_SHA:].encode('utf-8')).hexdigest()[-SHA_LENGTH:]])
    
  # TODO: optimize chunker so sentences don't get cut off
  def chunk_article(self, article: Article) -> list[Chunk]:
    chunk_metadata = article['metadata']
    
    article_chunks: list[Chunk] = []
    for section in article['content']:
      title_plus_header = article['title'] + ", " + ", ".join(section['header'])
      title_size_tokens = self._tokenizer.count_tokens(title_plus_header)
      
      max_tokens_to_take = self._token_limit_per_chunk - self.TOKEN_BUFFER - title_size_tokens
      
      section_tokens = self._tokenizer.encode(section['text'])
      section_tokens_dq = deque(section_tokens)
      
      section_chunks: list[Chunk] = []
      while (len(section_tokens_dq) > 0):
        available_tokens = min(max_tokens_to_take, len(section_tokens_dq))
        chunk_dq = [section_tokens_dq.popleft() for _ in range(available_tokens)]
        
        num_chunk_tokens = len(chunk_dq)
        self._chunk_tracker.update(num_chunk_tokens)
        
        chunk = list(chunk_dq)
        chunk_text_decoded = self._tokenizer.decode(chunk)
              
        section_chunks.append({
          'id': self.generate_id(article, section, chunk_text_decoded),
          'num_tokens': num_chunk_tokens,
          'content': chunk_text_decoded,
          'title': article['title'],
          'headers': section['header'],
          'text_metadata': chunk_metadata,
        })
      
      article_chunks.extend(section_chunks)
    
    return article_chunks
  
  def print_chunker_stats(self) -> None:
    print(f"""
      number of chunks over {self._token_limit_per_chunk} tokens: {self._chunk_tracker.get_num_chunks_over_limit()}
      average chunk length: {self._chunk_tracker.get_chunk_avg_length()}
      number of tokens: {self._chunk_tracker.get_total_token_count()}
      number of chunks: {self._chunk_tracker.get_total_token_count()}
    """)