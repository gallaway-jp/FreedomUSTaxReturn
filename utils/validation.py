"""
Input validation utilities
"""

import re
from datetime import datetime

def validate_ssn(ssn):
    """Validate Social Security Number format"""
    # Remove any hyphens or spaces
    ssn_clean = ssn.replace('-', '').replace(' ', '')
    
    # Check if it's 9 digits
    if not re.match(r'^\d{9}$', ssn_clean):
        return False, "SSN must be 9 digits (XXX-XX-XXXX)"
    
    # Check for invalid patterns
    if ssn_clean[0:3] == '000' or ssn_clean[0:3] == '666':
        return False, "Invalid SSN"
    
    # Note: We no longer reject 9XX as those are valid ITINs
    
    if ssn_clean[3:5] == '00':
        return False, "Invalid SSN"
    
    if ssn_clean[5:9] == '0000':
        return False, "Invalid SSN"
    
    return True, ssn_clean

def validate_date(date_str, format="%m/%d/%Y"):
    """Validate date format"""
    try:
        date_obj = datetime.strptime(date_str, format)
        return True, date_obj
    except ValueError:
        return False, None

def validate_zip_code(zip_code):
    """Validate ZIP code format"""
    # Support both 5-digit and 9-digit ZIP codes
    if re.match(r'^\d{5}(-\d{4})?$', zip_code):
        return True, zip_code
    return False, "ZIP code must be 5 digits or 9 digits (XXXXX-XXXX)"

def validate_phone(phone):
    """Validate phone number format"""
    # Remove all non-digit characters
    phone_clean = re.sub(r'\D', '', phone)
    
    if len(phone_clean) == 10:
        return True, phone_clean
    elif len(phone_clean) == 11 and phone_clean[0] == '1':
        return True, phone_clean
    else:
        return False, "Phone number must be 10 digits"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, email
    return False, "Invalid email format"

def validate_currency(amount_str):
    """Validate and parse currency amount"""
    try:
        # Remove $ and commas
        clean_amount = amount_str.replace('$', '').replace(',', '').strip()
        amount = float(clean_amount)
        
        if amount < 0:
            return False, "Amount cannot be negative"
        
        return True, amount
    except ValueError:
        return False, "Invalid amount"

def validate_ein(ein):
    """Validate Employer Identification Number"""
    # Remove any hyphens
    ein_clean = ein.replace('-', '')
    
    if not re.match(r'^\d{9}$', ein_clean):
        return False, "EIN must be 9 digits (XX-XXXXXXX)"
    
    # Check for all zeros
    if ein_clean == '000000000':
        return False, "Invalid EIN"
    
    return True, ein_clean
