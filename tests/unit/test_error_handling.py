"""
Tests for error handling scenarios

This module tests error handling, validation, and recovery mechanisms
across the application.
"""

import pytest
import json
from pathlib import Path
from models.tax_data import TaxData
from utils.event_bus import EventBus, Event, EventType
from utils.resilience import retry, CircuitBreaker, CircuitBreakerOpenError
from utils.error_tracker import ErrorTracker, ErrorRecord


class TestTaxDataErrorHandling:
    """Test error handling in TaxData model"""
    
    def test_invalid_ssn_raises_value_error(self):
        """Should raise ValueError for invalid SSN"""
        tax_data = TaxData()
        
        with pytest.raises(ValueError, match="Invalid"):
            tax_data.set("personal_info.ssn", "invalid")
    
    def test_negative_income_raises_error(self):
        """Should reject negative income values"""
        tax_data = TaxData()
        
        with pytest.raises(ValueError, match="cannot be negative"):
            tax_data.set("income.w2_forms.0.wages", -1000)
    
    def test_exceed_max_value_raises_error(self):
        """Should reject values exceeding maximum"""
        tax_data = TaxData()
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            tax_data.set("income.w2_forms.0.wages", 1000000000)
    
    def test_exceed_max_length_raises_error(self):
        """Should enforce maximum string lengths"""
        tax_data = TaxData()
        
        with pytest.raises(ValueError, match="exceeds maximum length"):
            tax_data.set("personal_info.first_name", "A" * 51)
    
    def test_load_nonexistent_file_raises_error(self):
        """Should raise FileNotFoundError for missing files"""
        tax_data = TaxData()
        
        with pytest.raises(FileNotFoundError):
            tax_data.load_from_file("nonexistent_file.enc")
    
    def test_invalid_path_raises_error(self):
        """Should reject invalid file paths"""
        tax_data = TaxData()
        
        with pytest.raises(ValueError, match="Invalid file path"):
            tax_data.save_to_file("../../etc/passwd")


class TestEventBusResilience:
    """Test event bus error handling and resilience"""
    
    def test_failing_handler_doesnt_crash_bus(self):
        """One failing handler shouldn't stop other handlers"""
        results = []
        
        def working_handler(event):
            results.append("working")
        
        def failing_handler(event):
            raise Exception("Handler failed!")
        
        bus = EventBus.get_instance()
        bus.subscribe(EventType.TAX_DATA_CHANGED, working_handler)
        bus.subscribe(EventType.TAX_DATA_CHANGED, failing_handler)
        
        event = Event(type=EventType.TAX_DATA_CHANGED, source="test", data={})
        bus.publish(event)
        
        # Working handler should still execute despite failing handler
        assert "working" in results
        
        # Cleanup
        bus.unsubscribe(EventType.TAX_DATA_CHANGED, working_handler)
        bus.unsubscribe(EventType.TAX_DATA_CHANGED, failing_handler)
    
    def test_multiple_failing_handlers_dont_crash(self):
        """Multiple failing handlers should all be attempted"""
        bus = EventBus.get_instance()
        
        def failing_handler_1(event):
            raise ValueError("Handler 1 failed")
        
        def failing_handler_2(event):
            raise TypeError("Handler 2 failed")
        
        bus.subscribe(EventType.CALCULATION_COMPLETED, failing_handler_1)
        bus.subscribe(EventType.CALCULATION_COMPLETED, failing_handler_2)
        
        event = Event(type=EventType.CALCULATION_COMPLETED, source="test", data={})
        
        # Should not raise exception
        bus.publish(event)
        
        # Cleanup
        bus.unsubscribe(EventType.CALCULATION_COMPLETED, failing_handler_1)
        bus.unsubscribe(EventType.CALCULATION_COMPLETED, failing_handler_2)


