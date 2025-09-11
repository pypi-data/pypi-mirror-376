"""Tests for logging injection functionality."""

import logging
import threading
import time
from io import StringIO
from unittest.mock import patch

import pytest

from grimoire_logging import (
    clear_logger_injection,
    get_logger,
    inject_logger,
)
from grimoire_logging.core import LoggerProxy


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.debug_calls = []
        self.info_calls = []
        self.warning_calls = []
        self.error_calls = []
        self.critical_calls = []

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.debug_calls.append(msg % args if args and "%" in msg else msg)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.info_calls.append(msg % args if args and "%" in msg else msg)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.warning_calls.append(msg % args if args and "%" in msg else msg)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.error_calls.append(msg % args if args and "%" in msg else msg)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.critical_calls.append(msg % args if args and "%" in msg else msg)


class TestLoggingBasics:
    """Test basic logging functionality."""

    def test_get_logger_returns_proxy(self):
        """Test that get_logger returns a logger proxy."""
        logger = get_logger("test_module")
        assert isinstance(logger, LoggerProxy)

    def test_logger_proxy_has_required_methods(self):
        """Test that logger proxy has all required methods."""
        logger = get_logger("test_module")

        # Should have all required methods
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_logger_proxy_works_with_standard_logging(self):
        """Test that logger proxy works with standard Python logging."""
        # Ensure no injected logger
        clear_logger_injection()

        logger = get_logger("test_module")

        # Should not raise any exceptions
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

    def test_get_logger_caches_instances(self):
        """Test that get_logger returns the same instance for same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names return different logger instances."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1 is not logger2


class TestLoggerInjection:
    """Test logger injection functionality."""

    def setup_method(self):
        """Reset logger injection before each test."""
        clear_logger_injection()

    def teardown_method(self):
        """Clean up after each test."""
        clear_logger_injection()

    def test_inject_custom_logger(self):
        """Test injecting a custom logger."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        logger = get_logger("test_module")
        logger.info("test message")

        assert "test message" in mock_logger.info_calls

    def test_inject_logger_affects_all_proxies(self):
        """Test that injecting logger affects all existing proxies."""
        # Create logger proxies before injection
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        mock_logger = MockLogger()
        inject_logger(mock_logger)

        # Both loggers should now use the injected logger
        logger1.info("message1")
        logger2.info("message2")

        assert "message1" in mock_logger.info_calls
        assert "message2" in mock_logger.info_calls

    def test_clear_logger_injection(self):
        """Test clearing logger injection."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        logger = get_logger("test_module")
        logger.info("with custom logger")

        # Clear injection
        clear_logger_injection()

        # Should now fall back to standard logging (no exception)
        logger.info("with standard logging")

        # Only first message should be in mock
        assert len(mock_logger.info_calls) == 1
        assert "with custom logger" in mock_logger.info_calls

    def test_inject_none_clears_injection(self):
        """Test that injecting None clears the injection."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        logger = get_logger("test_module")
        logger.info("with custom logger")

        # Inject None
        inject_logger(None)

        # Should now fall back to standard logging (no exception)
        logger.info("with standard logging")

        # Only first message should be in mock
        assert len(mock_logger.info_calls) == 1
        assert "with custom logger" in mock_logger.info_calls

    def test_logger_protocol_compliance(self):
        """Test that mock logger implements the protocol correctly."""
        mock_logger = MockLogger()

        # Test method calls
        mock_logger.debug("debug message")
        mock_logger.info("info message")
        mock_logger.warning("warning message")
        mock_logger.error("error message")
        mock_logger.critical("critical message")

        assert "debug message" in mock_logger.debug_calls
        assert "info message" in mock_logger.info_calls
        assert "warning message" in mock_logger.warning_calls
        assert "error message" in mock_logger.error_calls
        assert "critical message" in mock_logger.critical_calls


class TestLoggerProxy:
    """Test LoggerProxy specific functionality."""

    def setup_method(self):
        """Reset logger injection before each test."""
        clear_logger_injection()

    def teardown_method(self):
        """Clean up after each test."""
        clear_logger_injection()

    def test_logger_proxy_module_name_extraction(self):
        """Test that LoggerProxy correctly extracts module names."""
        # Test simple name
        proxy1 = LoggerProxy("simple")
        assert proxy1._name == "simple"

        # Test dotted name
        proxy2 = LoggerProxy("package.module.submodule")
        assert proxy2._name == "package.module.submodule"

    def test_logger_proxy_fallback_behavior(self):
        """Test that LoggerProxy falls back to standard logging correctly."""
        # Ensure no injection
        clear_logger_injection()

        proxy = LoggerProxy("test_module")

        # Mock standard logging to verify fallback
        with patch.object(proxy._fallback_logger, "info") as mock_info:
            proxy.info("test message")
            mock_info.assert_called_once_with("test message")

    def test_logger_proxy_injection_behavior(self):
        """Test that LoggerProxy uses injected logger when available."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        proxy = LoggerProxy("test_module")
        proxy.info("test message")

        assert "test message" in mock_logger.info_calls

    def test_all_log_levels(self):
        """Test all log levels work correctly."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        proxy = LoggerProxy("test_module")

        proxy.debug("debug msg")
        proxy.info("info msg")
        proxy.warning("warning msg")
        proxy.error("error msg")
        proxy.critical("critical msg")

        assert "debug msg" in mock_logger.debug_calls
        assert "info msg" in mock_logger.info_calls
        assert "warning msg" in mock_logger.warning_calls
        assert "error msg" in mock_logger.error_calls
        assert "critical msg" in mock_logger.critical_calls


