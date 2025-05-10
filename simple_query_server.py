#!/usr/bin/env python
"""
Start the Simple Alert Analysis Index Server.

This script is a convenience wrapper for starting the simple index server.
"""

from src.server.simple_server import main

if __name__ == "__main__":
    exit(main())
