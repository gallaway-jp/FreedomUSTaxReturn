"""
Property-based tests for tax calculations using Hypothesis.

These tests generate random valid inputs to verify mathematical properties
and invariants of tax calculations.
"""
import pytest
from hypothesis import given, strategies as st, assume
from decimal import Decimal
from utils.tax_calculations import (
    calculate_standard_deduction,
    calculate_income_tax,
    calculate_earned_income_credit,
    calculate_child_tax_credit,
    calculate_self_employment_tax
)


# Custom strategies for tax data
@st.composite
def filing_status_strategy(draw):
    """Generate valid filing status."""
    return draw(st.sampled_from(['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household']))


@st.composite
def positive_income_strategy(draw):
    """Generate realistic positive income (0 to 10 million)."""
    return draw(st.integers(min_value=0, max_value=10_000_000))


@st.composite
def child_count_strategy(draw):
    """Generate realistic number of children (0 to 10)."""
    return draw(st.integers(min_value=0, max_value=10))


class TestStandardDeductionProperties:
    """Property-based tests for standard deduction calculation."""
    
    @given(filing_status=filing_status_strategy())
    def test_standard_deduction_is_positive(self, filing_status):
        """Property: Standard deduction is always positive."""
        deduction = calculate_standard_deduction(filing_status=filing_status)
        assert deduction > 0
    
    @given(filing_status=filing_status_strategy())
    def test_standard_deduction_has_expected_range(self, filing_status):
        """Property: Standard deduction falls within expected range for 2025."""
        deduction = calculate_standard_deduction(filing_status=filing_status)
        # 2025 deductions range from ~$15k (single) to ~$30k (MFJ)
        assert 10_000 <= deduction <= 35_000
    
    def test_mfj_deduction_at_least_single(self):
        """Property: MFJ deduction is at least as much as single."""
        single_deduction = calculate_standard_deduction(filing_status='single')
        mfj_deduction = calculate_standard_deduction(filing_status='married_filing_jointly')
        assert mfj_deduction >= single_deduction
    
    def test_deduction_consistency_across_years(self):
        """Property: Deductions are consistent for same filing status and year."""
        deduction1 = calculate_standard_deduction(filing_status='single', tax_year=2025)
        deduction2 = calculate_standard_deduction(filing_status='single', tax_year=2025)
        assert deduction1 == deduction2


class TestIncomeTaxProperties:
    """Property-based tests for income tax calculation."""
    
    @given(
        taxable_income=positive_income_strategy(),
        filing_status=filing_status_strategy()
    )
    def test_income_tax_not_negative(self, taxable_income, filing_status):
        """Property: Income tax is never negative."""
        tax = calculate_income_tax(taxable_income, filing_status)
        assert tax >= 0
    
    @given(
        taxable_income=positive_income_strategy(),
        filing_status=filing_status_strategy()
    )
    def test_income_tax_not_greater_than_income(self, taxable_income, filing_status):
        """Property: Income tax cannot exceed taxable income."""
        tax = calculate_income_tax(taxable_income, filing_status)
        assert tax <= taxable_income
    
    @given(
        income1=positive_income_strategy(),
        income2=positive_income_strategy(),
        filing_status=filing_status_strategy()
    )
    def test_income_tax_monotonic_increasing(self, income1, income2, filing_status):
        """Property: Higher income results in equal or higher tax (monotonicity)."""
        assume(income1 != income2)
        
        tax1 = calculate_income_tax(income1, filing_status)
        tax2 = calculate_income_tax(income2, filing_status)
        
        if income1 < income2:
            assert tax1 <= tax2
        else:
            assert tax1 >= tax2
    
    @given(filing_status=filing_status_strategy())
    def test_zero_income_zero_tax(self, filing_status):
        """Property: Zero taxable income results in zero tax."""
        tax = calculate_income_tax(0, filing_status)
        assert tax == 0
    
    @given(
        taxable_income=st.integers(min_value=1, max_value=1_000_000),
        filing_status=filing_status_strategy()
    )
    def test_average_tax_rate_bounded(self, taxable_income, filing_status):
        """Property: Average tax rate is between 0% and 37% (max bracket)."""
        tax = calculate_income_tax(taxable_income, filing_status)
        average_rate = (tax / taxable_income) * 100
        assert 0 <= average_rate <= 37


