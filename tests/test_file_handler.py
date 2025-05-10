"""Tests for the file handling utilities."""

import gzip
import json
import os
import pytest
import tempfile
from pathlib import Path

from src.utils.file_handler import FileHandler
from src.models import AlertEvent


class TestFileHandler:
    """Tests for the FileHandler class."""

    @pytest.fixture
    def sample_event_data(self):
        """Sample event data for testing."""
        return [{"event_id": "event-123",
                 "alert_id": "alert-456",
                 "timestamp": "2023-01-01T12:00:00Z",
                 "state": "NEW",
                 "type": "Disk Usage Alert",
                 "tags": {"host": "host-789",
                          "dc": "dc-123",
                          "volume": "vol-456"}},
                {"event_id": "event-124",
                 "alert_id": "alert-456",
                 "timestamp": "2023-01-01T12:05:00Z",
                 "state": "ACK",
                 "type": "Disk Usage Alert",
                 "tags": {"host": "host-789",
                          "dc": "dc-123",
                          "volume": "vol-456"}},
                {"event_id": "event-125",
                 "alert_id": "alert-456",
                 "timestamp": "2023-01-01T12:10:00Z",
                 "state": "RSV",
                 "type": "Disk Usage Alert",
                 "tags": {"host": "host-789",
                          "dc": "dc-123",
                          "volume": "vol-456"}}]

    @pytest.fixture
    def sample_json_file(self, sample_event_data):
        """Create a sample JSON file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            for event in sample_event_data:
                f.write(json.dumps(event) + '\n')

        file_path = Path(f.name)
        yield file_path

        # Cleanup
        if file_path.exists():
            os.unlink(file_path)

    @pytest.fixture
    def sample_gzip_file(self, sample_event_data):
        """Create a sample gzipped JSON file for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gz') as f:
            with gzip.open(f, 'wt') as gz:
                for event in sample_event_data:
                    gz.write(json.dumps(event) + '\n')

        file_path = Path(f.name)
        yield file_path

        # Cleanup
        if file_path.exists():
            os.unlink(file_path)

    @pytest.fixture
    def invalid_json_file(self):
        """Create a file with invalid JSON for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            # Write valid JSON events that will pass validation
            f.write('{"event_id": "event-123", "alert_id": "alert-456", "timestamp": "2023-01-01T12:00:00Z", "state": "NEW", "type": "Disk Usage Alert", "tags": {"host": "host-789"}}\n')
            # Write invalid JSON that will fail parsing
            f.write('{"event_id": "event-124", "alert_id": "alert-457",\n')
            # Write another valid JSON event
            f.write('{"event_id": "event-125", "alert_id": "alert-458", "timestamp": "2023-01-01T12:00:00Z", "state": "NEW", "type": "Disk Usage Alert", "tags": {"host": "host-789"}}\n')

        file_path = Path(f.name)
        yield file_path

        # Cleanup
        if file_path.exists():
            os.unlink(file_path)

    @pytest.fixture
    def invalid_gzip_file(self):
        """Create an invalid gzip file for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gz') as f:
            f.write(b'This is not a valid gzip file')

        file_path = Path(f.name)
        yield file_path

        # Cleanup
        if file_path.exists():
            os.unlink(file_path)

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        handler = FileHandler()
        nonexistent_path = "/path/that/definitely/does/not/exist/file.json"

        with pytest.raises(FileNotFoundError):
            # list call is to trigger the iterator next method
            list(handler.read_events(nonexistent_path))

    def test_read_json_file(self, sample_json_file, sample_event_data):
        """Test reading events from a JSON file."""
        handler = FileHandler()
        events = list(handler.read_events(sample_json_file))

        assert len(events) == len(sample_event_data)
        assert all(isinstance(event, AlertEvent) for event in events)

        # Check first event
        assert events[0].event_id == sample_event_data[0]['event_id']
        assert events[0].alert_id == sample_event_data[0]['alert_id']
        assert events[0].state == sample_event_data[0]['state']
        assert events[0].type == sample_event_data[0]['type']

    def test_read_gzip_file(self, sample_gzip_file, sample_event_data):
        """Test reading events from a gzipped file."""
        handler = FileHandler()
        events = list(handler.read_events(sample_gzip_file))

        assert len(events) == len(sample_event_data)
        assert all(isinstance(event, AlertEvent) for event in events)

        # Check first event
        assert events[0].event_id == sample_event_data[0]['event_id']
        assert events[0].alert_id == sample_event_data[0]['alert_id']
        assert events[0].state == sample_event_data[0]['state']
        assert events[0].type == sample_event_data[0]['type']

    def test_read_events_list(self, sample_json_file, sample_event_data):
        """Test reading all events into a list."""
        handler = FileHandler()
        events = handler.read_events_list(sample_json_file)

        assert len(events) == len(sample_event_data)
        assert all(isinstance(event, AlertEvent) for event in events)

    def test_invalid_json(self, invalid_json_file):
        """Test handling of invalid JSON."""
        handler = FileHandler()

        # This should not raise an exception, but log an error and skip the
        # invalid line
        events = list(handler.read_events(invalid_json_file))
        assert len(events) == 2  # Only the valid lines should be processed

        # Check that the events are the ones we expect
        assert events[0].event_id == "event-123"
        assert events[1].event_id == "event-125"

    def test_invalid_gzip(self, invalid_gzip_file):
        """Test handling of invalid gzip file."""
        handler = FileHandler()

        with pytest.raises(ValueError):
            list(handler.read_events(invalid_gzip_file))

    def test_is_gzipped(self, sample_json_file, sample_gzip_file):
        """Test detection of gzipped files."""
        handler = FileHandler()

        assert handler._is_gzipped(sample_json_file) is False
        assert handler._is_gzipped(sample_gzip_file) is True
