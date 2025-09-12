# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added

- Initial release of serilog-python
- Structured JSON logging with Serilog-compatible output format
- Service and environment context filtering
- Environment variable configuration support
- FastAPI and SQLAlchemy integration examples
- Comprehensive test suite
- Full type hints support
- Complete documentation and README

### Features

- `SerilogLikeJSONFormatter`: JSON formatter with Serilog-compatible structure
- `ContextFilter`: Adds service name, version, and environment to all log records
- `setup_logging()`: One-line configuration for complete logging setup
- Environment variable support for configuration
- Proper log level mapping (Python → Serilog)
- Exception handling with structured error information
- Timestamp formatting in ISO 8601 with milliseconds and 'Z' suffix
- ECS version support for Elastic Common Schema compatibility

### Dependencies

- Python 3.8+
- No external dependencies (uses only standard library)

### Documentation

- Comprehensive README with usage examples
- API reference documentation
- Framework integration examples (FastAPI, SQLAlchemy)
- Development setup instructions