class TestThreadSafety:
    """Test thread safety of logging operations."""

    def setup_method(self):
        """Reset logger injection before each test."""
        clear_logger_injection()

    def teardown_method(self):
        """Clean up after each test."""
        clear_logger_injection()

    def test_concurrent_logger_injection(self):
        """Test that logger injection is thread-safe."""
        results = []
        mock_loggers = [MockLogger() for _ in range(10)]

        def inject_and_log(logger_idx):
            inject_logger(mock_loggers[logger_idx])
            logger = get_logger(f"test_module_{logger_idx}")
            logger.info(f"Message from thread {logger_idx}")
            results.append(logger_idx)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=inject_and_log, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have completed without exceptions
        assert len(results) == 10

    def test_concurrent_logger_access(self):
        """Test that getting loggers concurrently is thread-safe."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        results = []

        def get_and_log(thread_id):
            logger = get_logger("shared_module")
            logger.info(f"Message from thread {thread_id}")
            results.append(thread_id)

        threads = []
        for i in range(20):
            thread = threading.Thread(target=get_and_log, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have 20 messages
        assert len(mock_logger.info_calls) == 20
        assert len(results) == 20

    def test_injection_during_logging(self):
        """Test injecting logger while other threads are logging."""
        mock_logger1 = MockLogger()
        mock_logger2 = MockLogger()

        inject_logger(mock_logger1)

        results = []

        def continuous_logging():
            logger = get_logger("test_module")
            for i in range(100):
                logger.info(f"Message {i}")
                time.sleep(0.001)  # Small delay
            results.append("logging_done")

        def switch_logger():
            time.sleep(0.05)  # Let some logging happen
            inject_logger(mock_logger2)
            results.append("logger_switched")

        # Start logging thread
        log_thread = threading.Thread(target=continuous_logging)
        switch_thread = threading.Thread(target=switch_logger)

        log_thread.start()
        switch_thread.start()

        log_thread.join()
        switch_thread.join()

        # Should complete without exceptions
        assert "logging_done" in results
        assert "logger_switched" in results

        # Messages should be distributed between the two loggers
        total_messages = len(mock_logger1.info_calls) + len(mock_logger2.info_calls)
        assert total_messages == 100


class TestIntegrationWithStandardLogging:
    """Test integration with Python's standard logging."""

    def setup_method(self):
        """Reset logger injection before each test."""
        clear_logger_injection()

    def teardown_method(self):
        """Clean up after each test."""
        clear_logger_injection()

    def test_standard_logging_integration(self):
        """Test that standard Python logging works properly."""
        # Capture standard logging output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)

        # Set up standard logger
        std_logger = logging.getLogger("grimoire_test")
        std_logger.setLevel(logging.DEBUG)
        std_logger.addHandler(handler)

        try:
            # Use our logging system without injection
            logger = get_logger("grimoire_test")
            logger.info("Test message")

            # Should appear in standard logging output
            log_output = log_capture.getvalue()
            assert "Test message" in log_output

        finally:
            std_logger.removeHandler(handler)

    def test_formatting_with_args(self):
        """Test that formatting with *args works correctly."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        logger = get_logger("test_module")
        logger.info("Hello %s, you have %d messages", "Alice", 5)

        # Should format the message
        assert "Hello Alice, you have 5 messages" in mock_logger.info_calls

    def test_kwargs_passed_through(self):
        """Test that **kwargs are passed through correctly."""
        # This is more of an integration test to ensure no exceptions
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        logger = get_logger("test_module")

        # Should not raise exceptions with extra kwargs
        logger.info("Test message", extra={"custom_field": "value"})
        logger.debug("Debug message", exc_info=False)

        assert len(mock_logger.info_calls) == 1
        assert len(mock_logger.debug_calls) == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Reset logger injection before each test."""
        clear_logger_injection()

    def teardown_method(self):
        """Clean up after each test."""
        clear_logger_injection()

    def test_invalid_logger_injection(self):
        """Test behavior with invalid logger objects."""

        # Object missing required methods
        class IncompleteLogger:
            def info(self, msg: str, *args, **kwargs) -> None:
                pass

            # Missing other required methods

        # Should not raise during injection
        inject_logger(IncompleteLogger())  # type: ignore

        logger = get_logger("test_module")

        # Should not raise for methods that exist
        logger.info("This should work")

        # Methods that don't exist should raise AttributeError
        with pytest.raises(AttributeError):
            logger.debug("This should fail")

    def test_exception_in_injected_logger(self):
        """Test behavior when injected logger raises exceptions."""

        class FaultyLogger:
            def info(self, msg: str, *args, **kwargs) -> None:
                raise ValueError("Logger error")

            def debug(self, msg: str, *args, **kwargs) -> None:
                pass

            def warning(self, msg: str, *args, **kwargs) -> None:
                pass

            def error(self, msg: str, *args, **kwargs) -> None:
                pass

            def critical(self, msg: str, *args, **kwargs) -> None:
                pass

        inject_logger(FaultyLogger())
        logger = get_logger("test_module")

        # Exception should propagate
        with pytest.raises(ValueError, match="Logger error"):
            logger.info("This will fail")

        # Other methods should still work
        logger.debug("This should work")
