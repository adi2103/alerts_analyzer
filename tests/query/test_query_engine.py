"""Tests for the QueryEngine class."""

import unittest
from unittest.mock import MagicMock, patch
from sortedcontainers import SortedDict

from src.models import EntityState
from src.indexing.dimension_index import Index
from src.indexing.index_manager import IndexManager
from src.query.query_engine import QueryEngine


class TestQueryEngine(unittest.TestCase):
    """Test cases for the QueryEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the IndexManager singleton
        IndexManager._instance = None
        
        # Create a mock IndexManager
        self.mock_index_manager = MagicMock(spec=IndexManager)
        IndexManager._instance = self.mock_index_manager
        
        # Create the QueryEngine
        self.query_engine = QueryEngine()
        
        # Set up a mock index
        self.mock_index = MagicMock(spec=Index)
        self.mock_index.name = "test_dimension"
        self.mock_index.ordered_entities = SortedDict()
        self.mock_index.entity_states = {}
        
        # Configure the mock index manager to return the mock index
        self.mock_index_manager.get_index.return_value = self.mock_index

    def test_get_top_k_returns_correct_number(self):
        """Test that get_top_k returns the correct number of entities."""
        # Set up mock data
        self._setup_mock_data(10)  # 10 entities
        
        # Get top 5 entities
        results = self.query_engine.get_top_k("test_dimension", 5)
        
        # Verify the correct number of entities is returned
        self.assertEqual(len(results), 5)
        
        # Get top 3 entities
        results = self.query_engine.get_top_k("test_dimension", 3)
        
        # Verify the correct number of entities is returned
        self.assertEqual(len(results), 3)
        
        # Get all entities when k is larger than the number of entities
        results = self.query_engine.get_top_k("test_dimension", 20)
        
        # Verify all entities are returned
        self.assertEqual(len(results), 10)

    def test_entities_sorted_by_unhealthy_time(self):
        """Test that entities are sorted by unhealthy time."""
        # Set up mock data
        self._setup_mock_data(5)  # 5 entities
        
        # Get top 5 entities
        results = self.query_engine.get_top_k("test_dimension", 5)
        
        # Verify entities are sorted by unhealthy time (descending)
        unhealthy_times = [entity["total_unhealthy_time"] for entity in results]
        self.assertEqual(unhealthy_times, sorted(unhealthy_times, reverse=True))
        
        # Verify the actual values
        self.assertEqual(unhealthy_times, [5000, 4000, 3000, 2000, 1000])

    def test_duplicate_entities_handled_correctly(self):
        """Test that duplicate entities are handled correctly."""
        # Set up mock data with duplicates
        self._setup_mock_data_with_duplicates()
        
        # Get top 5 entities
        results = self.query_engine.get_top_k("test_dimension", 5)
        
        # Verify no duplicates in results
        entity_ids = [entity["test_dimension_id"] for entity in results]
        self.assertEqual(len(entity_ids), len(set(entity_ids)))
        
        # Verify the correct entities are returned
        self.assertEqual(set(entity_ids), {"entity-1", "entity-2", "entity-3"})

    def test_results_format(self):
        """Test that results have the correct format."""
        # Set up mock data
        self._setup_mock_data(1)  # 1 entity
        
        # Get top 1 entity
        results = self.query_engine.get_top_k("test_dimension", 1)
        
        # Verify there's one result
        self.assertEqual(len(results), 1)
        
        # Verify the result has the correct format
        result = results[0]
        self.assertIn("test_dimension_id", result)
        self.assertIn("total_unhealthy_time", result)
        self.assertIn("alert_types", result)
        
        # Verify the values
        self.assertEqual(result["test_dimension_id"], "entity-1")
        self.assertEqual(result["total_unhealthy_time"], 1000)
        self.assertEqual(result["alert_types"], {"alert-type-1": 1})

    def test_dimension_not_registered(self):
        """Test that ValueError is raised when dimension is not registered."""
        # Configure the mock index manager to raise ValueError
        self.mock_index_manager.get_index.side_effect = ValueError("Dimension not registered")
        
        # Verify ValueError is raised
        with self.assertRaises(ValueError):
            self.query_engine.get_top_k("unknown_dimension")

    def _setup_mock_data(self, num_entities):
        """Set up mock data with the specified number of entities."""
        # Clear existing data
        self.mock_index.ordered_entities.clear()
        self.mock_index.entity_states.clear()
        
        # Add entities with decreasing unhealthy times
        for i in range(1, num_entities + 1):
            # Create entity state
            entity_state = EntityState()
            entity_state.total_unhealthy_time = i * 1000
            entity_state.alert_type_counts["alert-type-1"] = 1
            
            # Add to entity states
            entity_id = f"entity-{i}"
            self.mock_index.entity_states[entity_id] = entity_state
            
            # Add to ordered entities
            neg_time = -i * 1000
            if neg_time not in self.mock_index.ordered_entities:
                self.mock_index.ordered_entities[neg_time] = set()
            self.mock_index.ordered_entities[neg_time].add(entity_id)

    def _setup_mock_data_with_duplicates(self):
        """Set up mock data with duplicate entities."""
        # Clear existing data
        self.mock_index.ordered_entities.clear()
        self.mock_index.entity_states.clear()
        
        # Create entity states
        for i in range(1, 4):
            entity_state = EntityState()
            entity_state.total_unhealthy_time = i * 1000
            entity_state.alert_type_counts["alert-type-1"] = 1
            
            # Add to entity states
            entity_id = f"entity-{i}"
            self.mock_index.entity_states[entity_id] = entity_state
        
        # Add entities to ordered entities with duplicates
        # entity-1 appears at both -1000 and -500
        self.mock_index.ordered_entities[-1000] = {"entity-1"}
        self.mock_index.ordered_entities[-500] = {"entity-1"}  # Duplicate
        self.mock_index.ordered_entities[-2000] = {"entity-2"}
        self.mock_index.ordered_entities[-3000] = {"entity-3"}


if __name__ == "__main__":
    unittest.main()
