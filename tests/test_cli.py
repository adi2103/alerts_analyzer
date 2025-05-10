"""Tests for the command-line interface."""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from src.__main__ import main, parse_args
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine


class TestCommandLineInterface(unittest.TestCase):
    """Test cases for the command-line interface."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    @patch('src.processors.event_processor.EventProcessor.process_file')
    def test_process_command(self, mock_process_file):
        """Test the process command."""
        # Mock the process_file method to return a specific value
        mock_process_file.return_value = 42

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Run the command
        with patch('sys.argv', ['src', 'process', 'test_file.gz']):
            main()

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Check that process_file was called with the correct arguments
        mock_process_file.assert_called_once_with('test_file.gz')

        # Check the output
        self.assertIn('Processed 42 events', captured_output.getvalue())

    @patch('src.query.query_engine.QueryEngine.get_top_k')
    def test_query_command(self, mock_get_top_k):
        """Test the query command."""
        # Mock the get_top_k method to return specific results
        mock_get_top_k.return_value = [
            {
                'host_id': 'test-host-1',
                'total_unhealthy_time': 3600,
                'alert_types': {'Test Alert': 1}
            },
            {
                'host_id': 'test-host-2',
                'total_unhealthy_time': 1800,
                'alert_types': {'Test Alert': 2}
            }
        ]

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Run the command
        with patch('sys.argv', ['src', 'query', 'host', '--top', '2']):
            main()

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Check that get_top_k was called with the correct arguments
        mock_get_top_k.assert_called_once_with('host', 2)

        # Check the output
        output = captured_output.getvalue()
        self.assertIn('test-host-1', output)
        self.assertIn('3600 seconds', output)
        self.assertIn('test-host-2', output)
        self.assertIn('1800 seconds', output)

    @patch('src.alert_analyzer.AlertAnalyzer.analyze_file')
    def test_legacy_mode(self, mock_analyze_file):
        """Test the legacy mode."""
        # Mock the analyze_file method to return specific results
        mock_analyze_file.return_value = [
            {
                'host_id': 'legacy-host-1',
                'total_unhealthy_time': 7200,
                'alert_types': {'Legacy Alert': 1}
            }
        ]

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Run the command
        with patch('sys.argv', ['src', 'legacy', 'test_file.gz', '--dimension', 'host', '--top', '1']):
            main()

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Check that analyze_file was called with the correct arguments
        mock_analyze_file.assert_called_once_with('test_file.gz', 'host', 1, None)

        # Check the output
        output = captured_output.getvalue()
        self.assertIn('legacy-host-1', output)
        self.assertIn('7200 seconds', output)

    @patch('src.alert_analyzer.AlertAnalyzer.analyze_file')
    def test_backward_compatibility(self, mock_analyze_file):
        """Test backward compatibility (no command specified)."""
        # Mock the analyze_file method to return specific results
        mock_analyze_file.return_value = [
            {
                'host_id': 'compat-host-1',
                'total_unhealthy_time': 5400,
                'alert_types': {'Compat Alert': 1}
            }
        ]

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Run the command with no explicit command (should default to legacy mode)
        with patch('sys.argv', ['src', 'test_file.gz', '--dimension', 'host']):
            main()

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Check that analyze_file was called with the correct arguments
        mock_analyze_file.assert_called_once_with('test_file.gz', 'host', 5, None)

        # Check the output
        output = captured_output.getvalue()
        self.assertIn('compat-host-1', output)
        self.assertIn('5400 seconds', output)

    def test_output_to_file(self):
        """Test writing output to a file."""
        # Mock the QueryEngine.get_top_k method
        with patch('src.query.query_engine.QueryEngine.get_top_k') as mock_get_top_k:
            # Set up the mock to return specific results
            mock_get_top_k.return_value = [
                {
                    'host_id': 'file-host-1',
                    'total_unhealthy_time': 1200,
                    'alert_types': {'File Alert': 1}
                }
            ]

            # Run the command with output to a file
            with patch('sys.argv', ['src', 'query', 'host', '--output', self.temp_file.name]):
                main()

            # Check that the file was created and contains the expected output
            with open(self.temp_file.name, 'r') as f:
                output = f.read()
                self.assertIn('file-host-1', output)
                self.assertIn('1200 seconds', output)

    def test_json_format(self):
        """Test JSON output format."""
        # Mock the QueryEngine.get_top_k method
        with patch('src.query.query_engine.QueryEngine.get_top_k') as mock_get_top_k:
            # Set up the mock to return specific results
            mock_results = [
                {
                    'host_id': 'json-host-1',
                    'total_unhealthy_time': 900,
                    'alert_types': {'JSON Alert': 1}
                }
            ]
            mock_get_top_k.return_value = mock_results

            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            # Run the command with JSON format
            with patch('sys.argv', ['src', 'query', 'host', '--format', 'json']):
                main()

            # Reset stdout
            sys.stdout = sys.__stdout__

            # Check that the output is valid JSON and contains the expected data
            output = captured_output.getvalue()
            parsed_output = json.loads(output)
            self.assertEqual(parsed_output, mock_results)

    def test_error_handling(self):
        """Test error handling."""
        # Mock the EventProcessor.process_file method to raise an exception
        with patch('src.processors.event_processor.EventProcessor.process_file') as mock_process_file:
            mock_process_file.side_effect = ValueError("Test error")

            # Capture stderr
            captured_error = StringIO()
            sys.stderr = captured_error

            # Run the command
            with patch('sys.argv', ['src', 'process', 'nonexistent_file.gz']):
                with self.assertRaises(SystemExit):
                    main()

            # Reset stderr
            sys.stderr = sys.__stderr__

            # Check the error output
            self.assertIn('Error: Test error', captured_error.getvalue())


if __name__ == '__main__':
    unittest.main()
