"""Results management utilities for the Alert Analysis System."""

import json
import datetime
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union


class ResultsManager:
    """
    Manages saving and loading analysis results.
    
    This class provides functionality to save analysis results with query metadata
    and load previously saved results.
    """
    
    def __init__(self, results_dir: str = "results"):
        """
        Initialize a ResultsManager.
        
        Args:
            results_dir: Directory to store results (default: "results")
        """
        self.results_dir = Path(results_dir)
        
        # Create results directory if it doesn't exist
        if not self.results_dir.exists():
            os.makedirs(self.results_dir)
    
    def save_results(self, 
                    results: List[Dict[str, Any]], 
                    data_file: str, 
                    dimension_name: str, 
                    k: int, 
                    alert_type: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Save analysis results with query metadata.
        
        Args:
            results: Analysis results to save
            data_file: Path to the data file that was analyzed
            dimension_name: Dimension that was analyzed
            k: Number of entities that were requested
            alert_type: Alert type filter that was applied (if any)
            
        Returns:
            Tuple of (filename, full_results)
        """
        # Generate timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create metadata about the query
        query_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "data_file": data_file,
            "parameters": {
                "dimension": dimension_name,
                "top_k": k,
                "alert_type": alert_type
            }
        }
        
        # Create the full result object
        full_results = {
            "query": query_info,
            "results": results
        }
        
        # Save results to file
        filename = self.results_dir / f'query_results_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        return str(filename), full_results
    
    def load_results(self, filename: Union[str, Path]) -> Dict[str, Any]:
        """
        Load previously saved results.
        
        Args:
            filename: Path to the results file
            
        Returns:
            Dictionary containing the loaded results
            
        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        filepath = self.results_dir / filename if isinstance(filename, str) else filename
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def list_results(self) -> List[Dict[str, Any]]:
        """
        List all saved results with their metadata.
        
        Returns:
            List of dictionaries containing result metadata
        """
        results = []
        
        for file in self.results_dir.glob('query_results_*.json'):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    
                    # Extract metadata
                    metadata = {
                        "filename": file.name,
                        "timestamp": data["query"]["timestamp"],
                        "data_file": data["query"]["data_file"],
                        "dimension": data["query"]["parameters"]["dimension"],
                        "top_k": data["query"]["parameters"]["top_k"],
                        "alert_type": data["query"]["parameters"]["alert_type"],
                        "result_count": len(data["results"])
                    }
                    
                    results.append(metadata)
            except (json.JSONDecodeError, KeyError):
                # Skip invalid files
                continue
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results
