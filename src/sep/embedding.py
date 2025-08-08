import os
from core.embedding.gemini_embedder import GeminiEmbedder
from core.batcher import BatcherFactory
from core.file_helper import JsonHelper

def main():
  base_filepath = os.path.join(os.getcwd(), 'data', 'sep_v2')
  base_read_filepath = os.path.join(base_filepath, 'chunked_articles')
  base_write_filepath = os.path.join(base_filepath, 'embeddings')
  
  embedder = GeminiEmbedder(
    output_dim=1536, # can try upleveling to 3072 if issues with retrieval
    task_type='RETRIEVAL_DOCUMENT'
  )
  
  MAX_TOKENS_PER_MINUTE = 200_000 # via vertex API (https://cloud.google.com/vertex-ai/generative-ai/docs/quotas_)
  
  # TODO: investigate request errors in log...embeddings seem to be coming out good
  
  batcher = BatcherFactory.from_max_tpm(MAX_TOKENS_PER_MINUTE)
  batches = batcher.get_batches(base_read_filepath)
  batcher.run_process_on_each_batch(
    batches=batches,
    fn=JsonHelper.process_and_write,
    write_directory=base_write_filepath,
    process=embedder.embed_text_in_dict,
  )

if __name__ == '__main__':
  main()