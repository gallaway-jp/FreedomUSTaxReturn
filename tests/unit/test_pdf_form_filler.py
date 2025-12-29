"""
Unit tests for PDF Form Filler
"""
import pytest
from pathlib import Path
from utils.pdf_form_filler import (
    PDFFormFiller,
    Form1040Mapper,
    DotDict,
    calculate_standard_deduction
)


class TestDotDict:
    """Test DotDict helper class"""
    
    def test_dotdict_simple_access(self):
        """Test accessing simple dotted keys"""
        data = {
            'personal_info.first_name': 'John',
            'personal_info.last_name': 'Doe',
        }
        dd = DotDict(data)
        assert dd.get('personal_info.first_name') == 'John'
    
    def test_dotdict_nested_access(self):
        """Test accessing nested dictionary"""
        data = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe'
            }
        }
        dd = DotDict(data)
        assert dd.get('personal_info.first_name') == 'John'
    
    def test_dotdict_default_value(self):
        """Test default value when key not found"""
        dd = DotDict({})
        assert dd.get('nonexistent.key', 'default') == 'default'
    
    def test_dotdict_mixed_access(self):
        """Test mixed dotted and nested access"""
        data = {
            'income': {
                'w2_forms': [
                    {'wages': 75000}
                ]
            }
        }
        dd = DotDict(data)
        assert dd.get('income.w2_forms')[0]['wages'] == 75000


class TestStandardDeductionCalculation:
    """Test standard deduction calculations"""
    
    def test_single_standard_deduction(self):
        """Test standard deduction for single filer"""
        deduction = calculate_standard_deduction('Single', 2025)
        assert deduction == 15750
    
    def test_married_filing_jointly(self):
        """Test standard deduction for MFJ"""
        deduction = calculate_standard_deduction('Married Filing Jointly', 2025)
        assert deduction == 31500
    
    def test_head_of_household(self):
        """Test standard deduction for HOH"""
        deduction = calculate_standard_deduction('Head of Household', 2025)
        assert deduction == 23625
    
    # NOTE: Age and blind deductions are no longer calculated by calculate_standard_deduction
    # They should be handled separately in the tax calculation logic if needed


class TestForm1040Mapper:
    """Test Form 1040 field mapping"""
    
    def test_map_personal_info(self, sample_personal_info):
        """Test mapping personal information"""
        data = DotDict({
            'personal_info': sample_personal_info
        })
        
        fields = Form1040Mapper.map_personal_info(data)
        
        assert 'topmostSubform[0].Page1[0].f1_01[0]' in fields
        assert fields['topmostSubform[0].Page1[0].f1_01[0]'] == 'John'
        assert fields['topmostSubform[0].Page1[0].f1_03[0]'] == 'Taxpayer'
        assert fields['topmostSubform[0].Page1[0].f1_04[0]'] == '123-45-6789'
    
    def test_map_filing_status_single(self):
        """Test mapping filing status - Single"""
        data = DotDict({
            'filing_status': {'status': 'Single'}
        })
        
        fields = Form1040Mapper.map_filing_status(data)
        
        assert 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]' in fields
        assert fields['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]'] == '/1'
    
    def test_map_filing_status_married_jointly(self):
        """Test mapping filing status - MFJ"""
        data = DotDict({
            'filing_status': {'status': 'Married Filing Jointly'}
        })
        
        fields = Form1040Mapper.map_filing_status(data)
        
        assert 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]' in fields
        assert fields['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]'] == '/1'
    
    def test_map_income_with_w2(self, sample_w2_form):
        """Test mapping income from W-2"""
        data = DotDict({
            'income': {
                'w2_forms': [sample_w2_form]
            }
        })
        
        fields = Form1040Mapper.map_income(data)
        
        assert 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]' in fields
        assert fields['topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]'] == '75,000.00'
    
    def test_map_income_multiple_w2s(self, sample_w2_form):
        """Test mapping income from multiple W-2s"""
        w2_2 = sample_w2_form.copy()
        w2_2['wages'] = 50000.00
        
        data = DotDict({
            'income': {
                'w2_forms': [sample_w2_form, w2_2]
            }
        })
        
        fields = Form1040Mapper.map_income(data)
        
        # Should sum both W-2s
        assert fields['topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]'] == '125,000.00'
    
    def test_map_payments_withholding(self, sample_w2_form):
        """Test mapping federal withholding"""
        data = DotDict({
            'income': {
                'w2_forms': [sample_w2_form]
            }
        })
        
        fields = Form1040Mapper.map_payments(data)
        
        assert 'topmostSubform[0].Page2[0].f2_18[0]' in fields
        assert fields['topmostSubform[0].Page2[0].f2_18[0]'] == '8,500.00'
    
    def test_map_deductions_standard(self):
        """Test mapping standard deduction"""
        data = DotDict({
            'deductions': {'method': 'standard'},
            'filing_status': {'status': 'Single'},
            'personal_info': {
                'age_65_or_older': False,
                'blind': False
            },
            'spouse_info': {
                'age_65_or_older': False,
                'blind': False
            }
        })
        
        fields = Form1040Mapper.map_deductions(data)
        
        assert 'topmostSubform[0].Page1[0].f1_37[0]' in fields
        assert '15,750' in fields['topmostSubform[0].Page1[0].f1_37[0]']
    
    def test_get_all_fields(self, sample_personal_info, sample_w2_form):
        """Test getting all mapped fields"""
        data = DotDict({
            'personal_info': sample_personal_info,
            'filing_status': {'status': 'Single'},
            'income': {
                'w2_forms': [sample_w2_form]
            },
            'deductions': {'method': 'standard'}
        })
        
        fields = Form1040Mapper.get_all_fields(data)
        
        # Should include fields from all sections
        assert len(fields) > 0
        assert 'topmostSubform[0].Page1[0].f1_01[0]' in fields  # Personal info
        assert 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]' in fields  # Filing status
        assert 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]' in fields  # Income


class TestPDFFormFiller:
    """Test PDFFormFiller class"""
    
    def test_get_form_path(self):
        """Test getting form path"""
        filler = PDFFormFiller()
        form_path = filler.get_form_path('Form 1040')
        
        assert form_path.exists()
        assert form_path.name == 'Form 1040.pdf'
    
    def test_get_form_path_nonexistent(self):
        """Test getting path for non-existent form"""
        filler = PDFFormFiller()
        
        with pytest.raises(FileNotFoundError):
            filler.get_form_path('Nonexistent Form')
    
    def test_inspect_form_fields(self):
        """Test inspecting form fields"""
        filler = PDFFormFiller()
        fields = filler.get_form_fields('Form 1040')
        
        assert isinstance(fields, dict)
        assert len(fields) > 0
        assert 'topmostSubform[0].Page1[0].f1_01[0]' in fields
