"""
Unit tests for Import Utilities
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from utils.import_utils import (
    TaxDataImporter,
    import_w2_from_pdf,
    import_1099_from_pdf,
    import_prior_year_return
)


class TestTaxDataImporter:
    """Test TaxDataImporter class"""

    def test_init(self):
        """Test importer initialization"""
        importer = TaxDataImporter()
        assert importer.supported_formats is not None
        assert 'json' in importer.supported_formats
        assert 'pdf' in importer.supported_formats
        assert 'txf' in importer.supported_formats

    def test_import_from_file_json(self):
        """Test importing from JSON file"""
        sample_data = {
            'personal_info': {'first_name': 'John', 'last_name': 'Doe'},
            'income': {'w2_forms': []}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            temp_path = f.name

        try:
            importer = TaxDataImporter()
            result = importer.import_from_file(temp_path)
            assert result == sample_data
        finally:
            Path(temp_path).unlink()

    def test_import_from_file_unsupported_format(self):
        """Test importing from unsupported file format"""
        importer = TaxDataImporter()
        
        # Create a temporary file with unsupported extension
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                importer.import_from_file(temp_path)
        finally:
            import os
            os.unlink(temp_path)

    def test_import_from_file_not_found(self):
        """Test importing from non-existent file"""
        importer = TaxDataImporter()

        with pytest.raises(FileNotFoundError):
            importer.import_from_file("nonexistent.json")

    def test_identify_form_type_w2(self):
        """Test identifying W-2 form"""
        importer = TaxDataImporter()
        w2_text = "W-2 Wage and Tax Statement\nSocial Security Wages: $50,000"
        assert importer._identify_form_type(w2_text) == 'w2'

    def test_identify_form_type_1099_div(self):
        """Test identifying 1099-DIV form"""
        importer = TaxDataImporter()
        div_text = "1099-DIV Dividends and Distributions\nOrdinary Dividends: $1,000"
        assert importer._identify_form_type(div_text) == '1099-div'

    def test_identify_form_type_1099_int(self):
        """Test identifying 1099-INT form"""
        importer = TaxDataImporter()
        int_text = "1099-INT Interest Income\nTaxable Interest: $500"
        assert importer._identify_form_type(int_text) == '1099-int'

    def test_identify_form_type_unknown(self):
        """Test identifying unknown form type"""
        importer = TaxDataImporter()
        unknown_text = "Some random document text"
        assert importer._identify_form_type(unknown_text) == 'unknown'

    def test_extract_w2_data(self):
        """Test extracting W-2 data from PDF text"""
        importer = TaxDataImporter()
        
        w2_text = """
        Employer EIN: 12-3456789
        Wages, tips, other compensation: $75,000.00
        Federal income tax withheld: $8,500.00
        Social security wages: $75,000.00
        Social security tax withheld: $4,650.00
        Medicare wages: $75,000.00
        Medicare tax withheld: $1,087.50
        """
        
        result = importer._extract_w2_data(w2_text)

        assert 'income' in result
        assert 'w2_forms' in result['income']
        assert len(result['income']['w2_forms']) == 1

        w2_form = result['income']['w2_forms'][0]
        assert w2_form['employer_ein'] == '12-3456789'
        assert w2_form['wages'] == 75000.00
        assert w2_form['federal_withholding'] == 8500.00
        assert w2_form['wages'] == 75000.00
        assert w2_form['federal_withholding'] == 8500.00

    def test_extract_1099_div_data(self):
        """Test extracting 1099-DIV data from PDF text"""
        importer = TaxDataImporter()
        
        div_text = """
        1099-DIV Dividends and Distributions
        Ordinary dividends: $1,500.00
        Qualified dividends: $800.00
        """
        
        result = importer._extract_1099_data(div_text, '1099-div')

        assert 'income' in result
        assert 'dividend_income' in result['income']
        assert len(result['income']['dividend_income']) == 1

        div_income = result['income']['dividend_income'][0]
        assert div_income['ordinary'] == 1500.00
        assert div_income['qualified'] == 800.00

    def test_import_from_txf_basic(self):
        """Test basic TXF import functionality"""
        importer = TaxDataImporter()

        # Create a temporary TXF file
        txf_content = """V042
ADavid Jones
T1040
L1^50000.00
L2^1000.00
L3^2000.00
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txf', delete=False) as f:
            f.write(txf_content)
            txf_file = f.name

        try:
            result = importer._import_from_txf(txf_file)

            # Verify basic structure
            assert 'personal_info' in result
            assert 'income' in result
            assert result['personal_info']['full_name'] == 'David Jones'

            # Verify income data was parsed
            assert 'wages' in result['income']
            assert result['income']['wages']['total_wages'] == 50000.00

        finally:
            os.unlink(txf_file)


class TestConvenienceFunctions:
    """Test convenience import functions"""

    @patch('utils.import_utils.TaxDataImporter._import_from_pdf')
    def test_import_w2_from_pdf(self, mock_import):
        """Test convenience function for W-2 import"""
        mock_import.return_value = {'income': {'w2_forms': []}}

        result = import_w2_from_pdf("w2.pdf")
        assert result == {'income': {'w2_forms': []}}
        mock_import.assert_called_once_with("w2.pdf")

    @patch('utils.import_utils.TaxDataImporter._import_from_pdf')
    def test_import_1099_from_pdf(self, mock_import):
        """Test convenience function for 1099 import"""
        mock_import.return_value = {'income': {'dividend_income': []}}

        result = import_1099_from_pdf("1099.pdf")
        assert result == {'income': {'dividend_income': []}}
        mock_import.assert_called_once_with("1099.pdf")

    @patch('utils.import_utils.TaxDataImporter._import_from_json')
    def test_import_prior_year_return(self, mock_import):
        """Test convenience function for prior year return import"""
        mock_import.return_value = {'personal_info': {}}

        result = import_prior_year_return("prior_year.json")
        assert result == {'personal_info': {}}
        mock_import.assert_called_once_with("prior_year.json")