"""Tests for the IndexManager class."""

import unittest
from unittest.mock import MagicMock
from datetime import datetime

from src.models import AlertState, EntityState
from src.indexing.dimension_index import Index
from src.indexing.index_manager import IndexManager


class TestIndexManager(unittest.TestCase):
    """Test cases for the IndexManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the singleton instance before each test
        IndexManager._instance = None
        self.index_manager = IndexManager.get_instance()

    def test_singleton_pattern(self):
        """Test that IndexManager follows the singleton pattern."""
        # Get another instance
        another_instance = IndexManager.get_instance()
        
        # Both instances should be the same object
        self.assertIs(self.index_manager, another_instance)
        
        # Creating a new instance directly should not affect the singleton
        direct_instance = IndexManager()
        self.assertIsNot(self.index_manager, direct_instance)
        
        # But getting the instance again should return the singleton
        yet_another_instance = IndexManager.get_instance()
        self.assertIs(self.index_manager, yet_another_instance)

    def test_register_dimension(self):
        """Test registering a new dimension."""
        # Define a test extractor function
        def test_extractor(alert_state):
            return alert_state.tags.get("test_dimension")
        
        # Register a new dimension
        self.index_manager.register_dimension("test_dimension", test_extractor)
        
        # Verify the dimension was registered
        self.assertIn("test_dimension", self.index_manager.dimensions)
        
        # Verify the index has the correct name and extractor function
        index = self.index_manager.dimensions["test_dimension"]
        self.assertEqual(index.name, "test_dimension")
        self.assertEqual(index.extractor_func, test_extractor)

    def test_standard_dimensions(self):
        """Test that standard dimensions are registered by default."""
        # Check that standard dimensions are registered
        standard_dimensions = ["host", "dc", "service", "volume"]
        for dimension in standard_dimensions:
            self.assertIn(dimension, self.index_manager.dimensions)
            self.assertIsInstance(self.index_manager.dimensions[dimension], Index)

    def test_get_index(self):
        """Test getting an index for a registered dimension."""
        # Get an index for a standard dimension
        host_index = self.index_manager.get_index("host")
        
        # Verify it's the correct index
        self.assertEqual(host_index.name, "host")
        self.assertIs(host_index, self.index_manager.dimensions["host"])

    def test_get_index_unknown_dimension(self):
        """Test getting an index for an unknown dimension raises ValueError."""
        with self.assertRaises(ValueError):
            self.index_manager.get_index("unknown_dimension")

    def test_extractor_functions(self):
        """Test that extractor functions work correctly."""
        # Create a mock alert state
        alert_state = MagicMock(spec=AlertState)
        alert_state.tags = {
            "host": "test-host",
            "dc": "test-dc",
            "service": "test-service",
            "volume": "test-volume"
        }
        
        # Test each standard dimension's extractor function
        dimensions = ["host", "dc", "service", "volume"]
        for dimension in dimensions:
            index = self.index_manager.dimensions[dimension]
            extracted_value = index.extractor_func(alert_state)
            self.assertEqual(extracted_value, f"test-{dimension}")
            
    def test_update_for_new_alert(self):
        """Test updating indices when a new alert is created."""
        # Create a mock alert state
        alert_state = MagicMock(spec=AlertState)
        alert_state.alert_id = "test-alert-id"
        alert_state.type = "test-alert-type"
        alert_state.tags = {"host": "test-host"}
        
        # Create a timestamp
        timestamp = datetime.now()
        
        # Update indices for the new alert
        self.index_manager.update_for_new_alert(alert_state, timestamp)
        
        # Verify the host dimension was updated
        host_index = self.index_manager.dimensions["host"]
        self.assertIn("test-host", host_index.entity_states)
        
        # Verify the entity state was updated correctly
        entity_state = host_index.entity_states["test-host"]
        self.assertIn("test-alert-id", entity_state.current_alerts)
        self.assertEqual(entity_state.alert_type_counts["test-alert-type"], 1)
        self.assertEqual(entity_state.unhealthy_start, timestamp)
        
    def test_update_for_resolved_alert(self):
        """Test updating indices when an alert is resolved."""
        # Create a mock alert state
        alert_state = MagicMock(spec=AlertState)
        alert_state.alert_id = "test-alert-id"
        alert_state.type = "test-alert-type"
        alert_state.tags = {"host": "test-host"}
        
        # Create timestamps
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        end_time = datetime(2023, 1, 1, 11, 0, 0)  # 1 hour later
        
        # First add the alert
        self.index_manager.update_for_new_alert(alert_state, start_time)
        
        # Then resolve it
        self.index_manager.update_for_resolved_alert(alert_state, end_time)
        
        # Verify the host dimension was updated
        host_index = self.index_manager.dimensions["host"]
        self.assertIn("test-host", host_index.entity_states)
        
        # Verify the entity state was updated correctly
        entity_state = host_index.entity_states["test-host"]
        self.assertNotIn("test-alert-id", entity_state.current_alerts)
        self.assertEqual(entity_state.total_unhealthy_time, 3600)  # 1 hour in seconds
        self.assertEqual(len(entity_state.unhealthy_periods), 1)
        self.assertEqual(entity_state.unhealthy_periods[0], (start_time, end_time))
        
        # Verify the entity position was updated in the ordered entities
        self.assertIn(-3600, host_index.ordered_entities)
        self.assertIn("test-host", host_index.ordered_entities[-3600])
        self.assertEqual(host_index.entity_positions["test-host"], 3600)
        
    def test_update_entity_position(self):
        """Test updating entity position in the sorted dict."""
        # Create a dimension index
        dimension_index = Index("test", lambda x: x.tags.get("test"))
        
        # Add an entity with initial time
        entity_value = "test-entity"
        old_time = 0
        new_time = 3600
        
        # Update entity position
        self.index_manager._update_entity_position(dimension_index, entity_value, old_time, new_time)
        
        # Verify the entity position was updated
        self.assertIn(-new_time, dimension_index.ordered_entities)
        self.assertIn(entity_value, dimension_index.ordered_entities[-new_time])
        self.assertEqual(dimension_index.entity_positions[entity_value], new_time)
        
        # Update to a new position
        old_time = new_time
        new_time = 7200
        
        # Update entity position again
        self.index_manager._update_entity_position(dimension_index, entity_value, old_time, new_time)
        
        # Verify the entity position was updated and removed from the old position
        self.assertNotIn(-old_time, dimension_index.ordered_entities)
        self.assertIn(-new_time, dimension_index.ordered_entities)
        self.assertIn(entity_value, dimension_index.ordered_entities[-new_time])
        self.assertEqual(dimension_index.entity_positions[entity_value], new_time)


if __name__ == "__main__":
    unittest.main()
