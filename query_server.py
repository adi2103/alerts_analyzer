#!/usr/bin/env python
"""
Alert Analysis Index Server.

This script starts a server that processes alert events and maintains indices in memory,
allowing for queries from multiple clients.
"""

from src.index_server import main

if __name__ == "__main__":
    exit(main())
