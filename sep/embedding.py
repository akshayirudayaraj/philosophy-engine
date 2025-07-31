import os
from embedding.gemini_embedder import GeminiEmbedder
from batcher import BatcherFactory
from file_helper import JsonHelper

def main():
  # client = genai.Client(
  #   vertexai=True,
  #   project=CLOUD_PROJECT_ID,
  #   location=CLOUD_REGION,
  # )
  
  # test_read_filepath = os.path.join(os.getcwd(), 'sep', 'chunked_articles', '18th-century-german-philosophy-prior-to-kant-life-and-works-83b92c37c1.json')
  # test_chunk = cast(Chunk, JsonHelper.load_file(test_read_filepath))
    
  # embedding = embed(client, test_chunk)
    
  # test_write_filepath = os.path.join(os.getcwd(), 'sep', 'embeddings', embedding['id'])
  # JsonHelper.write_dict_to_json(cast(dict, embedding), test_write_filepath)
  
  base_filepath = os.path.join(os.getcwd(), 'data', 'sep')
  base_read_filepath = os.path.join(base_filepath, 'chunked_articles')
  base_write_filepath = os.path.join(base_filepath, 'embeddings')
  
  embedder = GeminiEmbedder(
    output_dim=1536, # can try upleveling to 3072 if issues with retrieval
    task_type='RETRIEVAL_DOCUMENT'
  )
  
  MAX_TOKENS_PER_MINUTE = 200_000 # via vertex API (https://cloud.google.com/vertex-ai/generative-ai/docs/quotas_)
  
  batcher = BatcherFactory.from_max_tpm(MAX_TOKENS_PER_MINUTE)
  batches = batcher.get_batches(base_read_filepath)
  batcher.run_process_on_each_batch(
    batches=batches,
    fn=JsonHelper.process_and_write,
    write_directory=base_write_filepath,
    process=embedder.embed_text_in_dict,
  )

# def embed_and_write(chunk: Chunk, base_write_filepath: str, client: Client):
#   # read_filepath = os.path.join(base_read_filepath, file)
#   # chunk = cast(Chunk, JsonHelper.load_file(read_filepath))
  
#   embedding = embed(client, chunk)
  
#   write_filepath = os.path.join(base_write_filepath, embedding['id'].replace('/', '-'))
#   JsonHelper.write_dict_to_json(cast(dict, embedding), write_filepath)

if __name__ == '__main__':
  main()