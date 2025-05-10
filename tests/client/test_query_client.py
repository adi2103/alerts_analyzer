"""
Tests for the Query Client.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from src.client.query_client import QueryClient

class TestQueryClient(unittest.TestCase):
    """Test cases for the QueryClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = QueryClient("http://localhost:5000")
        
    @patch('requests.post')
    def test_query_text_format(self, mock_post):
        """Test querying with text output format."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"host_id": "host1", "total_unhealthy_time": 3600, "alert_types": {"Disk Usage Alert": 1}},
            {"host_id": "host2", "total_unhealthy_time": 1800, "alert_types": {"System Service Failed": 1}}
        ]
        mock_post.return_value = mock_response
        
        # Make a query
        result = self.client.query("host", 2, "text")
        
        # Check the result
        self.assertIn("Top 2 unhealthiest hosts:", result)
        self.assertIn("host1: 3600 seconds", result)
        self.assertIn("host2: 1800 seconds", result)
        self.assertIn("Alert types:", result)
        
        # Verify the mock was called with the correct arguments
        mock_post.assert_called_once_with(
            "http://localhost:5000/query",
            json={"dimension": "host", "top": 2}
        )
        
    @patch('requests.post')
    def test_query_json_format(self, mock_post):
        """Test querying with JSON output format."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_results = [
            {"host_id": "host1", "total_unhealthy_time": 3600, "alert_types": {"Disk Usage Alert": 1}},
            {"host_id": "host2", "total_unhealthy_time": 1800, "alert_types": {"System Service Failed": 1}}
        ]
        mock_response.json.return_value = mock_results
        mock_post.return_value = mock_response
        
        # Make a query
        result = self.client.query("host", 2, "json")
        
        # Check the result
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, mock_results)
        
        # Verify the mock was called with the correct arguments
        mock_post.assert_called_once_with(
            "http://localhost:5000/query",
            json={"dimension": "host", "top": 2}
        )
        
    @patch('requests.post')
    def test_query_error(self, mock_post):
        """Test handling of server errors."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Make a query
        result = self.client.query("host", 2)
        
        # Check the result
        self.assertIn("Error: 500", result)
        self.assertIn("Internal Server Error", result)
        
    @patch('requests.post')
    def test_query_connection_error(self, mock_post):
        """Test handling of connection errors."""
        # Mock the response
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Make a query
        result = self.client.query("host", 2)
        
        # Check the result
        self.assertIn("Error: Could not connect to server", result)

if __name__ == '__main__':
    unittest.main()
