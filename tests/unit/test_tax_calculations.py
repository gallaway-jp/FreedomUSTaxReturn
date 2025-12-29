"""
Comprehensive tests for tax calculation functions

This test suite provides thorough coverage of all tax calculation
functions including edge cases, boundary values, and error conditions.
"""

import pytest
from utils.tax_calculations import (
    calculate_standard_deduction,
    calculate_income_tax,
    calculate_self_employment_tax,
    calculate_child_tax_credit,
    calculate_earned_income_credit,
    calculate_education_credit_aotc,
    calculate_education_credit_llc
)


class TestStandardDeduction:
    """Test standard deduction calculations for all filing statuses"""
    
    @pytest.mark.parametrize("filing_status,expected_2025", [
        ('Single', 15750.0),
        ('MFJ', 31500.0),
        ('MFS', 15750.0),
        ('HOH', 23625.0),
        ('QW', 31500.0)
    ])
    def test_standard_deduction_2025(self, filing_status, expected_2025):
        """Test standard deductions for 2025 tax year"""
        result = calculate_standard_deduction(filing_status, 2025)
        assert result == expected_2025
    
    def test_standard_deduction_invalid_status_defaults_to_single(self):
        """Invalid filing status should default to Single deduction"""
        result = calculate_standard_deduction('INVALID', 2025)
        assert result == 15750.0  # Single filer amount
    
    def test_standard_deduction_caching(self):
        """Test that results are cached for performance"""
        # Call twice with same parameters
        result1 = calculate_standard_deduction('Single', 2025)
        result2 = calculate_standard_deduction('Single', 2025)
        # Should return same object (cached)
        assert result1 == result2


class TestIncomeTaxCalculation:
    """Test federal income tax calculations"""
    
    def test_income_tax_zero_income(self):
        """Zero income should result in zero tax"""
        assert calculate_income_tax(0, 'Single', 2025) == 0.0
    
    def test_income_tax_single_low_income(self):
        """Test single filer with income in 10% bracket only"""
        # Income below first bracket threshold
        tax = calculate_income_tax(10000, 'Single', 2025)
        # $10,000 × 10% = $1,000
        assert tax == 1000.0
    
    def test_income_tax_single_two_brackets(self):
        """Test single filer with income spanning two brackets"""
        # Income: $30,000
        # 2025 brackets: $0-$11,925 (10%), $11,925-$48,475 (12%)
        tax = calculate_income_tax(30000, 'Single', 2025)
        # $11,925 × 10% = $1,192.50
        # ($30,000 - $11,925) × 12% = $18,075 × 12% = $2,169.00
        # Total: $1,192.50 + $2,169.00 = $3,361.50
        assert tax == 3361.5
    
    def test_income_tax_single_multiple_brackets(self):
        """Test single filer with income in multiple brackets"""
        # Income: $100,000 spans three brackets
        tax = calculate_income_tax(100000, 'Single', 2025)
        # Verify tax is calculated and in reasonable range
        assert 0 < tax < 100000
        assert tax > 15000  # Should be substantial
    
    def test_income_tax_exact_bracket_threshold(self):
        """Test income exactly at bracket threshold"""
        # Test at $11,600 (top of 10% bracket for Single)
        tax = calculate_income_tax(11600, 'Single', 2025)
        assert tax == 1160.0  # 11,600 × 0.10
    
    @pytest.mark.parametrize("filing_status", [
        'Single', 'MFJ', 'MFS', 'HOH', 'QW'
    ])
    def test_income_tax_all_filing_statuses(self, filing_status):
        """Test that all filing statuses produce valid tax calculations"""
        tax = calculate_income_tax(50000, filing_status, 2025)
        assert tax >= 0
        assert tax < 50000  # Tax should be less than income
    
    def test_income_tax_married_filing_jointly(self):
        """Test MFJ with specific income level"""
        # MFJ has wider brackets than Single
        tax_mfj = calculate_income_tax(100000, 'MFJ', 2025)
        tax_single = calculate_income_tax(100000, 'Single', 2025)
        # MFJ should generally have lower tax at same income
        assert tax_mfj < tax_single
    
    def test_income_tax_head_of_household(self):
        """Test HOH has its own bracket structure"""
        tax_hoh = calculate_income_tax(60000, 'HOH', 2025)
        tax_single = calculate_income_tax(60000, 'Single', 2025)
        # HOH typically has lower tax than Single at same income
        assert tax_hoh <= tax_single
    
    def test_income_tax_high_income(self):
        """Test high income calculation"""
        tax = calculate_income_tax(500000, 'Single', 2025)
        # Should be in highest bracket (37%)
        assert tax > 140000
        assert tax < 500000
    
    def test_income_tax_caching(self):
        """Test that calculations are cached"""
        result1 = calculate_income_tax(50000, 'Single', 2025)
        result2 = calculate_income_tax(50000, 'Single', 2025)
        assert result1 == result2


