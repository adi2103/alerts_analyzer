"""Tests for the data models."""

import pytest
from datetime import datetime
import json
from src.models import AlertEvent, AlertState


class TestAlertEvent:
    """Tests for the AlertEvent class."""
    
    def test_init(self):
        """Test initialization of AlertEvent."""
        event = AlertEvent(
            event_id="event-123",
            alert_id="alert-456",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        )
        
        assert event.event_id == "event-123"
        assert event.alert_id == "alert-456"
        assert event.timestamp == datetime(2023, 1, 1, 12, 0, 0)
        assert event.state == "NEW"
        assert event.type == "Disk Usage Alert"
        assert event.tags == {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
    
    def test_from_json_string(self):
        """Test creating AlertEvent from JSON string."""
        json_str = '''
        {
            "event_id": "event-123",
            "alert_id": "alert-456",
            "timestamp": "2023-01-01T12:00:00Z",
            "state": "NEW",
            "type": "Disk Usage Alert",
            "tags": {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        }
        '''
        
        event = AlertEvent.from_json(json_str)
        
        assert event.event_id == "event-123"
        assert event.alert_id == "alert-456"
        assert event.timestamp.year == 2023
        assert event.timestamp.month == 1
        assert event.timestamp.day == 1
        assert event.state == "NEW"
        assert event.type == "Disk Usage Alert"
        assert event.tags == {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
    
    def test_from_json_dict(self):
        """Test creating AlertEvent from dictionary."""
        json_dict = {
            "event_id": "event-123",
            "alert_id": "alert-456",
            "timestamp": "2023-01-01T12:00:00Z",
            "state": "NEW",
            "type": "Disk Usage Alert",
            "tags": {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        }
        
        event = AlertEvent.from_json(json_dict)
        
        assert event.event_id == "event-123"
        assert event.alert_id == "alert-456"
        assert event.timestamp.year == 2023
        assert event.state == "NEW"
        assert event.type == "Disk Usage Alert"
        assert event.tags == {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
    
    def test_missing_field(self):
        """Test handling of missing fields."""
        json_dict = {
            "event_id": "event-123",
            "alert_id": "alert-456",
            "timestamp": "2023-01-01T12:00:00Z",
            "state": "NEW",
            # Missing "type" field
            "tags": {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        }
        
        with pytest.raises(ValueError) as excinfo:
            AlertEvent.from_json(json_dict)
        
        assert "Missing required field" in str(excinfo.value)
    
    def test_invalid_state(self):
        """Test handling of invalid state."""
        json_dict = {
            "event_id": "event-123",
            "alert_id": "alert-456",
            "timestamp": "2023-01-01T12:00:00Z",
            "state": "INVALID",  # Invalid state
            "type": "Disk Usage Alert",
            "tags": {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        }
        
        with pytest.raises(ValueError) as excinfo:
            AlertEvent.from_json(json_dict)
        
        assert "Invalid state" in str(excinfo.value)
    
    def test_invalid_timestamp(self):
        """Test handling of invalid timestamp."""
        json_dict = {
            "event_id": "event-123",
            "alert_id": "alert-456",
            "timestamp": "not-a-timestamp",  # Invalid timestamp
            "state": "NEW",
            "type": "Disk Usage Alert",
            "tags": {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        }
        
        with pytest.raises(ValueError) as excinfo:
            AlertEvent.from_json(json_dict)
        
        assert "Invalid timestamp" in str(excinfo.value)
    
    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        json_str = '''
        {
            "event_id": "event-123",
            "alert_id": "alert-456",
            "timestamp": "2023-01-01T12:00:00Z",
            "state": "NEW",
            "type": "Disk Usage Alert",
            "tags": {"host": "host-789", "dc": "dc-123", "volume": "vol-456"
        }
        '''  # Missing closing brace
        
        with pytest.raises(json.JSONDecodeError):
            AlertEvent.from_json(json_str)


class TestAlertState:
    """Tests for the AlertState class."""
    
    def test_init(self):
        """Test initialization of AlertState."""
        state = AlertState(
            alert_id="alert-456",
            alert_type="Disk Usage Alert",
            tags={"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        )
        
        assert state.alert_id == "alert-456"
        assert state.type == "Disk Usage Alert"
        assert state.tags == {"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        assert state.current_state is None
        assert state.start_time is None
        assert state.end_time is None
        assert state.state_history == []
    
    def test_update_state_new(self):
        """Test updating state to NEW."""
        state = AlertState(
            alert_id="alert-456",
            alert_type="Disk Usage Alert",
            tags={"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        )
        
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        state.update_state(timestamp, "NEW")
        
        assert state.current_state == "NEW"
        assert state.start_time == timestamp
        assert state.end_time is None
        assert state.state_history == [(timestamp, "NEW")]
        assert state.is_active() is True
    
    def test_update_state_ack(self):
        """Test updating state to ACK."""
        state = AlertState(
            alert_id="alert-456",
            alert_type="Disk Usage Alert",
            tags={"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        )
        
        timestamp1 = datetime(2023, 1, 1, 12, 0, 0)
        state.update_state(timestamp1, "NEW")
        
        timestamp2 = datetime(2023, 1, 1, 12, 5, 0)
        state.update_state(timestamp2, "ACK")
        
        assert state.current_state == "ACK"
        assert state.start_time == timestamp1  # Start time should be from NEW
        assert state.end_time is None
        assert state.state_history == [(timestamp1, "NEW"), (timestamp2, "ACK")]
        assert state.is_active() is True
    
    def test_update_state_rsv(self):
        """Test updating state to RSV."""
        state = AlertState(
            alert_id="alert-456",
            alert_type="Disk Usage Alert",
            tags={"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        )
        
        timestamp1 = datetime(2023, 1, 1, 12, 0, 0)
        state.update_state(timestamp1, "NEW")
        
        timestamp2 = datetime(2023, 1, 1, 12, 5, 0)
        state.update_state(timestamp2, "ACK")
        
        timestamp3 = datetime(2023, 1, 1, 12, 10, 0)
        state.update_state(timestamp3, "RSV")
        
        assert state.current_state == "RSV"
        assert state.start_time == timestamp1
        assert state.end_time == timestamp3
        assert state.state_history == [
            (timestamp1, "NEW"),
            (timestamp2, "ACK"),
            (timestamp3, "RSV")
        ]
        assert state.is_active() is False
    
    def test_get_duration(self):
        """Test calculating alert duration."""
        state = AlertState(
            alert_id="alert-456",
            alert_type="Disk Usage Alert",
            tags={"host": "host-789", "dc": "dc-123", "volume": "vol-456"}
        )
        
        # No duration yet
        assert state.get_duration() is None
        
        # Set start time
        timestamp1 = datetime(2023, 1, 1, 12, 0, 0)
        state.update_state(timestamp1, "NEW")
        assert state.get_duration() is None
        
        # Set end time (10 minutes later)
        timestamp2 = datetime(2023, 1, 1, 12, 10, 0)
        state.update_state(timestamp2, "RSV")
        assert state.get_duration() == 600  # 10 minutes = 600 seconds
