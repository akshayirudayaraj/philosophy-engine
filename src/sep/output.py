from core.storage.pinecone_helper import PineconeDB
from core.embedding.gemini_embedder import GeminiEmbedder
from core.prompting.prompt_handler import PromptHandlerFactory, LargeLanguageModels

def main():
  user_query = "To what extent, if any, can a machine be considered conscious?"
  
  gemini_embedder = GeminiEmbedder(output_dim=1536, task_type='RETRIEVAL_QUERY')
  query_vector = gemini_embedder.embed(user_query)
  
  pinecone = PineconeDB.from_environment()
  
  result = pinecone.query(query_vector, num_res_to_retrieve=10, namespace='better_article_data')    
  top_k_vectors = result['matches']
  print(f'usage: {result['usage']}')
  
  prompt_handler = PromptHandlerFactory.create_prompt_handler(LargeLanguageModels.GPT_5, max_response_words=5000)
  prompt = prompt_handler.construct_prompt(user_query, top_k_vectors)
  prompt_handler.prompt_model(prompt)
  
if __name__ == '__main__':
  main()