#!/usr/bin/env python3
"""Integration example showing how to use grimoire-logging with third-party libraries.

This example demonstrates:
- Integration with standard Python logging
- Wrapping existing loggers
- Using with web frameworks (simulated)
- Custom adapters for different logging libraries
"""

import logging
import sys
from typing import Any, Dict

from grimoire_logging import clear_logger_injection, get_logger, inject_logger


class StandardLoggingAdapter:
    """Adapter that integrates with Python's standard logging."""

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


class WebFrameworkLogger:
    """Simulated web framework logger integration."""

    def __init__(self, request_id: str = "req_123"):
        self.request_id = request_id

    def _format_message(self, msg: str) -> str:
        """Add request context to messages."""
        return f"[Request {self.request_id}] {msg}"

    def debug(self, msg: str, *args, **kwargs) -> None:
        print(f"DEBUG: {self._format_message(msg)}")

    def info(self, msg: str, *args, **kwargs) -> None:
        print(f"INFO: {self._format_message(msg)}")

    def warning(self, msg: str, *args, **kwargs) -> None:
        print(f"WARNING: {self._format_message(msg)}")

    def error(self, msg: str, *args, **kwargs) -> None:
        print(f"ERROR: {self._format_message(msg)}")

    def critical(self, msg: str, *args, **kwargs) -> None:
        print(f"CRITICAL: {self._format_message(msg)}")


class ConfigurableLogger:
    """Logger that can be configured at runtime."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled_levels = set(
            config.get("enabled_levels", ["info", "warning", "error", "critical"])
        )
        self.prefix = config.get("prefix", "")
        self.include_timestamp = config.get("include_timestamp", False)

    def _should_log(self, level: str) -> bool:
        return level in self.enabled_levels

    def _format_message(self, level: str, msg: str) -> str:
        """Format message according to configuration."""
        parts = []

        if self.include_timestamp:
            from datetime import datetime

            timestamp = datetime.now().strftime("%H:%M:%S")
            parts.append(f"[{timestamp}]")

        if self.prefix:
            parts.append(f"[{self.prefix}]")

        parts.extend([level.upper() + ":", msg])
        return " ".join(parts)

    def debug(self, msg: str, *args, **kwargs) -> None:
        if self._should_log("debug"):
            print(self._format_message("debug", msg))

    def info(self, msg: str, *args, **kwargs) -> None:
        if self._should_log("info"):
            print(self._format_message("info", msg))

    def warning(self, msg: str, *args, **kwargs) -> None:
        if self._should_log("warning"):
            print(self._format_message("warning", msg))

    def error(self, msg: str, *args, **kwargs) -> None:
        if self._should_log("error"):
            print(self._format_message("error", msg))

    def critical(self, msg: str, *args, **kwargs) -> None:
        if self._should_log("critical"):
            print(self._format_message("critical", msg))


def simulate_application_module():
    """Simulate an application module using grimoire-logging."""
    logger = get_logger("myapp.core")

    logger.info("Application module initialized")
    logger.debug("Loading configuration")
    logger.info("Configuration loaded successfully")

    # Simulate some work
    logger.debug("Processing user request")
    logger.warning("Cache miss, loading from database")
    logger.info("Request processed successfully")


def simulate_database_module():
    """Simulate a database module using grimoire-logging."""
    logger = get_logger("myapp.database")

    logger.info("Establishing database connection")
    logger.debug("Connection pool created with 5 connections")
    logger.info("Database ready")

    # Simulate database operations
    logger.debug("Executing query: SELECT * FROM users")
    logger.info("Query executed successfully (42 rows)")


def simulate_web_request_handler():
    """Simulate handling a web request with per-request logging."""
    logger = get_logger("myapp.web")

    logger.info("Received GET /api/users request")
    logger.debug("Validating request parameters")
    logger.debug("Request validation passed")
    logger.info("Returning user list (status: 200)")


def demonstrate_standard_logging_integration():
    """Show integration with Python's standard logging."""
    print("=== Standard Logging Integration ===")

    # Set up standard logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    # Use standard logging adapter
    adapter = StandardLoggingAdapter("grimoire_integration")
    inject_logger(adapter)

    print("Using grimoire-logging with standard logging backend:")
    simulate_application_module()
    simulate_database_module()

    print()


def demonstrate_web_framework_integration():
    """Show integration with a web framework."""
    print("=== Web Framework Integration ===")

    # Simulate different request contexts
    requests = ["req_001", "req_002", "req_003"]

    for request_id in requests:
        print(f"\n--- Handling Request {request_id} ---")

        # Inject logger with request context
        web_logger = WebFrameworkLogger(request_id)
        inject_logger(web_logger)

        # Handle request
        simulate_web_request_handler()

    print()


def demonstrate_configurable_logging():
    """Show configurable logging scenarios."""
    print("=== Configurable Logging ===")

    configs = [
        {
            "name": "Development",
            "config": {
                "enabled_levels": ["debug", "info", "warning", "error", "critical"],
                "prefix": "DEV",
                "include_timestamp": True,
            },
        },
        {
            "name": "Production",
            "config": {
                "enabled_levels": ["warning", "error", "critical"],
                "prefix": "PROD",
                "include_timestamp": True,
            },
        },
        {
            "name": "Testing",
            "config": {
                "enabled_levels": ["info", "error"],
                "prefix": "TEST",
                "include_timestamp": False,
            },
        },
    ]

    for config_info in configs:
        print(f"\n--- {config_info['name']} Configuration ---")

        configurable_logger = ConfigurableLogger(config_info["config"])
        inject_logger(configurable_logger)

        # Run same code with different logging configurations
        logger = get_logger("configurable_example")
        logger.debug("This is a debug message")
        logger.info("Application started")
        logger.warning("This is a warning")
        logger.error("This is an error")

    print()


def demonstrate_library_integration():
    """Show how a library can use grimoire-logging."""
    print("=== Library Integration Example ===")

    class GameEngine:
        """Example game engine that uses grimoire-logging."""

        def __init__(self):
            self.logger = get_logger("gameengine")

        def initialize(self):
            self.logger.info("Game engine initializing")
            self.logger.debug("Loading game assets")
            self.logger.debug("Initializing graphics system")
            self.logger.info("Game engine ready")

        def start_game(self):
            self.logger.info("Starting new game")
            self.logger.debug("Creating game world")
            self.logger.debug("Spawning player character")
            self.logger.info("Game started successfully")

        def handle_error(self):
            self.logger.error("An error occurred in the game engine")
            self.logger.warning("Attempting to recover")
            self.logger.info("Recovery successful")

    # Use with different logger configurations
    print("Using library with standard logging:")
    adapter = StandardLoggingAdapter("gameengine")
    inject_logger(adapter)

    engine = GameEngine()
    engine.initialize()
    engine.start_game()
    engine.handle_error()

    print("\nUsing library with custom logger:")
    custom_logger = ConfigurableLogger(
        {
            "enabled_levels": ["info", "warning", "error"],
            "prefix": "GAME",
            "include_timestamp": True,
        }
    )
    inject_logger(custom_logger)

    engine2 = GameEngine()
    engine2.initialize()
    engine2.start_game()
    engine2.handle_error()

    print()


def main():
    """Run all integration examples."""
    print("=== Grimoire Logging Integration Examples ===\n")

    try:
        demonstrate_standard_logging_integration()
        demonstrate_web_framework_integration()
        demonstrate_configurable_logging()
        demonstrate_library_integration()

    finally:
        # Clean up
        clear_logger_injection()

    print("=== All Integration Examples Complete ===")


if __name__ == "__main__":
    main()
