"""
Simple Query Client for Alert Analysis System.

This module provides a client for querying the Simple Alert Analysis Index Server.
"""

import argparse
import json
import urllib.request
import urllib.parse
import urllib.error
import logging

class SimpleQueryClient:
    """
    A client for querying the Simple Alert Analysis Index Server.
    """
    
    def __init__(self, server_url="http://localhost:5000"):
        """
        Initialize the SimpleQueryClient.
        
        Args:
            server_url: URL of the index server
        """
        self.server_url = server_url
        self.logger = logging.getLogger("simple_query_client")
        
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
            # Build the query URL
            query_params = urllib.parse.urlencode({
                "dimension": dimension,
                "top": top
            })
            url = f"{self.server_url}/query?{query_params}"
            
            self.logger.info(f"Sending request to {url}")
            
            # Send the request
            with urllib.request.urlopen(url) as response:
                data = response.read().decode('utf-8')
                results = json.loads(data)
                
                if output_format == "json":
                    return json.dumps(results, indent=2)
                else:
                    # Format as text
                    output = f"Top {top} unhealthiest {dimension}s:\n"
                    for i, entity in enumerate(results, 1):
                        output += f"{i}. {entity[f'{dimension}_id']}: {entity['total_unhealthy_time']} seconds\n"
                        output += f"   Alert types: {entity['alert_types']}\n"
                    return output
                    
        except urllib.error.URLError as e:
            self.logger.error(f"URL error: {str(e)}")
            return f"Error: Could not connect to server at {self.server_url}"
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP error: {e.code} - {e.reason}")
            return f"Error: {e.code} - {e.reason}"
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return f"Error: {str(e)}"

def main():
    """Main entry point for the simple query client."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Query Simple Alert Analysis Index Server")
    parser.add_argument("dimension", help="Dimension to analyze (host, dc, service, etc.)")
    parser.add_argument("--top", "-k", type=int, default=5, help="Number of entities to return")
    parser.add_argument("--server", default="http://localhost:5000", help="Index server URL")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    client = SimpleQueryClient(args.server)
    result = client.query(args.dimension, args.top, args.format)
    
    print(result)
    
    return 0

if __name__ == "__main__":
    exit(main())
