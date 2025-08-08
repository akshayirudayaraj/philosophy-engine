from typing import cast, Generator
from pinecone import Vector
from core.file_helper import JsonHelper
import os
from core.storage.pinecone_helper import PineconeDB

def main():  
  read_directory = os.path.join('data', 'sep_v2', 'embeddings')
  pinecone = PineconeDB.from_environment()
  
  vectors = JsonHelper.process_files(read_directory=read_directory, fn=pinecone.process_and_clean_vector)
  pinecone.upsert_all_vectors(cast(Generator[Vector], vectors), namespace="better_article_data") # FIXME: type checker confusion about Vector & dict
  
if __name__ == '__main__':
  main()