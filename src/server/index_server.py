"""
Index Server for Alert Analysis System.

This module provides a simple server that processes alert events and maintains indices in memory,
allowing for queries from multiple clients.
"""

import argparse
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine
import logging

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
        # Enable CORS for all routes
        CORS(self.app)
        self.logger = logging.getLogger("index_server")
        
        # Register routes
        self.register_routes()
        
    def register_routes(self):
        """Register the API routes."""
        @self.app.route("/query", methods=["POST"])
        def query():
            """Handle query requests."""
            try:
                data = request.json
                if not data:
                    # If no JSON data, try to get from form or query parameters
                    dimension = request.values.get("dimension", "host")
                    k = int(request.values.get("top", 5))
                else:
                    dimension = data.get("dimension", "host")
                    k = data.get("top", 5)
                
                self.logger.info(f"Processing query: dimension={dimension}, top={k}")
                results = self.query_engine.get_top_k(dimension, k)
                
                return jsonify(results)
            except Exception as e:
                self.logger.error(f"Error processing query: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/health", methods=["GET"])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "healthy"})
            
        # Add a GET endpoint for queries as well
        @self.app.route("/query", methods=["GET"])
        def query_get():
            """Handle GET query requests."""
            try:
                dimension = request.args.get("dimension", "host")
                k = int(request.args.get("top", 5))
                
                self.logger.info(f"Processing GET query: dimension={dimension}, top={k}")
                results = self.query_engine.get_top_k(dimension, k)
                
                return jsonify(results)
            except Exception as e:
                self.logger.error(f"Error processing GET query: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
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
        return events_processed
        
    def start(self, host="localhost", port=5000):
        """
        Start the server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.logger.info(f"Starting server on {host}:{port}")
        self.app.run(host=host, port=port)

def main():
    """Main entry point for the index server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("index_server")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Alert Analysis Index Server")
    parser.add_argument("file_path", help="Path to the alert event file to process")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    
    args = parser.parse_args()
    
    try:
        # Create and start the server
        server = IndexServer()
        server.process_file(args.file_path)
        server.start(args.host, args.port)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
