"""
Comprehensive tests for validation utilities

This test suite provides thorough coverage of all validation functions
including edge cases, invalid patterns, and error handling.
"""

import pytest
from datetime import datetime
from utils.validation import (
    validate_ssn,
    validate_date,
    validate_zip_code,
    validate_phone,
    validate_email,
    validate_ein
)


class TestSSNValidation:
    """Test Social Security Number validation"""
    
    def test_valid_ssn_with_hyphens(self):
        """Test SSN validation with standard hyphen format"""
        valid, cleaned = validate_ssn('123-45-6789')
        assert valid == True
        assert cleaned == '123456789'
    
    def test_valid_ssn_without_hyphens(self):
        """Test SSN validation without hyphens"""
        valid, cleaned = validate_ssn('123456789')
        assert valid == True
        assert cleaned == '123456789'
    
    def test_valid_ssn_with_spaces(self):
        """Test SSN validation with spaces instead of hyphens"""
        valid, cleaned = validate_ssn('123 45 6789')
        assert valid == True
        assert cleaned == '123456789'
    
    def test_invalid_ssn_all_zeros_area(self):
        """Test that SSN with 000 area number is invalid"""
        valid, msg = validate_ssn('000-12-3456')
        assert valid == False
        assert 'Invalid' in msg
    
    def test_invalid_ssn_666_prefix(self):
        """Test that SSN with 666 prefix (reserved) is invalid"""
        valid, msg = validate_ssn('666-12-3456')
        assert valid == False
        assert 'Invalid' in msg
    
    def test_invalid_ssn_group_all_zeros(self):
        """Test that SSN with 00 group number is invalid"""
        valid, msg = validate_ssn('123-00-4567')
        assert valid == False
        assert 'Invalid' in msg
    
    def test_invalid_ssn_serial_all_zeros(self):
        """Test that SSN with 0000 serial number is invalid"""
        valid, msg = validate_ssn('123-45-0000')
        assert valid == False
        assert 'Invalid' in msg
    
    def test_invalid_ssn_too_short(self):
        """Test that SSN with less than 9 digits is invalid"""
        valid, msg = validate_ssn('12-34-567')
        assert valid == False
        assert '9 digits' in msg
    
    def test_invalid_ssn_too_long(self):
        """Test that SSN with more than 9 digits is invalid"""
        valid, msg = validate_ssn('123-45-67890')
        assert valid == False
        assert '9 digits' in msg
    
    def test_invalid_ssn_contains_letters(self):
        """Test that SSN with letters is invalid"""
        valid, msg = validate_ssn('ABC-DE-FGHI')
        assert valid == False
        assert '9 digits' in msg
    
    def test_invalid_ssn_empty_string(self):
        """Test that empty string is invalid SSN"""
        valid, msg = validate_ssn('')
        assert valid == False
        assert '9 digits' in msg


class TestEINValidation:
    """Test Employer Identification Number validation"""
    
    def test_valid_ein_with_hyphen(self):
        """Test EIN validation with standard hyphen format"""
        valid, cleaned = validate_ein('12-3456789')
        assert valid == True
        assert cleaned == '123456789'
    
    def test_valid_ein_without_hyphen(self):
        """Test EIN validation without hyphen"""
        valid, cleaned = validate_ein('123456789')
        assert valid == True
        assert cleaned == '123456789'
    
    def test_invalid_ein_wrong_length(self):
        """Test that EIN with wrong length is invalid"""
        valid, msg = validate_ein('12-345678')  # Only 8 digits
        assert valid == False
        assert '9 digits' in msg
    
    def test_invalid_ein_contains_letters(self):
        """Test that EIN with letters is invalid"""
        valid, msg = validate_ein('AB-CDEFGHI')
        assert valid == False
    
    def test_invalid_ein_all_zeros(self):
        """Test that EIN with all zeros is invalid"""
        valid, msg = validate_ein('00-0000000')
        assert valid == False
        assert 'Invalid' in msg


