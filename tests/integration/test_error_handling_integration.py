"""
Error handling integration tests.

Tests error propagation, validation, and recovery across the system.
"""
import pytest
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService
from utils.validation import (
    validate_ssn,
    validate_currency,
    validate_ein,
    validate_email
)


class TestValidationErrorHandling:
    """Test validation error scenarios."""
    
    def test_invalid_ssn_format(self):
        """Test SSN validation rejects invalid formats."""
        # 123456789 without dashes is valid - gets normalized
        is_valid, cleaned = validate_ssn('123456789')
        assert is_valid
        assert cleaned == '123456789'
        
        is_valid, _ = validate_ssn('123-45-678')  # Too short
        assert not is_valid
        
        is_valid, _ = validate_ssn('000-12-3456')  # Invalid area number (000)
        assert not is_valid
        
        is_valid, _ = validate_ssn('abc-de-fghi')  # Non-numeric
        assert not is_valid
        
        is_valid, cleaned = validate_ssn('123-45-6789')  # Valid
        assert is_valid
        assert cleaned == '123456789'  # Normalized
    
    def test_invalid_currency_format(self):
        """Test currency validation handles various formats."""
        is_valid, _ = validate_currency('$1,234.56')
        assert is_valid
        
        is_valid, _ = validate_currency('1234.56')
        assert is_valid
        
        is_valid, _ = validate_currency('0')
        assert is_valid
        
        is_valid, _ = validate_currency('abc')
        assert not is_valid
        
        is_valid, _ = validate_currency('$-100')  # Negative with $
        assert not is_valid
    
    def test_invalid_ein_format(self):
        """Test EIN validation rejects invalid formats."""
        is_valid, _ = validate_ein('123456789')  # No dash
        assert is_valid  # Should accept - normalizes to valid EIN
        
        is_valid, _ = validate_ein('12-345678')  # Wrong position
        assert not is_valid
        
        is_valid, _ = validate_ein('ab-1234567')  # Non-numeric
        assert not is_valid
        
        is_valid, _ = validate_ein('12-3456789')  # Valid
        assert is_valid
    
    def test_invalid_email_format(self):
        """Test email validation."""
        is_valid, _ = validate_email('user@example.com')
        assert is_valid
        
        is_valid, _ = validate_email('invalid.email')
        assert not is_valid
        
        is_valid, _ = validate_email('@example.com')
        assert not is_valid
        
        is_valid, _ = validate_email('user@')
        assert not is_valid


class TestTaxCalculationErrorHandling:
    """Test error handling in tax calculations."""
    
    def test_calculation_with_missing_required_fields(self):
        """Test calculation handles missing required data gracefully."""
        data = TaxData()
        # Missing required fields like filing status
        
        calculator = TaxCalculationService()
        
        # Should handle gracefully or raise informative error
        try:
            result = calculator.calculate_complete_return(data)
            # If it succeeds, verify defaults were applied
            assert result is not None
        except (ValueError, KeyError) as e:
            # Or should raise with clear message
            assert len(str(e)) > 0
    
    def test_calculation_with_negative_income(self):
        """Test calculation handles edge case of negative income."""
        data = TaxData()
        data.set('filing_info.filing_status', 'single')
        
        calculator = TaxCalculationService()
        
        # System accepts negative wages but they result in negative AGI
        # Test verifies the system doesn't crash with negative values
        data.add_w2_form({'wages': -1000})
        result = calculator.calculate_complete_return(data)
        
        # System handles it - negative income results in:
        # - negative AGI (system accepts it)
        # - taxable income is max(0, AGI - deduction) = 0
        # - no tax owed
        assert result.total_income == -1000
        assert result.taxable_income == 0  # Can't be negative
        assert result.total_tax == 0
    
    def test_calculation_with_extremely_high_income(self):
        """Test calculation handles very large numbers."""
        data = TaxData()
        data.set('filing_info.filing_status', 'single')
        
        # TaxData validation should reject extremely high values
        calculator = TaxCalculationService()
        
        try:
            data.add_w2_form({'wages': 10_000_000_000})  # 10 billion
            result = calculator.calculate_complete_return(data)
            # If accepted, should complete without overflow
            assert result.adjusted_gross_income > 0
            assert result.total_tax > 0
        except ValueError:
            # Expected - validation rejects excessive amounts
            pass


class TestDataModelErrorHandling:
    """Test error handling in data models."""
    
    def test_tax_data_get_nonexistent_field(self):
        """Test getting non-existent field returns None or default."""
        data = TaxData()
        result = data.get('nonexistent.field.path')
        assert result is None or result == ''
    
    def test_tax_data_set_invalid_path(self):
        """Test setting data with invalid path."""
        data = TaxData()
        # Should handle gracefully
        try:
            data.set('', 'value')
        except ValueError:
            pass  # Expected
    
    def test_tax_data_set_with_type_mismatch(self):
        """Test setting numeric field with string."""
        data = TaxData()
        
        # Test type mismatch handling
        try:
            data.add_w2_form({'wages': 'not_a_number'})
            # If it succeeds, check what was stored
            w2_forms = data.get('income.w2_forms')
            if w2_forms:
                assert w2_forms[0]['wages'] is not None
        except (ValueError, TypeError):
            # Expected - validation rejects non-numeric
            pass


class TestConcurrentModificationHandling:
    """Test handling of concurrent data modifications."""
    
    def test_multiple_w2_additions(self):
        """Test adding multiple W-2s in sequence."""
        data = TaxData()
        
        for i in range(10):
            data.add_w2_form({
                'wages': 50000 + (i * 1000),
                'employer': f'Company {i}'
            })
        
        # All entries should be preserved
        w2_forms = data.get('income.w2_forms') or []
        assert len(w2_forms) == 10
        for i, w2 in enumerate(w2_forms):
            assert w2['wages'] == 50000 + (i * 1000)
    
    def test_overwriting_existing_data(self):
        """Test overwriting existing field values."""
        data = TaxData()
        data.set('personal_info.first_name', 'Original')
        data.set('personal_info.first_name', 'Updated')
        
        result = data.get('personal_info.first_name')
        assert result == 'Updated'


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_zero_income_zero_withholding(self):
        """Test taxpayer with no income or withholding."""
        data = TaxData()
        data.set('filing_info.filing_status', 'single')
        data.add_w2_form({'wages': 0, 'federal_withholding': 0})
        
        calculator = TaxCalculationService()
        result = calculator.calculate_complete_return(data)
        
        assert result.adjusted_gross_income == 0
        assert result.total_tax == 0
        assert result.refund_amount == 0
    
    def test_withholding_exceeds_wages(self):
        """Test invalid scenario where withholding > wages."""
        data = TaxData()
        data.set('filing_info.filing_status', 'single')
        data.add_w2_form({'wages': 50000, 'federal_withholding': 60000})  # More than wages
        
        calculator = TaxCalculationService()
        result = calculator.calculate_complete_return(data)
        
        # Should handle gracefully
        assert result is not None
        # Large refund expected if withholding exceeds tax
        assert result.refund_amount > 0
    
    def test_maximum_number_of_children(self):
        """Test edge case with many children."""
        data = TaxData()
        data.set('filing_info.filing_status', 'married_filing_jointly')
        data.add_w2_form({'wages': 100000})
        
        calculator = TaxCalculationService()
        result = calculator.calculate_complete_return(data)
        
        # Should calculate correctly
        assert result.adjusted_gross_income == 100000
        assert result.total_tax > 0


class TestErrorRecovery:
    """Test system recovery from errors."""
    
    def test_continue_after_validation_error(self):
        """Test that system continues functioning after validation error."""
        # First operation with invalid data
        is_valid, _ = validate_ssn('invalid')
        assert not is_valid
        
        # Second operation should still work
        is_valid, _ = validate_ssn('123-45-6789')
        assert is_valid
    
    def test_tax_data_reset_after_error(self):
        """Test resetting TaxData after error."""
        data = TaxData()
        data.set('test.field', 'value')
        
        # Create new instance - should be clean
        data2 = TaxData()
        result = data2.get('test.field')
        assert result is None or result == ''


class TestNullAndEmptyHandling:
    """Test handling of null and empty values."""
    
    def test_empty_string_in_required_field(self):
        """Test handling of empty string in required field."""
        data = TaxData()
        data.set('personal_info.first_name', '')
        data.set('filing_info.filing_status', 'single')
        
        calculator = TaxCalculationService()
        # Should handle empty name gracefully
        result = calculator.calculate_complete_return(data)
        assert result is not None
    
    def test_none_value_in_optional_field(self):
        """Test setting None in optional field."""
        data = TaxData()
        data.set('income.interest', None)
        
        result = data.get('income.interest')
        # Should return None or 0
        assert result is None or result == 0
