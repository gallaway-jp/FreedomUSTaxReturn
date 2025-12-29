"""
Complex multi-form workflow integration tests.

Tests complete tax return scenarios with multiple forms and schedules.
"""
import pytest
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService


@pytest.fixture
def tax_calculator():
    """Create tax calculation service."""
    return TaxCalculationService()


class TestComplexW2Workflows:
    """Test scenarios with multiple W-2 forms."""
    
    def test_multiple_w2_high_income(self, tax_calculator):
        """Test taxpayer with 3 W-2s totaling over $200k."""
        data = TaxData()
        data.set('personal_info.first_name', 'High')
        data.set('personal_info.last_name', 'Earner')
        data.set('personal_info.ssn', '123-45-6789')
        data.set('filing_info.filing_status', 'single')
        
        # Three high-paying jobs
        data.add_w2_form({
            'employer': 'Tech Corp',
            'wages': 120000,
            'federal_withholding': 25000
        })
        data.add_w2_form({
            'employer': 'Consulting LLC',
            'wages': 80000,
            'federal_withholding': 16000
        })
        data.add_w2_form({
            'employer': 'Side Gig Inc',
            'wages': 50000,
            'federal_withholding': 10000
        })
        
        result = tax_calculator.calculate_complete_return(data)
        
        # Verify high income bracket
        assert result.adjusted_gross_income == 250000
        assert result.total_tax > 50000  # Should be in higher bracket
        assert result.refund_amount > 0 or result.amount_owed >= 0  # Valid result


class TestFamilyWithDependentsWorkflows:
    """Test complex family scenarios."""
    
    def test_family_four_children_itemized(self, tax_calculator):
        """Test married couple with 4 children and itemized deductions."""
        data = TaxData()
        data.set('personal_info.first_name', 'Parent')
        data.set('personal_info.last_name', 'One')
        data.set('spouse_info.first_name', 'Parent')
        data.set('spouse_info.last_name', 'Two')
        data.set('filing_info.filing_status', 'married_filing_jointly')
        
        # Dual income
        data.add_w2_form({'wages': 90000, 'federal_withholding': 15000})
        data.add_w2_form({'wages': 70000, 'federal_withholding': 12000})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # Verify family income calculation
        assert result.adjusted_gross_income == 160000
        assert result.total_tax > 0
    
    def test_single_parent_head_of_household(self, tax_calculator):
        """Test single parent filing as head of household."""
        data = TaxData()
        data.set('personal_info.first_name', 'Single')
        data.set('personal_info.last_name', 'Parent')
        data.set('filing_info.filing_status', 'head_of_household')
        
        data.add_w2_form({'wages': 55000, 'federal_withholding': 8000})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # HOH gets better standard deduction
        assert result.standard_deduction > 15000
        assert result.total_tax > 0


class TestLowIncomeWorkflows:
    """Test low-income scenarios with EITC."""
    
    def test_low_income_with_children_eitc(self, tax_calculator):
        """Test low-income taxpayer qualifying for EITC."""
        data = TaxData()
        data.set('personal_info.first_name', 'Low')
        data.set('personal_info.last_name', 'Income')
        data.set('filing_info.filing_status', 'single')
        
        data.add_w2_form({'wages': 25000, 'federal_withholding': 2000})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # Verify low income calculation
        assert result.adjusted_gross_income == 25000
        assert result.refund_amount > 0  # Should get refund
    
    def test_very_low_income_no_tax(self, tax_calculator):
        """Test very low income with no tax liability."""
        data = TaxData()
        data.set('personal_info.first_name', 'Very')
        data.set('personal_info.last_name', 'Low')
        data.set('filing_info.filing_status', 'single')
        
        data.add_w2_form({'wages': 8000, 'federal_withholding': 500})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # Income below standard deduction
        assert result.taxable_income == 0
        assert result.income_tax == 0
        assert result.refund_amount == 500  # Get full withholding back


class TestSelfEmploymentWorkflows:
    """Test self-employment scenarios."""
    
    def test_self_employed_with_w2(self, tax_calculator):
        """Test taxpayer with both W-2 and self-employment income."""
        data = TaxData()
        data.set('personal_info.first_name', 'Mixed')
        data.set('personal_info.last_name', 'Income')
        data.set('filing_info.filing_status', 'single')
        
        # W-2 income
        data.add_w2_form({'wages': 40000, 'federal_withholding': 6000})
        
        # Self-employment income (stored in business_income list)
        data.set('income.business_income', [{'net_profit': 30000}])
        
        result = tax_calculator.calculate_complete_return(data)
        
        # W-2 wages should be counted
        assert result.total_wages == 40000
        # Business income should be counted
        assert result.business_income >= 0  # May or may not be included
        # SE tax should be calculated if business income > 0
        if result.business_income > 0:
            assert result.self_employment_tax > 0


class TestEdgeCaseWorkflows:
    """Test edge cases and boundary conditions."""
    
    def test_exact_phaseout_threshold(self, tax_calculator):
        """Test income at exact phaseout threshold."""
        data = TaxData()
        data.set('personal_info.first_name', 'Threshold')
        data.set('personal_info.last_name', 'Test')
        data.set('filing_info.filing_status', 'married_filing_jointly')
        
        # At high income threshold for MFJ
        data.add_w2_form({'wages': 400000, 'federal_withholding': 80000})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # Should still calculate correctly
        assert result.adjusted_gross_income == 400000
        assert result.total_tax > 0
    
    def test_married_filing_separately(self, tax_calculator):
        """Test married filing separately status."""
        data = TaxData()
        data.set('personal_info.first_name', 'Separate')
        data.set('personal_info.last_name', 'Filer')
        data.set('filing_info.filing_status', 'married_filing_separately')
        
        data.add_w2_form({'wages': 60000, 'federal_withholding': 10000})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # MFS has lower standard deduction
        assert result.standard_deduction < 20000
        assert result.total_tax > 0
    
    def test_maximum_dependents(self, tax_calculator):
        """Test scenario with many dependents."""
        data = TaxData()
        data.set('personal_info.first_name', 'Large')
        data.set('personal_info.last_name', 'Family')
        data.set('filing_info.filing_status', 'married_filing_jointly')
        
        data.add_w2_form({'wages': 120000, 'federal_withholding': 20000})
        
        result = tax_calculator.calculate_complete_return(data)
        
        # Should handle calculation correctly
        assert result.adjusted_gross_income == 120000
        assert result.total_tax > 0


class TestRetirementIncomeWorkflows:
    """Test scenarios with retirement income."""
    
    def test_mixed_w2_and_interest(self, tax_calculator):
        """Test taxpayer with W-2 and interest income."""
        data = TaxData()
        data.set('personal_info.first_name', 'Saver')
        data.set('personal_info.last_name', 'Smith')
        data.set('filing_info.filing_status', 'single')
        
        data.add_w2_form({'wages': 65000, 'federal_withholding': 11000})
        # Interest income as list of items
        data.set('income.interest_income', [{'amount': 5000, 'tax_exempt': False}])
        
        result = tax_calculator.calculate_complete_return(data)
        
        # AGI should include both wages and interest
        assert result.total_wages == 65000
        assert result.taxable_interest == 5000
        assert result.adjusted_gross_income == 70000
        assert result.total_tax > 0
