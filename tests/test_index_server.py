"""
Tests for the Index Server.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.index_server import IndexServer


class TestIndexServer(unittest.TestCase):
    """Test cases for the IndexServer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = IndexServer()
        self.app = self.server.app.test_client()

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.app.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")

    @patch("src.query_engine.QueryEngine.get_top_k")
    def test_query_endpoint(self, mock_get_top_k):
        """Test the query endpoint."""
        # Mock the query engine response
        mock_results = [
            {
                "host_id": "host1",
                "total_unhealthy_time": 3600,
                "alert_types": {"Disk Usage Alert": 1},
            },
            {
                "host_id": "host2",
                "total_unhealthy_time": 1800,
                "alert_types": {"System Service Failed": 1},
            },
        ]
        mock_get_top_k.return_value = mock_results

        # Make a request to the query endpoint
        response = self.app.post(
            "/query",
            data=json.dumps({"dimension": "host", "top": 2}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, mock_results)

        # Verify the mock was called with the correct arguments
        mock_get_top_k.assert_called_once_with("host", 2)

    @patch("src.event_processor.EventProcessor.process_file")
    def test_process_file(self, mock_process_file):
        """Test processing a file."""
        # Mock the event processor response
        mock_process_file.return_value = 100

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name

        try:
            # Process the file
            events_processed = self.server.process_file(temp_path)

            # Check the result
            self.assertEqual(events_processed, 100)

            # Verify the mock was called with the correct arguments
            mock_process_file.assert_called_once_with(temp_path)

        finally:
            # Clean up
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
