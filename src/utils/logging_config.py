"""Logging configuration for the Alert Analysis System."""

import logging
import sys
from typing import Optional


def configure_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Configure logging for the Alert Analysis System.
    
    Args:
        log_file: Path to the log file (if None, logs to console only)
        level: Logging level (default: INFO)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
