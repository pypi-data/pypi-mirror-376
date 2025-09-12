"""Configuration utilities for setting up structured logging."""

import logging
import os
import sys
from typing import Optional

from .filter import ContextFilter
from .formatter import SerilogLikeJSONFormatter


def get_application_name(default: Optional[str] = None) -> str:
    """Get application name from environment variable or use default.

    Environment variable: APPLICATION_NAME
    Default: GsControlUnit or provided default

    Args:
        default: Custom default value to use if env var is not set

    Returns:
        str: Application name
    """
    env_value = os.getenv("APPLICATION_NAME")
    if env_value:
        return env_value
    return default or "GsControlUnit"


def get_environment(default: Optional[str] = None) -> str:
    """Get environment from environment variable or use default.

    Environment variable: ENVIRONMENT
    Default: development or provided default

    Args:
        default: Custom default value to use if env var is not set

    Returns:
        str: Environment name
    """
    env_value = os.getenv("ENVIRONMENT")
    if env_value:
        return env_value
    return default or "development"


def get_application_version(default: Optional[str] = None) -> str:
    """Get application version from environment variable or use default.

    Environment variable: APPLICATION_VERSION
    Default: 0.0.1 or provided default

    Args:
        default: Custom default value to use if env var is not set

    Returns:
        str: Application version
    """
    env_value = os.getenv("APPLICATION_VERSION")
    if env_value:
        return env_value
    return default or "0.0.1"


def setup_logging(
    level: str = "INFO",
    disable_access_logs: bool = True,
    sql_level: Optional[str] = None,
    application_name: Optional[str] = None,
    application_version: Optional[str] = None,
    environment: Optional[str] = None,
    exclude_fields: Optional[list] = None,
    stack_trace_limit: Optional[int] = None,
) -> None:
    """Configure structured logging for the application.

    This function sets up comprehensive logging configuration with:
    - JSON formatting compatible with Serilog
    - Service and environment context
    - Proper handler configuration for common frameworks

    Args:
        level: Logging level for the application (default: "INFO")
        disable_access_logs: Whether to disable web server access logs (default: True)
        sql_level: Logging level for SQL-related loggers (default: WARNING)
        application_name: Override for application name (default: from env)
        application_version: Override for application version (default: from env)
        environment: Override for environment (default: from env)
        exclude_fields: List of field names to exclude from logs
        stack_trace_limit: Limit for stack trace depth (not implemented yet)
    """
    # Use parameters if provided, otherwise fall back to environment variables
    app_name = (
        application_name if application_name is not None else get_application_name()
    )
    app_version = (
        application_version
        if application_version is not None
        else get_application_version()
    )
    app_environment = environment if environment is not None else get_environment()

    # Create context filter
    context_filter = ContextFilter(app_name, app_version, app_environment)

    # Create JSON formatter
    formatter = SerilogLikeJSONFormatter(
        include_ecs_version="8.10.0", exclude_fields=exclude_fields
    )

    # Create stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(context_filter)

    # Configure numeric level
    numeric_level = getattr(logging, str(level).upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers = [handler]
    root_logger.filters.clear()
    root_logger.addFilter(context_filter)

    # Configure specific loggers
    loggers_config = [
        ("httpx", numeric_level),
        ("sqlalchemy", sql_level or logging.WARNING),
        ("app", numeric_level),
    ]

    # Configure web framework loggers (only if they exist)
    web_loggers = [
        ("uvicorn", numeric_level),
        ("uvicorn.error", numeric_level),
        ("uvicorn.access", logging.WARNING if disable_access_logs else numeric_level),
        ("fastapi", numeric_level),
        ("starlette", numeric_level),
        ("django", numeric_level),
        ("django.request", numeric_level),
        ("django.server", numeric_level),
        ("flask", numeric_level),
        ("werkzeug", numeric_level),
        ("gunicorn", numeric_level),
        ("gunicorn.access", logging.WARNING if disable_access_logs else numeric_level),
    ]

    # Only configure loggers that actually exist in the application
    for logger_name, logger_level in web_loggers:
        try:
            logger = logging.getLogger(logger_name)
            # Only configure if logger has handlers or will be used
            if logger.handlers or logger.hasHandlers():
                logger.setLevel(logger_level)
                logger.handlers = [handler]
                logger.filters.clear()
                logger.addFilter(context_filter)
                logger.propagate = False
        except:
            # Skip loggers that don't exist
            pass

    for logger_name, logger_level in loggers_config:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
        logger.handlers = [handler]
        logger.filters.clear()
        logger.addFilter(context_filter)
        logger.propagate = False

    # Log configuration startup
    app_logger = logging.getLogger("app")
    app_logger.info(
        "logging_configured",
        extra={
            "service": {"name": app_name, "version": app_version},
            "environment": app_environment,
            "event": {"category": "application", "action": "logging_started"},
            "message_template": "logging_configured",
        },
    )
