from core.storage.pinecone_helper import PineconeDB
from core.embedding.gemini_embedder import GeminiEmbedder
from core.prompting.prompt_handler import PromptHandler, LargeLanguageModels

def main():
  user_query = "To what extent, if any, can a machine be considered conscious?"
  
  gemini_embedder = GeminiEmbedder(output_dim=1536, task_type='RETRIEVAL_QUERY')
  query_vector = gemini_embedder.embed(user_query)
  
  pinecone = PineconeDB.from_environment()
  
  results = pinecone.query(query_vector, num_res_to_retrieve=10)    
  print(f'usage: {results['usage']}')
  
  prompt_handler = PromptHandler(LargeLanguageModels.CLAUDE_HAIKU_3_5)
  prompt = prompt_handler.construct_prompt(user_query, results)
  prompt_handler.prompt_model(prompt)
  
if __name__ == '__main__':
  main()