from collections.abc import Callable, Mapping
import os
from typing import Any, cast

from core.file_helper import JsonHelper
from core.storage.sqlite_helper import SqliteHelper
from core.embedding.chunker import Chunker
from core.embedding.tokenizer import Tokenizer

def main():
  TOKENIZER_MODEL_PATH = os.environ.get('TOKENIZER_MODEL_PATH')
  TOKEN_LIMIT_PER_STRING = 2048
  
  base_filepath = os.path.join(os.getcwd(), 'data', 'sep_v2')
  base_read_filepath = os.path.join(base_filepath, 'articles')
  base_write_filepath = os.path.join(base_filepath, 'chunked_articles')
  
  tokenizer = Tokenizer(str(TOKENIZER_MODEL_PATH))
  chunker = Chunker(token_limit_per_chunk=TOKEN_LIMIT_PER_STRING, tokenizer=tokenizer)
  
  # sqlite_helper = SqliteHelper('sep.db')
  
  JsonHelper.read_process_write(
    read_directory=base_read_filepath,
    write_directory=base_write_filepath,
    process=cast(Callable[..., Mapping[str, Any]], chunker.chunk_article_from_json), # dodgy cast solution but not sure how to get around this
                                                                          # Chunk is a basically a Mapping (immutable dict) at runtime
  )

if __name__ == '__main__':
  main()