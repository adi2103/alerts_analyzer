"""Tests for the results management functionality."""

import pytest
import os
import json
import tempfile
import time
from pathlib import Path

from src.utils.results_manager import ResultsManager


class TestResultsManager:
    """Tests for the ResultsManager class."""
    
    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary directory for results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_results(self):
        """Sample results for testing."""
        return [
            {
                "host_id": "host-123",
                "total_unhealthy_time": 3600,
                "alert_types": {"Disk Usage Alert": 2}
            },
            {
                "host_id": "host-456",
                "total_unhealthy_time": 1800,
                "alert_types": {"System Service Failed": 1}
            }
        ]
    
    def test_save_results(self, temp_results_dir, sample_results):
        """Test saving results."""
        # Create results manager
        manager = ResultsManager(temp_results_dir)
        
        # Save results
        filename, full_results = manager.save_results(
            sample_results,
            "test_data.gz",
            "host",
            2,
            None
        )
        
        # Check that file exists
        assert os.path.exists(filename)
        
        # Check file content
        with open(filename, 'r') as f:
            saved_data = json.load(f)
        
        assert "query" in saved_data
        assert "results" in saved_data
        assert saved_data["query"]["data_file"] == "test_data.gz"
        assert saved_data["query"]["parameters"]["dimension"] == "host"
        assert saved_data["query"]["parameters"]["top_k"] == 2
        assert saved_data["query"]["parameters"]["alert_type"] is None
        assert saved_data["results"] == sample_results
    
    def test_load_results(self, temp_results_dir, sample_results):
        """Test loading results."""
        # Create results manager
        manager = ResultsManager(temp_results_dir)
        
        # Save results
        filename, _ = manager.save_results(
            sample_results,
            "test_data.gz",
            "host",
            2,
            None
        )
        
        # Load results
        loaded_data = manager.load_results(Path(filename).name)
        
        # Check loaded data
        assert "query" in loaded_data
        assert "results" in loaded_data
        assert loaded_data["results"] == sample_results
    
    def test_list_results(self, temp_results_dir):
        """Test listing results."""
        # Create results manager
        manager = ResultsManager(temp_results_dir)
        
        # Save first result
        manager.save_results(
            [{"host_id": "host-1", "total_unhealthy_time": 3600, "alert_types": {}}],
            "data1.gz",
            "host",
            1,
            None
        )
        
        # Wait a moment to ensure different timestamps
        time.sleep(0.1)
        
        # Save second result
        manager.save_results(
            [{"dc_id": "dc-1", "total_unhealthy_time": 7200, "alert_types": {}}],
            "data2.gz",
            "dc",
            1,
            "Disk Usage Alert"
        )
        
        # List results
        results_list = manager.list_results()
        
        # Check list
        assert len(results_list) == 2
        
        # Check second result (most recent first)
        assert results_list[0]["data_file"] == "data2.gz"
        assert results_list[0]["dimension"] == "dc"
        assert results_list[0]["alert_type"] == "Disk Usage Alert"
        
        # Check first result
        assert results_list[1]["data_file"] == "data1.gz"
        assert results_list[1]["dimension"] == "host"
        assert results_list[1]["alert_type"] is None
