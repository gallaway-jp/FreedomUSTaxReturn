"""
Unit tests for State E-Filing functionality in EFilingService
"""
import pytest
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from services.e_filing_service import EFilingService
from services.state_tax_service import StateCode
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestStateEFiling:
    """Test state e-filing functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = AppConfig()
        self.service = EFilingService(self.config)

    def test_supported_state_efile_states(self):
        """Test getting list of states that support e-filing"""
        supported_states = self.service.get_supported_state_efile_states()

        assert isinstance(supported_states, list)
        assert len(supported_states) >= 10  # Should support major states

        # Check that major states are included
        assert 'CA' in supported_states
        assert 'NY' in supported_states
        assert 'TX' in supported_states
        assert 'FL' in supported_states

    def test_generate_state_efile_xml_california(self):
        """Test generating state e-file XML for California"""
        # Create test tax data
        tax_data = TaxData()
        tax_data.data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789',
                'address': {
                    'street': '123 Main St',
                    'city': 'Los Angeles',
                    'state': 'CA',
                    'zip_code': '90210'
                }
            },
            'filing_status': {'status': 'single'},
            'dependents': [],
            'income': {
                'wages': 75000.0,
                'interest': 1000.0,
                'dividends': 2000.0
            },
            'adjustments': {},
            'payments': {
                'state_withholding': 5000.0,
                'state_estimated_payments': 2000.0
            }
        }

        # Generate XML
        xml_content = self.service.generate_state_efile_xml(tax_data, 'CA', 2025)

        # Verify XML structure
        assert xml_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert '<StateTaxReturn' in xml_content
        assert 'state="CA"' in xml_content
        assert 'taxYear="2025"' in xml_content
        assert '<FirstName>John</FirstName>' in xml_content
        assert '<LastName>Doe</LastName>' in xml_content
        assert '<StateCode>CA</StateCode>' in xml_content

    def test_generate_state_efile_xml_unsupported_state(self):
        """Test generating XML for unsupported state raises error"""
        tax_data = TaxData()

        with pytest.raises(ValueError, match="State ZZ is not supported"):
            self.service.generate_state_efile_xml(tax_data, 'ZZ', 2025)

    def test_submit_state_efile_success(self):
        """Test successful state e-file submission"""
        tax_data = TaxData()
        tax_data.data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789',
                'address': {
                    'street': '123 Main St',
                    'city': 'Anytown',
                    'state': 'CA',
                    'zip_code': '12345'
                }
            },
            'filing_status': {'status': 'single'},
            'income': {'wages': 50000}
        }

        result = self.service.submit_state_efile(tax_data, 'CA')

        assert result['success'] is True
        assert 'confirmation_number' in result
        assert result['confirmation_number'].startswith('STATE-CA-')

    def test_submit_state_efile_unsupported_state(self):
        """Test submitting to unsupported state raises error"""
        tax_data = TaxData()
        tax_data.data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789',
                'address': {
                    'street': '123 Main St',
                    'city': 'Anytown',
                    'state': 'CA',
                    'zip_code': '12345'
                }
            },
            'filing_status': {'status': 'single'},
            'income': {'wages': 50000}
        }

        with pytest.raises(ValueError, match="State ZZ is not supported"):
            self.service.submit_state_efile(tax_data, 'ZZ')

    def test_submit_state_efile_validation_failure(self):
        """Test submission fails when data validation fails"""
        tax_data = TaxData()
        # Missing required data
        tax_data.data = {
            'personal_info': {},
            'filing_status': {},
            'income': {}
        }

        with pytest.raises(ValueError, match="State e-file not ready"):
            self.service.submit_state_efile(tax_data, 'CA')

    def test_check_state_submission_status_found(self):
        """Test checking status of existing submission"""
        # First record a submission
        confirmation_number = 'STATE-CA-TEST123'
        submission_data = {
            'confirmation_number': confirmation_number,
            'state_code': 'CA',
            'timestamp': '2025-01-01T12:00:00',
            'status': 'submitted',
            'test_mode': True
        }

        self.service.record_state_submission(confirmation_number, submission_data)

        # Now check status
        status = self.service.check_state_submission_status(confirmation_number, 'CA')

        assert status['confirmation_number'] == confirmation_number
        assert status['status'] == 'submitted'
        assert status['state_code'] == 'CA'

    def test_check_state_submission_status_not_found(self):
        """Test checking status of non-existent submission"""
        status = self.service.check_state_submission_status('NONEXISTENT', 'CA')

        assert status['status'] == 'not_found'
        assert 'not found' in status['message'].lower()

    def test_validate_state_efile_readiness_complete(self):
        """Test validation when all required data is present"""
        tax_data = TaxData()
        tax_data.data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789',
                'address': {
                    'street': '123 Main St',
                    'city': 'Anytown',
                    'state': 'CA',
                    'zip_code': '12345'
                }
            },
            'filing_status': {'status': 'single'},
            'income': {'wages': 50000.0}
        }

        result = self.service.validate_state_efile_readiness(tax_data, 'CA')

        assert result['ready'] is True
        assert len(result['issues']) == 0
        assert result['state_supported'] is True

    def test_validate_state_efile_readiness_missing_data(self):
        """Test validation when required data is missing"""
        tax_data = TaxData()
        tax_data.data = {
            'personal_info': {},
            'filing_status': {},
            'income': {}
        }

        result = self.service.validate_state_efile_readiness(tax_data, 'CA')

        assert result['ready'] is False
        assert len(result['issues']) > 0
        assert any('First Name' in issue for issue in result['issues'])
        assert any('Filing status' in issue for issue in result['issues'])

    def test_validate_state_efile_readiness_unsupported_state(self):
        """Test validation for unsupported state"""
        tax_data = TaxData()

        result = self.service.validate_state_efile_readiness(tax_data, 'ZZ')

        assert result['ready'] is False
        assert result['state_supported'] is False
        assert len(result['issues']) > 0

    def test_state_filing_status_codes_mapping(self):
        """Test that state filing status codes are properly mapped"""
        # Test California codes
        ca_codes = self.service.state_filing_status_codes['CA']
        assert ca_codes['single'] == '1'
        assert ca_codes['married_filing_jointly'] == '2'
        assert ca_codes['head_of_household'] == '4'

        # Test Illinois codes (has widow/er status)
        il_codes = self.service.state_filing_status_codes['IL']
        assert 'widow_er' in il_codes
        assert il_codes['widow_er'] == '5'

    def test_state_endpoints_configuration(self):
        """Test that state endpoints are properly configured"""
        assert 'CA' in self.service.state_endpoints
        assert 'test' in self.service.state_endpoints['CA']
        assert 'production' in self.service.state_endpoints['CA']

        # Verify URLs contain expected patterns
        ca_test_url = self.service.state_endpoints['CA']['test']
        assert 'ftb.ca.gov' in ca_test_url or 'test' in ca_test_url

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_record_state_submission(self, mock_json_dump, mock_file):
        """Test recording state submission"""
        confirmation_number = 'STATE-NY-TEST456'
        submission_data = {
            'state_code': 'NY',
            'timestamp': '2025-01-01T12:00:00',
            'xml_content': '<?xml version="1.0"?><test></test>'
        }

        self.service.record_state_submission(confirmation_number, submission_data)

        # Verify json.dump was called
        mock_json_dump.assert_called_once()
        call_args = mock_json_dump.call_args[0][0]  # First positional argument

        assert confirmation_number in call_args
        assert call_args[confirmation_number]['state_code'] == 'NY'
        assert call_args[confirmation_number]['status'] == 'submitted'

    def test_calculate_federal_agi(self):
        """Test federal AGI calculation"""
        tax_data = TaxData()
        tax_data.data = {
            'income': {
                'wages': 50000.0,
                'interest': 1000.0,
                'dividends': 2000.0,
                'business_income': 5000.0
            },
            'adjustments': {
                'traditional_ira': 2000.0,
                'student_loan_interest': 500.0
            }
        }

        agi = self.service._calculate_federal_agi(tax_data)

        # 50000 + 1000 + 2000 + 5000 - 2000 - 500 = 55500
        expected_agi = 50000 + 1000 + 2000 + 5000 - 2000 - 500
        assert agi == expected_agi

    def test_calculate_federal_agi_no_adjustments(self):
        """Test federal AGI calculation with no adjustments"""
        tax_data = TaxData()
        tax_data.data = {
            'income': {
                'wages': 60000.0,
                'interest': 500.0
            },
            'adjustments': {}
        }

        agi = self.service._calculate_federal_agi(tax_data)

        assert agi == 60500.0