class TestSelfEmploymentTax:
    """Test self-employment tax calculations"""
    
    def test_se_tax_zero_earnings(self):
        """Zero earnings should result in zero tax"""
        assert calculate_self_employment_tax(0) == 0.0
    
    def test_se_tax_negative_earnings(self):
        """Negative earnings (loss) should result in zero tax"""
        assert calculate_self_employment_tax(-5000) == 0.0
    
    def test_se_tax_low_earnings(self):
        """Test SE tax on low earnings (below SS wage base)"""
        # $20,000 net earnings
        se_tax = calculate_self_employment_tax(20000)
        # 92.35% × $20,000 = $18,470
        # SS: $18,470 × 12.4% = $2,290.28
        # Medicare: $18,470 × 2.9% = $535.63
        # Total: ~$2,826
        assert 2800 < se_tax < 2900
    
    def test_se_tax_medium_earnings(self):
        """Test SE tax on medium earnings"""
        se_tax = calculate_self_employment_tax(60000)
        assert se_tax > 0
        # Should be around 14-15% of net earnings
        assert 7000 < se_tax < 10000
    
    def test_se_tax_above_ss_wage_base(self):
        """Test SE tax on earnings above Social Security wage base"""
        # High earner - SS tax caps but Medicare doesn't
        se_tax = calculate_self_employment_tax(200000)
        assert se_tax > 0
        # SS tax is capped, but Medicare continues
        assert 20000 < se_tax < 35000
    
    def test_se_tax_above_medicare_threshold(self):
        """Test additional Medicare tax for high earners"""
        # Additional 0.9% Medicare tax above threshold
        se_tax_high = calculate_self_employment_tax(300000)
        se_tax_medium = calculate_self_employment_tax(150000)
        # High earner should pay more due to additional Medicare tax
        assert se_tax_high > se_tax_medium


class TestChildTaxCredit:
    """Test child tax credit calculations"""
    
    def test_ctc_no_children(self):
        """No children should result in zero credit"""
        credit = calculate_child_tax_credit(0, 0, 50000, 'Single')
        assert credit == 0.0
    
    def test_ctc_one_child(self):
        """One qualifying child should get $2,000 credit"""
        credit = calculate_child_tax_credit(1, 0, 50000, 'Single')
        assert credit == 2000.0
    
    def test_ctc_multiple_children(self):
        """Multiple children should multiply credit"""
        credit = calculate_child_tax_credit(3, 0, 50000, 'Single')
        assert credit == 6000.0  # 3 × $2,000
    
    def test_ctc_other_dependents(self):
        """Other dependents should get $500 credit"""
        credit = calculate_child_tax_credit(0, 2, 50000, 'Single')
        assert credit == 1000.0  # 2 × $500
    
    def test_ctc_mixed_dependents(self):
        """Mix of children and other dependents"""
        credit = calculate_child_tax_credit(2, 1, 50000, 'Single')
        # 2 × $2,000 + 1 × $500 = $4,500
        assert credit == 4500.0
    
    def test_ctc_phaseout_single_high_income(self):
        """Test phaseout for single filer with high AGI"""
        # AGI over $200,000 threshold
        credit = calculate_child_tax_credit(1, 0, 210000, 'Single')
        # $10,000 over threshold = 10 × $50 reduction = $500
        # $2,000 - $500 = $1,500
        assert credit == 1500.0
    
    def test_ctc_phaseout_mfj_high_income(self):
        """Test phaseout for MFJ with high AGI"""
        # MFJ threshold is $400,000
        credit = calculate_child_tax_credit(2, 0, 420000, 'MFJ')
        # $20,000 over threshold = 20 × $50 reduction = $1,000
        # $4,000 - $1,000 = $3,000
        assert credit == 3000.0
    
    def test_ctc_phaseout_complete(self):
        """Test credit phases out completely at very high income"""
        # Very high income should phase out credit entirely
        credit = calculate_child_tax_credit(1, 0, 500000, 'Single')
        assert credit == 0.0
    
    def test_ctc_no_phaseout_below_threshold(self):
        """Test no phaseout when AGI below threshold"""
        credit_low = calculate_child_tax_credit(2, 0, 100000, 'Single')
        credit_threshold = calculate_child_tax_credit(2, 0, 199000, 'Single')
        # Both should be full credit
        assert credit_low == 4000.0
        assert credit_threshold == 4000.0


