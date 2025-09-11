# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.1.0 (2025-09-11)

### Added

- Initial release of grimoire-logging
- Protocol-based dependency injection system for flexible logger implementations
- Thread-safe logger proxy with re-entrant locks for concurrent environments
- Zero-dependency core library with fallback to Python standard logging
- Comprehensive test suite with 100% core functionality coverage (22 tests)
- Type-safe implementation with full mypy compliance
- Easy-to-use API with `get_logger()`, `inject_logger()`, and `clear_logger_injection()`
- Three comprehensive examples demonstrating basic, advanced, and integration patterns
- GitHub Actions CI/CD pipeline with matrix testing across Python versions
- Extensive documentation including README, API reference, and usage examples
- Development tooling setup with pytest, mypy, ruff, and coverage reporting
- Support for structured logging and custom logger implementations
- Thread-safe global logger injection affecting all logger instances
- Automatic module name extraction for logger naming
- Compatible with Python 3.8+ (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
