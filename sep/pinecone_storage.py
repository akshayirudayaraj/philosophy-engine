from typing import cast, Generator
from pinecone import Vector
from file_helper import JsonHelper
import os
from storage.pinecone_helper import PineconeDB

def main():  
  read_directory = os.path.join('data', 'sep', 'embeddings')
  pinecone = PineconeDB.from_environment()
  
  vectors = JsonHelper.process_files(read_directory=read_directory, fn=PineconeDB.process_and_clean_vector)
  pinecone.upsert_all_vectors(cast(Generator[Vector], vectors)) # FIXME: type checker confusion about Vector & dict
  
  # pc = Pinecone(PINECONE_API_KEY)
  # index = pc.Index(host=PC_INDEX, 
  #                  pool_threads=10)
    
  # with index: # generators are so cool!
  #   vectors = process_vectors()
  #   batches = fast_chunker(vectors)
    
  #   for batch in batches:
      # futures = [index.upsert(cast(list[Vector], batch), async_req=True, show_progress=True)]
      
      # for future in futures: # using ignores here bc i'm following docs (future.get() should raise on error)
      #   try:
      #     future.get() # type: ignore
      #   except Exception:
      #     logging.error(f"Error upserting {future.get()}") # type: ignore
  
if __name__ == '__main__':
  main()