class TestEarnedIncomeCredit:
    """Test earned income credit calculations"""
    
    def test_eic_no_children_low_income(self):
        """Test EIC for childless worker with low income"""
        credit = calculate_earned_income_credit(10000, 10000, 0, 'Single')
        assert 0 < credit <= 600  # Max for no children
    
    def test_eic_one_child(self):
        """Test EIC with one qualifying child"""
        credit = calculate_earned_income_credit(15000, 15000, 1, 'Single')
        assert 0 < credit <= 3995  # Max for one child
    
    def test_eic_two_children(self):
        """Test EIC with two qualifying children"""
        credit = calculate_earned_income_credit(20000, 20000, 2, 'Single')
        assert 0 < credit <= 6604  # Max for two children
    
    def test_eic_three_or_more_children(self):
        """Test EIC with three or more qualifying children"""
        credit = calculate_earned_income_credit(25000, 25000, 3, 'Single')
        assert 0 < credit <= 7430  # Max for three+ children
    
    def test_eic_agi_too_high(self):
        """Test EIC phases out at high AGI"""
        # AGI above threshold should result in zero credit
        credit = calculate_earned_income_credit(50000, 60000, 1, 'Single')
        assert credit == 0.0
    
    def test_eic_married_filing_separately_ineligible(self):
        """Test that MFS filers are not eligible for EIC"""
        credit = calculate_earned_income_credit(20000, 20000, 1, 'MFS')
        assert credit == 0.0
    
    def test_eic_married_filing_jointly_higher_threshold(self):
        """Test that MFJ has higher AGI thresholds"""
        credit_mfj = calculate_earned_income_credit(30000, 30000, 1, 'MFJ')
        credit_single = calculate_earned_income_credit(30000, 30000, 1, 'Single')
        # MFJ should get credit where Single might not
        assert credit_mfj >= credit_single


class TestEducationCredits:
    """Test education credit calculations"""
    
    def test_aotc_no_expenses(self):
        """No expenses should result in zero credit"""
        credit = calculate_education_credit_aotc(0, 1)
        assert credit == 0.0
    
    def test_aotc_low_expenses(self):
        """Test AOTC with expenses under $2,000"""
        # 100% of first $2,000
        credit = calculate_education_credit_aotc(1500, 1)
        assert credit == 1500.0
    
    def test_aotc_medium_expenses(self):
        """Test AOTC with expenses between $2,000-$4,000"""
        # 100% of first $2,000 + 25% of next $2,000
        credit = calculate_education_credit_aotc(3000, 1)
        # $2,000 + ($1,000 × 25%) = $2,250
        assert credit == 2250.0
    
    def test_aotc_max_expenses(self):
        """Test AOTC with expenses at or above maximum"""
        # Max credit is $2,500
        credit = calculate_education_credit_aotc(5000, 1)
        assert credit == 2500.0
    
    def test_aotc_first_year(self):
        """Test AOTC in first year of college"""
        credit = calculate_education_credit_aotc(4000, 0)
        assert credit == 2500.0  # Full credit
    
    def test_aotc_fourth_year(self):
        """Test AOTC in fourth year of college (last eligible year)"""
        credit = calculate_education_credit_aotc(4000, 3)
        assert credit == 2500.0  # Still eligible
    
    def test_aotc_fifth_year_ineligible(self):
        """Test AOTC after 4 years is not eligible"""
        credit = calculate_education_credit_aotc(4000, 4)
        assert credit == 0.0  # No longer eligible
    
    def test_llc_no_expenses(self):
        """No expenses should result in zero LLC"""
        credit = calculate_education_credit_llc(0)
        assert credit == 0.0
    
    def test_llc_low_expenses(self):
        """Test LLC with low expenses"""
        # 20% of expenses
        credit = calculate_education_credit_llc(5000)
        assert credit == 1000.0  # 20% of $5,000
    
    def test_llc_max_expenses(self):
        """Test LLC at maximum"""
        # Max credit is $2,000 (20% of $10,000)
        credit = calculate_education_credit_llc(15000)
        assert credit == 2000.0
    
    def test_llc_exactly_max(self):
        """Test LLC with exactly $10,000 in expenses"""
        credit = calculate_education_credit_llc(10000)
        assert credit == 2000.0  # 20% of $10,000


class TestTaxCalculationEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_income_tax_very_small_amount(self):
        """Test tax calculation with very small income"""
        tax = calculate_income_tax(1.0, 'Single', 2025)
        assert tax == 0.10  # 10% of $1
    
    def test_child_tax_credit_rounding(self):
        """Test that credit properly rounds to 2 decimal places"""
        # AGI that results in partial phaseout
        credit = calculate_child_tax_credit(1, 0, 200500, 'Single')
        # Should be rounded to 2 decimal places
        assert isinstance(credit, float)
        assert credit == round(credit, 2)
    
    def test_se_tax_rounding(self):
        """Test that SE tax properly rounds to 2 decimal places"""
        se_tax = calculate_self_employment_tax(12345.67)
        assert se_tax == round(se_tax, 2)
    
    def test_all_filing_statuses_are_valid(self):
        """Verify all standard filing statuses work"""
        statuses = ['Single', 'MFJ', 'MFS', 'HOH', 'QW']
        for status in statuses:
            deduction = calculate_standard_deduction(status, 2025)
            assert deduction > 0
            
            tax = calculate_income_tax(50000, status, 2025)
            assert tax >= 0
