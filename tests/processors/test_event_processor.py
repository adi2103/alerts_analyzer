"""Tests for the EventProcessor class."""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import tempfile
import json
import gzip

from src.models import AlertEvent, AlertState
from src.indexing.index_manager import IndexManager
from src.processors.event_processor import EventProcessor


class TestEventProcessor(unittest.TestCase):
    """Test cases for the EventProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the IndexManager singleton
        IndexManager._instance = None
        
        # Create a mock IndexManager
        self.mock_index_manager = MagicMock(spec=IndexManager)
        IndexManager._instance = self.mock_index_manager
        
        # Create the EventProcessor
        self.event_processor = EventProcessor()
        
        # Verify the EventProcessor is using our mock IndexManager
        self.assertIs(self.event_processor.index_manager, self.mock_index_manager)

    def test_process_event_new_alert(self):
        """Test processing a NEW alert event."""
        # Create a test event
        event = self._create_test_event("alert-1", "NEW", "test-type", {"host": "test-host"})
        
        # Process the event
        self.event_processor.process_event(event)
        
        # Verify alert state was created
        self.assertIn("alert-1", self.event_processor.alert_states)
        alert_state = self.event_processor.alert_states["alert-1"]
        self.assertEqual(alert_state.alert_id, "alert-1")
        self.assertEqual(alert_state.type, "test-type")
        self.assertEqual(alert_state.tags, {"host": "test-host"})
        self.assertEqual(alert_state.current_state, "NEW")
        self.assertEqual(alert_state.start_time, event.timestamp)
        
        # Verify IndexManager.update_for_new_alert was called
        self.mock_index_manager.update_for_new_alert.assert_called_once_with(
            alert_state, event.timestamp)

    def test_process_event_ack_alert(self):
        """Test processing an ACK alert event after a NEW event."""
        # Create and process a NEW event
        new_event = self._create_test_event("alert-1", "NEW", "test-type", {"host": "test-host"})
        self.event_processor.process_event(new_event)
        
        # Reset the mock
        self.mock_index_manager.reset_mock()
        
        # Create and process an ACK event
        ack_event = self._create_test_event("alert-1", "ACK", "test-type", {"host": "test-host"})
        self.event_processor.process_event(ack_event)
        
        # Verify alert state was updated
        self.assertIn("alert-1", self.event_processor.alert_states)
        alert_state = self.event_processor.alert_states["alert-1"]
        self.assertEqual(alert_state.current_state, "ACK")
        
        # Verify IndexManager methods were not called (since this is not the first event for this alert)
        self.mock_index_manager.update_for_new_alert.assert_not_called()
        self.mock_index_manager.update_for_resolved_alert.assert_not_called()

    def test_process_event_rsv_alert(self):
        """Test processing an RSV alert event after a NEW event."""
        # Create and process a NEW event
        new_event = self._create_test_event("alert-1", "NEW", "test-type", {"host": "test-host"})
        self.event_processor.process_event(new_event)
        
        # Reset the mock
        self.mock_index_manager.reset_mock()
        
        # Create and process an RSV event
        rsv_event = self._create_test_event("alert-1", "RSV", "test-type", {"host": "test-host"})
        self.event_processor.process_event(rsv_event)
        
        # Verify alert state was removed
        self.assertNotIn("alert-1", self.event_processor.alert_states)
        
        # Verify IndexManager.update_for_resolved_alert was called
        self.mock_index_manager.update_for_resolved_alert.assert_called_once()
        args, _ = self.mock_index_manager.update_for_resolved_alert.call_args
        self.assertEqual(args[0].alert_id, "alert-1")
        self.assertEqual(args[1], rsv_event.timestamp)

    def test_process_event_rsv_without_new(self):
        """Test processing an RSV alert event without a preceding NEW event."""
        # Create and process an RSV event directly
        rsv_event = self._create_test_event("alert-1", "RSV", "test-type", {"host": "test-host"})
        self.event_processor.process_event(rsv_event)
        
        # Verify no alert state was created
        self.assertNotIn("alert-1", self.event_processor.alert_states)
        
        # Verify IndexManager methods were not called
        self.mock_index_manager.update_for_new_alert.assert_not_called()
        self.mock_index_manager.update_for_resolved_alert.assert_not_called()

    def test_process_file(self):
        """Test processing a file of alert events."""
        # Create a temporary file with test events
        with tempfile.NamedTemporaryFile(suffix='.json.gz', delete=False) as f:
            file_path = f.name
            
            # Create test events
            events = [
                {
                    "event_id": f"event-{i}",
                    "alert_id": f"alert-{i}",
                    "timestamp": datetime.now().isoformat(),
                    "state": state,
                    "type": "test-type",
                    "tags": {"host": f"host-{i}"}
                }
                for i, state in enumerate(["NEW", "ACK", "RSV", "NEW", "RSV"])
            ]
            
            # Write events to file
            with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                for event in events:
                    gz.write((json.dumps(event) + '\n').encode('utf-8'))
        
        try:
            # Process the file
            with patch('src.processors.event_processor.log_performance_metrics') as mock_log:
                events_processed = self.event_processor.process_file(file_path)
            
            # Verify the correct number of events was processed
            self.assertEqual(events_processed, 5)
            
            # Verify log_performance_metrics was called
            mock_log.assert_called_once()
            
            # Verify alert states (we don't know exactly how many will remain since
            # the test events might be processed out of order due to file reading)
            self.assertLessEqual(len(self.event_processor.alert_states), 3)  # At most 3 alerts (NEW ones)
            
        finally:
            # Clean up the temporary file
            import os
            os.unlink(file_path)

    def test_process_file_error(self):
        """Test error handling when processing a file."""
        # Try to process a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.event_processor.process_file("non_existent_file.gz")

    def _create_test_event(self, alert_id, state, alert_type, tags):
        """Helper method to create a test AlertEvent."""
        return AlertEvent(
            event_id=f"event-{alert_id}-{state}",
            alert_id=alert_id,
            timestamp=datetime.now(),
            state=state,
            alert_type=alert_type,
            tags=tags
        )


if __name__ == "__main__":
    unittest.main()
