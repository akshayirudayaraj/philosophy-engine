import sentencepiece as spm
import os

class Tokenizer:
  def __init__(self, model_path: str):
    assert os.path.exists(model_path), 'Unable to find model!'

    self._tokenizer = spm.SentencePieceProcessor()
    self._tokenizer.LoadFromFile(model_path)
  
  def encode(self, text: str) -> list[str]:
    return self._tokenizer.Encode(text, out_type=str)

  def decode(self, tokens: list[str]) -> str:
    return self._tokenizer.Decode(tokens)
  
  def count_tokens(self, text: str) -> int:
    encoded_text = self.encode(text)
    return len(encoded_text)