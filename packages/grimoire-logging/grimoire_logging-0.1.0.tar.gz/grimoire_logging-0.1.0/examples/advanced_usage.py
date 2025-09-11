#!/usr/bin/env python3
"""Advanced usage example for grimoire-logging.

This example demonstrates advanced scenarios:
- Structured logging with JSON output
- Filtering and transforming log messages
- Integration with third-party logging libraries
- Thread-safe concurrent logging
"""

import json
import threading
import time
from datetime import datetime
from typing import Any, Dict

from grimoire_logging import clear_logger_injection, get_logger, inject_logger


class JSONLogger:
    """Custom logger that outputs structured JSON logs."""

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Output a structured JSON log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": "grimoire_logging",
            "message": message,
            "thread_id": threading.current_thread().ident,
            **kwargs,
        }
        print(json.dumps(log_entry))

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._log("DEBUG", msg, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._log("INFO", msg, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._log("WARNING", msg, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._log("ERROR", msg, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._log("CRITICAL", msg, **kwargs)


class FilteringLogger:
    """Logger that filters and transforms messages."""

    def __init__(self, base_logger, ignored_patterns=None):
        self.base_logger = base_logger
        self.ignored_patterns = ignored_patterns or []
        self.message_count = 0

    def _should_log(self, message: str) -> bool:
        """Check if message should be logged based on filters."""
        return not any(pattern in message for pattern in self.ignored_patterns)

    def _transform_message(self, message: str) -> str:
        """Transform the message before logging."""
        self.message_count += 1
        return f"[#{self.message_count:04d}] {message}"

    def debug(self, msg: str, *args, **kwargs) -> None:
        if self._should_log(msg):
            self.base_logger.debug(self._transform_message(msg), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        if self._should_log(msg):
            self.base_logger.info(self._transform_message(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        # Always log warnings
        self.base_logger.warning(self._transform_message(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        # Always log errors
        self.base_logger.error(self._transform_message(msg), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        # Always log critical
        self.base_logger.critical(self._transform_message(msg), *args, **kwargs)


class GameEventLogger:
    """Specialized logger for game events in a tabletop RPG context."""

    def __init__(self):
        self.session_id = "session_" + str(int(time.time()))
        self.events = []

    def _log_event(self, level: str, message: str, event_type: str = "general"):
        """Log a game event with context."""
        event = {
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event_type": event_type,
            "message": message,
        }
        self.events.append(event)

        # Format for display
        display_msg = f"🎲 [{event_type.upper()}] {message}"
        print(f"{level}: {display_msg}")

    def debug(self, msg: str, *args, **kwargs) -> None:
        event_type = kwargs.pop("event_type", "debug")
        self._log_event("DEBUG", msg, event_type)

    def info(self, msg: str, *args, **kwargs) -> None:
        event_type = kwargs.pop("event_type", "info")
        self._log_event("INFO", msg, event_type)

    def warning(self, msg: str, *args, **kwargs) -> None:
        event_type = kwargs.pop("event_type", "warning")
        self._log_event("WARNING", msg, event_type)

    def error(self, msg: str, *args, **kwargs) -> None:
        event_type = kwargs.pop("event_type", "error")
        self._log_event("ERROR", msg, event_type)

    def critical(self, msg: str, *args, **kwargs) -> None:
        event_type = kwargs.pop("event_type", "critical")
        self._log_event("CRITICAL", msg, event_type)

    def get_events_summary(self) -> Dict[str, Any]:
        """Get a summary of logged events."""
        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "events_by_type": {
                event_type: len(
                    [e for e in self.events if e["event_type"] == event_type]
                )
                for event_type in {e["event_type"] for e in self.events}
            },
            "events": self.events,
        }


def demonstrate_json_logging():
    """Demonstrate structured JSON logging."""
    print("=== JSON Structured Logging ===")

    json_logger = JSONLogger()
    inject_logger(json_logger)

    logger = get_logger("json_example")
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("This is a warning")

    print()


def demonstrate_filtering():
    """Demonstrate message filtering and transformation."""
    print("=== Filtered and Transformed Logging ===")

    # Create a filtering logger that ignores debug messages
    base_logger = JSONLogger()
    filtering_logger = FilteringLogger(base_logger, ignored_patterns=["debug", "trace"])

    inject_logger(filtering_logger)

    logger = get_logger("filtering_example")
    logger.info("This message will be logged with a counter")
    logger.debug("This debug message will be ignored")
    logger.info("This is another info message")
    logger.warning("Warnings are always logged")
    logger.debug("Another ignored debug message")
    logger.error("Errors are always logged")

    print()


def demonstrate_game_logging():
    """Demonstrate specialized game event logging."""
    print("=== Game Event Logging ===")

    game_logger = GameEventLogger()
    inject_logger(game_logger)

    # Simulate game events
    logger = get_logger("game")

    logger.info("New player joined the session", event_type="player_action")
    logger.info("Rolling initiative for combat", event_type="combat")
    logger.debug("Player rolled 18 for initiative", event_type="dice_roll")
    logger.warning("Player health is low", event_type="status_warning")
    logger.info("Combat round completed", event_type="combat")
    logger.error("Player character died", event_type="player_death")

    # Show event summary
    print("\n--- Event Summary ---")
    summary = game_logger.get_events_summary()
    print(json.dumps(summary, indent=2))

    print()


def demonstrate_thread_safety():
    """Demonstrate thread-safe logging with multiple loggers."""
    print("=== Thread-Safe Concurrent Logging ===")

    json_logger = JSONLogger()
    inject_logger(json_logger)

    def worker_thread(worker_id: int):
        """Worker function that logs from multiple threads."""
        logger = get_logger(f"worker_{worker_id}")

        for i in range(5):
            logger.info(f"Worker {worker_id} processing item {i}")
            time.sleep(0.1)  # Simulate work

        logger.info(f"Worker {worker_id} completed")

    # Start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All workers completed\n")


def main():
    """Run all advanced examples."""
    print("=== Grimoire Logging Advanced Examples ===\n")

    try:
        demonstrate_json_logging()
        demonstrate_filtering()
        demonstrate_game_logging()
        demonstrate_thread_safety()

    finally:
        # Clean up
        clear_logger_injection()

    print("=== All Examples Complete ===")


if __name__ == "__main__":
    main()
