"""File handling utilities for the Alert Analysis System."""

import gzip
import json
import logging
import os
from pathlib import Path
from typing import Iterator, List, Optional, Union, Dict, Any

from src.models import AlertEvent
from src.utils.logging_config import log_event_error


class FileHandler:
    """
    Handles file operations for the Alert Analysis System.

    This class provides functionality to read and parse alert event data from
    compressed or uncompressed JSON files.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize a FileHandler.

        Args:
            logger: Logger to use (default: file_handler logger)
        """
        self.logger = logger or logging.getLogger("file_handler")

    def read_events(self, file_path: Union[str, Path]) -> Iterator[AlertEvent]:
        """
        Read alert events from a file (gzipped or plain JSON).

        Args:
            file_path: Path to the file

        Yields:
            AlertEvent objects parsed from the file

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
            ValueError: If the file is not a valid file
        """
        file_path = Path(file_path)

        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not file_path.is_file():
            error_msg = f"Not a file: {file_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Check if file is gzipped
        is_gzipped = self._is_gzipped(file_path)

        try:
            # Open file with appropriate method
            opener = gzip.open if is_gzipped else open
            mode = 'rt' if is_gzipped else 'r'

            with opener(file_path, mode) as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Parse JSON
                        event_data = json.loads(line)

                        # Create AlertEvent
                        event = AlertEvent.from_json(event_data)
                        yield event

                    except json.JSONDecodeError as e:
                        log_event_error(
                            {"line_number": line_number},
                            "json_decode_error",
                            f"Invalid JSON at line {line_number}: {e}",
                            self.logger
                        )

                    except ValueError as e:
                        log_event_error(
                            event_data if 'event_data' in locals() else {
                                "line_number": line_number},
                            "validation_error",
                            f"Invalid event data at line {line_number}: {e}",
                            self.logger)

        except gzip.BadGzipFile:
            error_msg = f"Not a valid gzip file: {file_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            self.logger.error(error_msg)
            raise

    def read_events_list(self,
                         file_path: Union[str,
                                          Path]) -> List[AlertEvent]:
        """
        Read all alert events from the file into a list.

        Args:
            file_path: Path to the file

        Returns:
            List of AlertEvent objects parsed from the file

        Raises:
            Same exceptions as read_events()
        """
        return list(self.read_events(file_path))

    def _is_gzipped(self, file_path: Union[str, Path]) -> bool:
        """
        Check if the file is gzipped.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is gzipped, False otherwise
        """
        file_path = Path(file_path)

        # Check file extension first
        if file_path.suffix.lower() == '.gz':
            return True

        # Check file magic number
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(2)
                return magic == b'\x1f\x8b'  # gzip magic number
        except IOError:
            return False
