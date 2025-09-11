"""Logging utilities with dependency injection support.

Thread Safety:
    All public functions in this module are thread-safe and can be safely called
    from multiple threads simultaneously. Internal state is protected using
    threading.RLock() to prevent race conditions during logger injection and
    registry access.

    - inject_logger(): Atomic update of global logger state
    - get_logger(): Atomic access to logger registry with lazy creation
    - LoggerProxy methods: Thread-safe delegation to current injected logger

    Note: While race conditions are theoretically possible without locking,
    they are rare in practice due to Python's GIL and the atomic nature of
    simple operations. The locking is provided for correctness and to ensure
    predictable behavior in all scenarios, especially future Python
    implementations or when using different interpreters.

Usage:
    # Safe to call from multiple threads
    inject_logger(custom_logger)
    logger = get_logger(__name__)
    logger.info("Thread-safe logging")
"""

import logging
import threading
from typing import Any, Dict, Optional, Protocol


class LoggerProtocol(Protocol):
    """Protocol defining the logger interface for dependency injection."""

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log error message."""
        ...

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message."""
        ...


class LoggerProxy:
    """Proxy that delegates to injected logger or falls back to standard logging."""

    def __init__(self, name: str):
        self._name = name
        module_name = name.split(".")[-1] if "." in name else name
        self._fallback_logger = logging.getLogger(module_name)

    def _get_current_logger(self) -> LoggerProtocol:
        """Get the current active logger (injected or fallback)."""
        global _injected_logger, _logger_lock
        with _logger_lock:
            return (
                _injected_logger
                if _injected_logger is not None
                else self._fallback_logger
            )

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._get_current_logger().debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._get_current_logger().info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._get_current_logger().warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._get_current_logger().error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._get_current_logger().critical(msg, *args, **kwargs)


# Global logger instance for injection with thread safety
_injected_logger: Optional[LoggerProtocol] = None
_logger_instances: Dict[str, LoggerProxy] = {}
_logger_lock = threading.RLock()  # Re-entrant lock for nested calls


def inject_logger(logger: Optional[LoggerProtocol]) -> None:
    """Inject a custom logger implementation.

    Thread-safe: Uses locking to ensure atomic updates of the global logger state.

    Args:
        logger: Logger implementation that conforms to LoggerProtocol,
                or None to revert to standard logging

    Example:
        >>> class CustomLogger:
        ...     def info(self, msg: str, *args, **kwargs) -> None:
        ...         print(f"INFO: {msg}")
        ...     def debug(self, msg: str, *args, **kwargs) -> None:
        ...         print(f"DEBUG: {msg}")
        ...     def warning(self, msg: str, *args, **kwargs) -> None:
        ...         print(f"WARNING: {msg}")
        ...     def error(self, msg: str, *args, **kwargs) -> None:
        ...         print(f"ERROR: {msg}")
        ...     def critical(self, msg: str, *args, **kwargs) -> None:
        ...         print(f"CRITICAL: {msg}")
        ...
        >>> inject_logger(CustomLogger())
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello, world!")
        INFO: Hello, world!
    """
    global _injected_logger, _logger_lock
    with _logger_lock:
        _injected_logger = logger


def clear_logger_injection() -> None:
    """Clear any injected logger and revert to default.

    This is equivalent to calling inject_logger(None).

    Example:
        >>> inject_logger(some_custom_logger)
        >>> clear_logger_injection()  # Back to standard logging
    """
    inject_logger(None)


def get_logger(name: str) -> LoggerProtocol:
    """Get a logger instance for the given name.

    Returns a logger proxy that automatically delegates to the current
    injected logger or falls back to standard Python logging.

    Thread-safe: Uses locking to ensure atomic access to the logger registry.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger proxy that conforms to LoggerProtocol

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This works with any injected logger")
        >>>
        >>> # Or with module name
        >>> logger = get_logger("my_module")
        >>> logger.debug("Debug message")
    """
    global _logger_instances, _logger_lock
    with _logger_lock:
        if name in _logger_instances:
            return _logger_instances[name]

        # Create a new proxy for this name
        proxy = LoggerProxy(name)
        _logger_instances[name] = proxy
        return proxy