class TestEITCProperties:
    """Property-based tests for Earned Income Tax Credit."""
    
    @given(
        earned_income=positive_income_strategy(),
        agi=positive_income_strategy(),
        filing_status=filing_status_strategy(),
        num_children=child_count_strategy()
    )
    def test_eitc_not_negative(self, earned_income, agi, filing_status, num_children):
        """Property: EITC is never negative."""
        eitc = calculate_earned_income_credit(
            earned_income=earned_income,
            agi=agi,
            num_children=num_children,
            filing_status=filing_status
        )
        assert eitc >= 0
    
    @given(
        earned_income=st.integers(min_value=0, max_value=100),
        filing_status=filing_status_strategy(),
        num_children=child_count_strategy()
    )
    def test_eitc_zero_for_very_low_income(self, earned_income, filing_status, num_children):
        """Property: Very low income (< $100) typically results in minimal EITC."""
        eitc = calculate_earned_income_credit(
            earned_income=earned_income,
            agi=earned_income,
            num_children=num_children,
            filing_status=filing_status
        )
        # EITC should be relatively small for very low income
        assert eitc < 1000
    
    @given(
        income=st.integers(min_value=100_000, max_value=10_000_000),
        filing_status=filing_status_strategy(),
        num_children=child_count_strategy()
    )
    def test_eitc_zero_for_high_income(self, income, filing_status, num_children):
        """Property: High income results in zero EITC (phases out)."""
        eitc = calculate_earned_income_credit(
            earned_income=income,
            agi=income,
            num_children=num_children,
            filing_status=filing_status
        )
        assert eitc == 0
    
    @given(
        income=st.integers(min_value=10_000, max_value=50_000),
        filing_status=filing_status_strategy()
    )
    def test_eitc_higher_with_children(self, income, filing_status):
        """Property: EITC with children >= EITC without children."""
        eitc_no_children = calculate_earned_income_credit(
            earned_income=income,
            agi=income,
            num_children=0,
            filing_status=filing_status
        )
        
        eitc_with_children = calculate_earned_income_credit(
            earned_income=income,
            agi=income,
            num_children=2,
            filing_status=filing_status
        )
        
        assert eitc_with_children >= eitc_no_children


class TestChildTaxCreditProperties:
    """Property-based tests for Child Tax Credit."""
    
    @given(
        num_qualifying_children=child_count_strategy(),
        num_other_dependents=child_count_strategy(),
        agi=positive_income_strategy(),
        filing_status=filing_status_strategy()
    )
    def test_ctc_not_negative(self, num_qualifying_children, num_other_dependents, agi, filing_status):
        """Property: Child Tax Credit is never negative."""
        ctc = calculate_child_tax_credit(
            num_qualifying_children=num_qualifying_children,
            num_other_dependents=num_other_dependents,
            agi=agi,
            filing_status=filing_status
        )
        assert ctc >= 0
    
    @given(
        agi=positive_income_strategy(),
        filing_status=filing_status_strategy()
    )
    def test_ctc_zero_without_dependents(self, agi, filing_status):
        """Property: No dependents means no Child Tax Credit."""
        ctc = calculate_child_tax_credit(
            num_qualifying_children=0,
            num_other_dependents=0,
            agi=agi,
            filing_status=filing_status
        )
        assert ctc == 0
    
    @given(
        num_children=st.integers(min_value=1, max_value=10),
        agi=st.integers(min_value=0, max_value=100_000),
        filing_status=filing_status_strategy()
    )
    def test_ctc_increases_with_children(self, num_children, agi, filing_status):
        """Property: More children means more credit (before phaseout)."""
        assume(num_children >= 2)
        
        ctc_fewer = calculate_child_tax_credit(
            num_qualifying_children=num_children - 1,
            num_other_dependents=0,
            agi=agi,
            filing_status=filing_status
        )
        
        ctc_more = calculate_child_tax_credit(
            num_qualifying_children=num_children,
            num_other_dependents=0,
            agi=agi,
            filing_status=filing_status
        )
        
        assert ctc_more >= ctc_fewer
    
    @given(
        num_children=st.integers(min_value=1, max_value=5),
        filing_status=filing_status_strategy()
    )
    def test_ctc_bounded_per_child(self, num_children, filing_status):
        """Property: CTC is bounded by $2000 per child."""
        # Test at low income (no phaseout)
        ctc = calculate_child_tax_credit(
            num_qualifying_children=num_children,
            num_other_dependents=0,
            agi=50_000,
            filing_status=filing_status
        )
        
        max_credit = num_children * 2000
        assert ctc <= max_credit


