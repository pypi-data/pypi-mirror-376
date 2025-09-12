"""Tests for the ContextFilter."""

import logging

from serilog_python.filter import ContextFilter


class TestContextFilter:
    """Test cases for the context filter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = ContextFilter(
            service_name="TestService", service_version="1.0.0", environment="test"
        )

    def test_filter_adds_service_context(self):
        """Test that the filter adds service information to log records."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = self.filter.filter(record)

        assert result is True  # Filter should always return True
        assert hasattr(record, "service")
        assert record.service["name"] == "TestService"
        assert record.service["version"] == "1.0.0"

    def test_filter_adds_environment_context(self):
        """Test that the filter adds environment information to log records."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        self.filter.filter(record)

        assert hasattr(record, "environment")
        assert record.environment == "test"

    def test_filter_preserves_existing_attributes(self):
        """Test that existing attributes are preserved."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Simulate existing attributes
        record.service = {"name": "ExistingService"}
        record.environment = "existing_env"

        self.filter.filter(record)

        # Existing attributes should not be overwritten
        assert record.service["name"] == "ExistingService"
        assert record.environment == "existing_env"

    def test_filter_with_different_service_info(self):
        """Test filter with different service information."""
        filter = ContextFilter(
            service_name="AnotherService",
            service_version="2.0.0",
            environment="production",
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter.filter(record)

        assert record.service["name"] == "AnotherService"
        assert record.service["version"] == "2.0.0"
        assert record.environment == "production"
