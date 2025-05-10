"""Tests for the AlertAnalyzer class with the new components."""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.models import AlertEvent
from src.alert_analyzer import AlertAnalyzer
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine


class TestAlertAnalyzer(unittest.TestCase):
    """Test cases for the AlertAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock EventProcessor and QueryEngine
        self.mock_processor = MagicMock(spec=EventProcessor)
        self.mock_query_engine = MagicMock(spec=QueryEngine)
        
        # Create patches for the components
        self.processor_patch = patch('src.alert_analyzer.EventProcessor', return_value=self.mock_processor)
        self.query_engine_patch = patch('src.alert_analyzer.QueryEngine', return_value=self.mock_query_engine)
        
        # Start patches
        self.processor_patch.start()
        self.query_engine_patch.start()
        
        # Create AlertAnalyzer
        self.analyzer = AlertAnalyzer()
        
        # Verify the analyzer is using our mocks
        self.assertIs(self.analyzer.processor, self.mock_processor)
        self.assertIs(self.analyzer.query_engine, self.mock_query_engine)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.processor_patch.stop()
        self.query_engine_patch.stop()
    
    def test_analyze_file(self):
        """Test that analyze_file uses the EventProcessor."""
        # Set up mock return values
        self.mock_processor.process_file.return_value = 100  # 100 events processed
        self.mock_query_engine.get_top_k.return_value = [{"host_id": "test-host"}]
        
        # Call analyze_file
        results = self.analyzer.analyze_file(
            "test_file.gz", 
            dimension_name="host", 
            k=5, 
            alert_type=None
        )
        
        # Verify EventProcessor.process_file was called with the correct arguments
        self.mock_processor.process_file.assert_called_once_with("test_file.gz")
        
        # Verify QueryEngine.get_top_k was called with the correct arguments
        self.mock_query_engine.get_top_k.assert_called_once_with("host", 5)
        
        # Verify the results are correct
        self.assertEqual(results, [{"host_id": "test-host"}])
    
    def test_get_top_k(self):
        """Test that get_top_k uses the QueryEngine."""
        # Set up mock return value
        self.mock_query_engine.get_top_k.return_value = [{"host_id": "test-host"}]
        
        # Call get_top_k
        results = self.analyzer.get_top_k("host", 5)
        
        # Verify QueryEngine.get_top_k was called with the correct arguments
        self.mock_query_engine.get_top_k.assert_called_once_with("host", 5)
        
        # Verify the results are correct
        self.assertEqual(results, [{"host_id": "test-host"}])
    
    def test_get_top_k_with_alert_type(self):
        """Test that get_top_k logs a warning when alert_type is specified."""
        # Set up mock return value
        self.mock_query_engine.get_top_k.return_value = [{"host_id": "test-host"}]
        
        # Call get_top_k with alert_type
        with self.assertLogs(level='WARNING') as cm:
            results = self.analyzer.get_top_k("host", 5, alert_type="Disk Usage Alert")
        
        # Verify warning was logged
        self.assertIn("Alert type filtering is not supported", cm.output[0])
        
        # Verify QueryEngine.get_top_k was called with the correct arguments (without alert_type)
        self.mock_query_engine.get_top_k.assert_called_once_with("host", 5)
        
        # Verify the results are correct
        self.assertEqual(results, [{"host_id": "test-host"}])
    
    def test_get_results(self):
        """Test that get_results calls get_top_k."""
        # Set up mock return value
        self.mock_query_engine.get_top_k.return_value = [{"host_id": "test-host"}]
        
        # Call get_results
        results = self.analyzer.get_results("host", 5, alert_type=None)
        
        # Verify QueryEngine.get_top_k was called with the correct arguments
        self.mock_query_engine.get_top_k.assert_called_once_with("host", 5)
        
        # Verify the results are correct
        self.assertEqual(results, [{"host_id": "test-host"}])


if __name__ == "__main__":
    unittest.main()
