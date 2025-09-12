"""Serilog-like JSON logging for Python.

This package provides structured logging capabilities with Serilog-compatible
JSON output format, designed for modern Python applications.
"""

from .config import (
    get_application_name,
    get_application_version,
    get_environment,
    setup_logging,
)
from .filter import ContextFilter
from .formatter import SerilogLikeJSONFormatter

__version__ = "0.1.0"
__all__ = [
    "SerilogLikeJSONFormatter",
    "ContextFilter",
    "setup_logging",
    "get_application_name",
    "get_environment",
    "get_application_version",
]
