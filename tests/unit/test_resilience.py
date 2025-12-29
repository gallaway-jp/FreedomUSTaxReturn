"""
Tests for resilience utilities (retry and circuit breaker patterns).

Tests cover:
- Retry decorator functionality
- Exponential backoff
- Circuit breaker state transitions
- Circuit breaker recovery
"""
import pytest
import time
from datetime import datetime, timedelta
from utils.resilience import retry, CircuitBreaker, CircuitState, CircuitBreakerOpenError


class TestRetryDecorator:
    """Test retry decorator with exponential backoff."""
    
    def test_retry_success_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = 0
        
        @retry(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test function succeeds after initial failures."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_fails_after_max_attempts(self):
        """Test function raises after max attempts."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError, match="Persistent error"):
            failing_function()
        
        assert call_count == 3
    
    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []
        
        @retry(max_attempts=3, delay=0.1, backoff=2.0)
        def failing_function():
            call_times.append(time.time())
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Check that delays increase exponentially
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay2 > delay1 * 1.5  # Should be roughly double
    
    def test_retry_specific_exceptions(self):
        """Test retry only catches specified exceptions."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError, IOError))
        def selective_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable")
            else:
                raise TypeError("Not retryable")
        
        with pytest.raises(TypeError, match="Not retryable"):
            selective_function()
        
        assert call_count == 2  # Failed on ValueError, then TypeError
    
    def test_retry_preserves_function_metadata(self):
        """Test retry decorator preserves function name and docstring."""
        
        @retry()
        def documented_function():
            """This is a docstring."""
            return True
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a docstring."


class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization."""
    
    def test_init_defaults(self):
        """Test circuit breaker initialization with defaults."""
        breaker = CircuitBreaker(name="TestBreaker")
        assert breaker.name == "TestBreaker"
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        breaker = CircuitBreaker(
            name="CustomBreaker",
            failure_threshold=3,
            recovery_timeout=30
        )
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30


class TestCircuitBreakerClosedState:
    """Test circuit breaker in CLOSED state."""
    
    def test_call_success_in_closed_state(self):
        """Test successful call keeps circuit closed."""
        breaker = CircuitBreaker(name="Test", failure_threshold=3)
        
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_call_failure_increments_count(self):
        """Test failed call increments failure count."""
        breaker = CircuitBreaker(name="Test", failure_threshold=3)
        
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        assert breaker.failure_count == 1
        assert breaker.state == CircuitState.CLOSED
    
    def test_call_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(name="Test", failure_threshold=3)
        
        # First 2 failures
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
            assert breaker.state == CircuitState.CLOSED
        
        # 3rd failure opens circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3


class TestCircuitBreakerOpenState:
    """Test circuit breaker in OPEN state."""
    
    def test_call_raises_when_open(self):
        """Test calls are rejected when circuit is open."""
        breaker = CircuitBreaker(name="Test", failure_threshold=2)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "success")
    
    def test_open_state_includes_recovery_time(self):
        """Test error message includes recovery time."""
        breaker = CircuitBreaker(name="Test", failure_threshold=1, recovery_timeout=30)
        
        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        # Should show recovery time
        with pytest.raises(CircuitBreakerOpenError, match="until \\d{2}:\\d{2}:\\d{2}"):
            breaker.call(lambda: "success")


class TestCircuitBreakerHalfOpenState:
    """Test circuit breaker in HALF_OPEN state."""
    
    def test_transitions_to_half_open_after_timeout(self):
        """Test circuit moves to half-open after timeout."""
        breaker = CircuitBreaker(name="Test", failure_threshold=1, recovery_timeout=0)
        
        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout (instant in this case)
        time.sleep(0.01)
        
        # Next call should attempt recovery
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    def test_half_open_success_closes_circuit(self):
        """Test successful call in half-open closes circuit."""
        breaker = CircuitBreaker(name="Test", failure_threshold=1, recovery_timeout=0)
        
        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        time.sleep(0.01)
        
        # Successful recovery
        breaker.call(lambda: "success")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_half_open_failure_reopens_circuit(self):
        """Test failed call in half-open reopens circuit."""
        breaker = CircuitBreaker(name="Test", failure_threshold=1, recovery_timeout=0)
        
        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error 1")))
        
        time.sleep(0.01)
        
        # Failed recovery attempt
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error 2")))
        
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerReset:
    """Test manual circuit breaker reset."""
    
    def test_manual_reset_clears_state(self):
        """Test manual reset clears failure count and state."""
        breaker = CircuitBreaker(name="Test", failure_threshold=2)
        
        # Accumulate failures
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        assert breaker.failure_count == 1
        
        # Manual reset
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.last_failure_time is None
    
    def test_reset_from_open_state(self):
        """Test reset from open state allows calls."""
        breaker = CircuitBreaker(name="Test", failure_threshold=1)
        
        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        assert breaker.state == CircuitState.OPEN
        
        # Reset and verify calls work
        breaker.reset()
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerGetState:
    """Test getting circuit breaker state."""
    
    def test_get_state_closed(self):
        """Test get_state returns CLOSED initially."""
        breaker = CircuitBreaker(name="Test")
        assert breaker.get_state() == CircuitState.CLOSED
    
    def test_get_state_open(self):
        """Test get_state returns OPEN after failures."""
        breaker = CircuitBreaker(name="Test", failure_threshold=1)
        
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
        
        assert breaker.get_state() == CircuitState.OPEN
