"""Context filter for adding service and environment information to log records."""

import logging


class ContextFilter(logging.Filter):
    """Filter that adds service and environment context to all log records.

    This filter automatically adds service name, version, and environment
    information to every log record, making them available for structured logging.
    """

    def __init__(self, service_name: str, service_version: str, environment: str):
        """Initialize the context filter.

        Args:
            service_name: Name of the service/application
            service_version: Version of the service/application
            environment: Deployment environment (development, production, etc.)
        """
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to the log record.

        Args:
            record: The log record to filter

        Returns:
            bool: Always returns True to allow the record to be processed
        """
        if not hasattr(record, "service"):
            record.service = {
                "name": self.service_name,
                "version": self.service_version,
            }
        if not hasattr(record, "environment"):
            record.environment = self.environment
        return True
