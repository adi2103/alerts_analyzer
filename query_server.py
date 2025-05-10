#!/usr/bin/env python
"""
Start the Alert Analysis Index Server.

This script is a convenience wrapper for starting the index server.
"""

from src.server.index_server import main

if __name__ == "__main__":
    exit(main())
