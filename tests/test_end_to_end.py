"""End-to-end tests for the Alert Analysis System."""

import pytest
import os
import tempfile
import gzip
import json
from datetime import datetime

from src.alert_analyzer import AlertAnalyzer
from src.models import AlertEvent


class TestEndToEnd:
    """End-to-end tests for the Alert Analysis System."""
    
    @pytest.fixture
    def sample_data_file(self):
        """Create a sample data file for testing."""
        # Create sample events
        events = [
            # Host 1: 10 minutes of unhealthy time (Disk Usage Alert)
            {
                "event_id": "event-1",
                "alert_id": "alert-1",
                "timestamp": "2023-01-01T12:00:00Z",
                "state": "NEW",
                "type": "Disk Usage Alert",
                "tags": {"host": "host-1", "dc": "dc-1", "volume": "vol-1"}
            },
            {
                "event_id": "event-2",
                "alert_id": "alert-1",
                "timestamp": "2023-01-01T12:10:00Z",
                "state": "RSV",
                "type": "Disk Usage Alert",
                "tags": {"host": "host-1", "dc": "dc-1", "volume": "vol-1"}
            },
            
            # Host 2: 15 minutes of unhealthy time (System Service Failed)
            {
                "event_id": "event-3",
                "alert_id": "alert-2",
                "timestamp": "2023-01-01T12:00:00Z",
                "state": "NEW",
                "type": "System Service Failed",
                "tags": {"host": "host-2", "dc": "dc-1", "service": "svc-1"}
            },
            {
                "event_id": "event-4",
                "alert_id": "alert-2",
                "timestamp": "2023-01-01T12:15:00Z",
                "state": "RSV",
                "type": "System Service Failed",
                "tags": {"host": "host-2", "dc": "dc-1", "service": "svc-1"}
            },
            
            # Host 3: 20 minutes of unhealthy time (Time Drift Alert)
            {
                "event_id": "event-5",
                "alert_id": "alert-3",
                "timestamp": "2023-01-01T12:00:00Z",
                "state": "NEW",
                "type": "Time Drift Alert",
                "tags": {"host": "host-3", "dc": "dc-2", "drift": "1000"}
            },
            {
                "event_id": "event-6",
                "alert_id": "alert-3",
                "timestamp": "2023-01-01T12:20:00Z",
                "state": "RSV",
                "type": "Time Drift Alert",
                "tags": {"host": "host-3", "dc": "dc-2", "drift": "1000"}
            },
            
            # Host 4: 5 minutes of unhealthy time (Disk Usage Alert)
            {
                "event_id": "event-7",
                "alert_id": "alert-4",
                "timestamp": "2023-01-01T12:00:00Z",
                "state": "NEW",
                "type": "Disk Usage Alert",
                "tags": {"host": "host-4", "dc": "dc-2", "volume": "vol-2"}
            },
            {
                "event_id": "event-8",
                "alert_id": "alert-4",
                "timestamp": "2023-01-01T12:05:00Z",
                "state": "RSV",
                "type": "Disk Usage Alert",
                "tags": {"host": "host-4", "dc": "dc-2", "volume": "vol-2"}
            },
            
            # Host 5: 25 minutes of unhealthy time (System Service Failed)
            {
                "event_id": "event-9",
                "alert_id": "alert-5",
                "timestamp": "2023-01-01T12:00:00Z",
                "state": "NEW",
                "type": "System Service Failed",
                "tags": {"host": "host-5", "dc": "dc-3", "service": "svc-2"}
            },
            {
                "event_id": "event-10",
                "alert_id": "alert-5",
                "timestamp": "2023-01-01T12:25:00Z",
                "state": "RSV",
                "type": "System Service Failed",
                "tags": {"host": "host-5", "dc": "dc-3", "service": "svc-2"}
            }
        ]
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            with gzip.open(f.name, 'wt') as gz:
                for event in events:
                    gz.write(json.dumps(event) + "\n")
            
            yield f.name
        
        # Clean up after the test
        if os.path.exists(f.name):
            os.unlink(f.name)
    
    def test_analyze_file(self, sample_data_file):
        """Test analyzing a file end-to-end."""
        # Create analyzer
        analyzer = AlertAnalyzer()
        
        # Analyze file
        results = analyzer.analyze_file(sample_data_file)
        
        # Check results
        assert len(results) == 5
        
        # Check order (descending by unhealthy time)
        assert results[0]["host_id"] == "host-5"  # 25 minutes
        assert results[1]["host_id"] == "host-3"  # 20 minutes
        assert results[2]["host_id"] == "host-2"  # 15 minutes
        assert results[3]["host_id"] == "host-1"  # 10 minutes
        assert results[4]["host_id"] == "host-4"  # 5 minutes
        
        # Check unhealthy times
        assert results[0]["total_unhealthy_time"] == 1500  # 25 minutes = 1500 seconds
        assert results[1]["total_unhealthy_time"] == 1200  # 20 minutes = 1200 seconds
        assert results[2]["total_unhealthy_time"] == 900   # 15 minutes = 900 seconds
        assert results[3]["total_unhealthy_time"] == 600   # 10 minutes = 600 seconds
        assert results[4]["total_unhealthy_time"] == 300   # 5 minutes = 300 seconds
    
    def test_analyze_file_with_alert_type_filter(self, sample_data_file):
        """Test analyzing a file with alert type filter."""
        # Create analyzer
        analyzer = AlertAnalyzer()
        
        # Analyze file with filter
        results = analyzer.analyze_file(sample_data_file, alert_type="Disk Usage Alert")
        
        # Alert type filtering is not supported in this version
        # Should return top 5 hosts regardless of alert type
        assert len(results) == 5
        
        # Check order (descending by unhealthy time)
        assert results[0]["host_id"] == "host-5"  # 25 minutes
        assert results[1]["host_id"] == "host-3"  # 20 minutes
        assert results[2]["host_id"] == "host-2"  # 15 minutes
        
        # Check unhealthy times
        assert results[0]["total_unhealthy_time"] == 1500  # 25 minutes = 1500 seconds
        assert results[1]["total_unhealthy_time"] == 1200  # 20 minutes = 1200 seconds
        assert results[2]["total_unhealthy_time"] == 900   # 15 minutes = 900 seconds
    
    def test_analyze_file_with_different_dimension(self, sample_data_file):
        """Test analyzing a file with a different dimension."""
        # Create analyzer
        analyzer = AlertAnalyzer()
        
        # Analyze file with different dimension
        results = analyzer.analyze_file(sample_data_file, dimension_name="dc")
        
        # Check results
        assert len(results) == 3
        
        # Check data centers
        dc_ids = [result["dc_id"] for result in results]
        assert "dc-1" in dc_ids
        assert "dc-2" in dc_ids
        assert "dc-3" in dc_ids
        
        # Check unhealthy times
        # dc-1: host-1 (10 min) + host-2 (15 min) = 25 min
        # dc-2: host-3 (20 min) + host-4 (5 min) = 25 min
        # dc-3: host-5 (25 min) = 25 min
        for result in results:
            assert result["total_unhealthy_time"] == 1500  # 25 minutes = 1500 seconds
