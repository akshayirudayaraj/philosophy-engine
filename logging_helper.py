import logging

class LoggingMixin: # trying a mixin here so i can enforce that each logger's name is its class
  def set_up_logging(self, filename: str):
    logger = logging.getLogger(self.__class__.__name__)
      
    if not logger.handlers:
      handler = logging.FileHandler(filename)
      handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
      logger.addHandler(handler)
      logger.setLevel(logging.INFO)
    
    return logger