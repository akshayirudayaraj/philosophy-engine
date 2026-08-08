from collections.abc import Generator
from typing import cast

import os
from pinecone import Pinecone, QueryResponse, Vector
from dotenv import load_dotenv

from core.file_helper import JsonHelper
from shared_types import Embedding
from core.batcher import BatcherFactory
from core.logging_helper import LoggingMixin

load_dotenv()

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
    # self.logger = self.set_up_logging(filename=os.path.join('logs', 'pinecone.log'))
  
  @classmethod
  def from_environment(cls, **kwargs):
    return cls(
      api_key=cast(str, os.getenv('PINECONE_API_KEY')),
      index=cast(str, os.getenv('PC_INDEX')),
      **kwargs,
    )

  # TODO: add logging
  def upsert_all_vectors(self, vectors: Generator[Vector], namespace: str = '__default__'):
    with self._index: # generators are cool!
      batcher = BatcherFactory.from_batch_size(batch_size=self._batch_size)
      batches = batcher.get_batches(cast(Generator[dict], vectors)) # FIXME: manual casting, weird type issues
    
    for batch in batches:
      self.upsert_vector_batch(batch, namespace)

  def upsert_vector_batch(self, batch: list[dict], namespace: str):
    futures = [self._index.upsert(cast(list[Vector], batch), namespace=namespace, async_req=True, show_progress=True)]
      
    for future in futures: # using ignores here bc i'm following docs (future.get() should raise on error)
      try:
        future.get() # type: ignore
      except Exception:
        print(f'"Error upserting {future.get()}"') # type: ignore
        # self.logger.error(f"Error upserting {future.get()}") # type: ignore

  def process_and_clean_vector(self, v: dict) -> Embedding:
    '''
    removes `revised_date` from metadata if empty,
    reduces bibliography size so that the whole vector < 2MB (pinecone requirement),
    removes non-ASCII characters (like special quotes) from `id`
    '''
    
    # v['values'] = cast(list[float], v.pop('embeddings'))
    
    if v['metadata'].get('revision_date') is None:
      del v['metadata']['revision_date']
      
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
      
    while JsonHelper.estimate_size(v) > self.MAX_VECTOR_SIZE_BYTES:
      intro_len = len(v['metadata']['intro'])
      indices_to_keep = int((PERCENT_TO_KEEP/100) * intro_len)
      
      if (intro_len > indices_to_keep):
        v['metadata']['intro'] = v['metadata']['intro'][:indices_to_keep]
      else:
        del v['metadata']['intro']
        break
      
    # assumption: no size concerns (vector always under 40kB) if bibliography and intro are removed
    if (JsonHelper.estimate_size(v) > self.MAX_VECTOR_SIZE_BYTES):
      print(f'vec id {v['id']}, {JsonHelper.estimate_size(v)}')
      
    return cast(Embedding, v)
    
  def remove_non_ascii_fast(self, text):
    return text.encode('ascii', 'ignore').decode('ascii')
  
  # TODO: add async support
  def query(self, query_vector: list[float], num_res_to_retrieve: int = 10, namespace: str = '__default__') -> QueryResponse:
    results = self._index.query(
      namespace=namespace,
      vector=query_vector,
      top_k=num_res_to_retrieve,
      include_metadata=True,
      include_values=True
    )
    
    if not isinstance(results, QueryResponse):
      raise Exception("retrieved results are not of type QueryResponse from Pinecone")

    return results

  def rerank(self, model: str, query: str, documents: list[str]):
    return self.pc.inference.rerank(
      model=model,
      query=query,
      documents=documents,
      top_n=len(documents),
      return_documents=False,
      parameters={'truncate': 'END'}, # truncate pairs over the model's token limit instead of erroring (local FlagReranker truncated silently)
    )

# TODO: will shift architecture a bit to a DatabaseFactory class if I get MySQL/SQLite or Neo4j involved  