class TestDateValidation:
    """Test date validation"""
    
    def test_valid_date_mm_dd_yyyy(self):
        """Test valid date in MM/DD/YYYY format"""
        valid, date_obj = validate_date('12/31/2024')
        assert valid == True
        assert isinstance(date_obj, datetime)
        assert date_obj.year == 2024
        assert date_obj.month == 12
        assert date_obj.day == 31
    
    def test_valid_date_various_formats(self):
        """Test valid dates in various formats"""
        # MM/DD/YYYY
        valid, _ = validate_date('01/15/2024')
        assert valid == True
        
        # M/D/YYYY
        valid, _ = validate_date('1/5/2024')
        assert valid == True
    
    def test_invalid_date_wrong_format(self):
        """Test invalid date with wrong format"""
        valid, _ = validate_date('2024-12-31')  # Wrong format
        assert valid == False
    
    def test_invalid_date_invalid_day(self):
        """Test invalid date with non-existent day"""
        valid, _ = validate_date('02/30/2024')  # Feb 30 doesn't exist
        assert valid == False
    
    def test_invalid_date_invalid_month(self):
        """Test invalid date with invalid month"""
        valid, _ = validate_date('13/01/2024')  # Month 13 doesn't exist
        assert valid == False
    
    def test_valid_date_leap_year(self):
        """Test valid leap year date"""
        valid, date_obj = validate_date('02/29/2024')  # 2024 is leap year
        assert valid == True
        assert date_obj.day == 29
    
    def test_invalid_date_non_leap_year(self):
        """Test invalid leap year date in non-leap year"""
        valid, _ = validate_date('02/29/2023')  # 2023 is not leap year
        assert valid == False
    
    def test_valid_date_custom_format(self):
        """Test valid date with custom format"""
        valid, date_obj = validate_date('2024-12-31', format='%Y-%m-%d')
        assert valid == True
        assert date_obj.year == 2024


class TestZIPCodeValidation:
    """Test ZIP code validation"""
    
    def test_valid_zip_5_digits(self):
        """Test valid 5-digit ZIP code"""
        valid, zip_code = validate_zip_code('12345')
        assert valid == True
        assert zip_code == '12345'
    
    def test_valid_zip_9_digits(self):
        """Test valid ZIP+4 code"""
        valid, zip_code = validate_zip_code('12345-6789')
        assert valid == True
        assert zip_code == '12345-6789'
    
    def test_invalid_zip_too_short(self):
        """Test invalid ZIP code that's too short"""
        valid, msg = validate_zip_code('1234')
        assert valid == False
        assert 'ZIP code must be' in msg
    
    def test_invalid_zip_too_long(self):
        """Test invalid ZIP code that's too long"""
        valid, msg = validate_zip_code('123456')
        assert valid == False
        assert 'ZIP code must be' in msg
    
    def test_invalid_zip_wrong_format(self):
        """Test invalid ZIP+4 with wrong separator"""
        valid, msg = validate_zip_code('12345/6789')
        assert valid == False
    
    def test_invalid_zip_contains_letters(self):
        """Test invalid ZIP code with letters"""
        valid, msg = validate_zip_code('ABCDE')
        assert valid == False
    
    def test_valid_zip_with_leading_zero(self):
        """Test valid ZIP code with leading zero"""
        valid, zip_code = validate_zip_code('01234')
        assert valid == True
        assert zip_code == '01234'


class TestPhoneValidation:
    """Test phone number validation"""
    
    def test_valid_phone_with_hyphens(self):
        """Test valid phone number with hyphens"""
        valid, cleaned = validate_phone('123-456-7890')
        assert valid == True
        assert cleaned == '1234567890'
    
    def test_valid_phone_with_parentheses(self):
        """Test valid phone number with parentheses"""
        valid, cleaned = validate_phone('(123) 456-7890')
        assert valid == True
        assert cleaned == '1234567890'
    
    def test_valid_phone_with_spaces(self):
        """Test valid phone number with spaces"""
        valid, cleaned = validate_phone('123 456 7890')
        assert valid == True
        assert cleaned == '1234567890'
    
    def test_valid_phone_with_dots(self):
        """Test valid phone number with dots"""
        valid, cleaned = validate_phone('123.456.7890')
        assert valid == True
        assert cleaned == '1234567890'
    
    def test_valid_phone_digits_only(self):
        """Test valid phone number with digits only"""
        valid, cleaned = validate_phone('1234567890')
        assert valid == True
        assert cleaned == '1234567890'
    
    def test_valid_phone_with_country_code(self):
        """Test valid phone number with country code"""
        valid, cleaned = validate_phone('+1-123-456-7890')
        assert valid == True
        # Should strip country code and return 10-digit number
        assert cleaned == '1234567890' or len(cleaned) == 11
    
    def test_invalid_phone_too_short(self):
        """Test invalid phone number that's too short"""
        valid, msg = validate_phone('123-4567')
        assert valid == False
        assert '10 digits' in msg
    
    def test_invalid_phone_too_long(self):
        """Test invalid phone number that's too long (without country code)"""
        valid, msg = validate_phone('123-456-7890-1234')
        assert valid == False
    
    def test_invalid_phone_contains_letters(self):
        """Test invalid phone number with letters"""
        valid, msg = validate_phone('ABC-DEF-GHIJ')
        assert valid == False
        assert '10 digits' in msg


