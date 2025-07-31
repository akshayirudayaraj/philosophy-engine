import json
from typing import Any, cast
from collections.abc import Callable, Generator, Mapping
from shared_types import Article
import os

class MalformedJson(Exception):
  pass

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
  
  # TODO: make directory passed in consistent with other functions (optional root dir)
  @staticmethod
  def load_files(read_directory: str) -> Generator[dict]:
    for file in os.listdir(read_directory):
      yield JsonHelper._load_file(file)
  
  # TODO: think about if it's possible to somehow pass in the type here so that the output is compatible
  # with other helper functions without manual casting
  @staticmethod
  def process_files(read_directory: str, fn: Callable[..., Mapping[str, Any]], **kwargs) -> Generator[Mapping[str, Any]]:
    for file in os.listdir(read_directory):
      content = JsonHelper._load_file(os.path.join(read_directory, file))
      processed = fn(content, **kwargs)
      yield processed
  
  @staticmethod
  def write_dict_to_json(dict: Mapping[str, Any], filepath: str) -> None:
    fp = os.path.join(os.getcwd(), filepath)
    with open(fp + '.json', 'w') as file:
      json.dump(dict, file, indent=4, ensure_ascii=False)
  
  # TODO: probably restructure the below methods because when calling the functions,
  # it's unclear that `data`` will be passed into `process`
  @staticmethod
  def read_process_write(read_directory: str, write_directory: str, process: Callable[..., Mapping[str, Any] | list[Mapping[str, Any]]], **kwargs) -> None:
    """reads JSONs from a directory, performs some process on each JSON, and writes to another directory\n
    if the process results in multiple dictionaries being created (list of dict), each one is written to a separate file
    
    Args:
        read_directory (str): directory to read from
        write_directory (str): directory to write to (filename is the 'id' field)
        process (Callable[..., Mapping[str, Any]  |  list[Mapping[str, Any]]]): function to be run on each JSON (must consume a dict)
  
    Raises:
        MalformedJson: no id in the file passed in -- using it for logging purposes  
    """
    for idx, file in enumerate(os.listdir(read_directory), 1):
      print(f'{idx}')
      
      content = JsonHelper.load_file(file, read_directory)
      
      print(f'Read {file} from {read_directory}')
      
      processed = process(content, **kwargs)
      
      print(f'Processed {file}')
      
      items_to_write = processed if isinstance(processed, list) else [processed]
      
      for processed_file in items_to_write:
        if 'id' not in processed_file:
          raise MalformedJson("every JSON object should have some ID associated with it!")
        
        JsonHelper.write_dict_to_json(processed_file, os.path.join(write_directory, processed_file['id']))
        print(f'Wrote {file} to {write_directory}')
  
  # TODO: prevent duplicate code
  @staticmethod
  def process_and_write(write_directory: str, data: dict, process: Callable[..., Mapping[str, Any] | list[Mapping[str, Any]]], **kwargs):
    """processes a JSON and writes to a directory\n
    if the process results in multiple dictionaries being created (list of dict), each one is written to a separate file

    Args:
        write_directory (str): directory to be written to
        data (dict): dictionary / JSON
        process (Callable[..., Mapping[str, Any]  |  list[Mapping[str, Any]]]): function to be run on each JSON (must consume a dict)

    Raises:
        MalformedJson: no id in the file passed in -- using it for logging purposes
    """
    processed = process(data, **kwargs)
    
    if 'id' not in data:
      raise MalformedJson("every JSON object should have some ID associated with it!")
      
    print(f'Processed {data['id']}')
    
    items_to_write = processed if isinstance(processed, list) else [processed]
    
    for processed_file in items_to_write:
      JsonHelper.write_dict_to_json(processed_file, os.path.join(write_directory, processed_file['id']))
      print(f'Wrote {data['id']} to {write_directory}')
      
  @staticmethod
  def estimate_size(vector: dict):
    return len(json.dumps(vector, ensure_ascii=False).encode('utf-8'))
  
class MdHelper:
  @staticmethod
  def write_to_md(filename: str, text: str):
    with open(filename + '.md', 'w') as file:
      file.write(text)