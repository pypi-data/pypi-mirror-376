"""
niorclconn - Oracle Database Connection Package

A Python package for managing Oracle database connections with support for
environment variables and convenient connection management.
"""

from .connector import ConnectionManager, open_connection, close_connection

__version__ = "0.1.0"
__author__ = "Deb Mishra"
__email__ = "infra@daedal.org"

__all__ = ["ConnectionManager", "open_connection", "close_connection"]
