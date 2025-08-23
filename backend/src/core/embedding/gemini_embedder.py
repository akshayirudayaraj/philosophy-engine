import os
from google import genai
from google.genai import types, Client
from google.oauth2 import service_account
from dotenv import load_dotenv

from core.embedding.embedder import DenseEmbedder
from shared_types import Chunk, Embedding, VectorMetadata

load_dotenv('./.env')

class GeminiEmbedder(DenseEmbedder):
  CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
  CLOUD_REGION = os.getenv('GOOGLE_CLOUD_LOCATION')
  EMBEDDING_MODEL_ID = 'gemini-embedding-001'
  
  _client: Client
    
  def __init__(self, output_dim: int, task_type: str):
    service_account_credentials_path = None
    if (os.getenv('ENVIRONMENT') == 'production'):
      service_account_credentials_path = os.getenv('GC_SERVICE_ACCOUNT_CREDENTIALS_FILEPATH')
  
    if service_account_credentials_path is not None:
      sa_credentials = service_account.Credentials.from_service_account_file(service_account_credentials_path).with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
    else:
      sa_credentials = None
    
    super().__init__(
      model_id=self.EMBEDDING_MODEL_ID,
      output_dim=output_dim,
      task_type=task_type,
      config={
        'vertexai': True,
        'project': self.CLOUD_PROJECT_ID,
        'location': self.CLOUD_REGION,
        'credentials': sa_credentials,
      },
    )
    
    self._client = genai.Client(**self._config)
    
  def embed(self, text: str, title: str = "") -> list[float]:
    embedding = self._client.models.embed_content(
      model=self._model_id,
      contents=text,
      config=types.EmbedContentConfig(
        title=title,
        task_type=self._task_type,
        output_dimensionality=self._dense_output_dimensionality,
        auto_truncate=False,
      )
    )
    
    if embedding is None:
      raise ValueError("The embedding is empty!")
    elif embedding.embeddings is None:
      raise ValueError("There's no embedding list in the embedding object!")
    elif len(embedding.embeddings) > 1:
      raise ValueError("There shouldn't be more than one set of embeddings in the object!")
    elif (chunk_embedding_values := embedding.embeddings[0].values) is None: # yay python!
      raise ValueError("No embedding values!")
    
    normalized_embeddings = self.normalize(chunk_embedding_values) # manually needed for the 768 and 1536 dimensions
    
    return normalized_embeddings

  def embed_text_in_dict(self, chunk: Chunk) -> Embedding:
    title = chunk['title']
    text = chunk['content']
    
    values = self.embed(text=text, title=title)
      
    vector_metadata: VectorMetadata = {
      **chunk['text_metadata'], # yay python!
      'title': title,
      'headers': chunk['headers'],
      'num_tokens': chunk['num_tokens'],
    }
      
    return {
      'id': chunk['id'],
      'values': values,
      'metadata': vector_metadata,
    }