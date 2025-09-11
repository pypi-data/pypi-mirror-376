# Grimoire Logging Examples

This directory contains example scripts demonstrating various uses of the grimoire-logging library.

## Examples

### 1. `basic_usage.py`

Demonstrates core functionality:

- Getting loggers with fallback to standard Python logging
- Injecting custom logger implementations
- Thread-safe logger management
- Multiple logger instances sharing the same injection

**Run with:**

```bash
python examples/basic_usage.py
```

### 2. `advanced_usage.py`

Shows advanced logging scenarios:

- Structured logging with JSON output
- Filtering and transforming log messages
- Specialized game event logging
- Thread-safe concurrent logging from multiple threads

**Run with:**

```bash
python examples/advanced_usage.py
```

### 3. `integration.py`

Demonstrates integration with other systems:

- Integration with Python's standard logging
- Web framework request context logging
- Configurable logging for different environments
- Library integration patterns

**Run with:**

```bash
python examples/integration.py
```

## Running Examples

Make sure you have grimoire-logging installed or the source available in your Python path:

```bash
# From the project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python examples/basic_usage.py
```

Or if you have the package installed:

```bash
pip install grimoire-logging
python examples/basic_usage.py
```

## Understanding the Examples

Each example is self-contained and demonstrates specific aspects of the library:

- **Basic Usage**: Start here to understand the core concepts
- **Advanced Usage**: Explore more sophisticated logging patterns
- **Integration**: See how to integrate with existing systems and libraries

The examples include extensive comments explaining the concepts and can serve as templates for your own logging implementations.
