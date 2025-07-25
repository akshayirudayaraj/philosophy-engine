from typing import NotRequired, TypedDict

class Section(TypedDict):
  header: list[str]
  text: str
  
class Metadata(TypedDict):
  organization: str
  authors: list[str]
  editors: list[str]
  original_date: str
  revised_date: NotRequired[str | None]
  link: str
  bibliography: list[str]
  
class VectorMetadata(Metadata):
  num_tokens: int
  
class Article(TypedDict):
  id: str
  title: str
  # metadata: Metadata # TODO: make this work - have to refactor scraper, etc. and rerun
  authors: list[str]
  editors: list[str]
  original_date: str
  revision_date: str | None
  link: str
  content: list[Section]
  bibliography: list[str]

class Chunk(TypedDict):
  id: str
  num_tokens: int
  content: str # must be under 1.95k tokens
  title: str # must be 0.05k - 0.98k tokens
  text_metadata: Metadata
  
# makes it easy for Pinecone ingestion
class Embedding(TypedDict):
  id: str
  values: list[float]
  metadata: VectorMetadata