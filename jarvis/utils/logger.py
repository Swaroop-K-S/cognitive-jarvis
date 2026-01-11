import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str = "BRO") -> logging.Logger:
    """
    Sets up a logger with console and file handlers.
    
    Args:
        name: The name of the logger (module name usually)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, assume it's configured to prevent duplicates
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # 1. Console Handler (Info+ only to keep it clean)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s') # Minimal for console
    console_handler.setFormatter(console_format)
    
    # 2. File Handler (Debug+, rotating)
    log_file = os.path.join(LOG_DIR, "bro.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
base_logger = setup_logger()
