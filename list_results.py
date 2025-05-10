#!/usr/bin/env python3

import argparse
from src.utils.results_manager import ResultsManager


def list_results():
    """List all saved analysis results."""
    results_manager = ResultsManager()
    results = results_manager.list_results()

    if not results:
        print("No saved results found.")
        return

    print(f"Found {len(results)} saved results:")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['filename']}")
        print(f"   Timestamp: {result['timestamp']}")
        print(f"   Data File: {result['data_file']}")
        print(f"   Query: Top {result['top_k']} {result['dimension']}s")
        if result['alert_type']:
            print(f"   Alert Type Filter: {result['alert_type']}")
        print(f"   Result Count: {result['result_count']}")
        print("-" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List saved analysis results")
    args = parser.parse_args()

    list_results()
