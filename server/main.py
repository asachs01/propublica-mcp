#!/usr/bin/env python3
"""
ProPublica MCP Extension - DXT Entry Point

This is the main entry point for the DXT extension following official DXT conventions.
Dependencies are bundled in the lib/ directory and loaded automatically.
"""

import sys
import os
from pathlib import Path

# Add the lib directory to Python path (DXT convention)
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    sys.path.insert(0, str(lib_path))

# Now import and run the server
from propublica_mcp.server import main

if __name__ == "__main__":
    main()