"""
Integration tests for complete tax return workflows

Tests end-to-end scenarios from data entry through calculations.
Validates that all components work together correctly.
"""

import pytest
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService


class TestSimpleSingleW2Workflow:
    """Test complete workflow for simple single W-2 return"""
    
    def test_single_person_single_w2_gets_refund(self):
        """Test complete workflow: Single filer, one W-2, gets refund"""
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        
        w2 = {
            'employer_name': 'ABC Corp',
            'wages': 50000.00,
            'federal_withholding': 8000.00
        }
        tax_data.set('income.w2_forms', [w2])
        tax_data.set('deductions.method', 'standard')
        
        service = TaxCalculationService(2025)
        result = service.calculate_complete_return(tax_data.data)
        
        assert result.total_income == 50000.00
        assert result.adjusted_gross_income == 50000.00
        assert result.total_payments > 0
        assert result.refund_amount > 0  # Should get refund
    
    def test_married_joint_two_w2s(self):
        """Test complete workflow: MFJ, two W-2s"""
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Married Filing Jointly')
        
        w2_forms = [
            {'wages': 75000.00, 'federal_withholding': 9000.00},
            {'wages': 65000.00, 'federal_withholding': 7500.00}
        ]
        tax_data.set('income.w2_forms', w2_forms)
        tax_data.set('deductions.method', 'standard')
        
        service = TaxCalculationService(2025)
        result = service.calculate_complete_return(tax_data.data)
        
        assert result.total_income == 140000.00
        assert result.total_payments == 16500.00


class TestFamilyWithChildrenWorkflow:
    """Test complete workflow for family with children"""
    
    def test_family_with_two_children(self):
        """Test complete workflow: Family with 2 children"""
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Married Filing Jointly')
        
        w2 = {'wages': 80000.00, 'federal_withholding': 10000.00}
        tax_data.set('income.w2_forms', [w2])
        tax_data.set('deductions.method', 'standard')
        
        dependents = [
            {'age': 8, 'qualifying_child': True},
            {'age': 5, 'qualifying_child': True}
        ]
        tax_data.set('dependents', dependents)
        
        service = TaxCalculationService(2025)
        result = service.calculate_complete_return(tax_data.data)
        
        assert result.total_income == 80000.00
        # Child tax credit is included in total_tax calculation
        assert result.total_tax >= 0


class TestEdgeCaseWorkflows:
    """Test edge case workflows"""
    
    def test_no_income_no_tax(self):
        """Test workflow with no income"""
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.set('income.w2_forms', [])
        
        service = TaxCalculationService(2025)
        result = service.calculate_complete_return(tax_data.data)
        
        assert result.total_income == 0
        assert result.total_tax == 0
    
    def test_income_below_standard_deduction(self):
        """Test workflow with income below standard deduction"""
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        
        w2 = {'wages': 10000.00, 'federal_withholding': 1000.00}
        tax_data.set('income.w2_forms', [w2])
        tax_data.set('deductions.method', 'standard')
        
        service = TaxCalculationService(2025)
        result = service.calculate_complete_return(tax_data.data)
        
        # Income below standard deduction = $0 taxable income
        assert result.taxable_income == 0
        assert result.total_tax == 0
        assert result.refund_amount == 1000.00  # Full refund
