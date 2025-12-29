"""
Comprehensive tests for TaxCalculationService

This test suite provides thorough coverage of the tax calculation
orchestration service including all calculation workflows.
"""

import pytest
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService, TaxResult


class TestTaxResultDataclass:
    """Test TaxResult dataclass functionality"""
    
    def test_tax_result_initialization(self):
        """Test TaxResult initializes with zero values"""
        result = TaxResult()
        assert result.total_wages == 0.0
        assert result.total_income == 0.0
        assert result.total_tax == 0.0
        assert result.refund_amount == 0.0
        assert result.amount_owed == 0.0
    
    def test_tax_result_to_dict(self):
        """Test TaxResult conversion to dictionary"""
        result = TaxResult(
            total_wages=50000.0,
            total_income=50000.0,
            total_tax=5000.0
        )
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['total_wages'] == 50000.0
        assert result_dict['total_income'] == 50000.0
        assert result_dict['total_tax'] == 5000.0
    
    def test_tax_result_all_fields_in_dict(self):
        """Test that to_dict includes all fields"""
        result = TaxResult()
        result_dict = result.to_dict()
        
        # Verify all key fields are present
        expected_keys = [
            'total_wages', 'taxable_interest', 'tax_exempt_interest',
            'ordinary_dividends', 'qualified_dividends', 'business_income',
            'total_income', 'standard_deduction', 'itemized_deduction',
            'deduction_used', 'adjusted_gross_income', 'taxable_income',
            'income_tax', 'self_employment_tax', 'total_tax',
            'federal_withholding', 'estimated_tax_payments', 'total_payments',
            'refund_amount', 'amount_owed'
        ]
        for key in expected_keys:
            assert key in result_dict


class TestTaxCalculationServiceInitialization:
    """Test service initialization"""
    
    def test_service_initialization_default_year(self):
        """Test service initializes with default tax year"""
        service = TaxCalculationService()
        assert service.tax_year == 2025
        assert service.config is not None


class TestSimpleW2Return:
    """Test calculations with simple W-2 income"""
    
    def test_calculate_simple_w2_single_filer(self, sample_w2_form):
        """Test complete return calculation with single W-2"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form(sample_w2_form)
        
        result = service.calculate_complete_return(tax_data)
        
        # Verify W-2 wages captured
        assert result.total_wages == sample_w2_form['wages']
        assert result.total_income == sample_w2_form['wages']
        assert result.adjusted_gross_income == sample_w2_form['wages']
        
        # Verify standard deduction applied
        assert result.standard_deduction == 15750.0  # 2025 Single
        assert result.deduction_used == 15750.0
        
        # Verify taxable income calculated
        expected_taxable = max(0, sample_w2_form['wages'] - 15750.0)
        assert result.taxable_income == expected_taxable
        
        # Verify income tax calculated
        assert result.income_tax > 0
        assert result.total_tax == result.income_tax  # No SE tax
        
        # Verify withholding captured
        assert result.federal_withholding == sample_w2_form['federal_withholding']
        assert result.total_payments == sample_w2_form['federal_withholding']
        
        # Verify refund or owed calculated
        if result.total_payments > result.total_tax:
            assert result.refund_amount == result.total_payments - result.total_tax
            assert result.amount_owed == 0
        else:
            assert result.amount_owed == result.total_tax - result.total_payments
            assert result.refund_amount == 0
    
    def test_calculate_multiple_w2_forms(self):
        """Test calculation with multiple W-2 forms"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        
        # Add two W-2 forms
        tax_data.add_w2_form({
            'employer_name': 'ABC Corp',
            'wages': 50000,
            'federal_withholding': 5000
        })
        tax_data.add_w2_form({
            'employer_name': 'XYZ Inc',
            'wages': 30000,
            'federal_withholding': 3000
        })
        
        result = service.calculate_complete_return(tax_data)
        
        # Verify wages summed
        assert result.total_wages == 80000
        assert result.total_income == 80000
        
        # Verify withholding summed
        assert result.federal_withholding == 8000
        
        # Verify tax calculated on combined income
        assert result.taxable_income == 80000 - 15750  # After standard deduction
        assert result.income_tax > 0
    
    def test_calculate_w2_with_refund(self):
        """Test W-2 return that results in refund"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({
            'employer_name': 'ABC Corp',
            'wages': 40000,
            'federal_withholding': 6000  # Over-withheld
        })
        
        result = service.calculate_complete_return(tax_data)
        
        # Should get refund
        assert result.refund_amount > 0
        assert result.amount_owed == 0
        assert result.refund_amount == result.total_payments - result.total_tax
    
    def test_calculate_w2_with_amount_owed(self):
        """Test W-2 return that results in amount owed"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({
            'employer_name': 'ABC Corp',
            'wages': 100000,
            'federal_withholding': 5000  # Under-withheld
        })
        
        result = service.calculate_complete_return(tax_data)
        
        # Should owe money
        assert result.amount_owed > 0
        assert result.refund_amount == 0
        assert result.amount_owed == result.total_tax - result.total_payments


