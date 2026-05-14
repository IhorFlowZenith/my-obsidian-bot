"""Logging configuration"""

import logging
from src.config import get_config

config = get_config()


def setup_logger(name: str) -> logging.Logger:
    """Setup logger for a module"""
    
    logger = logging.getLogger(name)
    logger.setLevel(config.LOG_LEVEL)
    
    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(config.LOG_LEVEL)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger
