"""
Tests for utils/tax_data_validator.py
"""
import pytest
from utils.tax_data_validator import TaxDataValidator


class TestTaxDataValidator:
    """Test tax data validation logic."""
    
    def test_validate_ssn_field_valid(self):
        """Test SSN validation with valid SSN."""
        error = TaxDataValidator.validate_field('personal_info.ssn', '123-45-6789')
        assert error is None
    
    def test_validate_ssn_field_invalid(self):
        """Test SSN validation with invalid SSN."""
        error = TaxDataValidator.validate_field('personal_info.ssn', 'invalid')
        assert error is not None
        assert 'ssn' in error.lower()
    
    def test_validate_email_field_valid(self):
        """Test email validation with valid email."""
        error = TaxDataValidator.validate_field('personal_info.email', 'user@example.com')
        assert error is None
    
    def test_validate_email_field_invalid(self):
        """Test email validation with invalid email."""
        error = TaxDataValidator.validate_field('personal_info.email', 'invalid-email')
        assert error is not None
    
    def test_validate_zip_code_valid(self):
        """Test zip code validation."""
        error = TaxDataValidator.validate_field('personal_info.zip_code', '12345')
        assert error is None
    
    def test_validate_phone_valid(self):
        """Test phone validation."""
        error = TaxDataValidator.validate_field('personal_info.phone', '123-456-7890')
        assert error is None
    
    def test_validate_field_length_limit_ok(self):
        """Test field length validation within limit."""
        error = TaxDataValidator.validate_field('personal_info.first_name', 'John')
        assert error is None
    
    def test_validate_field_length_limit_exceeded(self):
        """Test field length validation exceeding limit."""
        # First name max is 50
        long_name = 'A' * 100
        error = TaxDataValidator.validate_field('personal_info.first_name', long_name)
        assert error is not None
        assert 'exceeds maximum length' in error
    
    def test_validate_field_no_validator(self):
        """Test validating field without registered validator."""
        error = TaxDataValidator.validate_field('some.random.field', 'value')
        assert error is None  # No validator, no error
    
    def test_validate_data_structure_all_valid(self):
        """Test validating complete data structure - all valid."""
        data = {
            'personal_info': {
                'ssn': '123-45-6789',
                'email': 'user@example.com',
                'zip_code': '12345',
                'phone': '123-456-7890'
            }
        }
        
        errors = TaxDataValidator.validate_data(data)
        assert len(errors) == 0
    
    def test_validate_data_structure_with_errors(self):
        """Test validating complete data structure - with errors."""
        data = {
            'personal_info': {
                'ssn': 'invalid',
                'email': 'invalid-email',
                'zip_code': '12345'
            }
        }
        
        errors = TaxDataValidator.validate_data(data)
        assert len(errors) > 0
        assert 'personal_info.ssn' in errors
        assert 'personal_info.email' in errors
    
    def test_validate_data_missing_fields(self):
        """Test validating data with missing fields."""
        data = {
            'personal_info': {
                'first_name': 'John'
                # SSN missing
            }
        }
        
        errors = TaxDataValidator.validate_data(data)
        # Missing fields shouldn't cause errors, just not validated
        assert len(errors) == 0
    
    def test_get_nested_value_simple(self):
        """Test getting nested value with simple path."""
        data = {'personal_info': {'ssn': '123-45-6789'}}
        value = TaxDataValidator._get_nested_value(data, 'personal_info.ssn')
        assert value == '123-45-6789'
    
    def test_get_nested_value_missing(self):
        """Test getting nested value that doesn't exist."""
        data = {'personal_info': {}}
        value = TaxDataValidator._get_nested_value(data, 'personal_info.ssn')
        assert value is None
    
    def test_get_nested_value_deep(self):
        """Test getting deeply nested value."""
        data = {
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        }
        value = TaxDataValidator._get_nested_value(data, 'level1.level2.level3')
        assert value == 'value'
    
    def test_validate_filing_status_valid(self):
        """Test valid filing statuses."""
        assert TaxDataValidator.validate_filing_status('Single') is None
        assert TaxDataValidator.validate_filing_status('MFJ') is None
        assert TaxDataValidator.validate_filing_status('MFS') is None
        assert TaxDataValidator.validate_filing_status('HOH') is None
        assert TaxDataValidator.validate_filing_status('QW') is None
    
    def test_validate_filing_status_invalid(self):
        """Test invalid filing status."""
        error = TaxDataValidator.validate_filing_status('INVALID')
        assert error is not None
        assert 'Invalid filing status' in error
    
    def test_validate_tax_year_valid(self):
        """Test valid tax years."""
        error = TaxDataValidator.validate_tax_year(2025)
        assert error is None
        
        error = TaxDataValidator.validate_tax_year(2024)
        assert error is None
        
        error = TaxDataValidator.validate_tax_year(2020)
        assert error is None
    
    def test_validate_tax_year_too_old(self):
        """Test tax year too old."""
        error = TaxDataValidator.validate_tax_year(2019)
        assert error is not None
        assert '2020' in error
    
    def test_validate_tax_year_future(self):
        """Test tax year in future."""
        error = TaxDataValidator.validate_tax_year(2030)
        assert error is not None
    
    def test_validate_amount_valid(self):
        """Test valid monetary amounts."""
        assert TaxDataValidator.validate_amount(100.50) is None
        assert TaxDataValidator.validate_amount(0) is None
        assert TaxDataValidator.validate_amount('123.45') is None
    
    def test_validate_amount_negative(self):
        """Test negative amount."""
        error = TaxDataValidator.validate_amount(-100)
        assert error is not None
        assert 'cannot be negative' in error
    
    def test_validate_amount_invalid(self):
        """Test invalid amount."""
        error = TaxDataValidator.validate_amount('abc')
        assert error is not None
        assert 'valid number' in error
    
    def test_validate_amount_custom_field_name(self):
        """Test amount validation with custom field name."""
        error = TaxDataValidator.validate_amount(-100, 'salary')
        assert error is not None
        assert 'salary' in error
    
    def test_spouse_ssn_validation(self):
        """Test spouse SSN validation."""
        data = {
            'spouse_info': {
                'ssn': 'invalid-ssn'
            }
        }
        
        errors = TaxDataValidator.validate_data(data)
        assert 'spouse_info.ssn' in errors
    
    def test_multiple_length_violations(self):
        """Test multiple fields exceeding length limits."""
        long_text = 'A' * 200
        data = {
            'personal_info': {
                'first_name': long_text,
                'last_name': long_text,
                'address': long_text
            }
        }
        
        error1 = TaxDataValidator.validate_field('personal_info.first_name', long_text)
        error2 = TaxDataValidator.validate_field('personal_info.last_name', long_text)
        error3 = TaxDataValidator.validate_field('personal_info.address', long_text)
        
        assert all([error1, error2, error3])
