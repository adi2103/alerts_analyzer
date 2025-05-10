#!/usr/bin/env python
"""
Query the Simple Alert Analysis Index Server.

This script is a convenience wrapper for querying the simple index server.
"""

from src.client.simple_client import main

if __name__ == "__main__":
    exit(main())
