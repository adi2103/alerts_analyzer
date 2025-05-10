"""
Query Client for Alert Analysis System.

This module provides a client for querying the Alert Analysis Index Server.
"""

import argparse
import json
import requests
import sys

class QueryClient:
    """
    A client for querying the Alert Analysis Index Server.
    """
    
    def __init__(self, server_url="http://localhost:5000"):
        """
        Initialize the QueryClient.
        
        Args:
            server_url: URL of the index server
        """
        self.server_url = server_url
        
    def query(self, dimension="host", top=5, output_format="text"):
        """
        Query the index server for top k unhealthiest entities.
        
        Args:
            dimension: Dimension to analyze (host, dc, service, etc.)
            top: Number of entities to return
            output_format: Output format (text or json)
            
        Returns:
            str: Formatted results
        """
        try:
            response = requests.post(
                f"{self.server_url}/query",
                json={"dimension": dimension, "top": top}
            )
            
            if response.status_code != 200:
                return f"Error: {response.status_code} - {response.text}"
                
            results = response.json()
            
            if output_format == "json":
                return json.dumps(results, indent=2)
            else:
                # Format as text
                output = f"Top {top} unhealthiest {dimension}s:\n"
                for i, entity in enumerate(results, 1):
                    output += f"{i}. {entity[f'{dimension}_id']}: {entity['total_unhealthy_time']} seconds\n"
                    output += f"   Alert types: {entity['alert_types']}\n"
                return output
                
        except requests.exceptions.ConnectionError:
            return f"Error: Could not connect to server at {self.server_url}"
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    """Main entry point for the query client."""
    parser = argparse.ArgumentParser(description="Query Alert Analysis Index Server")
    parser.add_argument("dimension", help="Dimension to analyze (host, dc, service, etc.)")
    parser.add_argument("--top", "-k", type=int, default=5, help="Number of entities to return")
    parser.add_argument("--server", default="http://localhost:5000", help="Index server URL")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    client = QueryClient(args.server)
    result = client.query(args.dimension, args.top, args.format)
    
    print(result)
    
    return 0

if __name__ == "__main__":
    exit(main())
