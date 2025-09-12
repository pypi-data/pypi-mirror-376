"""JSON formatter with Serilog-compatible output format."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class SerilogLikeJSONFormatter(logging.Formatter):
    """JSON formatter that produces Serilog-compatible structured log output.

    This formatter converts Python log records into JSON format compatible
    with Serilog, including proper timestamp formatting, level mapping,
    and structured error information.
    """

    # Mapping from Python logging levels to Serilog levels
    SERILOG_LEVELS = {
        "CRITICAL": "Fatal",
        "ERROR": "Error",
        "WARNING": "Warning",
        "INFO": "Information",
        "DEBUG": "Debug",
        "NOTSET": "Verbose",
    }

    def __init__(
        self,
        include_ecs_version: Optional[str] = "8.10.0",
        exclude_fields: Optional[list] = None,
    ):
        """Initialize the JSON formatter.

        Args:
            include_ecs_version: ECS version to include in logs (default: "8.10.0")
            exclude_fields: List of field names to exclude from logs
        """
        super().__init__()
        self.include_ecs_version = include_ecs_version
        self.exclude_fields = set(exclude_fields or [])

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            str: JSON formatted log entry
        """
        doc: Dict[str, Any] = {}

        # Format timestamp in ISO format with milliseconds and 'Z' suffix
        ts = (
            datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        doc["@timestamp"] = ts

        # Map Python log level to Serilog level
        level = self.SERILOG_LEVELS.get(
            record.levelname.upper(), record.levelname.title()
        )
        # Remove ANSI color codes if present
        if isinstance(level, str):
            level = level.replace("\u001b[31m", "").replace("\u001b[39m", "")
        doc["level"] = level

        # Add the log message
        doc["message"] = record.getMessage()

        # Handle exception information
        if record.exc_info:
            doc["exception"] = self.formatException(record.exc_info)
            exc_type = (
                record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
            )
            exc_msg = str(record.exc_info[1]) if record.exc_info[1] else doc["message"]
            doc["error"] = {
                "type": exc_type,
                "message": exc_msg,
                "stack_trace": doc["exception"],
            }

        # Fields to skip from the record (standard logging fields)
        skip_fields = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }

        # Add any extra fields from the record
        for k, v in record.__dict__.items():
            if k not in skip_fields and k not in doc and k not in self.exclude_fields:
                doc[k] = v

        # Add ECS version if specified
        if self.include_ecs_version:
            doc["ecs.version"] = self.include_ecs_version

        return json.dumps(doc, ensure_ascii=False)
