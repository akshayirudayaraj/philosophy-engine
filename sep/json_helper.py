import json

class JsonHelper:
  @staticmethod
  def load_file(filepath: str) -> dict:
    with open(filepath, 'r') as file:
      article = json.load(file)
      return article
  
  @staticmethod
  def write_dict_to_json(dict: dict, filepath: str) -> None:
    with open(filepath + '.json', 'w') as file:
      json.dump(dict, file, indent=4, ensure_ascii=False)