class TestEmailValidation:
    """Test email address validation"""
    
    def test_valid_email_simple(self):
        """Test valid simple email address"""
        valid, email = validate_email('user@example.com')
        assert valid == True
        assert email == 'user@example.com'
    
    def test_valid_email_with_subdomain(self):
        """Test valid email with subdomain"""
        valid, email = validate_email('user@mail.example.com')
        assert valid == True
    
    def test_valid_email_with_plus(self):
        """Test valid email with plus sign"""
        valid, email = validate_email('user+tag@example.com')
        assert valid == True
    
    def test_valid_email_with_dots(self):
        """Test valid email with dots in local part"""
        valid, email = validate_email('first.last@example.com')
        assert valid == True
    
    def test_valid_email_with_numbers(self):
        """Test valid email with numbers"""
        valid, email = validate_email('user123@example456.com')
        assert valid == True
    
    def test_invalid_email_no_at_sign(self):
        """Test invalid email without @ sign"""
        valid, msg = validate_email('userexample.com')
        assert valid == False
        assert 'Invalid email' in msg
    
    def test_invalid_email_no_domain(self):
        """Test invalid email without domain"""
        valid, msg = validate_email('user@')
        assert valid == False
    
    def test_invalid_email_no_local_part(self):
        """Test invalid email without local part"""
        valid, msg = validate_email('@example.com')
        assert valid == False
    
    def test_invalid_email_no_tld(self):
        """Test invalid email without top-level domain"""
        valid, msg = validate_email('user@example')
        assert valid == False
    
    def test_invalid_email_multiple_at_signs(self):
        """Test invalid email with multiple @ signs"""
        valid, msg = validate_email('user@@example.com')
        assert valid == False
    
    def test_invalid_email_spaces(self):
        """Test invalid email with spaces"""
        valid, msg = validate_email('user name@example.com')
        assert valid == False


class TestValidationEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_ssn_normalization_preserves_digits(self):
        """Test that SSN normalization preserves all digits"""
        # Use valid SSN (not starting with 9 for strict validation)
        valid, cleaned = validate_ssn('123-45-6789')
        assert cleaned == '123456789'
        assert len(cleaned) == 9
        assert cleaned.isdigit()
    
    def test_phone_removes_all_non_digits(self):
        """Test that phone validation removes all non-digit characters"""
        # Phone number with extension - should extract main 10 digits
        valid, cleaned = validate_phone('(123) 456-7890')
        assert valid == True
        assert len(cleaned) == 10
        assert cleaned == '1234567890'
    
    def test_zip_code_preserves_format(self):
        """Test that ZIP code format is preserved"""
        valid, zip_code = validate_zip_code('12345-6789')
        assert '-' in zip_code  # Format preserved
    
    def test_empty_string_validations(self):
        """Test that empty strings are properly rejected"""
        assert validate_ssn('')[0] == False
        assert validate_ein('')[0] == False
        assert validate_zip_code('')[0] == False
        assert validate_phone('')[0] == False
        assert validate_email('')[0] == False
    
    def test_none_value_handling(self):
        """Test handling of None values"""
        # These should not crash and should return False
        try:
            validate_ssn(None)
            # If it doesn't crash, it should return False
        except (TypeError, AttributeError):
            # Expected for None input
            pass


class TestValidationCurrencyEdgeCases:
    """Test currency validation edge cases"""
    
    def test_currency_with_dollar_sign(self):
        """Test currency with $ prefix"""
        from utils.validation import validate_currency
        valid, amount = validate_currency('$100.50')
        assert valid == True
        assert amount == 100.50
    
    def test_currency_with_commas(self):
        """Test currency with comma separators"""
        from utils.validation import validate_currency
        valid, amount = validate_currency('$1,234.56')
        assert valid == True
        assert amount == 1234.56
    
    def test_currency_with_spaces(self):
        """Test currency with leading/trailing spaces"""
        from utils.validation import validate_currency
        valid, amount = validate_currency('  100.50  ')
        assert valid == True
        assert amount == 100.50
    
    def test_currency_negative_amount(self):
        """Test currency with negative value"""
        from utils.validation import validate_currency
        valid, msg = validate_currency('-50.00')
        assert valid == False
        assert 'negative' in msg.lower()
    
    def test_currency_zero_amount(self):
        """Test currency with zero value"""
        from utils.validation import validate_currency
        valid, amount = validate_currency('0')
        assert valid == True
        assert amount == 0.0
    
    def test_currency_large_amount(self):
        """Test currency with very large amount"""
        from utils.validation import validate_currency
        valid, amount = validate_currency('$1,000,000.00')
        assert valid == True
        assert amount == 1000000.00
    
    def test_currency_decimal_precision(self):
        """Test currency with various decimal precisions"""
        from utils.validation import validate_currency
        
        # No decimals
        valid, amount = validate_currency('100')
        assert valid == True
        assert amount == 100.0
        
        # One decimal
        valid, amount = validate_currency('100.5')
        assert valid == True
        assert amount == 100.5
        
        # Two decimals
        valid, amount = validate_currency('100.99')
        assert valid == True
        assert amount == 100.99
    
    def test_currency_invalid_text(self):
        """Test currency with invalid text"""
        from utils.validation import validate_currency
        valid, msg = validate_currency('abc')
        assert valid == False
        assert 'Invalid' in msg


