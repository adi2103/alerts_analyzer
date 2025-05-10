"""Tests for the dimension indexing functionality."""

import pytest
from datetime import datetime

from src.models import AlertState, EntityState
from src.indexing.dimension_index import Index


class TestIndex:
    """Tests for the Index class."""

    @pytest.fixture
    def host_extractor(self):
        """Function to extract host from an AlertState."""
        return lambda alert_state: alert_state.tags.get("host")

    @pytest.fixture
    def host_index(self, host_extractor):
        """Create a host index for testing."""
        return Index("host", host_extractor)

    @pytest.fixture
    def sample_alert_state(self):
        """Create a sample AlertState for testing."""
        alert_state = AlertState(
            alert_id="alert-123",
            alert_type="Disk Usage Alert",
            tags={"host": "host-456", "dc": "dc-789", "volume": "vol-123"}
        )
        alert_state.start_time = datetime(2023, 1, 1, 12, 0, 0)
        alert_state.end_time = datetime(
            2023, 1, 1, 12, 10, 0)  # 10 minutes later
        return alert_state

    def test_init(self, host_index):
        """Test initialization of Index."""
        assert host_index.name == "host"
        assert callable(host_index.extractor_func)
        assert host_index.entity_states == {}
        assert len(host_index.ordered_entities) == 0
        assert host_index.entity_positions == {}

    def test_get_entity_state(self, host_index):
        """Test getting an EntityState from the index."""
        entity_state = host_index.get_entity_state("host-456")

        assert isinstance(entity_state, EntityState)
        assert "host-456" in host_index.entity_states
        assert host_index.entity_positions["host-456"] == 0

    def test_update_entity_position_new_entity(self, host_index):
        """Test updating position for a new entity."""
        host_index.update_entity_position("host-456", 0, 600)

        assert -600 in host_index.ordered_entities
        assert "host-456" in host_index.ordered_entities[-600]
        assert host_index.entity_positions["host-456"] == 600

    def test_update_entity_position_existing_entity(self, host_index):
        """Test updating position for an existing entity."""
        # First update
        host_index.update_entity_position("host-456", 0, 600)

        # Second update
        host_index.update_entity_position("host-456", 600, 900)

        assert -600 not in host_index.ordered_entities
        assert -900 in host_index.ordered_entities
        assert "host-456" in host_index.ordered_entities[-900]
        assert host_index.entity_positions["host-456"] == 900

    def test_update_entity_position_multiple_entities(self, host_index):
        """Test updating positions for multiple entities."""
        host_index.update_entity_position("host-456", 0, 600)
        host_index.update_entity_position("host-789", 0, 900)
        host_index.update_entity_position("host-123", 0, 600)

        assert -600 in host_index.ordered_entities
        assert -900 in host_index.ordered_entities
        assert len(host_index.ordered_entities[-600]) == 2
        assert "host-456" in host_index.ordered_entities[-600]
        assert "host-123" in host_index.ordered_entities[-600]
        assert "host-789" in host_index.ordered_entities[-900]

    def test_get_top_k(self, host_index):
        """Test getting top k entities."""
        # Add entities with different unhealthy times
        host_index.update_entity_position("host-456", 0, 600)
        host_index.get_entity_state(
            "host-456").alert_type_counts["Disk Usage Alert"] = 1

        host_index.update_entity_position("host-789", 0, 900)
        host_index.get_entity_state(
            "host-789").alert_type_counts["System Service Failed"] = 2

        host_index.update_entity_position("host-123", 0, 300)
        host_index.get_entity_state(
            "host-123").alert_type_counts["Time Drift Alert"] = 1

        # Get top 2 entities
        top_entities = host_index.get_top_k(2)

        assert len(top_entities) == 2
        assert "host-789" in top_entities
        assert "host-456" in top_entities
        assert "host-123" not in top_entities

        assert top_entities["host-789"]["total_unhealthy_time"] == 900
        assert top_entities["host-456"]["total_unhealthy_time"] == 600

        assert top_entities["host-789"]["alert_types"] == {
            "System Service Failed": 2}
        assert top_entities["host-456"]["alert_types"] == {
            "Disk Usage Alert": 1}

    def test_get_top_k_with_ties(self, host_index):
        """Test getting top k entities with ties in unhealthy time."""
        # Add entities with same unhealthy times
        host_index.update_entity_position("host-456", 0, 600)
        host_index.get_entity_state("host-456")  # Create entity state

        host_index.update_entity_position("host-789", 0, 600)
        host_index.get_entity_state("host-789")  # Create entity state

        host_index.update_entity_position("host-123", 0, 300)
        host_index.get_entity_state("host-123")  # Create entity state

        # Get top 2 entities
        top_entities = host_index.get_top_k(2)

        assert len(top_entities) == 2
        # Both host-456 and host-789 should be included (tie at 600)
        assert all(
            entity in top_entities for entity in [
                "host-456", "host-789"])
        assert "host-123" not in top_entities

    def test_extractor_function(self, host_index, sample_alert_state):
        """Test the extractor function."""
        entity_value = host_index.extractor_func(sample_alert_state)
        assert entity_value == "host-456"
