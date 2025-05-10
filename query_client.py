#!/usr/bin/env python
"""
Query the Alert Analysis Index Server.

This script is a convenience wrapper for querying the index server.
"""

from src.client.query_client import main

if __name__ == "__main__":
    exit(main())
