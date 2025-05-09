"""File handling utilities for the Alert Analysis System."""

import gzip
import json
import logging
from pathlib import Path
from typing import Iterator, List, Optional, Union

from src.models import AlertEvent


class FileHandler:
    """
    Handles file operations for the Alert Analysis System.
    
    This class provides functionality to read and parse alert event data from
    compressed or uncompressed JSON files.
    """
    
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize a FileHandler.
        
        Args:
            file_path: Path to the file to be processed
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        # Check if file is readable
        if not self.file_path.is_file():
            raise ValueError(f"Not a file: {self.file_path}")
        
        # Check if we have read permission
        try:
            with open(self.file_path, 'rb') as _:
                pass
        except PermissionError:
            raise PermissionError(f"Permission denied: {self.file_path}")
    
    def read_events(self) -> Iterator[AlertEvent]:
        """
        Read and parse alert events from the file.
        
        Yields:
            AlertEvent objects parsed from the file
            
        Raises:
            IOError: If there's an error reading the file
            json.JSONDecodeError: If the file contains malformed JSON
            ValueError: If an event has invalid or missing fields
        """
        try:
            # Check if file is gzipped
            is_gzipped = self._is_gzipped()
            
            # Open file with appropriate method
            opener = gzip.open if is_gzipped else open
            
            with opener(self.file_path, 'rt', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue  # Skip empty lines
                    
                    try:
                        # Parse JSON and create AlertEvent
                        event_data = json.loads(line)
                        yield AlertEvent.from_json(event_data)
                    except json.JSONDecodeError as e:
                        # Add line number to error message
                        error_msg = f"JSON decode error at line {line_num}: {e}"
                        logging.error(error_msg)
                        raise json.JSONDecodeError(
                            msg=error_msg,
                            doc=line,
                            pos=e.pos
                        )
                    except ValueError as e:
                        # Log validation errors but continue processing
                        logging.warning(f"Skipping invalid event at line {line_num}: {e}")
        except gzip.BadGzipFile:
            error_msg = f"Invalid or corrupt gzip file: {self.file_path}"
            logging.error(error_msg)
            raise IOError(error_msg)
        except IOError as e:
            error_msg = f"Error reading file {self.file_path}: {e}"
            logging.error(error_msg)
            raise
    
    def read_events_list(self) -> List[AlertEvent]:
        """
        Read all alert events from the file into a list.
        
        Returns:
            List of AlertEvent objects parsed from the file
            
        Raises:
            Same exceptions as read_events()
        """
        return list(self.read_events())
    
    def _is_gzipped(self) -> bool:
        """
        Check if the file is gzipped.
        
        Returns:
            True if the file is gzipped, False otherwise
        """
        # Check file extension first
        if self.file_path.suffix.lower() == '.gz':
            return True
        
        # Check file magic number
        try:
            with open(self.file_path, 'rb') as f:
                magic = f.read(2)
                return magic == b'\x1f\x8b'  # gzip magic number
        except IOError:
            return False
