from collections.abc import Callable, Mapping
from core.embedding.tokenizer import Tokenizer

from typing import Any, cast

from core.file_helper import JsonHelper
from core.storage.sqlite_helper import SqliteHelper
from core.embedding.chunker import Chunker
import os

# any potential consequences of passing in a title and empty string to the embedding model
# could that meaningfully through things off? can probably just do a little check before embedding

def main():
  TOKENIZER_MODEL_PATH = os.path.join('src', 'core', 'embedding', 'tokenizing_models', 'gemma_tokenizer.model')
  TOKEN_LIMIT_PER_STRING = 2048
  
  base_filepath = os.path.join(os.getcwd(), 'data', 'sep_v2')
  base_read_filepath = os.path.join(base_filepath, 'articles')
  base_write_filepath = os.path.join(base_filepath, 'chunked_articles')
  
  tokenizer = Tokenizer(TOKENIZER_MODEL_PATH)
  chunker = Chunker(token_limit_per_chunk=TOKEN_LIMIT_PER_STRING, tokenizer=tokenizer)
  
  # sqlite_helper = SqliteHelper('sep.db')
  
  JsonHelper.read_process_write(
    read_directory=base_read_filepath,
    write_directory=base_write_filepath,
    process=cast(Callable[..., Mapping[str, Any]], chunker.chunk_article_from_json), # dodgy cast solution but not sure how to get around this
                                                                          # Chunk is a basically a Mapping (immutable dict) at runtime
  )
  
  # for idx, file in enumerate(os.listdir(base_read_filepath), 1):
  #   print("Reading " + file)
    
  #   read_filepath = os.path.join(base_read_filepath, file)
  #   article = JsonHelper.load_article(read_filepath)
    
  #   article_chunks = chunker.chunk_article(article, tokenizer)

  #   for chunk in article_chunks:
  #     write_filepath = os.path.join(base_write_filepath, chunk['id'].replace('/', "-"))
  #     JsonHelper.write_dict_to_json(cast(dict, chunk), write_filepath)
    
  #   print("Wrote " + file)
  #   print(f'{idx}/1840') # 1840 and not 1852 because 12 SEP entries have been retired

if __name__ == '__main__':
  main()