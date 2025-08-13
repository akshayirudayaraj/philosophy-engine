from pydantic import BaseModel # pref'd over TypedDict for actual runtime validation (rather than js type hints)

class Document(BaseModel):
  title: str
  header_tree: str
  link: str
  original_rank: int # FIXME: eventually remove bc this is just for me
  text: str
  
class Input(BaseModel):
  user_query: str

class Output(BaseModel):
  related_documents: list[Document]
  model_output: str