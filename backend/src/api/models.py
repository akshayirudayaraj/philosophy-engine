from typing import Self

from pydantic import BaseModel # pref'd over TypedDict for actual runtime validation (rather than js type hints)

class Document(BaseModel, frozen=True):
  title: str
  header_tree: str
  link: str
  original_rank: int # FIXME: eventually remove bc this is just for me
  text: str
  
  def __hash__(self):
    return hash("-".join([self.title.lower(), 
                          self.header_tree.lower()]))
  
  def __eq__(self, other: Self) -> bool:
    if not isinstance(other, Document):
      raise Exception("Comparing a document with something of another type")

    return self.header_tree == other.header_tree and self.title == other.title 
  
class Input(BaseModel):
  user_query: str

class Output(BaseModel):
  related_documents: list[Document]
  model_output: str