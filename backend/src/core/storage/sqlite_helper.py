from collections.abc import Generator
import sqlite3

import os

from shared_types import Article

# TODO: future proof this for when i need more than one database to interact with
class SqliteHelper:
  _db_instance = None
  
  def __new__(cls, db_name: str): # runs before __init__
    if cls._db_instance is None:
      cls._db_instance = super().__new__(cls) # manually allocates memory for this object
              # ensures that memory is only allocated once bc calling the constructor would allocate new memory
      db_path = os.path.join(os.getcwd(), 'data', db_name)
      print(f"Connecting to {db_path}")
      cls._connection = sqlite3.connect(db_path)
      cls._cursor = cls._connection.cursor()
      
    return cls._db_instance
  
  def create_table_if_not_created(self, table_name: str, *table_cols):
    tables_with_name = self.execute_selection(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if len(tables_with_name) == 0:
      self.execute_change(f"CREATE TABLE {table_name} ({",".join(table_cols)});")
  
  def execute_change(self, cmd: str, *args) -> None:
    self._cursor.execute(cmd, *args)
    self._connection.commit()
  
  def execute_selection(self, cmd: str) -> list:
    results = self._cursor.execute(cmd)
    return results.fetchall()
  
  def close_connection(self):
    self._connection.close()
    
class ArticleStorage:
  """ 
  article_metadata -> stores id, title, and other metadata\n
  - authors and editors are joined by commas into a string, bibliography is joined by newlines\n
  article_content -> stores id, header_tree_name, text_associated, where there are multiple entries for each id since there are multiple sections in each article
  """
  def __init__(self, sqlite_wrapper: SqliteHelper):
    self._sqlite_interface = sqlite_wrapper
  
  # FIXME: make less ugly if possible
  def create_article_content_and_metadata_tables(self):
    self._sqlite_interface.create_table_if_not_created(
      "article_metadata",
      "id TEXT PRIMARY KEY",
      "title TEXT NOT NULL",
      "organization TEXT NOT NULL",
      "intro TEXT",
      "authors TEXT NOT NULL",
      "editors TEXT",
      "original_date_published TEXT NOT NULL",
      "date_revised TEXT",
      "link TEXT NOT NULL",
      "bibliography TEXT"
    )

    self._sqlite_interface.create_table_if_not_created(
      "article_content",
      "section_id TEXT PRIMARY KEY",
      "associated_article_id INTEGER NOT NULL",
      "header_list TEXT NOT NULL",
      "content TEXT NOT NULL",
      "FOREIGN KEY (associated_article_id) REFERENCES article_metadata(id) ON DELETE CASCADE"
    )
  
  def store_article_dictionaries(self, data: Generator[Article]):
    for idx, datum in enumerate(data, 1):
      formatted_datum = self._format_article_for_db(datum)
      self._insert_article_metadata(formatted_datum)
      self._insert_article_content(datum)
      print(f'finished storing article {datum['title']}, #{idx}')
        
  def _insert_article_metadata(self, formatted_datum: dict):
    self._sqlite_interface.execute_change("""
                        INSERT OR REPLACE 
                        INTO article_metadata
                        VALUES (
                          :id, :title, :organization, :intro, :authors, :editors, :original_date,
                          :revised_date, :link, :bibliography
                        );
                        """, formatted_datum)
    
  def _insert_article_content(self, datum: Article):
    for section in datum['content']:
        deepest_header = section['header'][-1]
        section_id = datum['id'] + '-' + deepest_header.lower().replace(' ', '-').replace('/', '-')
        header_list = ",".join(section['header'])
        
        self._sqlite_interface.execute_change("""
                          INSERT OR REPLACE
                          INTO article_content
                          VALUES (?, ?, ?, ?);
                          """, (section_id, datum['id'], header_list, section['text']))

  def _format_article_for_db(self, datum: Article) -> dict:
    return {
        'id': datum['id'], # NEVER CHANGE otherwise cross-referencing will break
        'title': datum['title'],
        'organization': datum['metadata']['organization'],
        'intro': datum['metadata']['intro'],
        'authors': ",".join(datum['metadata']['authors']),
        'editors': ",".join(datum['metadata']['editors']),
        'original_date': datum['metadata']['original_date_published'],
        'revised_date': datum['metadata']['revision_date'],
        'link': datum['metadata']['link'],
        'bibliography': '\n'.join(datum['metadata']['bibliography'])
    }