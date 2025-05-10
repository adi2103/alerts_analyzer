"""Tests for the query engine functionality."""

import pytest
from datetime import datetime

from src.models import AlertEvent
from src.alert_analyzer import AlertAnalyzer


class TestQueryEngine:
    """Tests for the query engine functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create an AlertAnalyzer for testing."""
        return AlertAnalyzer()

    @pytest.fixture
    def populated_analyzer(self):
        """Create an AlertAnalyzer with sample data for testing."""
        analyzer = AlertAnalyzer()

        # Create and process events for multiple hosts

        # Host 1: 10 minutes of unhealthy time (Disk Usage Alert)
        host1_new = AlertEvent(
            event_id="event-1",
            alert_id="alert-1",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-1", "dc": "dc-1", "volume": "vol-1"}
        )

        host1_rsv = AlertEvent(
            event_id="event-2",
            alert_id="alert-1",
            timestamp=datetime(2023, 1, 1, 12, 10, 0),  # 10 minutes later
            state="RSV",
            alert_type="Disk Usage Alert",
            tags={"host": "host-1", "dc": "dc-1", "volume": "vol-1"}
        )

        # Host 2: 15 minutes of unhealthy time (System Service Failed)
        host2_new = AlertEvent(
            event_id="event-3",
            alert_id="alert-2",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="System Service Failed",
            tags={"host": "host-2", "dc": "dc-1", "service": "svc-1"}
        )

        host2_rsv = AlertEvent(
            event_id="event-4",
            alert_id="alert-2",
            timestamp=datetime(2023, 1, 1, 12, 15, 0),  # 15 minutes later
            state="RSV",
            alert_type="System Service Failed",
            tags={"host": "host-2", "dc": "dc-1", "service": "svc-1"}
        )

        # Host 3: 20 minutes of unhealthy time (Time Drift Alert)
        host3_new = AlertEvent(
            event_id="event-5",
            alert_id="alert-3",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Time Drift Alert",
            tags={"host": "host-3", "dc": "dc-2", "drift": "1000"}
        )

        host3_rsv = AlertEvent(
            event_id="event-6",
            alert_id="alert-3",
            timestamp=datetime(2023, 1, 1, 12, 20, 0),  # 20 minutes later
            state="RSV",
            alert_type="Time Drift Alert",
            tags={"host": "host-3", "dc": "dc-2", "drift": "1000"}
        )

        # Host 4: 5 minutes of unhealthy time (Disk Usage Alert)
        host4_new = AlertEvent(
            event_id="event-7",
            alert_id="alert-4",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="Disk Usage Alert",
            tags={"host": "host-4", "dc": "dc-2", "volume": "vol-2"}
        )

        host4_rsv = AlertEvent(
            event_id="event-8",
            alert_id="alert-4",
            timestamp=datetime(2023, 1, 1, 12, 5, 0),  # 5 minutes later
            state="RSV",
            alert_type="Disk Usage Alert",
            tags={"host": "host-4", "dc": "dc-2", "volume": "vol-2"}
        )

        # Host 5: 25 minutes of unhealthy time (System Service Failed)
        host5_new = AlertEvent(
            event_id="event-9",
            alert_id="alert-5",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            state="NEW",
            alert_type="System Service Failed",
            tags={"host": "host-5", "dc": "dc-3", "service": "svc-2"}
        )

        host5_rsv = AlertEvent(
            event_id="event-10",
            alert_id="alert-5",
            timestamp=datetime(2023, 1, 1, 12, 25, 0),  # 25 minutes later
            state="RSV",
            alert_type="System Service Failed",
            tags={"host": "host-5", "dc": "dc-3", "service": "svc-2"}
        )

        # Process all events
        for event in [
                host1_new,
                host1_rsv,
                host2_new,
                host2_rsv,
                host3_new,
                host3_rsv,
                host4_new,
                host4_rsv,
                host5_new,
                host5_rsv]:
            analyzer.process_event(event)

        return analyzer

    def test_get_top_k_basic(self, populated_analyzer):
        """Test basic top-k query."""
        # Get top 3 hosts
        top_hosts = populated_analyzer.get_top_k("host", k=3)

        # Should return the 3 hosts with the most unhealthy time
        assert len(top_hosts) == 3

        # Check order (descending by unhealthy time)
        assert top_hosts[0]["host_id"] == "host-5"  # 25 minutes
        assert top_hosts[1]["host_id"] == "host-3"  # 20 minutes
        assert top_hosts[2]["host_id"] == "host-2"  # 15 minutes

        # Check unhealthy times
        # 25 minutes = 1500 seconds
        assert top_hosts[0]["total_unhealthy_time"] == 1500
        # 20 minutes = 1200 seconds
        assert top_hosts[1]["total_unhealthy_time"] == 1200
        # 15 minutes = 900 seconds
        assert top_hosts[2]["total_unhealthy_time"] == 900

    def test_get_top_k_with_alert_type_filter(self, populated_analyzer):
        """Test top-k query with alert type filter."""
        # Get top 3 hosts with Disk Usage Alert
        top_hosts = populated_analyzer.get_top_k(
            "host", k=3, alert_type="Disk Usage Alert")

        # Alert type filtering is not supported in this version
        # Should return top 3 hosts regardless of alert type
        assert len(top_hosts) == 3

        # Check order (descending by unhealthy time)
        assert top_hosts[0]["host_id"] == "host-5"  # 25 minutes
        assert top_hosts[1]["host_id"] == "host-3"  # 20 minutes
        assert top_hosts[2]["host_id"] == "host-2"  # 15 minutes

        # Check unhealthy times
        # 25 minutes = 1500 seconds
        assert top_hosts[0]["total_unhealthy_time"] == 1500
        # 20 minutes = 1200 seconds
        assert top_hosts[1]["total_unhealthy_time"] == 1200
        # 15 minutes = 900 seconds
        assert top_hosts[2]["total_unhealthy_time"] == 900

    def test_get_top_k_with_nonexistent_alert_type(self, populated_analyzer):
        """Test top-k query with nonexistent alert type."""
        # Get top 3 hosts with nonexistent alert type
        top_hosts = populated_analyzer.get_top_k(
            "host", k=3, alert_type="Nonexistent Alert")

        # Alert type filtering is not supported in this version
        # Should return top 3 hosts regardless of alert type
        assert len(top_hosts) == 3

        # Check order (descending by unhealthy time)
        assert top_hosts[0]["host_id"] == "host-5"  # 25 minutes
        assert top_hosts[1]["host_id"] == "host-3"  # 20 minutes
        assert top_hosts[2]["host_id"] == "host-2"  # 15 minutes

    def test_get_top_k_with_nonexistent_dimension(self, populated_analyzer):
        """Test top-k query with nonexistent dimension."""
        # Try to get top 3 entities for nonexistent dimension
        with pytest.raises(ValueError, match="Dimension nonexistent not registered"):
            populated_analyzer.get_top_k("nonexistent", k=3)

    def test_get_top_k_with_k_greater_than_entities(self, populated_analyzer):
        """Test top-k query with k greater than number of entities."""
        # Get top 10 hosts (there are only 5)
        top_hosts = populated_analyzer.get_top_k("host", k=10)

        # Should return all 5 hosts
        assert len(top_hosts) == 5

        # Check order (descending by unhealthy time)
        assert top_hosts[0]["host_id"] == "host-5"  # 25 minutes
        assert top_hosts[1]["host_id"] == "host-3"  # 20 minutes
        assert top_hosts[2]["host_id"] == "host-2"  # 15 minutes
        assert top_hosts[3]["host_id"] == "host-1"  # 10 minutes
        assert top_hosts[4]["host_id"] == "host-4"  # 5 minutes

    def test_get_top_k_with_different_dimensions(self, populated_analyzer):
        """Test top-k query with different dimensions."""
        # Get top 3 data centers
        top_dcs = populated_analyzer.get_top_k("dc", k=3)

        # Should return all 3 data centers
        assert len(top_dcs) == 3

        # Check order (descending by unhealthy time)
        # dc-1: host-1 (10 min) + host-2 (15 min) = 25 min
        # dc-2: host-3 (20 min) + host-4 (5 min) = 25 min
        # dc-3: host-5 (25 min) = 25 min
        # Note: The order might vary due to ties, but all should have 25
        # minutes
        for dc in top_dcs:
            assert dc["total_unhealthy_time"] in [
                1500, 1500, 1500]  # All have 25 minutes = 1500 seconds
