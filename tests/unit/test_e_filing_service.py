"""
Unit tests for E-Filing Service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from services.e_filing_service import EFilingService
from config.app_config import AppConfig
from models.tax_data import TaxData


class TestEFilingService:
    """Test E-Filing Service functionality"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return AppConfig.from_env()

    @pytest.fixture
    def audit_service(self):
        """Create mock audit service"""
        return Mock()

    @pytest.fixture
    def e_filing_service(self, config, audit_service):
        """Create e-filing service instance"""
        return EFilingService(config, audit_service)

    @pytest.fixture
    def sample_tax_data(self):
        """Create sample tax data for testing"""
        tax_data = TaxData()
        tax_data.data['years'][2026]['personal_info']['first_name'] = 'John'
        tax_data.data['years'][2026]['personal_info']['last_name'] = 'Doe'
        tax_data.data['years'][2026]['personal_info']['ssn'] = '123-45-6789'
        tax_data.data['years'][2026]['personal_info']['address'] = '123 Main St'
        tax_data.data['years'][2026]['personal_info']['city'] = 'Anytown'
        tax_data.data['years'][2026]['personal_info']['state'] = 'CA'
        tax_data.data['years'][2026]['personal_info']['zip_code'] = '12345'
        tax_data.data['years'][2026]['filing_status']['status'] = 'single'
        tax_data.data['years'][2026]['income']['w2_forms'] = [{'wages': 50000, 'employer_name': 'Test Corp'}]
        tax_data.data['years'][2026]['income']['interest_income'] = 1000
        tax_data.data['years'][2026]['income']['dividend_income'] = 2000
        tax_data.data['years'][2026]['deductions']['standard_deduction'] = 13850
        tax_data.data['years'][2026]['credits']['child_tax_credit'] = 2000
        tax_data.data['years'][2026]['payments']['federal_withholding'] = 8000
        return tax_data

    def test_initialization(self, e_filing_service):
        """Test service initialization"""
        assert e_filing_service.config is not None
        assert e_filing_service.audit_service is not None
        assert 'test' in e_filing_service.irs_endpoints
        assert 'production' in e_filing_service.irs_endpoints

    def test_generate_efile_xml(self, e_filing_service, sample_tax_data, audit_service):
        """Test XML generation for e-filing"""
        xml_content = e_filing_service.generate_efile_xml(sample_tax_data, 2026)

        # Verify XML structure
        assert '<?xml' in xml_content
        assert 'MeF' in xml_content
        assert 'John' in xml_content
        assert 'Doe' in xml_content
        assert '123-45-6789' in xml_content
        assert '1' in xml_content

        # Verify audit logging
        audit_service.log_event.assert_called_once()
        call_args = audit_service.log_event.call_args
        assert call_args[0][0] == 'e_file_generated'
        assert '2026' in call_args[0][1]

    def test_validate_efile_xml_valid(self, e_filing_service, sample_tax_data):
        """Test XML validation with valid data"""
        xml_content = e_filing_service.generate_efile_xml(sample_tax_data, 2026)

        result = e_filing_service.validate_efile_xml(xml_content)

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_efile_xml_invalid_ssn(self, e_filing_service, sample_tax_data):
        """Test XML validation with invalid SSN"""
        # Generate XML first, then manually modify it for testing
        xml_content = e_filing_service.generate_efile_xml(sample_tax_data, 2026)
        
        # Replace valid SSN with invalid one in the XML
        invalid_xml = xml_content.replace('123-45-6789', 'invalid-ssn')
        
        result = e_filing_service.validate_efile_xml(invalid_xml)

        assert any('Invalid SSN format' in error for error in result['errors'])

    def test_validate_efile_xml_missing_taxpayer(self, e_filing_service):
        """Test XML validation with missing taxpayer info"""
        # Create minimal invalid XML
        invalid_xml = '''<?xml version="1.0"?>
        <MeF xmlns="http://www.irs.gov/efile" version="1.0">
            <Transmission id="test-id">
                <Header>
                    <TaxYear>2026</TaxYear>
                    <TaxpayerId>123-45-6789</TaxpayerId>
                    <SoftwareId>FreedomUSTaxReturn</SoftwareId>
                    <SoftwareVersion>3.0</SoftwareVersion>
                    <TransmissionType>Original</TransmissionType>
                </Header>
                <ReturnData>
                    <Form1040 taxYear="2026"/>
                </ReturnData>
            </Transmission>
        </MeF>'''

        result = e_filing_service.validate_efile_xml(invalid_xml)

        assert result['valid'] is False
        assert 'Missing required element: Taxpayer in Transmission' in result['errors']

    def test_submit_efile(self, e_filing_service, sample_tax_data):
        """Test e-file submission (mock)"""
        xml_content = e_filing_service.generate_efile_xml(sample_tax_data, 2026)

        result = e_filing_service.submit_efile(xml_content, test_mode=True)

        assert result['success'] is True
        assert 'confirmation_number' in result
        assert result['confirmation_number'].startswith('EF')
        assert 'timestamp' in result
        assert result['status'] == 'accepted'

    def test_check_submission_status(self, e_filing_service):
        """Test submission status checking"""
        confirmation_number = 'EF12345678'

        result = e_filing_service.check_submission_status(confirmation_number)

        assert result['confirmation_number'] == confirmation_number
        assert 'status' in result
        assert 'last_updated' in result