import os
import sqlite3
from typing import Any

# TODO: future proof this for when i need more than one database to interact with
class SqliteHelper:
  _db_instance = None
  
  def __new__(cls, db_name: str): # runs before __init__
    if cls._db_instance is None:
      cls._db_instance = super().__new__(cls) # manually allocates memory for this object
              # ensures that memory is only allocated once bc calling the constructor would allocate new memory
      print(f"Connecting to {os.path.join(os.getcwd(), db_name)}")
      cls._connection = sqlite3.connect(os.path.join(os.getcwd(), db_name))
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