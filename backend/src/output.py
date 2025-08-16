from typing import cast

from FlagEmbedding import FlagReranker

from core.storage.pinecone_helper import PineconeDB
from core.embedding.gemini_embedder import GeminiEmbedder
from core.prompting.prompt_handler import PromptHandlerFactory, LargeLanguageModels
from api.models import Document

async def get_model_output_from_query(user_query: str) -> tuple[list[Document], str]:  
  gemini_embedder = GeminiEmbedder(output_dim=1536, task_type='RETRIEVAL_QUERY')
  query_vector = gemini_embedder.embed(user_query)
  
  pinecone = PineconeDB.from_environment()
  
  result = pinecone.query(query_vector, num_res_to_retrieve=30, namespace='better_article_data')
  top_k_vectors = result['matches']
  print(f'usage: {result['usage']}')
  
  prompt_handler = PromptHandlerFactory.create_prompt_handler(LargeLanguageModels.GPT_5)
  
  top_k_docs = prompt_handler.get_matched_docs_from_vector_metadata(top_k_vectors)
  reranked_top_k_docs = rerank(top_k_docs, user_query)
  
  num_sections_for_context = 12
  docs_for_context = reranked_top_k_docs[:num_sections_for_context]
  prompt = prompt_handler.construct_prompt(user_query, docs_for_context)
  model_output = await prompt_handler.prompt_model(prompt)
  
  return docs_for_context, model_output

def rerank(docs: list[Document], user_query: str) -> list[Document]:
  reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
  top_k_docs_and_query = [(user_query, doc.text) for doc in docs]
  cross_encoder_scores = reranker.compute_score([*top_k_docs_and_query], normalize=True) # TODO: add async support
  
  cross_encoder_scores_and_docs = [{
    'score': score,
    'doc': doc,
  } for score, doc in zip(cast(list, cross_encoder_scores), docs)]
  
  reranked_cross_encoder_scores_and_docs = sorted(cross_encoder_scores_and_docs, key=lambda rank: rank['score'])
  reranked_docs = [rank['doc'] for rank in reranked_cross_encoder_scores_and_docs]
  
  return reranked_docs