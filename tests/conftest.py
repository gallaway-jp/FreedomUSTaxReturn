"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_personal_info():
    """Sample personal information for testing"""
    return {
        'first_name': 'John',
        'middle_initial': 'Q',
        'last_name': 'Taxpayer',
        'ssn': '123-45-6789',
        'address': '123 Main Street',
        'apartment': '',
        'city': 'Anytown',
        'state': 'CA',
        'zip_code': '90210',
        'phone': '5551234567',
        'email': 'john@example.com',
        'occupation': 'Software Engineer',
        'age_65_or_older': False,
        'blind': False,
    }


@pytest.fixture
def sample_spouse_info():
    """Sample spouse information for testing"""
    return {
        'first_name': 'Jane',
        'middle_initial': 'A',
        'last_name': 'Taxpayer',
        'ssn': '234-56-7890',  # Valid SSN (not starting with 9, 666, or 000)
        'phone': '5559876543',
        'email': 'jane@example.com',
        'occupation': 'Teacher',
        'age_65_or_older': False,
        'blind': False,
    }


@pytest.fixture
def sample_filing_status():
    """Sample filing status"""
    return {
        'status': 'Single',
        'spouse_name': '',
    }


@pytest.fixture
def sample_w2_form():
    """Sample W-2 form data"""
    return {
        'employer_name': 'ABC Corporation',
        'employer_ein': '12-3456789',
        'employer_address': '456 Business Ave, City, ST 12345',
        'wages': 75000.00,
        'federal_withholding': 8500.00,
        'social_security_wages': 75000.00,
        'social_security_withholding': 4650.00,
        'medicare_wages': 75000.00,
        'medicare_withholding': 1087.50,
        'state': 'CA',
        'state_wages': 75000.00,
        'state_withholding': 3000.00,
    }


@pytest.fixture
def sample_deductions():
    """Sample deduction data"""
    return {
        'method': 'standard',
        'medical_expenses': 0,
        'state_local_taxes': 0,
        'mortgage_interest': 0,
        'charitable_contributions': 0,
    }


@pytest.fixture
def test_output_dir(tmp_path):
    """Create temporary output directory for tests"""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir
