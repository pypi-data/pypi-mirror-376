"""Tests for the SerilogLikeJSONFormatter."""

import json
import logging
from datetime import datetime, timezone

from serilog_python.formatter import SerilogLikeJSONFormatter


class TestSerilogLikeJSONFormatter:
    """Test cases for the JSON formatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = SerilogLikeJSONFormatter(include_ecs_version="8.10.0")

    def test_basic_formatting(self):
        """Test basic log record formatting."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = datetime(
            2024, 1, 15, 10, 30, 45, 123000, tzinfo=timezone.utc
        ).timestamp()

        result = self.formatter.format(record)
        parsed = json.loads(result)

        assert parsed["@timestamp"] == "2024-01-15T10:30:45.123Z"
        assert parsed["level"] == "Information"
        assert parsed["message"] == "Test message"
        assert parsed["ecs.version"] == "8.10.0"

    def test_log_level_mapping(self):
        """Test that Python log levels are correctly mapped to Serilog levels."""
        test_cases = [
            (logging.DEBUG, "Debug"),
            (logging.INFO, "Information"),
            (logging.WARNING, "Warning"),
            (logging.ERROR, "Error"),
            (logging.CRITICAL, "Fatal"),
        ]

        for level, expected in test_cases:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="",
                lineno=0,
                msg="test",
                args=(),
                exc_info=None,
            )
            result = self.formatter.format(record)
            parsed = json.loads(result)
            assert parsed["level"] == expected

    def test_extra_fields(self):
        """Test that extra fields are included in the JSON output."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test with extra",
            args=(),
            exc_info=None,
        )
        record.user_id = 123
        record.action = "login"
        record.custom_field = {"nested": "value"}

        result = self.formatter.format(record)
        parsed = json.loads(result)

        assert parsed["user_id"] == 123
        assert parsed["action"] == "login"
        assert parsed["custom_field"] == {"nested": "value"}

    def test_exception_formatting(self):
        """Test that exceptions are properly formatted."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            exc_info = (type(e), e, e.__traceback__)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Exception occurred",
            args=(),
            exc_info=exc_info,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "error" in parsed
        assert parsed["error"]["type"] == "ValueError"
        assert parsed["error"]["message"] == "Test exception"
        assert "stack_trace" in parsed["error"]

    def test_no_ecs_version(self):
        """Test formatter without ECS version."""
        formatter = SerilogLikeJSONFormatter(include_ecs_version=None)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "ecs" not in parsed

    def test_message_with_args(self):
        """Test formatting with message arguments."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %s logged in",
            args=("john",),
            exc_info=None,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        assert parsed["message"] == "User john logged in"

    def test_exclude_fields_functionality(self):
        """Test that exclude_fields parameter works correctly."""
        exclude_fields = ["sensitive", "password", "token"]
        formatter = SerilogLikeJSONFormatter(
            include_ecs_version="8.10.0", exclude_fields=exclude_fields
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test with excluded fields",
            args=(),
            exc_info=None,
        )

        # Add extra fields including ones to exclude
        record.user_id = 123
        record.sensitive = "secret_data"  # Should be excluded
        record.password = "pass123"  # Should be excluded
        record.token = "token123"  # Should be excluded
        record.safe_field = "safe_value"  # Should be included

        result = formatter.format(record)
        parsed = json.loads(result)

        # Check that excluded fields are not present
        assert "sensitive" not in parsed
        assert "password" not in parsed
        assert "token" not in parsed

        # Check that safe fields are present
        assert parsed["user_id"] == 123
        assert parsed["safe_field"] == "safe_value"

    def test_exclude_fields_empty_list(self):
        """Test that empty exclude_fields list works correctly."""
        formatter = SerilogLikeJSONFormatter(exclude_fields=[])

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test with empty exclude",
            args=(),
            exc_info=None,
        )

        record.test_field = "test_value"
        record.another_field = "another_value"

        result = formatter.format(record)
        parsed = json.loads(result)

        # All extra fields should be present when exclude list is empty
        assert parsed["test_field"] == "test_value"
        assert parsed["another_field"] == "another_value"

    def test_exclude_fields_none(self):
        """Test that None exclude_fields works correctly (default behavior)."""
        formatter = SerilogLikeJSONFormatter(exclude_fields=None)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test with None exclude",
            args=(),
            exc_info=None,
        )

        record.test_field = "test_value"
        record.password = "secret"

        result = formatter.format(record)
        parsed = json.loads(result)

        # All extra fields should be present when exclude is None
        assert parsed["test_field"] == "test_value"
        assert parsed["password"] == "secret"
