"""Tests for the ResultsManager class."""

import os
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

from src.utils.results_manager import ResultsManager
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine


class TestResultsManager(unittest.TestCase):
    """Test cases for the ResultsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test results
        self.temp_dir = tempfile.TemporaryDirectory()
        self.results_manager = ResultsManager(self.temp_dir.name)
        
        # Sample results for testing
        self.sample_results = [
            {
                "host_id": "test-host-1",
                "total_unhealthy_time": 3600,
                "alert_types": {"Test Alert": 1}
            },
            {
                "host_id": "test-host-2",
                "total_unhealthy_time": 1800,
                "alert_types": {"Test Alert": 2}
            }
        ]

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_save_results(self):
        """Test saving results."""
        # Save results
        filename, full_results = self.results_manager.save_results(
            self.sample_results,
            "test_file.gz",
            "host",
            2,
            None
        )
        
        # Check that the file was created
        self.assertTrue(os.path.exists(filename))
        
        # Check the structure of the saved results
        with open(filename, 'r') as f:
            saved_data = json.load(f)
            
        self.assertIn("query", saved_data)
        self.assertIn("results", saved_data)
        self.assertEqual(saved_data["results"], self.sample_results)
        self.assertEqual(saved_data["query"]["data_file"], "test_file.gz")
        self.assertEqual(saved_data["query"]["parameters"]["dimension"], "host")
        self.assertEqual(saved_data["query"]["parameters"]["top_k"], 2)
        self.assertIsNone(saved_data["query"]["parameters"]["alert_type"])

    def test_load_results(self):
        """Test loading results."""
        # Save results first
        filename, _ = self.results_manager.save_results(
            self.sample_results,
            "test_file.gz",
            "host",
            2,
            None
        )
        
        # Load the results
        loaded_results = self.results_manager.load_results(Path(filename).name)
        
        # Check that the loaded results match the original
        self.assertEqual(loaded_results["results"], self.sample_results)
        self.assertEqual(loaded_results["query"]["data_file"], "test_file.gz")

    def test_list_results(self):
        """Test listing results."""
        # Save multiple results
        self.results_manager.save_results(
            self.sample_results,
            "test_file1.gz",
            "host",
            2,
            None
        )
        
        self.results_manager.save_results(
            self.sample_results,
            "test_file2.gz",
            "dc",
            3,
            "Test Alert"
        )
        
        # List the results
        results_list = self.results_manager.list_results()
        
        # Check that both results are in the list
        self.assertEqual(len(results_list), 2)
        
        # Check that the metadata is correct
        self.assertEqual(results_list[0]["data_file"], "test_file2.gz")
        self.assertEqual(results_list[0]["dimension"], "dc")
        self.assertEqual(results_list[0]["top_k"], 3)
        self.assertEqual(results_list[0]["alert_type"], "Test Alert")
        
        self.assertEqual(results_list[1]["data_file"], "test_file1.gz")
        self.assertEqual(results_list[1]["dimension"], "host")
        self.assertEqual(results_list[1]["top_k"], 2)
        self.assertIsNone(results_list[1]["alert_type"])

    def test_save_results_with_alert_type(self):
        """Test saving results with alert type filter."""
        # Save results with alert type
        filename, full_results = self.results_manager.save_results(
            self.sample_results,
            "test_file.gz",
            "host",
            2,
            "Test Alert"
        )
        
        # Check the alert type in the saved results
        with open(filename, 'r') as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data["query"]["parameters"]["alert_type"], "Test Alert")

    def test_integration_with_new_components(self):
        """Test integration with EventProcessor and QueryEngine."""
        # This is a more comprehensive test that verifies the integration
        # between the new components and the ResultsManager
        
        # Create a temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            # Write some test alert events
            temp_file.write('{"event_id": "e1", "alert_id": "a1", "timestamp": "2023-01-01T10:00:00", "state": "NEW", "type": "Test Alert", "tags": {"host": "test-host-1"}}\n')
            temp_file.write('{"event_id": "e2", "alert_id": "a1", "timestamp": "2023-01-01T11:00:00", "state": "RSV", "type": "Test Alert", "tags": {"host": "test-host-1"}}\n')
            temp_file_path = temp_file.name
        
        try:
            # Use save_results function from the updated script
            from save_results import save_results
            
            # Save results using the new components
            filename, full_results = save_results(
                temp_file_path,
                dimension_name="host",
                k=1,
                alert_type=None
            )
            
            # Check that the results were saved correctly
            self.assertTrue(os.path.exists(filename))
            
            # Check the structure of the saved results
            with open(filename, 'r') as f:
                saved_data = json.load(f)
                
            self.assertIn("query", saved_data)
            self.assertIn("results", saved_data)
            self.assertEqual(len(saved_data["results"]), 1)
            self.assertEqual(saved_data["query"]["data_file"], temp_file_path)
            
            # Check that the results contain the expected host
            result = saved_data["results"][0]
            self.assertEqual(result["host_id"], "test-host-1")
            self.assertEqual(result["total_unhealthy_time"], 3600)  # 1 hour
            self.assertIn("Test Alert", result["alert_types"])
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


if __name__ == '__main__':
    unittest.main()
