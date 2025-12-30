"""
Test PDF Generator functionality
"""
import pytest
from pathlib import Path
from utils.pdf.pdf_generator import TaxReturnPDFGenerator
from utils.pdf.field_mapper import DotDict


class TestTaxReturnPDFGenerator:
    """Test TaxReturnPDFGenerator class"""

    def test_init(self):
        """Test PDF generator initialization"""
        generator = TaxReturnPDFGenerator()
        assert generator.form_filler is not None
        assert generator.output_directory.exists()

    def test_determine_required_forms_basic(self):
        """Test determining required forms for basic return"""
        generator = TaxReturnPDFGenerator()

        tax_data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789'
            },
            'filing_status': {'status': 'Single'},
            'income': {
                'w2_forms': [{'wages': 75000, 'federal_withholding': 8500}]
            },
            'deductions': {'method': 'standard'}
        }

        required_forms = generator.determine_required_forms(tax_data)
        assert 'Form 1040' in required_forms
        assert len(required_forms) == 1  # Only Form 1040 for basic return

    def test_determine_required_forms_with_schedules(self):
        """Test determining required forms with schedules"""
        generator = TaxReturnPDFGenerator()

        tax_data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789'
            },
            'filing_status': {'status': 'Single'},
            'income': {
                'w2_forms': [{'wages': 75000, 'federal_withholding': 8500}],
                'capital_gains': [{'description': 'Stock sale', 'gain_loss': 5000}]
            },
            'schedules': {
                'schedule_c': {'business_name': 'Test Business', 'gross_receipts': 50000}
            },
            'deductions': {'method': 'itemized', 'mortgage_interest': 10000}
        }

        required_forms = generator.determine_required_forms(tax_data)
        assert 'Form 1040' in required_forms
        assert 'Form 1040 (Schedule 1)' in required_forms
        assert 'Form 1040 (Schedule A)' in required_forms
        assert 'Form 1040 (Schedule C)' in required_forms
        assert 'Form 1040 (Schedule D)' in required_forms
        assert 'Form 8949' in required_forms

    def test_validate_pdf_generation_valid(self):
        """Test validation with valid data"""
        generator = TaxReturnPDFGenerator()

        tax_data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789'
            }
        }

        is_valid, error = generator.validate_pdf_generation(tax_data)
        assert is_valid
        assert error is None

    def test_validate_pdf_generation_missing_required(self):
        """Test validation with missing required data"""
        generator = TaxReturnPDFGenerator()

        tax_data = {
            'personal_info': {
                'first_name': 'John'
                # Missing last_name and ssn
            }
        }

        is_valid, error = generator.validate_pdf_generation(tax_data)
        assert not is_valid
        assert 'Missing required field' in error

    def test_get_output_path(self):
        """Test generating output path"""
        generator = TaxReturnPDFGenerator()

        tax_data = DotDict({
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789'
            }
        })

        output_path = generator._get_output_path('Form 1040', tax_data)
        assert 'Doe_John_6789_Form_1040.pdf' in str(output_path)
        assert output_path.parent == generator.output_directory

    def test_generate_complete_return_basic(self):
        """Test generating a complete basic return"""
        generator = TaxReturnPDFGenerator()

        tax_data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789',
                'address': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zip_code': '12345'
            },
            'filing_status': {'status': 'Single'},
            'income': {
                'w2_forms': [{'wages': 75000, 'federal_withholding': 8500}]
            },
            'deductions': {'method': 'standard'}
        }

        # Test validation first
        is_valid, error = generator.validate_pdf_generation(tax_data)
        assert is_valid, f"Validation failed: {error}"

        # Generate the return
        generated_files = generator.generate_complete_return(tax_data, flatten=True)

        # Should have generated Form 1040
        assert 'Form 1040' in generated_files
        assert Path(generated_files['Form 1040']).exists()

        # Clean up
        for file_path in generated_files.values():
            Path(file_path).unlink(missing_ok=True)