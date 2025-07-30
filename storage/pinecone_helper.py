from collections.abc import Generator
from typing import cast
from json_helper import JsonHelper
from shared_types import Embedding
from batcher import BatcherFactory
from logging_helper import LoggingMixin
import os
from pinecone import Pinecone, Vector

class PineconeDB(LoggingMixin):
  MAX_VECTOR_SIZE_BYTES = 40_960
  
  # TODO: probably allow more flexibility using **kwargs (would make the user put in pool_threads)
  def __init__(self, api_key: str, index: str, batch_size: int = 100, pool_threads: int = 10):
    self.pc = Pinecone(api_key=api_key)
    self._index = self.pc.Index(
      host=index,
      pool_threads=pool_threads
    )
    
    self._batch_size = batch_size
    self.logger = self.set_up_logging(filename='pinecone.log')
  
  @classmethod
  def from_environment(cls, **kwargs):
    return cls(
      api_key=cast(str, os.getenv('PINECONE_API_KEY')),
      index=cast(str, os.getenv('PC_INDEX')),
      **kwargs,
    )

  def upsert_all_vectors(self, vectors: Generator[Vector]):
    with self._index: # generators are cool!
      batcher = BatcherFactory.from_batch_size(batch_size=self._batch_size)
      batches = batcher.get_batches(cast(Generator[dict], vectors)) # FIXME: manual casting, weird type issues
    
    for batch in batches:
      self.upsert_vector_batch(batch)

  def upsert_vector_batch(self, batch: list[dict]):
    futures = [self._index.upsert(cast(list[Vector], batch), async_req=True, show_progress=True)]
      
    for future in futures: # using ignores here bc i'm following docs (future.get() should raise on error)
      try:
        future.get() # type: ignore
      except Exception:
        self.logger.error(f"Error upserting {future.get()}") # type: ignore

  def process_and_clean_vector(self, v: dict) -> Embedding:
    '''
    removes `revised_date` from metadata if empty,
    reduces bibliography size so that the whole vector < 2MB (pinecone requirement),
    removes non-ASCII characters (like special quotes) from `id`
    '''
    
    # v['values'] = cast(list[float], v.pop('embeddings'))
    
    if v['metadata'].get('revised_date') is None:
      del v['metadata']['revised_date']
      
    original_id = v['id']
    cleaned_id = self.remove_non_ascii_fast(v['id'])
    if cleaned_id != original_id:
      v['id'] = cleaned_id # only reassign if difference (since most ids don't need cleaning)
    
    PERCENT_TO_KEEP = 70
    while JsonHelper.estimate_size(v) > self.MAX_VECTOR_SIZE_BYTES:
      biblio_len = len(v['metadata']['bibliography'])
      indices_to_keep = int((PERCENT_TO_KEEP/100) * biblio_len)
      
      if (biblio_len > indices_to_keep):
        v['metadata']['bibliography'] = v['metadata']['bibliography'][:indices_to_keep]
      else:
        del v['metadata']['bibliography']
        break
      
    # assumption: no size concerns (vector always under 40kB) if bibliography is removed
    if (JsonHelper.estimate_size(v) > self.MAX_VECTOR_SIZE_BYTES):
      print(f'vec id {v['id']}, {JsonHelper.estimate_size(v)}')
      
    return cast(Embedding, v)
    
  def remove_non_ascii_fast(self, text):
    return text.encode('ascii', 'ignore').decode('ascii')
      

# TODO: will shift architecture a bit to a DatabaseFactory class if I get MySQL/SQLite or Neo4j involved  