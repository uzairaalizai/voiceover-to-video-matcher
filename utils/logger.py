"""Logging utilities."""
import logging
import os
from datetime import datetime
from utils.config import Config

class Logger:
    """Custom logger for the application."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        
        self.logger = logging.getLogger('voiceover-matcher')
        self.logger.setLevel(logging.DEBUG if Config.DEBUG else logging.INFO)
        
        # File handler
        log_file = os.path.join(
            Config.LOGS_DIR,
            f"voiceover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if Config.VERBOSE else logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self._initialized = True
    
    def get_logger(self):
        """Get the logger instance."""
        return self.logger


def get_logger():
    """Get or create logger."""
    return Logger().get_logger()
