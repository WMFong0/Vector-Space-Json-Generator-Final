import logging  
from logging.handlers import RotatingFileHandler  
  
def setup_logger(name, log_file='project.log', level=logging.INFO):  
    """  
    Sets up a logger with a rotating file handler.  
    """  
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')  
  
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding='utf-8')  
    handler.setFormatter(formatter)  
    handler.setLevel(level)  
  
    stream_handler = logging.StreamHandler()  
    stream_handler.setFormatter(formatter)  
    stream_handler.setLevel(logging.INFO)  
  
    logger = logging.getLogger(name)  
    logger.setLevel(level)  
    logger.addHandler(handler)  
    logger.addHandler(stream_handler)  
    logger.propagate = False  
    return logger  
  
# Example usage in other modules:  
# logger = setup_logger(__name__)  