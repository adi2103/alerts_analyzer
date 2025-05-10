"""
Index Server for Alert Analysis System.

This module provides a server that processes alert events and maintains indices in memory,
allowing for queries from multiple clients.
"""

import argparse
import logging
import os

from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from src.event_processor import EventProcessor
from src.query_engine import QueryEngine


class IndexServer:
    """
    A server that processes alert events and maintains indices in memory.

    The server exposes a REST API for querying the indices.
    """

    def __init__(self):
        """Initialize the IndexServer."""
        self.processor = EventProcessor()
        self.query_engine = QueryEngine()
        self.app = Flask(__name__)
        self.processed_files = []

        # Enable CORS for all routes with all origins
        CORS(self.app, resources={r"/*": {"origins": "*"}})

        self.logger = logging.getLogger("index_server")

        # Register routes
        self.register_routes()

    def register_routes(self):
        """Register the API routes."""

        @self.app.route("/", methods=["GET"])
        def index():
            """Root endpoint."""
            return jsonify(
                {
                    "status": "ok",
                    "message": "Alert Analysis Index Server is running",
                    "endpoints": ["/health", "/query", "/files"],
                    "processed_files": self.processed_files,
                }
            )

        @self.app.route("/query", methods=["POST", "GET"])
        def query():
            """Handle query requests."""
            try:
                # Log the request details for debugging
                self.logger.info(f"Request method: {request.method}")
                self.logger.info(f"Request headers: {dict(request.headers)}")
                self.logger.info(f"Request args: {dict(request.args)}")

                if request.method == "GET":
                    # Handle GET request
                    dimension = request.args.get("dimension", "host")
                    try:
                        k = int(request.args.get("top", 5))
                    except (ValueError, TypeError):
                        k = 5
                elif request.is_json:
                    # Handle JSON POST request
                    data = request.json
                    dimension = data.get("dimension", "host")
                    k = data.get("top", 5)
                else:
                    # Handle form POST request
                    dimension = request.form.get("dimension", "host")
                    try:
                        k = int(request.form.get("top", 5))
                    except (ValueError, TypeError):
                        k = 5

                self.logger.info(f"Processing query: dimension={dimension}, top={k}")
                results = self.query_engine.get_top_k(dimension, k)

                # Return results with explicit CORS headers
                response = jsonify(results)
                response.headers.add("Access-Control-Allow-Origin", "*")
                response.headers.add(
                    "Access-Control-Allow-Headers", "Content-Type,Authorization"
                )
                response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
                return response

            except Exception as e:
                self.logger.error(f"Error processing query: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/health", methods=["GET"])
        def health():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "processed_files": self.processed_files,
                    "processed_file_count": len(self.processed_files),
                }
            )

        @self.app.route("/files", methods=["GET"])
        def files():
            """List processed files."""
            return jsonify(
                {
                    "processed_files": self.processed_files,
                    "count": len(self.processed_files),
                }
            )

        @self.app.route("/query", methods=["OPTIONS"])
        def options():
            """Handle OPTIONS requests for CORS preflight."""
            response = Response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type,Authorization"
            )
            response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            return response

    def process_file(self, file_path):
        """
        Process a file and update the indices.

        Args:
            file_path: Path to the file to process

        Returns:
            int: Number of events processed
        """
        self.logger.info(f"Processing file: {file_path}")
        events_processed = self.processor.process_file(file_path)
        self.logger.info(f"Processed {events_processed} events")

        # Add to processed files list
        if file_path not in self.processed_files:
            self.processed_files.append(file_path)

        return events_processed

    def start(self, host="localhost", port=8080, debug=False):
        """
        Start the server.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Whether to run in debug mode
        """
        self.logger.info(f"Starting server on {host}:{port}")
        # Set environment variable to enable development mode
        if debug:
            os.environ["FLASK_ENV"] = "development"
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main entry point for the index server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("index_server")

    # Parse arguments
    parser = argparse.ArgumentParser(description="Alert Analysis Index Server")
    parser.add_argument(
        "file_paths", nargs="+", help="Path(s) to the alert event file(s) to process"
    )
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    try:
        # Create and start the server
        server = IndexServer()

        # Process all specified files
        for file_path in args.file_paths:
            try:
                server.process_file(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")

        server.start(args.host, args.port, args.debug)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
