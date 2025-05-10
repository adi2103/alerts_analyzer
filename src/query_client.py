"""
Query Client for Alert Analysis System.

This module provides a client for querying the Alert Analysis Index Server
and managing analysis results.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List

import requests

from src.results_manager import ResultsManager


class QueryClient:
    """
    A client for querying the Alert Analysis Index Server and managing results.
    """

    def __init__(self, server_url="http://localhost:8080"):
        """
        Initialize the QueryClient.

        Args:
            server_url: URL of the index server
        """
        self.server_url = server_url
        self.logger = logging.getLogger("query_client")
        self.results_manager = ResultsManager()

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
            # First try a GET request
            self.logger.info(f"Sending GET request to {self.server_url}/query")
            response = requests.get(
                f"{self.server_url}/query",
                params={"dimension": dimension, "top": top},
                headers={"Content-Type": "application/json"},
            )

            # If GET fails, try POST
            if response.status_code != 200:
                self.logger.info(
                    f"GET request failed with status {response.status_code}, trying POST"
                )
                response = requests.post(
                    f"{self.server_url}/query",
                    json={"dimension": dimension, "top": top},
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code != 200:
                self.logger.error(
                    f"Request failed with status {response.status_code}: {response.text}"
                )
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

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {str(e)}")
            return f"Error: Could not connect to server at {self.server_url}"
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return f"Error: {str(e)}"

    def save_results(
        self, results: List[Dict[str, Any]], dimension: str, top: int
    ) -> str:
        """
        Save query results with metadata.

        Args:
            results: The query results to save
            dimension: The dimension that was queried
            top: The number of results requested

        Returns:
            str: Path to the saved results file
        """
        filename, _ = self.results_manager.save_results(
            results, dimension, top, None  # No alert type filtering
        )
        return filename

    def list_results(self, output_format="text"):
        """
        List all saved analysis results.

        Args:
            output_format: Output format (text or json)

        Returns:
            str: Formatted list of results
        """
        results = self.results_manager.list_results()

        if not results:
            return "No saved results found."

        if output_format == "json":
            return json.dumps(results, indent=2)
        else:
            output = f"Found {len(results)} saved results:\n"
            output += "=" * 80 + "\n"

            for i, result in enumerate(results, 1):
                output += f"{i}. {result['filename']}\n"
                output += f"   Timestamp: {result['timestamp']}\n"
                output += f"   Data File: {result['data_file']}\n"
                output += f"   Query: Top {result['top_k']} {result['dimension']}s\n"
                output += f"   Result Count: {result['result_count']}\n"
                output += "-" * 80 + "\n"

            return output

    def load_result(self, filename: str, output_format="text"):
        """
        Load a saved result.

        Args:
            filename: Name of the result file to load
            output_format: Output format (text or json)

        Returns:
            str: Formatted result
        """
        try:
            result = self.results_manager.load_results(filename)

            if output_format == "json":
                return json.dumps(result, indent=2)
            else:
                dimension = result["query"]["parameters"]["dimension"]
                top = result["query"]["parameters"]["top_k"]

                output = f"Results from {filename}:\n"
                output += f"Query: Top {top} unhealthiest {dimension}s\n"
                output += f"Data File: {result['query']['data_file']}\n"
                output += f"Timestamp: {result['query']['timestamp']}\n"
                output += "=" * 80 + "\n"

                for i, entity in enumerate(result["results"], 1):
                    output += f"{i}. {entity[f'{dimension}_id']}: {entity['total_unhealthy_time']} seconds\n"
                    output += f"   Alert types: {entity['alert_types']}\n"

                return output

        except FileNotFoundError:
            return f"Error: Result file '{filename}' not found"
        except json.JSONDecodeError:
            return f"Error: Result file '{filename}' is not valid JSON"
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    """Main entry point for the query client."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Alert Analysis System Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Query command
    query_parser = subparsers.add_parser(
        "query", help="Query the server for unhealthy entities"
    )
    query_parser.add_argument(
        "dimension", help="Dimension to analyze (host, dc, service, etc.)"
    )
    query_parser.add_argument(
        "--top", "-k", type=int, default=5, help="Number of entities to return"
    )
    query_parser.add_argument(
        "--server", default="http://localhost:8080", help="Index server URL"
    )
    query_parser.add_argument(
        "--format", "-f", choices=["text", "json"], default="text", help="Output format"
    )
    query_parser.add_argument(
        "--save", "-s", action="store_true", help="Save the query results"
    )
    query_parser.add_argument(
        "--data-file", "-d", help="Data file name (for metadata when saving)"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List saved analysis results")
    list_parser.add_argument(
        "--format", "-f", choices=["text", "json"], default="text", help="Output format"
    )

    # Load command
    load_parser = subparsers.add_parser("load", help="Load a saved analysis result")
    load_parser.add_argument("filename", help="Name of the result file to load")
    load_parser.add_argument(
        "--format", "-f", choices=["text", "json"], default="text", help="Output format"
    )

    # Common options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Default to query command if none specified
    if not args.command:
        if len(sys.argv) > 1:
            # Assume the first argument is the dimension for backward compatibility
            args.command = "query"
            args.dimension = sys.argv[1]
            args.top = 5
            args.server = "http://localhost:8080"
            args.format = "text"
            args.save = False
            args.data_file = None
        else:
            parser.print_help()
            return 1

    client = QueryClient(getattr(args, "server", "http://localhost:8080"))

    if args.command == "query":
        results_text = client.query(args.dimension, args.top, args.format)
        print(results_text)

        # Save results if requested
        if args.save:
            try:
                # Parse the results to get the actual data
                if args.format == "json":
                    results_data = json.loads(results_text)
                else:
                    # For text format, we need to query again to get the raw data
                    response = requests.get(
                        f"{client.server_url}/query",
                        params={"dimension": args.dimension, "top": args.top},
                    )
                    results_data = response.json()

                # Use provided data file name or a default
                data_file = args.data_file or "unknown_data_file"

                # Save the results
                filename = client.save_results(
                    results_data, args.dimension, args.top
                )
                print(f"\nResults saved to {filename}")
            except Exception as e:
                print(f"Error saving results: {str(e)}")

    elif args.command == "list":
        results = client.list_results(args.format)
        print(results)

    elif args.command == "load":
        result = client.load_result(args.filename, args.format)
        print(result)

    return 0


if __name__ == "__main__":
    exit(main())
