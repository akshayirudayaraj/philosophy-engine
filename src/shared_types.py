from typing import NotRequired, TypedDict

class Section(TypedDict):
  header: list[str]
  text: str

class Metadata(TypedDict):
  organization: str
  intro: str # either a preamble for SEP or abstract for papers
  authors: list[str]
  editors: list[str]
  original_date: str
  revised_date: NotRequired[str | None]
  link: str
  bibliography: list[str]
  
class VectorMetadata(Metadata):
  title: str
  headers: list[str]
  num_tokens: int
  
class Article(TypedDict):
  id: str
  title: str
  content: list[Section]
  metadata: Metadata

class Chunk(TypedDict):
  id: str
  num_tokens: int
  text_metadata: Metadata
  content: str # must be under 1.95k tokens
  # must be 0.05k - 0.98k tokens
  title: str
  headers: list[str]
  
# makes it easy for Pinecone ingestion
# TODO: probably transition to Pinecone's very own Vector dataclass
class Embedding(TypedDict):
  id: str
  values: list[float]
  metadata: VectorMetadata