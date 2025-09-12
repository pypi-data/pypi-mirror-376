"""Integration tests for the complete logging setup."""

import json
import logging
from io import StringIO
from unittest.mock import patch

from serilog_python import setup_logging


class TestIntegration:
    """Integration tests for the complete logging system."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        # Capture stdout to check log output
        captured_output = StringIO()

        with patch("sys.stdout", captured_output):
            setup_logging(level="INFO", application_name="TestApp")

            logger = logging.getLogger("app")
            logger.info("Test message", extra={"test_field": "test_value"})

        # Parse the JSON output (skip the configuration log message)
        output = captured_output.getvalue().strip()
        assert output, "Should have log output"

        # Find the last JSON line (our test message, not the config message)
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        test_line = lines[-1]  # Get the last line (our test message)
        parsed = json.loads(test_line)

        # Check basic structure
        assert "@timestamp" in parsed
        assert parsed["level"] == "Information"
        assert parsed["message"] == "Test message"
        assert parsed["service"]["name"] == "TestApp"
        assert parsed["test_field"] == "test_value"

    def test_setup_logging_with_custom_env(self):
        """Test logging setup with custom environment variables."""
        env_vars = {
            "APPLICATION_NAME": "CustomApp",
            "APPLICATION_VERSION": "2.0.0",
            "ENVIRONMENT": "production",
        }

        captured_output = StringIO()

        with patch.dict("os.environ", env_vars), patch("sys.stdout", captured_output):
            setup_logging()

            logger = logging.getLogger("test")
            logger.warning("Warning message")

        output = captured_output.getvalue().strip()
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        test_line = lines[-1]  # Get the last line (our test message)
        parsed = json.loads(test_line)

        assert parsed["service"]["name"] == "CustomApp"
        assert parsed["service"]["version"] == "2.0.0"
        assert parsed["environment"] == "production"
        assert parsed["level"] == "Warning"

    def test_setup_logging_log_levels(self):
        """Test that different log levels are handled correctly."""
        captured_output = StringIO()

        with patch("sys.stdout", captured_output):
            setup_logging(level="DEBUG")

            logger = logging.getLogger("test")
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")

        output = captured_output.getvalue()
        lines = [line.strip() for line in output.split("\n") if line.strip()]

        assert len(lines) == 4  # 1 config message + 3 test messages

        for line in lines:
            parsed = json.loads(line)
            assert "@timestamp" in parsed
            assert "message" in parsed

    def test_setup_logging_disables_access_logs(self):
        """Test that web server access logs are disabled by default."""
        with patch("sys.stdout"):
            setup_logging(disable_access_logs=True)

            access_logger = logging.getLogger("uvicorn.access")
            assert access_logger.level == logging.WARNING

    def test_setup_logging_enables_access_logs(self):
        """Test that web server access logs can be enabled."""
        with patch("sys.stdout"):
            setup_logging(disable_access_logs=False, level="INFO")

            access_logger = logging.getLogger("uvicorn.access")
            assert access_logger.level == logging.INFO

    def test_setup_logging_with_custom_parameters(self):
        """Test setup logging with custom application parameters."""
        captured_output = StringIO()

        with patch("sys.stdout", captured_output):
            setup_logging(
                application_name="CustomApp",
                application_version="3.0.0",
                environment="staging",
            )

            logger = logging.getLogger("test")
            logger.info("Test with custom params")

        output = captured_output.getvalue().strip()
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        test_line = lines[-1]  # Get the last line (our test message)
        parsed = json.loads(test_line)

        assert parsed["service"]["name"] == "CustomApp"
        assert parsed["service"]["version"] == "3.0.0"
        assert parsed["environment"] == "staging"

    def test_setup_logging_parameters_override_env(self):
        """Test that setup parameters override environment variables."""
        env_vars = {
            "APPLICATION_NAME": "EnvApp",
            "APPLICATION_VERSION": "1.0.0",
            "ENVIRONMENT": "development",
        }

        captured_output = StringIO()

        with patch.dict("os.environ", env_vars), patch("sys.stdout", captured_output):
            # Parameters should override environment variables
            setup_logging(
                application_name="ParamApp",
                application_version="2.0.0",
                environment="production",
            )

            logger = logging.getLogger("test")
            logger.info("Test parameter override")

        output = captured_output.getvalue().strip()
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        test_line = lines[-1]  # Get the last line (our test message)
        parsed = json.loads(test_line)

        # Should use parameter values, not environment values
        assert parsed["service"]["name"] == "ParamApp"
        assert parsed["service"]["version"] == "2.0.0"
        assert parsed["environment"] == "production"

    def test_setup_logging_with_exclude_fields(self):
        """Test setup logging with exclude_fields parameter."""
        captured_output = StringIO()

        with patch("sys.stdout", captured_output):
            setup_logging(
                application_name="TestApp",
                exclude_fields=["sensitive_data", "password", "token"],
            )

            logger = logging.getLogger("test")
            logger.info(
                "Test with excluded fields",
                extra={
                    "user_id": 123,
                    "username": "test_user",
                    "sensitive_data": "secret",  # Should be excluded
                    "password": "pass123",  # Should be excluded
                    "token": "token123",  # Should be excluded
                    "safe_field": "safe_value",  # Should be included
                },
            )

        output = captured_output.getvalue().strip()
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        test_line = lines[-1]  # Get the last line (our test message)
        parsed = json.loads(test_line)

        # Check that excluded fields are not present
        assert "sensitive_data" not in parsed
        assert "password" not in parsed
        assert "token" not in parsed

        # Check that safe fields are present
        assert parsed["user_id"] == 123
        assert parsed["username"] == "test_user"
        assert parsed["safe_field"] == "safe_value"
        assert parsed["service"]["name"] == "TestApp"
