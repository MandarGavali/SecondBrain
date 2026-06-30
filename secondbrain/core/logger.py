import logging
import os
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format: Timestamp | Log Level | Logger Name | Message
        # Example: 2026-06-29 14:52:01 | INFO | retriever | Retrieved 5 documents
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        BASE_DIR = Path(__file__).resolve().parents[2]
        log_dir = BASE_DIR / "logs"
        
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
            
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
