import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json

from backend.config import settings

def setup_logging():    
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(settings.LOG_DIR, f"medical_chatbot_{current_date}.log")
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    logger.handlers = []
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create a file handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
                
            return json.dumps(log_record)
    
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    file_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger