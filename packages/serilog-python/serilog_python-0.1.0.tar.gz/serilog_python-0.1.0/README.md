# Serilog Python

[![PyPI version](https://badge.fury.io/py/serilog-python.svg)](https://pypi.org/project/serilog-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/serilog-python.svg)](https://pypi.org/project/serilog-python/)
[![License](https://img.shields.io/pypi/l/serilog-python.svg)](https://github.com/yourusername/serilog-python/blob/main/LICENSE)

Serilog-like JSON structured logging for Python applications. This package provides a complete logging solution with structured JSON output, service context, and environment information - perfect for modern Python applications, especially those using FastAPI, Django, Flask, or other web frameworks.

## Features

- **Structured JSON Logging**: Output logs in JSON format compatible with Serilog
- **Service Context**: Automatically adds service name, version, and environment to all logs
- **Framework Integration**: Pre-configured for common Python frameworks (FastAPI, Django, Flask, SQLAlchemy, HTTPX, etc.)
- **Environment Configuration**: Automatic detection of application settings from environment variables
- **Type Safety**: Full type hints for better IDE support and code reliability
- **Production Ready**: Optimized for performance and reliability in production environments

## Installation

```bash
pip install serilog-python
```

## Quick Start

### Basic Usage

```python
import logging
from serilog_python import setup_logging

# Configure logging with default settings
setup_logging()

# Now all your logs will be in structured JSON format
logger = logging.getLogger(__name__)
logger.info("Application started", extra={"user_id": 123, "action": "login"})
```

### Advanced Configuration

````python
import logging
from serilog_python import setup_logging

# Configure with custom settings
setup_logging(
    level="DEBUG",
    disable_access_logs=False,
    sql_level="INFO",
    application_name="MyAwesomeApp",
    application_version="2.1.0",
    environment="production"
)

logger = logging.getLogger(__name__)
logger.error("Database connection failed", extra={
    "error_code": "DB_001",
    "retry_count": 3,
    "database": "postgresql"
})

### Excluding Fields from Logs

```python
import logging
from serilog_python import setup_logging

# Exclude sensitive fields from logs
setup_logging(
    application_name="SecureApp",
    exclude_fields=["password", "token", "api_key", "credit_card"]
)

logger = logging.getLogger(__name__)
logger.info("User login", extra={
    "user_id": 123,
    "username": "john_doe",
    "password": "secret123",  # This will be excluded
    "token": "abc123",        # This will be excluded
    "ip_address": "192.168.1.1"  # This will be included
})
# Result: password and token fields will not appear in the log
````

## Configuration Priority

You can configure the logging system in three ways, with the following priority order:

1. **Function parameters** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

### Environment Variables

Configure your application through environment variables:

```bash
export APPLICATION_NAME="MyService"
export APPLICATION_VERSION="1.2.3"
export ENVIRONMENT="production"
```

| Variable              | Description            | Default         |
| --------------------- | ---------------------- | --------------- |
| `APPLICATION_NAME`    | Service name           | `"MyService"`   |
| `APPLICATION_VERSION` | Service version        | `"0.0.1"`       |
| `ENVIRONMENT`         | Deployment environment | `"development"` |

### Parameter Override

Function parameters take precedence over environment variables:

```python
# This will use "CustomName" even if APPLICATION_NAME is set
setup_logging(application_name="CustomName", environment="production")
```

## Log Output Format

All logs are output in JSON format with the following structure:

```json
{
  "@timestamp": "2024-01-15T10:30:45.123Z",
  "level": "Information",
  "message": "User logged in",
  "service": {
    "name": "MyService",
    "version": "1.2.3"
  },
  "environment": "production",
  "user_id": 123,
  "action": "login",
  "ecs": {
    "version": "8.10.0"
  }
}
```

## Framework Integration Examples

### FastAPI

```python
from fastapi import FastAPI
from serilog_python import setup_logging

# Configure logging before creating the app
setup_logging(level="INFO", disable_access_logs=True)

app = FastAPI(title="My API")

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    logger = logging.getLogger(__name__)
    logger.info("Fetching user", extra={"user_id": user_id, "endpoint": "/users/{user_id}"})
    return {"user_id": user_id, "name": "John Doe"}
```

### With SQLAlchemy

```python
from sqlalchemy import create_engine
from serilog_python import setup_logging

setup_logging(sql_level="WARNING")  # Only log SQL errors and warnings

engine = create_engine("postgresql://user:pass@localhost/db")
```

### With Django

```python
# settings.py
from serilog_python import setup_logging

# Configure logging before Django settings
setup_logging(
    application_name="MyDjangoApp",
    environment="production",
    disable_access_logs=True
)

# Django will use the configured logging
```

### With Flask

```python
from flask import Flask
from serilog_python import setup_logging

# Configure logging
setup_logging(
    application_name="MyFlaskApp",
    disable_access_logs=False
)

app = Flask(__name__)
```

### Custom Logger Configuration

```python
import logging
from serilog_python import ContextFilter, SerilogLikeJSONFormatter

# Create custom components
context_filter = ContextFilter(
    service_name="CustomService",
    service_version="2.0.0",
    environment="staging"
)

formatter = SerilogLikeJSONFormatter(include_ecs_version="8.11.0")

# Configure a specific logger
logger = logging.getLogger("my_custom_logger")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.addFilter(context_filter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

## API Reference

### Functions

#### `setup_logging(level="INFO", disable_access_logs=True, sql_level=None, application_name=None, application_version=None, environment=None, exclude_fields=None)`

Configure the entire logging system for your application.

**Parameters:**

- `level` (str): Logging level for the application
- `disable_access_logs` (bool): Whether to disable web server access logs (uvicorn, gunicorn, etc.)
- `sql_level` (str, optional): Logging level for SQL-related loggers
- `application_name` (str, optional): Override for application name
- `application_version` (str, optional): Override for application version
- `environment` (str, optional): Override for environment
- `exclude_fields` (list, optional): List of field names to exclude from logs

### Classes

#### `ContextFilter(service_name, service_version, environment)`

Filter that adds service and environment context to log records.

#### `SerilogLikeJSONFormatter(include_ecs_version="8.10.0")`

JSON formatter compatible with Serilog output format.

**Parameters:**

- `include_ecs_version` (str, optional): ECS version to include in logs

### Utility Functions

#### `get_application_name() -> str`

Get application name from environment or default.

#### `get_environment() -> str`

Get environment from environment or default.

#### `get_application_version() -> str`

Get application version from environment or default.

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/serilog-python.git
cd serilog-python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest`
5. Format your code: `black src/ && isort src/`
6. Commit your changes: `git commit -am 'Add your feature'`
7. Push to the branch: `git push origin feature/your-feature`
8. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Support

- 📖 [Documentation](https://github.com/yourusername/serilog-python#readme)
- 🐛 [Issues](https://github.com/yourusername/serilog-python/issues)
- 💬 [Discussions](https://github.com/yourusername/serilog-python/discussions)

---

Made with ❤️ for the Python logging community
