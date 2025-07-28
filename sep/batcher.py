from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
import time
from typing import cast

from sep.json_helper import JsonHelper

logging.basicConfig(
    filename='embed_errors.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
  
# TODO: maybe abstract further to include other parameters to batch based on e.g., requests per minute
class Batcher:
  """given a list of chunks, batches the chunks into lists of chunks based on how many tokens can be sent in per minute\n
  some function (like embedding) can be run on each chunk in parallel within the batch
  """
  _max_tokens_per_minute: int
  
  def __init__(self, max_tpm: int):
    self._max_tokens_per_minute = max_tpm
  
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
            logging.error(f'Exception in batch {i0}, chunk {i1}; {future.exception()}', exc_info=True)
            # break
      
      time_passed = time.time() - start
      time.sleep(max(0, 60 - time_passed))