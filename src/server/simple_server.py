"""
Simple HTTP Server for Alert Analysis System.

This module provides a simple HTTP server that processes alert events and maintains indices in memory,
allowing for queries from multiple clients.
"""

import argparse
import json
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine

class AlertAnalysisHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Alert Analysis queries."""
    
    def do_GET(self):
        """Handle GET requests."""
        # Parse the URL and query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Add CORS headers to all responses
        self.send_cors_headers()
        
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy'}
            self.wfile.write(json.dumps(response).encode())
            
        elif path == '/query':
            # Parse query parameters
            query_params = urllib.parse.parse_qs(parsed_path.query)
            dimension = query_params.get('dimension', ['host'])[0]
            try:
                top_k = int(query_params.get('top', ['5'])[0])
            except (ValueError, IndexError):
                top_k = 5
                
            self.handle_query(dimension, top_k)
            
        elif path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'Alert Analysis Index Server is running',
                'endpoints': ['/health', '/query']
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': 'Not Found'}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        # Add CORS headers to all responses
        self.send_cors_headers()
        
        if self.path == '/query':
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                # Read and parse the request body
                body = self.rfile.read(content_length).decode('utf-8')
                try:
                    data = json.loads(body)
                    dimension = data.get('dimension', 'host')
                    top_k = data.get('top', 5)
                    self.handle_query(dimension, top_k)
                except json.JSONDecodeError:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {'error': 'Invalid JSON'}
                    self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'error': 'Empty request body'}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': 'Not Found'}
            self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def handle_query(self, dimension, top_k):
        """Handle a query for top k unhealthiest entities."""
        try:
            # Get the query engine from the server
            query_engine = self.server.query_engine
            
            # Execute the query
            results = query_engine.get_top_k(dimension, top_k)
            
            # Send the response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            
        except Exception as e:
            self.server.logger.error(f"Error processing query: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response).encode())

class SimpleIndexServer(HTTPServer):
    """Simple HTTP server for Alert Analysis System."""
    
    def __init__(self, server_address, RequestHandlerClass, file_path):
        """
        Initialize the server.
        
        Args:
            server_address: (host, port) tuple
            RequestHandlerClass: Request handler class
            file_path: Path to the alert event file to process
        """
        super().__init__(server_address, RequestHandlerClass)
        
        # Configure logging
        self.logger = logging.getLogger("simple_index_server")
        
        # Initialize components
        self.processor = EventProcessor()
        self.query_engine = QueryEngine()
        
        # Process the file
        self.logger.info(f"Processing file: {file_path}")
        events_processed = self.processor.process_file(file_path)
        self.logger.info(f"Processed {events_processed} events")

def run_server(host="localhost", port=5000, file_path=None):
    """
    Run the server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        file_path: Path to the alert event file to process
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("simple_index_server")
    
    server_address = (host, port)
    httpd = SimpleIndexServer(server_address, AlertAnalysisHandler, file_path)
    
    logger.info(f"Starting server on {host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        httpd.server_close()
        logger.info("Server stopped")

def main():
    """Main entry point for the simple index server."""
    parser = argparse.ArgumentParser(description="Simple Alert Analysis Index Server")
    parser.add_argument("file_path", help="Path to the alert event file to process")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    
    args = parser.parse_args()
    
    try:
        run_server(args.host, args.port, args.file_path)
        return 0
    except Exception as e:
        logging.getLogger("simple_index_server").error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
