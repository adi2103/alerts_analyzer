"""Tests for the data models."""

import pytest
from datetime import datetime
import json
from collections import defaultdict
from src.models import AlertEvent, AlertState, EntityState


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
        assert event.tags == {
            "host": "host-789",
            "dc": "dc-123",
            "volume": "vol-456"}

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
        assert event.tags == {
            "host": "host-789",
            "dc": "dc-123",
            "volume": "vol-456"}

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
        assert event.tags == {
            "host": "host-789",
            "dc": "dc-123",
            "volume": "vol-456"}

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
        assert state.tags == {
            "host": "host-789",
            "dc": "dc-123",
            "volume": "vol-456"}
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
        assert state.state_history == [
            (timestamp1, "NEW"), (timestamp2, "ACK")]
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


class TestEntityState:
    """Tests for the EntityState class."""

    def test_init(self):
        """Test initialization of EntityState."""
        state = EntityState()

        assert state.total_unhealthy_time == 0
        assert state.current_alerts == set()
        assert state.unhealthy_start is None
        assert state.unhealthy_periods == []
        assert isinstance(state.alert_type_counts, defaultdict)
        assert len(state.alert_type_counts) == 0

    def test_add_alert(self):
        """Test adding an alert to the entity."""
        state = EntityState()
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        state.add_alert("alert-123", "Disk Usage Alert", timestamp)

        assert "alert-123" in state.current_alerts
        assert state.unhealthy_start == timestamp
        assert state.alert_type_counts["Disk Usage Alert"] == 1
        assert state.is_unhealthy() is True

    def test_add_multiple_alerts(self):
        """Test adding multiple alerts to the entity."""
        state = EntityState()
        timestamp1 = datetime(2023, 1, 1, 12, 0, 0)
        timestamp2 = datetime(2023, 1, 1, 12, 5, 0)

        state.add_alert("alert-123", "Disk Usage Alert", timestamp1)
        state.add_alert("alert-456", "System Service Failed", timestamp2)

        assert "alert-123" in state.current_alerts
        assert "alert-456" in state.current_alerts
        # Should be the first alert's timestamp
        assert state.unhealthy_start == timestamp1
        assert state.alert_type_counts["Disk Usage Alert"] == 1
        assert state.alert_type_counts["System Service Failed"] == 1
        assert state.is_unhealthy() is True

    def test_remove_alert(self):
        """Test removing an alert from the entity."""
        state = EntityState()
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 10, 0)  # 10 minutes later

        state.add_alert("alert-123", "Disk Usage Alert", start_time)
        state.remove_alert("alert-123", end_time)

        assert "alert-123" not in state.current_alerts
        assert state.unhealthy_start is None
        assert state.total_unhealthy_time == 600  # 10 minutes = 600 seconds
        assert state.unhealthy_periods == [(start_time, end_time)]
        assert state.is_unhealthy() is False

    def test_remove_one_of_multiple_alerts(self):
        """Test removing one alert when multiple are active."""
        state = EntityState()
        timestamp1 = datetime(2023, 1, 1, 12, 0, 0)
        timestamp2 = datetime(2023, 1, 1, 12, 5, 0)
        timestamp3 = datetime(2023, 1, 1, 12, 10, 0)

        state.add_alert("alert-123", "Disk Usage Alert", timestamp1)
        state.add_alert("alert-456", "System Service Failed", timestamp2)
        state.remove_alert("alert-123", timestamp3)

        assert "alert-123" not in state.current_alerts
        assert "alert-456" in state.current_alerts
        # Should still be the first alert's timestamp
        assert state.unhealthy_start == timestamp1
        assert state.total_unhealthy_time == 0  # No unhealthy time added yet
        assert state.unhealthy_periods == []  # No periods recorded yet
        assert state.is_unhealthy() is True  # Still unhealthy due to alert-456

    def test_remove_all_alerts(self):
        """Test removing all alerts from the entity."""
        state = EntityState()
        timestamp1 = datetime(2023, 1, 1, 12, 0, 0)
        timestamp2 = datetime(2023, 1, 1, 12, 5, 0)
        timestamp3 = datetime(2023, 1, 1, 12, 10, 0)
        timestamp4 = datetime(2023, 1, 1, 12, 15, 0)

        state.add_alert("alert-123", "Disk Usage Alert", timestamp1)
        state.add_alert("alert-456", "System Service Failed", timestamp2)
        state.remove_alert("alert-123", timestamp3)
        state.remove_alert("alert-456", timestamp4)

        assert state.current_alerts == set()
        assert state.unhealthy_start is None
        assert state.total_unhealthy_time == 900  # 15 minutes = 900 seconds
        assert state.unhealthy_periods == [(timestamp1, timestamp4)]
        assert state.is_unhealthy() is False

    def test_calculate_unhealthy_time_in_range_no_bounds(self):
        """Test calculating unhealthy time with no time bounds."""
        state = EntityState()
        state.unhealthy_periods = [
            (datetime(2023, 1, 1, 12, 0, 0), datetime(
                2023, 1, 1, 12, 10, 0)),  # 10 minutes
            (datetime(2023, 1, 1, 12, 20, 0), datetime(
                2023, 1, 1, 12, 30, 0))   # 10 minutes
        ]

        assert state.calculate_unhealthy_time_in_range() == 1200  # 20 minutes = 1200 seconds

    def test_calculate_unhealthy_time_in_range_with_bounds(self):
        """Test calculating unhealthy time within specific time bounds."""
        state = EntityState()
        state.unhealthy_periods = [
            (datetime(2023, 1, 1, 12, 0, 0), datetime(
                2023, 1, 1, 12, 10, 0)),  # 10 minutes
            (datetime(2023, 1, 1, 12, 20, 0), datetime(
                2023, 1, 1, 12, 30, 0))   # 10 minutes
        ]

        # Only include the second period
        start_time = datetime(2023, 1, 1, 12, 15, 0)
        end_time = datetime(2023, 1, 1, 12, 35, 0)

        assert state.calculate_unhealthy_time_in_range(
            start_time, end_time) == 600  # 10 minutes = 600 seconds

    def test_calculate_unhealthy_time_in_range_partial_overlap(self):
        """Test calculating unhealthy time with partial overlap of time bounds."""
        state = EntityState()
        state.unhealthy_periods = [
            (datetime(2023, 1, 1, 12, 0, 0), datetime(
                2023, 1, 1, 12, 10, 0)),  # 10 minutes
            (datetime(2023, 1, 1, 12, 20, 0), datetime(
                2023, 1, 1, 12, 30, 0))   # 10 minutes
        ]

        # Partially overlap both periods
        start_time = datetime(2023, 1, 1, 12, 5, 0)
        end_time = datetime(2023, 1, 1, 12, 25, 0)

        # First period: 5 minutes, Second period: 5 minutes
        assert state.calculate_unhealthy_time_in_range(
            start_time, end_time) == 600  # 10 minutes = 600 seconds