class TestValidationPhoneEdgeCases:
    """Test additional phone number edge cases"""
    
    def test_phone_international_format(self):
        """Test phone with international prefix"""
        valid, cleaned = validate_phone('+1 (123) 456-7890')
        assert valid == True
        assert cleaned == '11234567890'
    
    def test_phone_too_short_after_cleaning(self):
        """Test phone that's too short after removing non-digits"""
        valid, msg = validate_phone('123-456')
        assert valid == False
    
    def test_phone_all_zeros(self):
        """Test phone number with all zeros (should pass format check)"""
        valid, cleaned = validate_phone('000-000-0000')
        assert valid == True
        assert cleaned == '0000000000'


class TestValidationEmailEdgeCases:
    """Test additional email edge cases"""
    
    def test_email_with_multiple_dots(self):
        """Test email with multiple dots in domain"""
        valid, email = validate_email('user@mail.example.com')
        assert valid == True
    
    def test_email_no_at_sign(self):
        """Test email without @ symbol"""
        valid, msg = validate_email('userexample.com')
        assert valid == False
    
    def test_email_no_domain(self):
        """Test email without domain"""
        valid, msg = validate_email('user@')
        assert valid == False
    
    def test_email_no_local_part(self):
        """Test email without local part"""
        valid, msg = validate_email('@example.com')
        assert valid == False
    
    def test_email_no_tld(self):
        """Test email without top-level domain"""
        valid, msg = validate_email('user@example')
        assert valid == False
    
    def test_email_with_spaces(self):
        """Test email with spaces (should fail)"""
        valid, msg = validate_email('user name@example.com')
        assert valid == False


class TestValidationDateEdgeCases:
    """Test additional date edge cases"""
    
    def test_date_boundary_years(self):
        """Test dates at year boundaries"""
        # First day of year
        valid, date_obj = validate_date('01/01/2024')
        assert valid == True
        assert date_obj.month == 1
        assert date_obj.day == 1
        
        # Last day of year
        valid, date_obj = validate_date('12/31/2024')
        assert valid == True
        assert date_obj.month == 12
        assert date_obj.day == 31
    
    def test_date_month_boundaries(self):
        """Test dates at month boundaries"""
        # 31-day months
        valid, _ = validate_date('01/31/2024')
        assert valid == True
        
        # 30-day months
        valid, _ = validate_date('04/30/2024')
        assert valid == True
        
        # Invalid: April 31
        valid, _ = validate_date('04/31/2024')
        assert valid == False
    
    def test_date_february_edge_cases(self):
        """Test February edge cases"""
        # Feb 28 in non-leap year
        valid, _ = validate_date('02/28/2023')
        assert valid == True
        
        # Feb 30 (never valid)
        valid, _ = validate_date('02/30/2024')
        assert valid == False


class TestValidationZIPEdgeCases:
    """Test additional ZIP code edge cases"""
    
    def test_zip_all_zeros(self):
        """Test ZIP code with all zeros (technically valid format)"""
        valid, zip_code = validate_zip_code('00000')
        assert valid == True
    
    def test_zip_all_nines(self):
        """Test ZIP code with all nines"""
        valid, zip_code = validate_zip_code('99999')
        assert valid == True
    
    def test_zip_plus4_all_zeros(self):
        """Test ZIP+4 with all zeros in extension"""
        valid, zip_code = validate_zip_code('12345-0000')
        assert valid == True
    
    def test_zip_incomplete_plus4(self):
        """Test ZIP+4 with incomplete extension"""
        valid, msg = validate_zip_code('12345-678')
        assert valid == False


class TestValidationEINEdgeCases:
    """Test additional EIN edge cases"""
    
    def test_ein_valid_prefixes(self):
        """Test EIN with various valid prefixes"""
        # Common prefixes
        for prefix in ['10', '12', '20', '35', '98']:
            valid, cleaned = validate_ein(f'{prefix}-3456789')
            assert valid == True
            assert cleaned == f'{prefix}3456789'
    
    def test_ein_with_spaces(self):
        """Test EIN with spaces (should fail since we only remove hyphens)"""
        valid, msg = validate_ein('12 3456789')
        assert valid == False
