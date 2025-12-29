"""
Tests to cover specific missing lines in high-coverage modules.

This test file targets exact missing lines to push modules from 94-98% to 100%.
"""

import pytest
import time
from unittest.mock import Mock, patch
from utils.resilience import retry, CircuitBreaker, CircuitBreakerOpenError, CircuitState
from services.tax_calculation_service import TaxCalculationService, TaxResult
from utils.pdf.field_mapper import DotDict
from utils.tax_data_validator import TaxDataValidator


class TestResilienceMissingLines:
    """Cover missing lines in resilience.py (lines 65-66, 170)"""
    
    def test_retry_exhausts_all_attempts_raises_last_exception(self):
        """Test that retry raises the last exception after all attempts fail."""
        attempt_count = 0
        
        @retry(max_attempts=3, delay=0.01, backoff=1)
        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError(f"Attempt {attempt_count}")
        
        # This should exhaust all retries and raise the last exception (line 65-66)
        with pytest.raises(ValueError, match="Attempt 3"):
            always_fails()
        
        assert attempt_count == 3
    
    def test_circuit_breaker_should_attempt_reset_with_no_failures(self):
        """Test circuit breaker _should_attempt_reset when last_failure_time is None (line 170)"""
        breaker = CircuitBreaker("test", failure_threshold=5, recovery_timeout=60)
        
        # Initially, last_failure_time is None
        assert breaker.last_failure_time is None
        
        # Manually set state to OPEN to trigger the check
        breaker.state = CircuitState.OPEN
        
        # Now calling _should_attempt_reset should return True (line 170)
        assert breaker._should_attempt_reset() is True
    
    def test_circuit_breaker_should_attempt_reset_after_timeout(self):
        """Test circuit breaker _should_attempt_reset with sufficient time passed (line 171)"""
        breaker = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0)
        
        # Force circuit to open
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout (0 seconds means immediate)
        time.sleep(0.01)
        
        # Now _should_attempt_reset should check line 171 (time comparison)
        # This is tested by calling the function again, which will check the condition
        def success_func():
            return "success"
        
        # This should transition to HALF_OPEN and then succeed
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


class TestTaxCalculationServiceMissingLines:
    """Cover missing lines in tax_calculation_service.py (lines 221, 272)"""
    
    def test_get_effective_tax_rate_with_zero_income(self):
        """Test effective tax rate calculation with zero income (line 221)"""
        service = TaxCalculationService(2025)
        
        # Create a tax result with zero AGI
        result = TaxResult(
            adjusted_gross_income=0,
            total_tax=500
        )
        
        # This should return 0.0 instead of dividing by zero (line 221)
        rate = service.get_effective_tax_rate(result)
        assert rate == 0.0
    
    def test_get_effective_tax_rate_with_negative_income(self):
        """Test effective tax rate calculation with negative income (line 221)"""
        service = TaxCalculationService(2025)
        
        # Create a tax result with negative AGI
        result = TaxResult(
            adjusted_gross_income=-5000,
            total_tax=0
        )
        
        # This should return 0.0 for negative income (line 221)
        rate = service.get_effective_tax_rate(result)
        assert rate == 0.0
    
    def test_get_marginal_tax_rate_highest_bracket(self):
        """Test marginal tax rate for income exceeding all brackets (line 272)"""
        service = TaxCalculationService(2025)
        
        # Use extremely high income to exceed all bracket thresholds
        # This should return the highest bracket rate (line 272)
        rate = service.get_marginal_tax_rate(1_000_000_000, "Single")
        
        # The highest federal tax bracket is 37%
        assert rate == 37.0


class TestFieldMapperMissingLines:
    """Cover missing lines in field_mapper.py (line 58)"""
    
    def test_dotdict_get_with_default_value(self):
        """Test DotDict.get() returning default when path not found (line 58)"""
        data = DotDict({'personal': {'name': 'John'}})
        
        # Test nested path that doesn't exist - should return default (line 58)
        result = data.get('personal.nonexistent.field', 'DEFAULT_VALUE')
        assert result == 'DEFAULT_VALUE'
    
    def test_dotdict_get_with_none_in_path(self):
        """Test DotDict.get() when None is encountered in path traversal (line 58)"""
        data = DotDict({'personal': None})
        
        # When traversing through None, should return default (line 58)
        result = data.get('personal.name', 'DEFAULT')
        assert result == 'DEFAULT'
    
    def test_dotdict_get_with_non_dict_in_path(self):
        """Test DotDict.get() when encountering non-dict value in path (line 58)"""
        data = DotDict({'personal': {'age': 25}})
        
        # Trying to traverse through a non-dict (int) should return default (line 58)
        result = data.get('personal.age.invalid', 'DEFAULT')
        assert result == 'DEFAULT'


class TestTaxDataValidatorMissingLines:
    """Cover missing lines in tax_data_validator.py (lines 64, 99, 114)"""
    
    def test_validate_field_with_invalid_format_custom_error(self):
        """Test validation error message generation (line 64)"""
        # This test ensures line 64 is hit (error message generation)
        error = TaxDataValidator.validate_field('personal_info.ssn', 'INVALID')
        assert error is not None
        assert 'ssn' in error.lower()
    
    def test_validate_data_with_invalid_values_stores_errors(self):
        """Test that validation errors are stored in errors dict (line 99)"""
        data = {
            'personal_info': {
                'ssn': '000-00-0000',  # Invalid SSN
                'email': 'not-an-email'  # Invalid email
            }
        }
        
        errors = TaxDataValidator.validate_data(data)
        
        # Both errors should be stored (line 99)
        assert 'personal_info.ssn' in errors
        assert 'personal_info.email' in errors
    
    def test_get_nested_value_with_none_returns_none(self):
        """Test _get_nested_value returns None when value is None (line 114)"""
        data = {
            'personal': {
                'name': None
            }
        }
        
        # This should traverse and find None, then return None (line 114)
        result = TaxDataValidator._get_nested_value(data, 'personal.name')
        assert result is None
    
    def test_get_nested_value_with_empty_nested_dict(self):
        """Test _get_nested_value with empty nested dictionaries"""
        data = {
            'personal': {}
        }
        
        # This should return None when key doesn't exist
        result = TaxDataValidator._get_nested_value(data, 'personal.name')
        assert result is None


class TestEdgeCasesForCompleteness:
    """Additional edge case tests to ensure robustness"""
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery from HALF_OPEN state"""
        breaker = CircuitBreaker("recovery_test", failure_threshold=1, recovery_timeout=0)
        
        # Fail once to open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait and try again - should go HALF_OPEN then CLOSED on success
        time.sleep(0.01)
        
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_tax_calculation_service_marginal_rate_all_filing_statuses(self):
        """Test marginal rate calculation for all filing statuses"""
        service = TaxCalculationService(2025)
        
        filing_statuses = [
            "Single",
            "Married Filing Jointly",
            "Married Filing Separately",
            "Head of Household"
        ]
        
        for status in filing_statuses:
            # Test high income that exceeds all brackets
            rate = service.get_marginal_tax_rate(500_000, status)
            assert rate > 0
            assert rate <= 37.0  # Max federal rate
    
    def test_dotdict_get_with_dotted_key_already_in_dict(self):
        """Test DotDict when dotted key exists directly in dict"""
        # Test the case where the path is already a key in the dict
        data = DotDict({'personal.name': 'Direct Key Value', 'personal': {'name': 'Nested Value'}})
        
        # Should return the direct key first
        result = data.get('personal.name')
        assert result == 'Direct Key Value'
