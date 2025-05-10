"""Tests for the IndexManager class."""

import unittest
from unittest.mock import MagicMock

from src.models import AlertState
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


if __name__ == "__main__":
    unittest.main()
