"""End-to-end tests for the Alert Analysis System."""

import os
import tempfile
import unittest
import json
from unittest.mock import patch
from io import StringIO
import sys

from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine
from src.alert_analyzer import AlertAnalyzer
from src.__main__ import main


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the Alert Analysis System."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file with test data
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        
        # Write some test alert events
        self.temp_file.write('{"event_id": "e1", "alert_id": "a1", "timestamp": "2023-01-01T10:00:00", "state": "NEW", "type": "Test Alert", "tags": {"host": "test-host-1", "dc": "dc-1"}}\n')
        self.temp_file.write('{"event_id": "e2", "alert_id": "a2", "timestamp": "2023-01-01T10:30:00", "state": "NEW", "type": "Test Alert", "tags": {"host": "test-host-2", "dc": "dc-1"}}\n')
        self.temp_file.write('{"event_id": "e3", "alert_id": "a1", "timestamp": "2023-01-01T11:00:00", "state": "RSV", "type": "Test Alert", "tags": {"host": "test-host-1", "dc": "dc-1"}}\n')
        self.temp_file.write('{"event_id": "e4", "alert_id": "a2", "timestamp": "2023-01-01T12:00:00", "state": "RSV", "type": "Test Alert", "tags": {"host": "test-host-2", "dc": "dc-1"}}\n')
        
        self.temp_file.close()

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        
        # Reset the singleton instance of IndexManager to ensure tests are isolated
        from src.indexing.index_manager import IndexManager
        IndexManager._instance = None

    def test_event_processor_and_query_engine(self):
        """Test the EventProcessor and QueryEngine workflow."""
        # Create an EventProcessor and process the test file
        processor = EventProcessor()
        events_processed = processor.process_file(self.temp_file.name)
        
        # Verify that all events were processed
        self.assertEqual(events_processed, 4)
        
        # Create a QueryEngine and query the top hosts
        query_engine = QueryEngine()
        results = query_engine.get_top_k("host", 2)
        
        # Verify the results
        self.assertEqual(len(results), 2)
        
        # Check that the hosts are sorted by unhealthy time
        # test-host-2 should be first (90 minutes = 5400 seconds)
        # test-host-1 should be second (60 minutes = 3600 seconds)
        self.assertEqual(results[0]["host_id"], "test-host-2")
        self.assertAlmostEqual(results[0]["total_unhealthy_time"], 5400, delta=1)
        self.assertEqual(results[1]["host_id"], "test-host-1")
        self.assertAlmostEqual(results[1]["total_unhealthy_time"], 3600, delta=1)
        
        # Query by data center
        dc_results = query_engine.get_top_k("dc", 1)
        
        # Verify the results
        self.assertEqual(len(dc_results), 1)
        self.assertEqual(dc_results[0]["dc_id"], "dc-1")
        # The total unhealthy time for dc-1 should be the sum of the unhealthy times
        # for test-host-1 and test-host-2, but accounting for overlap
        # Since both hosts are in dc-1, the total is not simply 5400 + 3600 = 9000
        # Instead, it's the total time the data center had at least one unhealthy host
        self.assertGreater(dc_results[0]["total_unhealthy_time"], 5400)  # At least as much as the longest host

    def test_backward_compatibility(self):
        """Test backward compatibility with AlertAnalyzer."""
        # Create an AlertAnalyzer
        analyzer = AlertAnalyzer()
        
        # Analyze the test file
        results = analyzer.analyze_file(self.temp_file.name, "host", 2)
        
        # Verify the results
        self.assertEqual(len(results), 2)
        
        # Check that the hosts are sorted by unhealthy time
        self.assertEqual(results[0]["host_id"], "test-host-2")
        self.assertAlmostEqual(results[0]["total_unhealthy_time"], 5400, delta=1)
        self.assertEqual(results[1]["host_id"], "test-host-1")
        self.assertAlmostEqual(results[1]["total_unhealthy_time"], 3600, delta=1)
        
        # Test with different dimension
        dc_results = analyzer.get_results("dc", 1)
        
        # Verify the results
        self.assertEqual(len(dc_results), 1)
        self.assertEqual(dc_results[0]["dc_id"], "dc-1")
        # The total unhealthy time for dc-1 should be the sum of the unhealthy times
        # for test-host-1 and test-host-2, but accounting for overlap
        self.assertGreater(dc_results[0]["total_unhealthy_time"], 5400)  # At least as much as the longest host

    def test_command_line_interface(self):
        """Test the command-line interface."""
        # Test the process command
        with patch('sys.argv', ['src', 'process', self.temp_file.name]):
            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output
            
            # Run the command
            main()
            
            # Reset stdout
            sys.stdout = sys.__stdout__
            
            # Check the output
            self.assertIn('Processed 4 events', captured_output.getvalue())
        
        # Test the query command
        with patch('sys.argv', ['src', 'query', 'host', '--top', '2']):
            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output
            
            # Run the command
            main()
            
            # Reset stdout
            sys.stdout = sys.__stdout__
            
            # Check the output
            output = captured_output.getvalue()
            self.assertIn('test-host-2', output)
            self.assertIn('test-host-1', output)
        
        # Test the legacy mode
        with patch('sys.argv', ['src', 'legacy', self.temp_file.name, '--dimension', 'dc', '--top', '1']):
            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output
            
            # Run the command
            main()
            
            # Reset stdout
            sys.stdout = sys.__stdout__
            
            # Check the output
            output = captured_output.getvalue()
            self.assertIn('dc-1', output)

    def test_with_sample_file(self):
        """Test with a small sample file to keep tests fast."""
        # Reset the singleton instance of IndexManager to ensure tests are isolated
        from src.indexing.index_manager import IndexManager
        IndexManager._instance = None
        
        # Create a smaller sample file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as sample_file:
            # Write a few test alert events
            sample_file.write('{"event_id": "e1", "alert_id": "a1", "timestamp": "2023-01-01T10:00:00", "state": "NEW", "type": "Sample Alert", "tags": {"host": "sample-host-1", "service": "service-1"}}\n')
            sample_file.write('{"event_id": "e2", "alert_id": "a1", "timestamp": "2023-01-01T10:30:00", "state": "RSV", "type": "Sample Alert", "tags": {"host": "sample-host-1", "service": "service-1"}}\n')
            sample_file_path = sample_file.name
        
        try:
            # Create an EventProcessor and process the sample file
            processor = EventProcessor()
            events_processed = processor.process_file(sample_file_path)
            
            # Verify that all events were processed
            self.assertEqual(events_processed, 2)
            
            # Create a QueryEngine and query the top hosts
            query_engine = QueryEngine()
            host_results = query_engine.get_top_k("host", 1)
            
            # Verify the results
            self.assertEqual(len(host_results), 1)
            self.assertEqual(host_results[0]["host_id"], "sample-host-1")
            self.assertAlmostEqual(host_results[0]["total_unhealthy_time"], 1800, delta=1)  # 30 minutes = 1800 seconds
            
            # Query by service
            service_results = query_engine.get_top_k("service", 1)
            
            # Verify the results
            self.assertEqual(len(service_results), 1)
            self.assertEqual(service_results[0]["service_id"], "service-1")
            self.assertAlmostEqual(service_results[0]["total_unhealthy_time"], 1800, delta=1)
            
        finally:
            # Clean up the sample file
            if os.path.exists(sample_file_path):
                os.unlink(sample_file_path)


if __name__ == '__main__':
    unittest.main()
