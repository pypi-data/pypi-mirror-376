# Grimoire Logging

[![Tests](https://github.com/wyrdbound/grimoire-logging/workflows/Tests/badge.svg)](https://github.com/wyrdbound/grimoire-logging/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Flexible logging utilities with dependency injection support for the Grimoire engine.**

Grimoire Logging provides a clean, thread-safe logging system with dependency injection capabilities. It allows applications to easily switch between different logging implementations without changing their logging code, making it ideal for libraries, applications, and testing scenarios.

## ✨ Features

- **🔄 Dependency Injection**: Inject custom logger implementations at runtime
- **🧵 Thread-Safe**: All operations are thread-safe and can be used in concurrent environments
- **🔄 Fallback Support**: Automatically falls back to Python's standard logging when no custom logger is injected
- **📦 Zero Dependencies**: Core functionality requires no external dependencies
- **🎯 Protocol-Based**: Clean interface definition using Python protocols
- **🔧 Easy Integration**: Simple API that works with existing codebases
- **🧪 Test-Friendly**: Easy to inject mock loggers for testing

## 🚀 Quick Start

### Installation

```bash
pip install grimoire-logging
```

### Basic Usage

```python
from grimoire_logging import get_logger, inject_logger

# Get a logger - falls back to standard Python logging by default
logger = get_logger(__name__)
logger.info("Hello, world!")

# Create a custom logger implementation
class CustomLogger:
    def info(self, msg: str, *args, **kwargs) -> None:
        print(f"📝 {msg}")

    def debug(self, msg: str, *args, **kwargs) -> None:
        print(f"🐛 {msg}")

    def warning(self, msg: str, *args, **kwargs) -> None:
        print(f"⚠️ {msg}")

    def error(self, msg: str, *args, **kwargs) -> None:
        print(f"❌ {msg}")

    def critical(self, msg: str, *args, **kwargs) -> None:
        print(f"💀 {msg}")

# Inject your custom logger - all existing loggers will now use it
inject_logger(CustomLogger())
logger.info("Now using custom logger!")  # Output: 📝 Now using custom logger!
```

### Thread-Safe Logger Management

```python
import threading
from grimoire_logging import get_logger, inject_logger

def worker_function(worker_id):
    logger = get_logger(f"worker_{worker_id}")
    logger.info(f"Worker {worker_id} starting")
    # Do work...
    logger.info(f"Worker {worker_id} finished")

# Inject a logger that will be used by all threads
inject_logger(CustomLogger())

# Start multiple threads - all will use the same injected logger
threads = []
for i in range(5):
    thread = threading.Thread(target=worker_function, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
```

### Integration with Standard Logging

```python
import logging
from grimoire_logging import get_logger, inject_logger

# Set up standard logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create an adapter to integrate with standard logging
class StandardLoggingAdapter:
    def __init__(self, logger_name: str = "grimoire"):
        self.logger = logging.getLogger(logger_name)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

# Use standard logging as the backend
inject_logger(StandardLoggingAdapter())

logger = get_logger("myapp")
logger.info("This will use standard Python logging with proper formatting")
```

### Structured Logging

```python
import json
from datetime import datetime
from grimoire_logging import get_logger, inject_logger

class JSONLogger:
    def _log(self, level: str, message: str):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message
        }
        print(json.dumps(log_entry))

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._log("DEBUG", msg)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._log("INFO", msg)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._log("WARNING", msg)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._log("ERROR", msg)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._log("CRITICAL", msg)

inject_logger(JSONLogger())
logger = get_logger("app")
logger.info("Application started")
# Output: {"timestamp": "2025-01-01T12:00:00Z", "level": "INFO", "message": "Application started"}
```

## 📚 Core Concepts

### Logger Protocol

Custom loggers must implement the `LoggerProtocol` interface:

```python
from typing import Protocol

class LoggerProtocol(Protocol):
    def debug(self, msg: str, *args, **kwargs) -> None: ...
    def info(self, msg: str, *args, **kwargs) -> None: ...
    def warning(self, msg: str, *args, **kwargs) -> None: ...
    def error(self, msg: str, *args, **kwargs) -> None: ...
    def critical(self, msg: str, *args, **kwargs) -> None: ...
```

### Dependency Injection

The library uses a global injection mechanism that affects all logger instances:

```python
from grimoire_logging import inject_logger, clear_logger_injection

# Inject a custom logger
inject_logger(my_custom_logger)

# All loggers now use the custom implementation
logger1 = get_logger("module1")
logger2 = get_logger("module2")
# Both use my_custom_logger

# Clear injection to return to standard logging
clear_logger_injection()
```

### Thread Safety

All operations are thread-safe and can be called from multiple threads:

```python
import threading
from grimoire_logging import get_logger, inject_logger

# Safe to call from any thread
inject_logger(custom_logger)
logger = get_logger(__name__)
logger.info("Thread-safe logging")
```

## 🔧 API Reference

### Main Functions

#### `get_logger(name: str) -> LoggerProtocol`

Get a logger instance for the given name.

**Parameters:**

- `name`: Logger name (typically `__name__`)

**Returns:**

- Logger proxy that conforms to `LoggerProtocol`

**Example:**

```python
logger = get_logger(__name__)
logger.info("Hello, world!")
```

#### `inject_logger(logger: Optional[LoggerProtocol]) -> None`

Inject a custom logger implementation.

**Parameters:**

- `logger`: Logger implementation or `None` to revert to standard logging

**Example:**

```python
inject_logger(CustomLogger())
# or
inject_logger(None)  # Clear injection
```

#### `clear_logger_injection() -> None`

Clear any injected logger and revert to default.

Equivalent to `inject_logger(None)`.

**Example:**

```python
clear_logger_injection()
```

### Protocol

#### `LoggerProtocol`

Protocol defining the interface for custom loggers.

**Methods:**

- `debug(msg: str, *args, **kwargs) -> None`
- `info(msg: str, *args, **kwargs) -> None`
- `warning(msg: str, *args, **kwargs) -> None`
- `error(msg: str, *args, **kwargs) -> None`
- `critical(msg: str, *args, **kwargs) -> None`

## 📖 Examples

See the [`examples/`](examples/) directory for comprehensive examples:

- [`basic_usage.py`](examples/basic_usage.py) - Core functionality and basic patterns
- [`advanced_usage.py`](examples/advanced_usage.py) - Structured logging, filtering, and concurrent usage
- [`integration.py`](examples/integration.py) - Integration with standard logging and frameworks

Run examples:

```bash
python examples/basic_usage.py
python examples/advanced_usage.py
python examples/integration.py
```

## 🧪 Development

### Setup

```bash
git clone https://github.com/wyrdbound/grimoire-logging.git
cd grimoire-logging
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=grimoire_logging

# Run specific test file
pytest tests/test_logging.py
```

### Code Quality

```bash
# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy src/
```

## 📋 Requirements

- Python 3.8+
- No runtime dependencies

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 The Wyrd One

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate and follow the existing code style.

If you have questions about the project, please contact: wyrdbound@proton.me

## 🎯 Use Cases

Grimoire Logging is particularly well-suited for:

- **🎲 Game Development**: Flexible logging for game engines and RPG systems
- **📚 Library Development**: Allow users to control logging behavior
- **🧪 Testing**: Easy injection of mock loggers for testing
- **🔌 Plugin Systems**: Different logging implementations for different environments
- **🌐 Web Applications**: Request-scoped logging and structured output
- **🔧 Configuration Management**: Runtime logging configuration changes

## 🏗️ Architecture

The library is built around several key components:

- **LoggerProxy**: Thread-safe proxy that delegates to injected or fallback loggers
- **Protocol Design**: Clean interface definition using Python protocols
- **Thread Safety**: Re-entrant locks ensure safe concurrent access
- **Minimal Dependencies**: Zero runtime dependencies for maximum compatibility

## 📈 Performance

- **Memory Efficient**: Logger instances are cached and reused
- **Thread Safe**: Designed for high-concurrency environments
- **Low Overhead**: Minimal impact when using standard logging fallback
- **Scalable**: Efficient delegation pattern supports many logger instances

## 🔍 Comparison with Other Solutions

| Feature              | Grimoire Logging | Python logging | loguru | structlog |
| -------------------- | ---------------- | -------------- | ------ | --------- |
| Dependency Injection | ✅               | ❌             | ❌     | Partial   |
| Zero Dependencies    | ✅               | ✅             | ❌     | ❌        |
| Thread Safety        | ✅               | ✅             | ✅     | ✅        |
| Protocol Based       | ✅               | ❌             | ❌     | Partial   |
| Easy Testing         | ✅               | Partial        | ✅     | ✅        |
| Fallback Support     | ✅               | N/A            | ❌     | ❌        |

Grimoire Logging is designed specifically for scenarios where you need clean dependency injection and the ability to completely swap out logging implementations at runtime, making it ideal for libraries and applications that need maximum flexibility.
