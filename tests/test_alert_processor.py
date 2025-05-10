"""Tests for the alert lifecycle processing functionality."""

import pytest
from datetime import datetime

from src.models import AlertEvent, AlertState
from src.alert_analyzer import AlertAnalyzer


class TestAlertAnalyzer:
    """Tests for the AlertAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create an AlertAnalyzer for testing."""
        return AlertAnalyzer()

    @pytest.fixture
    def sample_alert_event_new(self):
        """Create a sample NEW alert event for testing."""
        return AlertEvent(
            event_id="event-123",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

    @pytest.fixture
    def sample_alert_event_ack(self):
        """Create a sample ACK alert event for testing."""
        return AlertEvent(
            event_id="event-124",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 5, 0),  # 5 minutes after NEW
            state="ACK",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

    @pytest.fixture
    def sample_alert_event_rsv(self):
        """Create a sample RSV alert event for testing."""
        return AlertEvent(
            event_id="event-125",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 10, 0),  # 10 minutes after NEW
            state="RSV",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

    def test_register_dimension(self, analyzer):
        """Test registering a new dimension."""
        # Register a new dimension
        analyzer.register_dimension(
            "test", lambda alert_state: alert_state.tags.get("test"))

        assert "test" in analyzer.dimensions
        assert analyzer.dimensions["test"].name == "test"

    def test_process_event_new(self, analyzer, sample_alert_event_new):
        """Test processing a NEW alert event."""
        analyzer.process_event(sample_alert_event_new)

        # Check alert state
        assert "alert-123" in analyzer.alert_states
        assert analyzer.alert_states["alert-123"].current_state == "NEW"
        assert analyzer.alert_states["alert-123"].start_time == sample_alert_event_new.timestamp

        # Check entity states
        host_index = analyzer.dimensions["host"]
        assert "host-456" in host_index.entity_states
        assert host_index.entity_states["host-456"].is_unhealthy()
        assert "alert-123" in host_index.entity_states["host-456"].current_alerts

    def test_process_event_ack(
            self,
            analyzer,
            sample_alert_event_new,
            sample_alert_event_ack):
        """Test processing an ACK alert event."""
        analyzer.process_event(sample_alert_event_new)
        analyzer.process_event(sample_alert_event_ack)

        # Check alert state
        assert "alert-123" in analyzer.alert_states
        assert analyzer.alert_states["alert-123"].current_state == "ACK"

        # Entity state should still be unhealthy
        host_index = analyzer.dimensions["host"]
        assert host_index.entity_states["host-456"].is_unhealthy()

    def test_process_event_rsv(
            self,
            analyzer,
            sample_alert_event_new,
            sample_alert_event_rsv):
        """Test processing an RSV alert event."""
        analyzer.process_event(sample_alert_event_new)
        analyzer.process_event(sample_alert_event_rsv)

        # Alert state should be removed
        assert "alert-123" not in analyzer.alert_states

        # Entity should no longer be unhealthy
        host_index = analyzer.dimensions["host"]
        assert not host_index.entity_states["host-456"].is_unhealthy()

        # Unhealthy time should be updated
        expected_time = 600  # 10 minutes = 600 seconds
        assert host_index.entity_states["host-456"].total_unhealthy_time == expected_time

        # Unhealthy period should be recorded
        assert len(host_index.entity_states["host-456"].unhealthy_periods) == 1
        start, end = host_index.entity_states["host-456"].unhealthy_periods[0]
        assert start == sample_alert_event_new.timestamp
        assert end == sample_alert_event_rsv.timestamp

        # Alert type count should be updated
        assert host_index.entity_states["host-456"].alert_type_counts["Disk Usage Alert"] == 1

        # Position in ordered entities should be updated
        assert -expected_time in host_index.ordered_entities
        assert "host-456" in host_index.ordered_entities[-expected_time]

    def test_full_alert_lifecycle(
            self,
            analyzer,
            sample_alert_event_new,
            sample_alert_event_ack,
            sample_alert_event_rsv):
        """Test the full alert lifecycle (NEW → ACK → RSV)."""
        analyzer.process_event(sample_alert_event_new)
        analyzer.process_event(sample_alert_event_ack)
        analyzer.process_event(sample_alert_event_rsv)

        # Alert state should be removed
        assert "alert-123" not in analyzer.alert_states

        # Entity should no longer be unhealthy
        host_index = analyzer.dimensions["host"]
        assert not host_index.entity_states["host-456"].is_unhealthy()

        # Unhealthy time should be updated
        expected_time = 600  # 10 minutes = 600 seconds
        assert host_index.entity_states["host-456"].total_unhealthy_time == expected_time

    def test_multiple_alerts_same_host(self, analyzer):
        """Test handling multiple alerts for the same host."""
        # Create two alerts for the same host
        alert1_new = AlertEvent(
            event_id="event-123",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

        alert2_new = AlertEvent(
            event_id="event-126",
            alert_id="alert-456",
            # 5 minutes after first alert
            timestamp=datetime(2023, 1, 1, 12, 5, 0),
            state="NEW",
            alert_type="System Service Failed",
            tags={"host": "host-456", "dc": "dc-789", "service": "svc-123"}
        )

        alert1_rsv = AlertEvent(
            event_id="event-125",
            alert_id="alert-123",
            # 10 minutes after first alert
            timestamp=datetime(2023, 1, 1, 12, 10, 0),
            state="RSV",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

        alert2_rsv = AlertEvent(
            event_id="event-127",
            alert_id="alert-456",
            # 15 minutes after first alert
            timestamp=datetime(2023, 1, 1, 12, 15, 0),
            state="RSV",
            alert_type="System Service Failed",
            tags={"host": "host-456", "dc": "dc-789", "service": "svc-123"}
        )

        # Process events
        analyzer.process_event(alert1_new)
        analyzer.process_event(alert2_new)
        analyzer.process_event(alert1_rsv)
        analyzer.process_event(alert2_rsv)

        # Check entity state
        host_index = analyzer.dimensions["host"]

        # Total unhealthy time should be 15 minutes (900 seconds)
        # The host was unhealthy from the first alert (12:00) until the last
        # alert was resolved (12:15)
        assert host_index.entity_states["host-456"].total_unhealthy_time == 900

        # Should have recorded both alert types
        assert host_index.entity_states["host-456"].alert_type_counts["Disk Usage Alert"] == 1
        assert host_index.entity_states["host-456"].alert_type_counts["System Service Failed"] == 1

    def test_rsv_without_new(self, analyzer):
        """Test handling an RSV event without a corresponding NEW event."""
        rsv_event = AlertEvent(
            event_id="event-125",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 10, 0),
            state="RSV",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

        # Process event - should be ignored
        analyzer.process_event(rsv_event)

        # No alert state should be created
        assert "alert-123" not in analyzer.alert_states

        # No entity state should be created
        host_index = analyzer.dimensions["host"]
        assert "host-456" not in host_index.entity_states

    def test_duplicate_new_events(self, analyzer):
        """Test handling duplicate NEW events for the same alert."""
        new_event1 = AlertEvent(
            event_id="event-123",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

        new_event2 = AlertEvent(
            event_id="event-124",
            alert_id="alert-123",
            timestamp=datetime(2023, 1, 1, 12, 5, 0),  # 5 minutes later
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )

        # Process events
        analyzer.process_event(new_event1)
        analyzer.process_event(new_event2)

        # Alert state should be updated
        assert analyzer.alert_states["alert-123"].current_state == "NEW"

        # Start time should be from the first event
        assert analyzer.alert_states["alert-123"].start_time == new_event1.timestamp

        # Entity should still be unhealthy
        host_index = analyzer.dimensions["host"]
        assert host_index.entity_states["host-456"].is_unhealthy()

        # Should only count as one alert
        assert len(host_index.entity_states["host-456"].current_alerts) == 1
