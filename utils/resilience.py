"""
Resilience Utilities - Retry and Circuit Breaker Patterns

This module provides utilities for handling transient failures and
preventing cascading errors in the application.
"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(IOError, PermissionError))
        def save_file(filename):
            # Will retry up to 3 times on IOError or PermissionError
            with open(filename, 'w') as f:
                f.write(data)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class CircuitState(Enum):
    """States of a circuit breaker"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests"""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing recovery, allow one request through
    
    Example:
        breaker = CircuitBreaker(
            name="PDFGenerator",
            failure_threshold=5,
            recovery_timeout=60
        )
        
        result = breaker.call(generate_pdf, tax_data)
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name for logging/identification
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type(s) that trigger the circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result of function call
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        # Check if circuit should move to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}': HALF_OPEN (testing recovery)")
            else:
                next_attempt = self.last_failure_time + timedelta(seconds=self.recovery_timeout)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable until {next_attempt.strftime('%H:%M:%S')}"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return datetime.now() >= self.last_failure_time + timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}': CLOSED (recovered)")
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker '{self.name}': OPEN after {self.failure_count} failures. "
                f"Will retry after {self.recovery_timeout}s"
            )
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state"""
        return self.state
