"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_log_record():
    """Create a sample log record for testing."""
    import logging

    return logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
