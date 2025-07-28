from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, cast
import numpy as np

class DenseEmbedder(ABC):
  _dense_output_dimensionality: int
  _model_id: str
  _config: dict[str, str]
  _task_type: str | None
  
  def __init__(self, model_id: str, output_dim: int, config: dict[str, Any], task_type=None):
    self._model_id = model_id
    self._dense_output_dimensionality = output_dim
    self._config = config
    self._task_type = task_type
    
  def normalize(self, embeddings: list[float]) -> list[float]:
    vec = np.array(embeddings)
    norm = np.linalg.norm(vec)
    normalized_vectors = vec / norm
    normalized_vectors_list = normalized_vectors.tolist()
    return cast(list[float], normalized_vectors_list)
    
  @abstractmethod
  def embed_text_in_dict(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
    pass
  
  @abstractmethod
  def embed(self, data: str, **kwargs) -> list[float]:
    pass