class TestFilingStatuses:
    """Test calculations with different filing statuses"""
    
    @pytest.mark.parametrize("filing_status,expected_deduction", [
        ('Single', 15750.0),
        ('MFJ', 31500.0),
        ('MFS', 15750.0),
        ('HOH', 23625.0),
        ('QW', 31500.0)
    ])
    def test_filing_status_deductions(self, filing_status, expected_deduction):
        """Test that each filing status gets correct standard deduction"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', filing_status)
        tax_data.add_w2_form({'wages': 50000, 'federal_withholding': 5000})
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.standard_deduction == expected_deduction
        assert result.deduction_used == expected_deduction
    
    def test_married_filing_jointly_lower_tax(self):
        """Test that MFJ typically has lower tax than Single at same income"""
        service = TaxCalculationService(tax_year=2025)
        
        # Single filer
        tax_data_single = TaxData()
        tax_data_single.set('filing_status.status', 'Single')
        tax_data_single.add_w2_form({'wages': 100000, 'federal_withholding': 0})
        result_single = service.calculate_complete_return(tax_data_single)
        
        # MFJ filer
        tax_data_mfj = TaxData()
        tax_data_mfj.set('filing_status.status', 'MFJ')
        tax_data_mfj.add_w2_form({'wages': 100000, 'federal_withholding': 0})
        result_mfj = service.calculate_complete_return(tax_data_mfj)
        
        # MFJ should have lower tax
        assert result_mfj.total_tax < result_single.total_tax


class TestMultipleIncomeTypes:
    """Test calculations with multiple income types"""
    
    def test_wages_plus_interest(self):
        """Test W-2 wages plus interest income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 50000, 'federal_withholding': 5000})
        tax_data.set('income.interest_income', [
            {'payer': 'Bank A', 'amount': 1000, 'tax_exempt': False}
        ])
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.total_wages == 50000
        assert result.taxable_interest == 1000
        assert result.total_income == 51000
    
    def test_tax_exempt_interest_excluded_from_income(self):
        """Test that tax-exempt interest is tracked but not in total income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 50000, 'federal_withholding': 5000})
        tax_data.set('income.interest_income', [
            {'payer': 'Bank A', 'amount': 1000, 'tax_exempt': False},
            {'payer': 'Muni Bonds', 'amount': 500, 'tax_exempt': True}
        ])
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.taxable_interest == 1000
        assert result.tax_exempt_interest == 500
        # Total income should only include taxable interest
        assert result.total_income == 51000  # 50000 + 1000
    
    def test_wages_plus_dividends(self):
        """Test W-2 wages plus dividend income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 50000, 'federal_withholding': 5000})
        tax_data.set('income.dividend_income', [
            {'payer': 'Stock A', 'ordinary': 1500, 'qualified': 1000}
        ])
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.total_wages == 50000
        assert result.ordinary_dividends == 1500
        assert result.qualified_dividends == 1000
        assert result.total_income == 51500  # Wages + ordinary dividends
    
    def test_multiple_income_sources(self):
        """Test with wages, interest, and dividends"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'MFJ')
        tax_data.add_w2_form({'wages': 75000, 'federal_withholding': 8000})
        tax_data.set('income.interest_income', [
            {'payer': 'Bank', 'amount': 2000, 'tax_exempt': False}
        ])
        tax_data.set('income.dividend_income', [
            {'payer': 'Stock', 'ordinary': 3000, 'qualified': 2000}
        ])
        
        result = service.calculate_complete_return(tax_data)
        
        # Total income = wages + interest + dividends
        assert result.total_income == 80000  # 75000 + 2000 + 3000
        assert result.adjusted_gross_income == 80000


class TestSelfEmploymentIncome:
    """Test calculations with self-employment income"""
    
    def test_business_income_triggers_se_tax(self):
        """Test that business income results in SE tax"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.set('income.business_income', 50000)
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.business_income == 50000
        assert result.total_income == 50000
        assert result.self_employment_tax > 0
        # Total tax includes both income tax and SE tax
        assert result.total_tax == result.income_tax + result.self_employment_tax
    
    def test_w2_plus_business_income(self):
        """Test combined W-2 and self-employment income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 40000, 'federal_withholding': 4000})
        tax_data.set('income.business_income', 20000)
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.total_wages == 40000
        assert result.business_income == 20000
        assert result.total_income == 60000
        assert result.self_employment_tax > 0  # SE tax on business income
        assert result.income_tax > 0  # Income tax on all income


class TestDeductions:
    """Test deduction calculations"""
    
    def test_standard_deduction_default(self):
        """Test that standard deduction is used by default"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 50000, 'federal_withholding': 5000})
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.standard_deduction == 15750.0
        assert result.deduction_used == 15750.0
    
    def test_itemized_deductions(self):
        """Test itemized deduction calculation"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 100000, 'federal_withholding': 10000})
        tax_data.set('deductions.method', 'itemized')
        tax_data.set('deductions.medical_expenses', 5000)
        tax_data.set('deductions.state_local_taxes', 10000)
        tax_data.set('deductions.mortgage_interest', 8000)
        tax_data.set('deductions.charitable_contributions', 3000)
        
        result = service.calculate_complete_return(tax_data)
        
        # Itemized total
        expected_itemized = 5000 + 10000 + 8000 + 3000
        assert result.itemized_deduction == expected_itemized
        assert result.deduction_used == expected_itemized


class TestPaymentsAndRefund:
    """Test payment and refund calculations"""
    
    def test_estimated_tax_payments(self):
        """Test estimated tax payments are included"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 50000, 'federal_withholding': 3000})
        tax_data.set('payments.estimated_tax', 2000)
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.federal_withholding == 3000
        assert result.estimated_tax_payments == 2000
        assert result.total_payments == 5000
    
    def test_refund_calculation(self):
        """Test refund is calculated correctly"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 30000, 'federal_withholding': 5000})
        
        result = service.calculate_complete_return(tax_data)
        
        # With lower income and high withholding, should get refund
        if result.total_payments > result.total_tax:
            assert result.refund_amount == result.total_payments - result.total_tax
            assert result.amount_owed == 0
    
    def test_amount_owed_calculation(self):
        """Test amount owed is calculated correctly"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 100000, 'federal_withholding': 1000})
        
        result = service.calculate_complete_return(tax_data)
        
        # With high income and low withholding, should owe
        if result.total_tax > result.total_payments:
            assert result.amount_owed == result.total_tax - result.total_payments
            assert result.refund_amount == 0


