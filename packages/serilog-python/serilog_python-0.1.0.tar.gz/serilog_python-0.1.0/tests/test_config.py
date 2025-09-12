"""Tests for configuration utilities."""

import os
from unittest.mock import patch

from serilog_python.config import (
    get_application_name,
    get_application_version,
    get_environment,
)


class TestConfigurationUtilities:
    """Test cases for configuration utility functions."""

    def test_get_application_name_default(self):
        """Test getting default application name."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_application_name() == "GsControlUnit"

    def test_get_application_name_from_env(self):
        """Test getting application name from environment variable."""
        with patch.dict(os.environ, {"APPLICATION_NAME": "MyApp"}):
            assert get_application_name() == "MyApp"

    def test_get_environment_default(self):
        """Test getting default environment."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_environment() == "development"

    def test_get_environment_from_env(self):
        """Test getting environment from environment variable."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert get_environment() == "production"

    def test_get_application_version_default(self):
        """Test getting default application version."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_application_version() == "0.0.1"

    def test_get_application_version_from_env(self):
        """Test getting application version from environment variable."""
        with patch.dict(os.environ, {"APPLICATION_VERSION": "2.1.0"}):
            assert get_application_version() == "2.1.0"

    def test_get_all_from_env(self):
        """Test getting all configuration from environment variables."""
        env_vars = {
            "APPLICATION_NAME": "TestApp",
            "APPLICATION_VERSION": "1.5.0",
            "ENVIRONMENT": "staging",
        }

        with patch.dict(os.environ, env_vars):
            assert get_application_name() == "TestApp"
            assert get_application_version() == "1.5.0"
            assert get_environment() == "staging"

    def test_get_application_name_with_default(self):
        """Test getting application name with custom default."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_application_name(default="CustomDefault") == "CustomDefault"

    def test_get_environment_with_default(self):
        """Test getting environment with custom default."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_environment(default="custom_env") == "custom_env"

    def test_get_application_version_with_default(self):
        """Test getting application version with custom default."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_application_version(default="9.9.9") == "9.9.9"

    def test_get_with_default_and_env(self):
        """Test that environment variables take precedence over defaults."""
        with patch.dict(os.environ, {"APPLICATION_NAME": "FromEnv"}):
            assert get_application_name(default="FromDefault") == "FromEnv"
