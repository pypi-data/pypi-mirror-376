#!/usr/bin/env python3
"""Basic usage example for grimoire-logging.

This example demonstrates the core functionality of the grimoire-logging library:
- Getting loggers with fallback to standard Python logging
- Injecting custom logger implementations
- Thread-safe logger management
"""

import logging
import sys

# Import grimoire-logging
from grimoire_logging import clear_logger_injection, get_logger, inject_logger


def setup_standard_logging():
    """Configure standard Python logging for demonstration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )


def main():
    print("=== Grimoire Logging Basic Example ===\n")

    # Set up standard logging so we can see the fallback behavior
    setup_standard_logging()

    print("1. Using standard logging (fallback behavior)")
    print("-" * 50)

    # Get a logger - will fall back to standard Python logging
    logger = get_logger(__name__)

    logger.info("This message uses standard Python logging")
    logger.debug("Debug message with standard logging")
    logger.warning("Warning message with standard logging")

    print("\n2. Creating and injecting a custom logger")
    print("-" * 50)

    # Create a simple custom logger
    class SimpleCustomLogger:
        def debug(self, msg: str, *args, **kwargs) -> None:
            print(f"🐛 DEBUG: {msg}")

        def info(self, msg: str, *args, **kwargs) -> None:
            print(f"INFO: {msg}")

        def warning(self, msg: str, *args, **kwargs) -> None:
            print(f"⚠️  WARNING: {msg}")

        def error(self, msg: str, *args, **kwargs) -> None:
            print(f"❌ ERROR: {msg}")

        def critical(self, msg: str, *args, **kwargs) -> None:
            print(f"💀 CRITICAL: {msg}")

    # Inject the custom logger
    custom_logger = SimpleCustomLogger()
    inject_logger(custom_logger)

    # Now all loggers will use our custom implementation
    logger.info("This message now uses the custom logger!")
    logger.debug("Custom debug message")
    logger.warning("Custom warning message")
    logger.error("Custom error message")

    print("\n3. Multiple loggers share the same injection")
    print("-" * 50)

    # Create loggers with different names
    app_logger = get_logger("myapp")
    db_logger = get_logger("myapp.database")
    auth_logger = get_logger("myapp.auth")

    # All use the same injected logger
    app_logger.info("Application starting up")
    db_logger.info("Database connection established")
    auth_logger.info("User authentication successful")

    print("\n4. Clearing injection returns to standard logging")
    print("-" * 50)

    # Clear the injection
    clear_logger_injection()

    # Back to standard logging
    logger.info("Back to standard Python logging")
    app_logger.warning("This also uses standard logging again")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