class TestServiceUtilityMethods:
    """Test service utility methods"""
    
    def test_get_effective_tax_rate(self):
        """Test effective tax rate calculation"""
        service = TaxCalculationService(tax_year=2025)
        
        result = TaxResult(
            adjusted_gross_income=100000,
            total_tax=15000
        )
        
        effective_rate = service.get_effective_tax_rate(result)
        assert effective_rate == 15.0  # 15%
    
    def test_get_effective_tax_rate_zero_agi(self):
        """Test effective tax rate with zero AGI"""
        service = TaxCalculationService(tax_year=2025)
        
        result = TaxResult(
            adjusted_gross_income=0,
            total_tax=0
        )
        
        effective_rate = service.get_effective_tax_rate(result)
        assert effective_rate == 0.0
    
    def test_get_marginal_tax_rate_single_low_income(self):
        """Test marginal tax rate for low income"""
        service = TaxCalculationService(tax_year=2025)
        
        # Income in 10% bracket
        marginal_rate = service.get_marginal_tax_rate(10000, 'Single')
        assert marginal_rate == 10.0
    
    def test_get_marginal_tax_rate_single_medium_income(self):
        """Test marginal tax rate for medium income"""
        service = TaxCalculationService(tax_year=2025)
        
        # Income in 22% bracket
        marginal_rate = service.get_marginal_tax_rate(50000, 'Single')
        assert marginal_rate == 22.0
    
    @pytest.mark.parametrize("filing_status", ['Single', 'MFJ', 'MFS', 'HOH', 'QW'])
    def test_get_marginal_tax_rate_all_statuses(self, filing_status):
        """Test marginal rate calculation for all filing statuses"""
        service = TaxCalculationService(tax_year=2025)
        
        marginal_rate = service.get_marginal_tax_rate(50000, filing_status)
        assert 0 < marginal_rate <= 37.0  # Valid tax rate range


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_no_income(self):
        """Test calculation with no income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.total_income == 0
        assert result.taxable_income == 0
        assert result.total_tax == 0
    
    def test_income_below_standard_deduction(self):
        """Test income below standard deduction results in zero taxable income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 10000, 'federal_withholding': 1000})
        
        result = service.calculate_complete_return(tax_data)
        
        # $10,000 - $15,750 = $0 (can't be negative)
        assert result.taxable_income == 0
        assert result.income_tax == 0
        # Should get full refund
        assert result.refund_amount == 1000
    
    def test_very_high_income(self):
        """Test calculation with very high income"""
        service = TaxCalculationService(tax_year=2025)
        
        tax_data = TaxData()
        tax_data.set('filing_status.status', 'Single')
        tax_data.add_w2_form({'wages': 1000000, 'federal_withholding': 300000})
        
        result = service.calculate_complete_return(tax_data)
        
        assert result.total_income == 1000000
        assert result.total_tax > 0
        # Should be in highest bracket
        marginal_rate = service.get_marginal_tax_rate(result.taxable_income, 'Single')
        assert marginal_rate == 37.0
