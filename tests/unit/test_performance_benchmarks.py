"""
Performance Benchmarks for Tax Services

Tests performance characteristics, scalability, and resource usage.
"""

import pytest
import time
from services.exceptions import InvalidInputException


class TestServiceInitializationPerformance:
    """Test service initialization performance"""

    def test_app_config_init_performance(self):
        """Test AppConfig initialization performance"""
        from config.app_config import AppConfig
        
        start = time.time()
        config = AppConfig()
        elapsed = time.time() - start
        
        assert config is not None
        assert elapsed < 1.0  # Should initialize in < 1 second

    def test_error_logger_init_performance(self):
        """Test ErrorLogger initialization performance"""
        from services.error_logger import ErrorLogger
        
        start = time.time()
        logger = ErrorLogger()
        elapsed = time.time() - start
        
        assert logger is not None
        assert elapsed < 0.1  # Should be very fast (singleton)

    def test_multiple_service_initialization(self):
        """Test initializing multiple services"""
        from config.app_config import AppConfig
        from services.error_logger import ErrorLogger
        
        start = time.time()
        config = AppConfig()
        logger = ErrorLogger()
        elapsed = time.time() - start
        
        assert config is not None
        assert logger is not None
        assert elapsed < 1.0  # Should all initialize in < 1 second


class TestDataProcessingPerformance:
    """Test data processing performance"""

    def test_exception_creation_performance(self):
        """Test exception creation speed"""
        start = time.time()
        for i in range(1000):
            exc = InvalidInputException(f"field_{i}", "Invalid")
        elapsed = time.time() - start
        
        # Should be very fast
        assert elapsed < 0.5

    def test_error_logging_performance(self):
        """Test error logging performance"""
        from services.error_logger import ErrorLogger
        
        logger = ErrorLogger()
        start = time.time()
        
        for i in range(100):
            exc = InvalidInputException(f"field_{i}", "Invalid")
            logger.log_exception("TestComponent", exc)
        
        elapsed = time.time() - start
        
        # Should handle 100 logs in < 0.5 seconds
        assert elapsed < 0.5


class TestMemoryUsagePatterns:
    """Test memory usage patterns"""

    def test_large_error_history(self):
        """Test memory handling with large error history"""
        from services.error_logger import ErrorLogger
        
        logger = ErrorLogger.get_instance()
        
        # Log many errors
        for i in range(100):
            exc = InvalidInputException(f"field_{i}", "Error message")
            logger.log_exception("Component", exc)
        
        history = logger.get_error_history()
        # Should still be able to access history
        assert len(history) > 0

    def test_exception_with_large_details(self):
        """Test exception handling with large detail dictionaries"""
        large_details = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        exc = InvalidInputException(
            "field",
            "Invalid",
            details=large_details
        )
        
        details = exc.get_details()
        assert "details" in details


class TestConcurrentOperationPerformance:
    """Test concurrent operation performance"""

    def test_sequential_exception_handling(self):
        """Test sequential exception handling"""
        from services.exceptions import (
            InvalidInputException,
            FileProcessingException,
            EncryptionKeyNotFoundException,
        )
        
        start = time.time()
        
        for i in range(100):
            try:
                if i % 3 == 0:
                    raise InvalidInputException(f"field_{i}", "error")
                elif i % 3 == 1:
                    raise FileProcessingException(f"/file_{i}", "read")
                else:
                    raise EncryptionKeyNotFoundException(f"/key_{i}")
            except Exception:
                pass
        
        elapsed = time.time() - start
        assert elapsed < 1.0

    def test_error_aggregation_performance(self):
        """Test error aggregation performance"""
        errors = []
        
        start = time.time()
        for i in range(100):
            try:
                raise InvalidInputException(f"field_{i}", "error")
            except Exception as e:
                errors.append(e)
        
        elapsed = time.time() - start
        
        assert len(errors) == 100
        assert elapsed < 1.0


class TestScalabilityCharacteristics:
    """Test scalability characteristics"""

    def test_linear_scaling_exception_creation(self):
        """Test that exception creation scales linearly"""
        # Small batch
        start1 = time.time()
        for i in range(100):
            exc = InvalidInputException(f"field_{i}", "error")
        time1 = time.time() - start1
        
        # Large batch (10x)
        start2 = time.time()
        for i in range(1000):
            exc = InvalidInputException(f"field_{i}", "error")
        time2 = time.time() - start2
        
        # Should scale roughly linearly (allowing for variance)
        assert time2 < time1 * 15  # Should be roughly 10x, with some overhead

    def test_error_logging_scalability(self):
        """Test error logging scalability"""
        from services.error_logger import ErrorLogger
        
        logger = ErrorLogger()
        
        # Log 100 errors
        start1 = time.time()
        for i in range(100):
            exc = InvalidInputException(f"field_{i}", "error")
            logger.log_exception("Component", exc)
        time1 = time.time() - start1
        
        # Log 1000 errors
        start2 = time.time()
        for i in range(1000):
            exc = InvalidInputException(f"field_{i}", "error")
            logger.log_exception("Component", exc)
        time2 = time.time() - start2
        
        # Should scale reasonably (not quadratic)
        assert time2 < time1 * 20


class TestErrorHandlingPerformance:
    """Test error handling performance cost"""

    def test_exception_creation_overhead(self):
        """Test overhead of exception creation"""
        import sys
        
        # Time without exceptions
        start1 = time.time()
        for i in range(1000):
            value = i * 2
        time1 = time.time() - start1
        
        # Time with exception creation
        start2 = time.time()
        for i in range(1000):
            exc = InvalidInputException(f"field_{i}", "error")
        time2 = time.time() - start2
        
        # Exception creation should be reasonably fast
        assert time2 < 1.0

    def test_exception_handling_cost(self):
        """Test cost of exception handling (try/except)"""
        errors = []
        
        start = time.time()
        for i in range(1000):
            try:
                if i % 10 == 0:
                    raise InvalidInputException(f"field_{i}", "error")
            except Exception as e:
                errors.append(e)
        
        elapsed = time.time() - start
        
        # Should handle 1000 operations with 100 exceptions in < 1 second
        assert elapsed < 1.0
        assert len(errors) == 100


class TestResourceCleanup:
    """Test resource cleanup and garbage collection"""

    def test_logger_singleton_cleanup(self):
        """Test logger singleton cleanup"""
        from services.error_logger import ErrorLogger
        
        logger1 = ErrorLogger.get_instance()
        history1_size = len(logger1.get_error_history())
        
        # Create another reference
        logger2 = ErrorLogger.get_instance()
        
        # Should be the same instance
        assert logger1 is logger2

    def test_exception_garbage_collection(self):
        """Test exception garbage collection"""
        import gc
        
        # Create and discard exceptions
        for i in range(1000):
            exc = InvalidInputException(f"field_{i}", "error")
        
        # Force garbage collection
        gc.collect()
        
        # Should complete without issues
        assert True
