#!/usr/bin/env python3

import json
import datetime
import argparse
from src.alert_analyzer import AlertAnalyzer
from src.utils.results_manager import ResultsManager

def save_results(file_path, dimension_name='host', k=5, alert_type=None):
    """
    Analyze alert data and save results with query metadata.
    
    Args:
        file_path: Path to the alert data file
        dimension_name: Dimension to analyze
        k: Number of entities to return
        alert_type: Optional filter for specific alert type
    """
    # Create analyzer
    analyzer = AlertAnalyzer()
    
    # Analyze file
    results = analyzer.analyze_file(file_path, dimension_name=dimension_name, k=k, alert_type=alert_type)
    
    # Save results using ResultsManager
    results_manager = ResultsManager()
    filename, full_results = results_manager.save_results(
        results,
        file_path,
        dimension_name,
        k,
        alert_type
    )
    
    print(f'Results saved to {filename}')
    
    # Print summary of results
    print(f"\nTop {k} Unhealthiest {dimension_name.capitalize()}s:")
    print("=" * 40)
    
    for i, result in enumerate(results, 1):
        # Get the entity ID (could be host_id, dc_id, etc.)
        entity_id_key = next((key for key in result.keys() if key.endswith("_id")), None)
        entity_id = result.get(entity_id_key, "Unknown")
        
        print(f"{i}. {entity_id}: {result['total_unhealthy_time']:.2f} seconds")
        
        # Print alert types
        if result['alert_types']:
            print("   Alert Types:")
            for alert_type, count in result['alert_types'].items():
                print(f"     - {alert_type}: {count}")
        
        print()
    
    return filename, full_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze alert data and save results")
    parser.add_argument("file_path", help="Path to the alert data file")
    parser.add_argument("--dimension", "-d", default="host", help="Dimension to analyze")
    parser.add_argument("--top", "-k", type=int, default=5, help="Number of entities to return")
    parser.add_argument("--alert-type", "-t", help="Filter by alert type")
    
    args = parser.parse_args()
    
    save_results(
        args.file_path,
        dimension_name=args.dimension,
        k=args.top,
        alert_type=args.alert_type
    )
