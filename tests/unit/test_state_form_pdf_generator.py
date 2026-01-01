"""
Unit tests for State Form PDF Generator
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from services.state_form_pdf_generator import StateFormPDFGenerator, StateFormData
from services.state_tax_service import StateCode, StateTaxCalculation


class TestStateFormPDFGenerator:
    """Test StateFormPDFGenerator functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.generator = StateFormPDFGenerator()

    def test_initialization(self):
        """Test generator initialization"""
        assert self.generator is not None
        assert self.generator.state_service is not None

    def test_get_supported_states(self):
        """Test getting supported states for PDF generation"""
        supported = self.generator.get_supported_states()
        assert isinstance(supported, list)
        assert len(supported) > 0

        # Check that major states are supported
        assert StateCode.CA in supported
        assert StateCode.NY in supported
        assert StateCode.NJ in supported

    def test_generate_state_form_pdf_california(self):
        """Test PDF generation for California"""

        # Create test data
        taxpayer_info = {
            'first_name': 'John',
            'last_name': 'Doe',
            'ssn': '123-45-6789',
            'address': '123 Main St',
            'city': 'Los Angeles',
            'state': 'CA',
            'zip_code': '90210'
        }

        income_data = {
            'federal_agi': 100000.0,
            'wages': 95000.0
        }

        tax_calc = StateTaxCalculation(
            state_code=StateCode.CA,
            taxable_income=85000.0,
            tax_owed=8500.0,
            effective_rate=0.085,
            credits=0.0,
            deductions=15000.0
        )

        form_data = StateFormData(
            state_code=StateCode.CA,
            tax_year=2024,
            taxpayer_info=taxpayer_info,
            income_data=income_data,
            tax_calculation=tax_calc,
            filing_status='single',
            dependents=0
        )

        # Mock template path to exist
        with patch.object(self.generator, '_get_template_path') as mock_template:
            mock_template_path = Mock()
            mock_template_path.exists.return_value = True
            mock_template.return_value = mock_template_path

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                output_path = tmp_file.name

            try:
                result = self.generator.generate_state_form_pdf(form_data, output_path)

                # Verify the result
                assert result == output_path
                # Verify the PDF file was created
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0

            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_generate_state_form_pdf_unsupported_state(self):
        """Test PDF generation for unsupported state"""
        form_data = StateFormData(
            state_code=StateCode.TX,  # Texas doesn't have PDF generation
            tax_year=2024,
            taxpayer_info={},
            income_data={},
            tax_calculation=Mock(),
            filing_status='single',
            dependents=0
        )

        with pytest.raises(ValueError, match="not supported for PDF generation"):
            self.generator.generate_state_form_pdf(form_data)

    def test_prepare_california_fields(self):
        """Test field preparation for California Form 540"""
        taxpayer_info = {
            'first_name': 'John',
            'last_name': 'Doe',
            'ssn': '123-45-6789',
            'address': '123 Main St',
            'city': 'Los Angeles',
            'state': 'CA',
            'zip_code': '90210'
        }

        income_data = {'federal_agi': 100000.0}

        tax_calc = StateTaxCalculation(
            state_code=StateCode.CA,
            taxable_income=85000.0,
            tax_owed=8500.0,
            effective_rate=0.085,
            credits=0.0,
            deductions=15000.0
        )

        form_data = StateFormData(
            state_code=StateCode.CA,
            tax_year=2024,
            taxpayer_info=taxpayer_info,
            income_data=income_data,
            tax_calculation=tax_calc,
            filing_status='single',
            dependents=0
        )

        fields = self.generator._prepare_california_fields(form_data)

        # Verify personal information fields
        assert fields['topmostSubform[0].Page1[0].SSN[0]'] == '123-45-6789'
        assert fields['topmostSubform[0].Page1[0].FirstName[0]'] == 'John'
        assert fields['topmostSubform[0].Page1[0].LastName[0]'] == 'Doe'

        # Verify address fields
        assert fields['topmostSubform[0].Page1[0].Address[0]'] == '123 Main St'
        assert fields['topmostSubform[0].Page1[0].City[0]'] == 'Los Angeles'
        assert fields['topmostSubform[0].Page1[0].ZIP[0]'] == '90210'

        # Verify filing status (single should be checked)
        assert fields['topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'] == '/1'

        # Verify tax data
        assert fields['topmostSubform[0].Page1[0].AGI[0]'] == '100000.00'
        assert fields['topmostSubform[0].Page1[0].CA_AGI[0]'] == '85000.00'
        assert fields['topmostSubform[0].Page1[0].Tax[0]'] == '8500.00'

    def test_prepare_new_york_fields(self):
        """Test field preparation for New York Form IT-201"""
        taxpayer_info = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'ssn': '987-65-4321',
            'address': '456 Oak Ave',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001'
        }

        income_data = {'federal_agi': 150000.0}

        tax_calc = StateTaxCalculation(
            state_code=StateCode.NY,
            taxable_income=140000.0,
            tax_owed=14000.0,
            effective_rate=0.093,
            credits=0.0,
            deductions=10000.0
        )

        form_data = StateFormData(
            state_code=StateCode.NY,
            tax_year=2024,
            taxpayer_info=taxpayer_info,
            income_data=income_data,
            tax_calculation=tax_calc,
            filing_status='married_joint',
            dependents=2
        )

        fields = self.generator._prepare_new_york_fields(form_data)

        # Verify personal information
        assert fields['topmostSubform[0].Page1[0].SSN[0]'] == '987-65-4321'
        assert fields['topmostSubform[0].Page1[0].FirstName[0]'] == 'Jane'
        assert fields['topmostSubform[0].Page1[0].LastName[0]'] == 'Smith'

        # Verify married filing jointly is checked
        assert fields['topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'] == '/1'

        # Verify tax data
        assert fields['topmostSubform[0].Page1[0].FederalAGI[0]'] == '150000.00'
        assert fields['topmostSubform[0].Page1[0].NY_AGI[0]'] == '140000.00'
        assert fields['topmostSubform[0].Page1[0].TaxableIncome[0]'] == '140000.00'

    def test_generate_output_path(self):
        """Test output path generation"""
        taxpayer_info = {'last_name': 'Johnson'}
        income_data = {}
        tax_calc = Mock()

        form_data = StateFormData(
            state_code=StateCode.CA,
            tax_year=2024,
            taxpayer_info=taxpayer_info,
            income_data=income_data,
            tax_calculation=tax_calc,
            filing_status='single',
            dependents=0
        )

        path = self.generator._generate_output_path(form_data)

        # Verify path contains expected components
        assert 'Johnson' in path
        assert 'CA' in path
        assert '2024' in path
        assert path.endswith('_tax_return.pdf')

    def test_get_template_path(self):
        """Test template path resolution"""
        # Test California
        ca_path = self.generator._get_template_path(StateCode.CA)
        assert ca_path.name == 'ca_540.pdf'

        # Test New York
        ny_path = self.generator._get_template_path(StateCode.NY)
        assert ny_path.name == 'ny_it201.pdf'

        # Test unsupported state
        with pytest.raises(ValueError):
            self.generator._get_template_path(StateCode.TX)