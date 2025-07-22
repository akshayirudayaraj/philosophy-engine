from typing import TypedDict

class Section(TypedDict):
  header_tree: list[str]
  text: str

class Article(TypedDict):
  id: str
  title: str
  authors: str | list[str]
  editors: str | list[str] | None
  original_date: str
  revision_date: str | None
  link: str
  content: list[Section]
  bibliography: list[str]