"""Logging configuration for the Alert Analysis System."""

import logging
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional


def configure_logging(log_file: str = "alert_analyzer.log", log_level: int = logging.INFO) -> None:
    """
    Configure logging for the Alert Analysis System.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


class StructuredLogFormatter(logging.Formatter):
    """
    Custom formatter for structured logging in JSON format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string representation of the log record
        """
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", str(uuid.uuid4()))
        }
        
        # Add extra fields if present
        if hasattr(record, "event_id"):
            log_data["event_id"] = record.event_id
        if hasattr(record, "alert_id"):
            log_data["alert_id"] = record.alert_id
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "details"):
            log_data["details"] = record.details
        
        return json.dumps(log_data)


def log_event_error(event: Any, error_type: str, details: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log an error related to an event.
    
    Args:
        event: The event that caused the error
        error_type: Type of error
        details: Error details
        logger: Logger to use (default: root logger)
    """
    if logger is None:
        logger = logging.getLogger()
    
    # Create extra fields for the log record
    extra = {
        "error_type": error_type,
        "event_id": getattr(event, "event_id", None),
        "alert_id": getattr(event, "alert_id", None),
        "details": details,
        "correlation_id": str(uuid.uuid4())
    }
    
    # Log the error
    logger.error(f"Error processing event: {error_type}", extra=extra)


def log_performance_metrics(start_time: datetime, end_time: datetime, events_processed: int, 
                           logger: Optional[logging.Logger] = None) -> None:
    """
    Log performance metrics.
    
    Args:
        start_time: When processing started
        end_time: When processing ended
        events_processed: Number of events processed
        logger: Logger to use (default: root logger)
    """
    if logger is None:
        logger = logging.getLogger()
    
    # Calculate duration and events per second
    duration = (end_time - start_time).total_seconds()
    events_per_second = events_processed / duration if duration > 0 else 0
    
    # Create extra fields for the log record
    extra = {
        "metric_type": "performance",
        "duration_seconds": duration,
        "events_processed": events_processed,
        "events_per_second": events_per_second,
        "correlation_id": str(uuid.uuid4())
    }
    
    # Log the metrics
    logger.info(f"Performance metrics: {events_processed} events in {duration:.2f} seconds "
               f"({events_per_second:.2f} events/sec)", extra=extra)
