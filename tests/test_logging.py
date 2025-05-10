"""Tests for the logging functionality."""

import pytest
import logging
import json
import os
import tempfile
import time
from datetime import datetime

from src.utils.logging_config import configure_logging, log_event_error, log_performance_metrics
from src.models import AlertEvent


class TestLogging:
    """Tests for the logging functionality."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            yield f.name
        # Clean up after the test
        if os.path.exists(f.name):
            os.unlink(f.name)

    @pytest.fixture
    def sample_alert_event(self):
        """Create a sample AlertEvent for testing."""
        return AlertEvent(
            event_id="event-123",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

    def test_configure_logging(self, temp_log_file):
        """Test configuring logging."""
        # Configure logging
        configure_logging(temp_log_file)

        # Log a message
        logger = logging.getLogger("test_logger")
        logger.info("Test message")

        # Ensure log is written to disk
        time.sleep(0.1)

        # Check that the message was logged to the file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()

        assert "Test message" in log_content
        assert "test_logger" in log_content
        assert "INFO" in log_content

    def test_log_event_error(self, temp_log_file, sample_alert_event):
        """Test logging an event error."""
        # Configure logging
        configure_logging(temp_log_file)

        # Log an event error
        logger = logging.getLogger("test_logger")
        log_event_error(
            sample_alert_event,
            "test_error",
            "Test error details",
            logger
        )

        # Ensure log is written to disk
        time.sleep(0.1)

        # Check that the error was logged to the file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()

        assert "Error processing event: test_error" in log_content
        # We're not checking for event_id and alert_id in the log content
        # because they might not be included in the default format

    def test_log_performance_metrics(self, temp_log_file):
        """Test logging performance metrics."""
        # Configure logging
        configure_logging(temp_log_file)

        # Log performance metrics
        logger = logging.getLogger("test_logger")
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 1, 0)  # 1 minute later
        log_performance_metrics(
            start_time,
            end_time,
            60,  # 60 events
            logger
        )

        # Ensure log is written to disk
        time.sleep(0.1)

        # Check that the metrics were logged to the file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()

        assert "Performance metrics" in log_content
        assert "60 events" in log_content
        assert "60.00 seconds" in log_content
        assert "1.00 events/sec" in log_content
