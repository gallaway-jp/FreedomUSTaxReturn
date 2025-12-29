"""
Tax data validation logic

This module extracts validation logic from the TaxData class
to improve maintainability and single responsibility principle.
"""

from typing import Dict, Callable, Any, Optional
from utils.validation import (
    validate_ssn,
    validate_email,
    validate_zip_code,
    validate_phone,
)


class TaxDataValidator:
    """
    Validates tax data fields and enforces business rules.
    
    Separates validation logic from data storage for better maintainability.
    """
    
    # Field validators mapping
    VALIDATORS: Dict[str, Callable] = {
        'personal_info.ssn': validate_ssn,
        'spouse_info.ssn': validate_ssn,
        'personal_info.email': validate_email,
        'personal_info.zip_code': validate_zip_code,
        'personal_info.phone': validate_phone,
    }
    
    # Input length limits for text fields
    MAX_LENGTHS: Dict[str, int] = {
        'first_name': 50,
        'last_name': 50,
        'address': 100,
        'city': 50,
        'email': 100,
        'occupation': 50,
    }
    
    @classmethod
    def validate_field(cls, field_path: str, value: Any) -> Optional[str]:
        """
        Validate a single field value.
        
        Args:
            field_path: Dot-notation path to field (e.g., 'personal_info.ssn')
            value: Value to validate
            
        Returns:
            Error message if validation fails, None if valid
            
        Example:
            >>> TaxDataValidator.validate_field('personal_info.ssn', '123-45-6789')
            None  # Valid
            >>> TaxDataValidator.validate_field('personal_info.ssn', 'invalid')
            'Invalid SSN format'
        """
        if field_path in cls.VALIDATORS:
            validator = cls.VALIDATORS[field_path]
            result = validator(value)
            # Validators return (is_valid, value_or_error) tuple
            if isinstance(result, tuple):
                is_valid, error_msg = result
                if not is_valid:
                    return f"Invalid {field_path.split('.')[-1]} format"
            elif not result:  # Fallback for boolean return
                return f"Invalid {field_path.split('.')[-1]} format"
        
        # Check length limits for text fields
        field_name = field_path.split('.')[-1]
        if field_name in cls.MAX_LENGTHS and isinstance(value, str):
            max_length = cls.MAX_LENGTHS[field_name]
            if len(value) > max_length:
                return f"{field_name} exceeds maximum length of {max_length}"
        
        return None
    
    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate entire tax data structure.
        
        Args:
            data: Complete tax data dictionary
            
        Returns:
            Dictionary of {field_path: error_message} for failed validations
            
        Example:
            >>> errors = TaxDataValidator.validate_data(tax_data)
            >>> if errors:
            ...     print(f"Validation errors: {errors}")
        """
        errors = {}
        
        # Validate all registered fields
        for field_path in cls.VALIDATORS.keys():
            value = cls._get_nested_value(data, field_path)
            if value:  # Only validate if value exists
                error = cls.validate_field(field_path, value)
                if error:
                    errors[field_path] = error
        
        return errors
    
    @staticmethod
    def _get_nested_value(data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None
        return value
    
    @classmethod
    def validate_filing_status(cls, filing_status: str) -> Optional[str]:
        """
        Validate filing status.
        
        Args:
            filing_status: Filing status code
            
        Returns:
            Error message if invalid, None if valid
        """
        valid_statuses = {'Single', 'MFJ', 'MFS', 'HOH', 'QW'}
        if filing_status not in valid_statuses:
            return f"Invalid filing status. Must be one of: {', '.join(valid_statuses)}"
        return None
    
    @classmethod
    def validate_tax_year(cls, tax_year: int) -> Optional[str]:
        """
        Validate tax year.
        
        Args:
            tax_year: Tax year (e.g., 2025)
            
        Returns:
            Error message if invalid, None if valid
        """
        from datetime import datetime
        current_year = datetime.now().year
        
        if tax_year < 2020 or tax_year > current_year:
            return f"Tax year must be between 2020 and {current_year}"
        return None
    
    @classmethod
    def validate_amount(cls, amount: Any, field_name: str = "amount") -> Optional[str]:
        """
        Validate monetary amount.
        
        Args:
            amount: Amount to validate
            field_name: Name of field for error message
            
        Returns:
            Error message if invalid, None if valid
        """
        try:
            amount_float = float(amount)
            if amount_float < 0:
                return f"{field_name} cannot be negative"
            return None
        except (ValueError, TypeError):
            return f"{field_name} must be a valid number"
