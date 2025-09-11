#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP MySQL Server - A MySQL MCP Server for cross-database queries with Chinese field mapping

This package provides a Model Context Protocol (MCP) server that connects to MySQL databases
and supports cross-database queries with Chinese field mapping for better frontend understanding.

Features:
- Cross-database query support
- Chinese field name mapping
- Real business SQL integration
- Multiple database configuration
- Secure connection handling

Author: Your Name
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

from .server import main

__all__ = ["main"]