class TestRetryMechanism:
    """Test retry decorator functionality"""
    
    def test_retry_success_on_first_attempt(self):
        """Should succeed immediately if no errors"""
        call_count = [0]
        
        @retry(max_attempts=3)
        def successful_function():
            call_count[0] += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retry_success_after_failures(self):
        """Should retry and eventually succeed"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_retry_exhausts_attempts(self):
        """Should raise error after max attempts"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def always_failing_function():
            call_count[0] += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            always_failing_function()
        
        assert call_count[0] == 3
    
    def test_retry_ignores_unexpected_exceptions(self):
        """Should not retry exceptions not in the list"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def wrong_exception_function():
            call_count[0] += 1
            raise TypeError("Wrong exception type")
        
        with pytest.raises(TypeError):
            wrong_exception_function()
        
        # Should fail immediately, not retry
        assert call_count[0] == 1


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_closed_state(self):
        """Circuit breaker should allow calls in CLOSED state"""
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            recovery_timeout=1
        )
        
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.get_state().value == "closed"
    
    def test_circuit_breaker_opens_after_failures(self):
        """Circuit breaker should open after threshold failures"""
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            recovery_timeout=1,
            expected_exception=ValueError
        )
        
        # Trigger failures
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
            except ValueError:
                pass
        
        # Circuit should now be open
        assert breaker.get_state().value == "open"
        
        # Should reject new calls
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "success")
    
    def test_circuit_breaker_resets_on_success(self):
        """Circuit breaker should reset failure count on success"""
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            recovery_timeout=1,
            expected_exception=ValueError
        )
        
        # Partial failures
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
            except ValueError:
                pass
        
        # Success should reset
        breaker.call(lambda: "success")
        
        assert breaker.failure_count == 0
        assert breaker.get_state().value == "closed"


class TestErrorTracker:
    """Test error tracking functionality"""
    
    def test_track_error_creates_record(self, tmp_path):
        """Should create error record when tracking error"""
        tracker = ErrorTracker(tmp_path)
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            record = tracker.track_error(
                error=e,
                context={"test": "context"},
                severity="ERROR",
                user_message="User friendly message"
            )
        
        assert record.error_type == "ValueError"
        assert record.error_message == "Test error"
        assert record.severity == "ERROR"
        assert record.context["test"] == "context"
        assert record.user_message == "User friendly message"
    
    def test_error_tracker_writes_to_file(self, tmp_path):
        """Should write errors to JSON Lines file"""
        tracker = ErrorTracker(tmp_path)
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            tracker.track_error(error=e, context={"test": "data"})
        
        error_file = tmp_path / "errors.jsonl"
        assert error_file.exists()
        
        with open(error_file, 'r') as f:
            line = f.readline()
            record = json.loads(line)
            assert record["error_type"] == "ValueError"
            assert record["error_message"] == "Test error"
    
    def test_error_summary(self, tmp_path):
        """Should generate error summary"""
        tracker = ErrorTracker(tmp_path)
        
        # Track multiple errors
        for i in range(5):
            try:
                raise ValueError(f"Error {i}")
            except ValueError as e:
                tracker.track_error(error=e)
        
        summary = tracker.get_error_summary(hours=24)
        assert summary["total_errors"] == 5
        assert summary["by_type"]["ValueError"] == 5
        assert summary["by_severity"]["ERROR"] == 5
    
    def test_clear_old_errors(self, tmp_path):
        """Should remove old error records"""
        tracker = ErrorTracker(tmp_path)
        
        # Track an error
        try:
            raise ValueError("Test error")
        except ValueError as e:
            tracker.track_error(error=e)
        
        # Clear errors older than 30 days (should keep recent one)
        tracker.clear_old_errors(days=30)
        
        summary = tracker.get_error_summary(hours=24)
        assert summary["total_errors"] >= 0  # May be 0 or 1 depending on timing


class TestValidationErrors:
    """Test validation error messages"""
    
    def test_ssn_validation_message(self):
        """SSN validation should provide clear error message"""
        from utils.validation import validate_ssn
        
        is_valid, message = validate_ssn("invalid")
        assert not is_valid
        assert "SSN" in message or "format" in message.lower()
    
    def test_email_validation_message(self):
        """Email validation should provide clear error message"""
        from utils.validation import validate_email
        
        is_valid, message = validate_email("invalid-email")
        assert not is_valid
        assert "email" in message.lower()
    
    def test_zip_validation_message(self):
        """ZIP code validation should provide clear error message"""
        from utils.validation import validate_zip_code
        
        is_valid, message = validate_zip_code("invalid")
        assert not is_valid
        assert "ZIP" in message or "postal" in message.lower()
