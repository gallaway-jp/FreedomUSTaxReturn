"""
Sample tax return data for testing
"""


def get_simple_single_return():
    """Simple single filer with W-2 income only"""
    return {
        'personal_info': {
            'first_name': 'John',
            'middle_initial': 'Q',
            'last_name': 'Taxpayer',
            'ssn': '123-45-6789',
            'address': '123 Main Street',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '90210',
            'phone': '555-1234',
            'email': 'john@example.com',
            'occupation': 'Software Engineer',
        },
        'filing_status': {
            'status': 'Single'
        },
        'income': {
            'w2_forms': [
                {
                    'employer_name': 'ABC Corporation',
                    'employer_ein': '12-3456789',
                    'wages': 75000.00,
                    'federal_withholding': 8500.00,
                    'social_security_wages': 75000.00,
                    'social_security_withholding': 4650.00,
                    'medicare_wages': 75000.00,
                    'medicare_withholding': 1087.50,
                }
            ]
        },
        'deductions': {
            'method': 'standard'
        },
        'metadata': {
            'tax_year': 2024
        }
    }


def get_married_filing_jointly_return():
    """Married filing jointly with two W-2s"""
    return {
        'personal_info': {
            'first_name': 'John',
            'middle_initial': 'Q',
            'last_name': 'Taxpayer',
            'ssn': '123-45-6789',
            'address': '456 Oak Avenue',
            'city': 'Springfield',
            'state': 'IL',
            'zip_code': '62701',
        },
        'spouse_info': {
            'first_name': 'Jane',
            'middle_initial': 'A',
            'last_name': 'Taxpayer',
            'ssn': '987-65-4321',
            'occupation': 'Teacher',
        },
        'filing_status': {
            'status': 'Married Filing Jointly'
        },
        'income': {
            'w2_forms': [
                {
                    'employer_name': 'ABC Corporation',
                    'wages': 75000.00,
                    'federal_withholding': 8500.00,
                },
                {
                    'employer_name': 'School District',
                    'wages': 55000.00,
                    'federal_withholding': 6000.00,
                }
            ]
        },
        'deductions': {
            'method': 'standard'
        },
        'metadata': {
            'tax_year': 2024
        }
    }


def get_return_with_dependents():
    """Tax return with dependents"""
    return {
        'personal_info': {
            'first_name': 'John',
            'last_name': 'Parent',
            'ssn': '111-22-3333',
            'address': '789 Family Lane',
            'city': 'Hometown',
            'state': 'TX',
            'zip_code': '75001',
        },
        'spouse_info': {
            'first_name': 'Jane',
            'last_name': 'Parent',
            'ssn': '444-55-6666',
        },
        'filing_status': {
            'status': 'Married Filing Jointly'
        },
        'dependents': {
            'list': [
                {
                    'first_name': 'Child',
                    'last_name': 'Parent',
                    'ssn': '777-88-9999',
                    'relationship': 'Son',
                    'months_lived_in_home': 12,
                },
                {
                    'first_name': 'Daughter',
                    'last_name': 'Parent',
                    'ssn': '888-99-0000',
                    'relationship': 'Daughter',
                    'months_lived_in_home': 12,
                }
            ]
        },
        'income': {
            'w2_forms': [
                {
                    'employer_name': 'Employer Inc',
                    'wages': 95000.00,
                    'federal_withholding': 12000.00,
                }
            ]
        },
        'deductions': {
            'method': 'standard'
        },
        'metadata': {
            'tax_year': 2024
        }
    }
