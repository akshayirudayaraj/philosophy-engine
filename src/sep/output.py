from FlagEmbedding import FlagReranker

from core.storage.pinecone_helper import PineconeDB
from core.embedding.gemini_embedder import GeminiEmbedder
from core.prompting.prompt_handler import PromptHandlerFactory, LargeLanguageModels

def main():
  user_query = "To what extent, if any, does free will exist?"

  gemini_embedder = GeminiEmbedder(output_dim=1536, task_type='RETRIEVAL_QUERY')
  query_vector = gemini_embedder.embed(user_query)
  
  pinecone = PineconeDB.from_environment()
  
  result = pinecone.query(query_vector, num_res_to_retrieve=30, namespace='better_article_data')
  top_k_vectors = result['matches']
  print(f'usage: {result['usage']}')
  
  prompt_handler = PromptHandlerFactory.create_prompt_handler(LargeLanguageModels.GPT_5)
  
  top_k_docs = prompt_handler.get_matched_docs_from_vector_metadata(top_k_vectors)
  reranker = FlagReranker('BAAI/bge-reranker-v2-m3')
  cross_encoder_scores = [{
    'score': reranker.compute_score((user_query, doc['text']), normalize=True),
    'doc': { # includes metadata
      **doc,
    }, 
  } for doc in top_k_docs]
  
  sorted_cross_encoder_scores = sorted(cross_encoder_scores, key=lambda rank: rank['score'])
  
  num_sections_for_context = 12
  prompt = prompt_handler.construct_prompt(user_query, [rank['doc'] for rank in sorted_cross_encoder_scores[:num_sections_for_context]])
  prompt_handler.prompt_model(prompt)
  
if __name__ == '__main__':
  main()