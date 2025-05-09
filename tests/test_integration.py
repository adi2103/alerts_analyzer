"""Integration tests for the Alert Analysis System."""

import pytest
import os
from pathlib import Path

from src.alert_analyzer import AlertAnalyzer


class TestIntegration:
    """Integration tests for the Alert Analysis System."""
    
    @pytest.fixture
    def data_file(self):
        """Path to the actual data file."""
        data_path = Path(__file__).parent.parent / "data" / "Alert_Event_Data.gz"
        if not data_path.exists():
            pytest.skip(f"Data file not found: {data_path}")
        return data_path
    
    def test_analyze_real_data(self, data_file):
        """Test analyzing the real data file."""
        # Create analyzer
        analyzer = AlertAnalyzer()
        
        # Analyze file
        results = analyzer.analyze_file(data_file, dimension_name='host', k=5)
        
        # Check results
        assert len(results) == 5
        
        # Verify the top 5 hosts match our expected results
        expected_hosts = [
            "host-89a9a342729c4e5b",
            "host-e757d9e2e784b5b0",
            "host-34fccaf645969be4",
            "host-4b878e6158364b3a",
            "host-45b4899390b28fdb"
        ]
        
        actual_hosts = [result["host_id"] for result in results]
        assert actual_hosts == expected_hosts
        
        # Verify the unhealthy times are correct (with some tolerance for floating point)
        expected_times = [
            145521.49419099998,
            84627.52385700001,
            61486.785445,
            60371.876107,
            56419.925382
        ]
        
        for i, result in enumerate(results):
            assert abs(result["total_unhealthy_time"] - expected_times[i]) < 0.01
        
        # Verify all hosts have Disk Usage Alert
        for result in results:
            assert "Disk Usage Alert" in result["alert_types"]
    
    def test_filter_by_alert_type(self, data_file):
        """Test filtering by alert type on the real data."""
        # Create analyzer
        analyzer = AlertAnalyzer()
        
        # Analyze file with filter
        results = analyzer.analyze_file(
            data_file, 
            dimension_name='host', 
            k=5, 
            alert_type="Disk Usage Alert"
        )
        
        # Check results
        assert len(results) == 5
        
        # Verify all hosts have only Disk Usage Alert
        for result in results:
            assert list(result["alert_types"].keys()) == ["Disk Usage Alert"]
    
    def test_system_service_failed_alert_type(self, data_file):
        """Test filtering by System Service Failed alert type."""
        # Create analyzer
        analyzer = AlertAnalyzer()
        
        # Analyze file with filter
        results = analyzer.analyze_file(
            data_file, 
            dimension_name='host', 
            k=5, 
            alert_type="System Service Failed"
        )
        
        # Check results
        assert len(results) == 4  # There are only 4 hosts with System Service Failed alerts
        
        # Verify the expected hosts and order
        expected_hosts = [
            "host-7f80606d430fb7da",
            "host-4e89fdb9fdfc429a",
            "host-bf499e046e947f4a",
            "host-22f1fddd19b60a0f"
        ]
        
        actual_hosts = [result["host_id"] for result in results]
        assert actual_hosts == expected_hosts
        
        # Verify the unhealthy times are correct (with some tolerance for floating point)
        expected_times = [
            15921.627101,
            7092.053203,
            5473.398237,
            2784.730161
        ]
        
        for i, result in enumerate(results):
            assert abs(result["total_unhealthy_time"] - expected_times[i]) < 0.01
        
        # Verify all hosts have System Service Failed alert
        for result in results:
            assert "System Service Failed" in result["alert_types"]
            
        # Verify no duplicates in results
        assert len(set(actual_hosts)) == len(actual_hosts)