class TestSelfEmploymentTaxProperties:
    """Property-based tests for self-employment tax."""
    
    @given(net_earnings=st.integers(min_value=0, max_value=500_000))
    def test_se_tax_not_negative(self, net_earnings):
        """Property: SE tax is never negative."""
        se_tax = calculate_self_employment_tax(net_earnings)
        assert se_tax >= 0
    
    @given(net_earnings=st.integers(min_value=0, max_value=500_000))
    def test_se_tax_not_exceeds_earnings(self, net_earnings):
        """Property: SE tax should not exceed net earnings."""
        se_tax = calculate_self_employment_tax(net_earnings)
        assert se_tax <= net_earnings
    
    def test_se_tax_zero_for_zero_earnings(self):
        """Property: Zero earnings means zero SE tax."""
        se_tax = calculate_self_employment_tax(0)
        assert se_tax == 0
    
    @given(
        earnings1=st.integers(min_value=0, max_value=500_000),
        earnings2=st.integers(min_value=0, max_value=500_000)
    )
    def test_se_tax_monotonic(self, earnings1, earnings2):
        """Property: Higher earnings means higher or equal SE tax."""
        assume(earnings1 != earnings2)
        
        se_tax1 = calculate_self_employment_tax(earnings1)
        se_tax2 = calculate_self_employment_tax(earnings2)
        
        if earnings1 < earnings2:
            assert se_tax1 <= se_tax2
        else:
            assert se_tax1 >= se_tax2


class TestTaxCalculationInvariants:
    """Test invariants across multiple tax calculations."""
    
    @given(
        income=positive_income_strategy(),
        filing_status=filing_status_strategy()
    )
    def test_total_tax_components_consistent(self, income, filing_status):
        """Property: Tax components combine consistently."""
        # Calculate taxable income
        deduction = calculate_standard_deduction(filing_status=filing_status)
        taxable = max(0, income - deduction)
        
        # Calculate income tax
        income_tax = calculate_income_tax(taxable, filing_status)
        
        # Tax should be non-negative and numeric
        assert income_tax >= 0
        assert isinstance(income_tax, (int, float, Decimal))
    
    @given(
        income=st.integers(min_value=10_000, max_value=999_999),
        filing_status=filing_status_strategy()
    )
    def test_marginal_rate_effect(self, income, filing_status):
        """Property: $1 more income results in <= $0.37 more tax (max marginal rate)."""
        # Calculate taxable income for both amounts
        deduction = calculate_standard_deduction(filing_status=filing_status)
        taxable1 = max(0, income - deduction)
        taxable2 = max(0, (income + 1) - deduction)
        
        tax1 = calculate_income_tax(taxable1, filing_status)
        tax2 = calculate_income_tax(taxable2, filing_status)
        
        # Tax increase should not exceed 37 cents (max marginal rate)
        # Add small epsilon for floating-point precision
        tax_increase = tax2 - tax1
        assert 0 <= tax_increase <= 0.37 + 0.01  # Allow 1 cent tolerance for FP errors
