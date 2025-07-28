import json
from typing import Any, cast
from collections.abc import Callable, Mapping
from shared_types import Article
import os

class JsonHelper:
  @staticmethod
  def _load_file(filepath: str) -> dict:
    fp = os.path.join(os.getcwd(), filepath)
    with open(fp, 'r') as file:
        d = json.load(file)
        return d
  
  @staticmethod
  def load_file(filepath: str, root=None) -> dict:
    if root is None:
      return JsonHelper._load_file(filepath)
    else:
      fp = os.path.join(root, filepath)
      return JsonHelper._load_file(fp)
    
  @staticmethod
  def load_article(filepath: str) -> Article:
    return cast(Article, JsonHelper.load_file(filepath))
  
  @staticmethod
  def write_dict_to_json(dict: Mapping[str, Any], filepath: str) -> None:
    fp = os.path.join(os.getcwd(), filepath)
    with open(fp + '.json', 'w') as file:
      json.dump(dict, file, indent=4, ensure_ascii=False)
  
  @staticmethod
  def read_process_write(read_directory: str, write_directory: str, process: Callable[..., Mapping[str, Any] | list[Mapping[str, Any]]], **kwargs) -> None:
    for idx, file in enumerate(os.listdir(read_directory), 1):
      print(f'{idx}')
      
      content = JsonHelper.load_file(file, read_directory)
      
      print(f'Read {file} from {read_directory}')
      
      processed = process(content, **kwargs)
      
      print(f'Processed {file}')
      
      items_to_write = processed if isinstance(processed, list) else [processed]
      
      for processed_file in items_to_write:
        JsonHelper.write_dict_to_json(processed_file, os.path.join(write_directory, processed_file['id']))
        print(f'Wrote {file} to {write_directory}')