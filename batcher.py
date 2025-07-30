from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging_helper import LoggingMixin
import os
import time
from typing import cast

from json_helper import JsonHelper

class BatcherFactory:
  @staticmethod
  def from_max_tpm(max_tpm: int):
    return _BatcherMaxTPM(max_tpm)
  
  @staticmethod
  def from_batch_size(batch_size: int):
    return _BatcherBatchSize(batch_size)

class _Batcher(ABC, LoggingMixin):
  """
  given a list of chunks, batches the chunks into lists of chunks based on how many
  tokens can be sent in per minute or the batch size\n
  some function (like embedding) can be run on each chunk in parallel within the batch
  """
  
  def __init__(self):
    self.logger = self.set_up_logging(filename="batch.log")
  
  @abstractmethod
  def get_batches(self, items: Generator[dict]) -> Generator[list[dict]]:
    pass
  
  # TODO: fix inconsistency with higher order function parameter naming (fn vs. process, etc.)
    # if i'm passing a higher order function into a higher order function, there becomes a conflict
  def run_process_on_each_batch(self, batches: list[list[dict]], fn: Callable, **kwargs):
    """runs some function on each chunk in a batch, in parallel
        
    Args:
        batches (list[list[dict]]): list of batches (each batch is a list of chunks)
        fn (Callable): function to be run on each chunk (function must consume a chunk)
    """
    for i0, batch in enumerate(batches, 1):
      start = time.time()
      num_chunks_in_batch = len(batch)
      
      with ThreadPoolExecutor(max_workers=num_chunks_in_batch) as executor:
        futures = [
          (executor.submit(
            fn,
            chunk,
            **kwargs
          ))
        for chunk in batch]
          
        for i1, future in enumerate(as_completed(futures), 1):
          try:
            future.result()
            print(f'{i1}/{num_chunks_in_batch} chunks in batch {i0}/{len(batches)}')
          except Exception:
            self.logger.error(f'Exception in batch {i0}, chunk {i1}; {future.exception()}', exc_info=True)
            # break
      
      time_passed = time.time() - start
      time.sleep(max(0, 60 - time_passed))

class _BatcherBatchSize(_Batcher):
  def __init__(self, batch_size: int):
    super().__init__()
    self._batch_size = batch_size
  
  # TODO: maybe it makes more sense for these to be static methods
  def get_batches(self, items: Generator[dict]) -> Generator[list[dict]]:
    batch = []
    
    for vector in items:
      batch.append(vector)
      
      if (len(batch) >= self._batch_size):
        yield batch
        batch = []
        
    # final partial batch
    if batch:
      yield batch

class _BatcherMaxTPM(_Batcher):
  def __init__(self, max_tpm: int):
    super().__init__()
    self._max_tokens_per_minute = max_tpm
  
  # TODO: rework to use generators (more efficient & would match parent function signature)
    # also pretty clunky that this takes in a filepath - that should taken care of separately
    # and this class should only handle the batching based on files
  def get_batches(self, base_read_filepath: str) -> list[list[dict]]:
    current_tokens = 0
    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    
    # TODO: maybe abstract into JsonHelper read + process function
    for file in os.listdir(base_read_filepath):
      read_filepath = os.path.join(base_read_filepath, file)
      chunk = cast(dict, JsonHelper.load_file(read_filepath))
      
      chunk_tokens = chunk['num_tokens']
      
      if (current_tokens + chunk_tokens) > self._max_tokens_per_minute:
        batches.append(current_batch)
        current_tokens = chunk_tokens
        current_batch = [chunk]
      else:
        current_batch.append(chunk)
        current_tokens += chunk_tokens
    
    if current_batch:
      batches.append(current_batch)
    
    return batches