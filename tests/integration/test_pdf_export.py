"""
Integration tests for PDF export functionality
"""
import pytest
from pathlib import Path
from pypdf import PdfReader
from models.tax_data import TaxData
from utils.pdf_form_filler import TaxReturnPDFExporter


class TestPDFExportIntegration:
    """Integration tests for complete PDF export workflow"""
    
    def test_export_1040_only_with_tax_data_object(
        self,
        sample_personal_info,
        sample_filing_status,
        sample_w2_form,
        test_output_dir
    ):
        """Test exporting Form 1040 with TaxData object"""
        # Create TaxData with sample data
        tax_data = TaxData()
        
        # Set personal info
        for key, value in sample_personal_info.items():
            tax_data.set(f'personal_info.{key}', value)
        
        # Set filing status
        tax_data.set('filing_status.status', sample_filing_status['status'])
        
        # Add W-2
        tax_data.add_w2_form(sample_w2_form)
        
        # Export PDF
        exporter = TaxReturnPDFExporter()
        output_file = test_output_dir / "test_1040.pdf"
        
        success = exporter.export_1040_only(tax_data, str(output_file))
        
        assert success
        assert output_file.exists()
        assert output_file.stat().st_size > 100000  # Should be reasonable size
    
    def test_export_1040_with_dict(
        self,
        sample_personal_info,
        sample_w2_form,
        test_output_dir
    ):
        """Test exporting Form 1040 with plain dictionary"""
        # Create dict with sample data
        tax_data = {
            'personal_info.first_name': sample_personal_info['first_name'],
            'personal_info.middle_initial': sample_personal_info['middle_initial'],
            'personal_info.last_name': sample_personal_info['last_name'],
            'personal_info.ssn': sample_personal_info['ssn'],
            'personal_info.address': sample_personal_info['address'],
            'personal_info.city': sample_personal_info['city'],
            'personal_info.state': sample_personal_info['state'],
            'personal_info.zip_code': sample_personal_info['zip_code'],
            'filing_status.status': 'Single',
            'income.w2_forms': [sample_w2_form],
        }
        
        # Export PDF
        exporter = TaxReturnPDFExporter()
        output_file = test_output_dir / "test_1040_dict.pdf"
        
        success = exporter.export_1040_only(tax_data, str(output_file))
        
        assert success
        assert output_file.exists()
    
    def test_exported_pdf_contains_data(
        self,
        sample_personal_info,
        sample_w2_form,
        test_output_dir
    ):
        """Test that exported PDF actually contains the filled data"""
        # Create and export
        tax_data = TaxData()
        for key, value in sample_personal_info.items():
            tax_data.set(f'personal_info.{key}', value)
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form(sample_w2_form)
        
        exporter = TaxReturnPDFExporter()
        output_file = test_output_dir / "test_filled.pdf"
        exporter.export_1040_only(tax_data, str(output_file))
        
        # Read back and verify
        reader = PdfReader(str(output_file))
        fields = reader.get_fields()
        
        # Check personal info is filled
        assert fields['topmostSubform[0].Page1[0].f1_01[0]']['/V'] == 'John'
        assert fields['topmostSubform[0].Page1[0].f1_03[0]']['/V'] == 'Taxpayer'
        # SSN is stored without dashes after validation
        assert fields['topmostSubform[0].Page1[0].f1_04[0]']['/V'] == '123456789'
        
        # Check filing status checkbox
        assert fields['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]']['/V'] == '/1'
        
        # Check wages
        assert fields['topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]']['/V'] == '75,000.00'
        
        # Check withholding
        assert fields['topmostSubform[0].Page2[0].f2_18[0]']['/V'] == '8,500.00'
    
    def test_export_with_spouse_info(
        self,
        sample_personal_info,
        sample_spouse_info,
        sample_w2_form,
        test_output_dir
    ):
        """Test exporting with spouse information (MFJ)"""
        tax_data = TaxData()
        
        # Set taxpayer info
        for key, value in sample_personal_info.items():
            tax_data.set(f'personal_info.{key}', value)
        
        # Set spouse info
        for key, value in sample_spouse_info.items():
            tax_data.set(f'spouse_info.{key}', value)
        
        # Set MFJ filing status
        tax_data.set('filing_status.status', 'Married Filing Jointly')
        
        # Add W-2
        tax_data.add_w2_form(sample_w2_form)
        
        # Export
        exporter = TaxReturnPDFExporter()
        output_file = test_output_dir / "test_mfj.pdf"
        
        success = exporter.export_1040_only(tax_data, str(output_file))
        
        assert success
        assert output_file.exists()
        
        # Verify spouse info is in PDF
        reader = PdfReader(str(output_file))
        fields = reader.get_fields()
        
        assert fields['topmostSubform[0].Page1[0].f1_06[0]']['/V'] == 'Jane'
        # Spouse SSN is normalized to digits only
        assert fields['topmostSubform[0].Page1[0].f1_09[0]']['/V'] == '234567890'
    
    def test_export_with_multiple_w2s(
        self,
        sample_personal_info,
        sample_w2_form,
        test_output_dir
    ):
        """Test exporting with multiple W-2 forms"""
        tax_data = TaxData()
        
        for key, value in sample_personal_info.items():
            tax_data.set(f'personal_info.{key}', value)
        tax_data.set('filing_status.status', 'Single')
        
        # Add two W-2s
        tax_data.add_w2_form(sample_w2_form)
        
        w2_2 = sample_w2_form.copy()
        w2_2['employer_name'] = 'XYZ Inc'
        w2_2['wages'] = 50000.00
        w2_2['federal_withholding'] = 5500.00
        tax_data.add_w2_form(w2_2)
        
        # Export
        exporter = TaxReturnPDFExporter()
        output_file = test_output_dir / "test_multiple_w2.pdf"
        
        success = exporter.export_1040_only(tax_data, str(output_file))
        assert success
        
        # Verify totals are summed
        reader = PdfReader(str(output_file))
        fields = reader.get_fields()
        
        # Total wages should be 125,000 (75000 + 50000)
        assert fields['topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]']['/V'] == '125,000.00'
        
        # Total withholding should be 14,000 (8500 + 5500)
        assert fields['topmostSubform[0].Page2[0].f2_18[0]']['/V'] == '14,000.00'
    
    def test_export_complete_return(
        self,
        sample_personal_info,
        sample_w2_form,
        test_output_dir
    ):
        """Test exporting complete return with multiple forms"""
        tax_data = TaxData()
        
        for key, value in sample_personal_info.items():
            tax_data.set(f'personal_info.{key}', value)
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form(sample_w2_form)
        
        # Export complete return
        exporter = TaxReturnPDFExporter()
        output_file = test_output_dir / "test_complete.pdf"
        
        success = exporter.export_complete_return(tax_data, str(output_file))
        
        assert success
        assert output_file.exists()
        
        # File should be reasonable size (may not be larger if schedules don't exist yet)
        assert output_file.stat().st_size > 100000
    
    def test_export_error_handling(self, test_output_dir):
        """Test error handling with invalid data"""
        exporter = TaxReturnPDFExporter()
        
        # Try to export with minimal/invalid data
        tax_data = TaxData()
        output_file = test_output_dir / "test_minimal.pdf"
        
        # Should still succeed (just with empty fields)
        success = exporter.export_1040_only(tax_data, str(output_file))
        assert success
        assert output_file.exists()
