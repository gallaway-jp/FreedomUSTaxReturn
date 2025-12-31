"""
Unit tests for State Tax Service
"""
import pytest
from services.state_tax_service import (
    StateTaxService, StateCode, StateTaxCalculation, StateTaxInfo
)


class TestStateTaxService:
    """Test StateTaxService functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = StateTaxService()

    def test_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert len(self.service.get_supported_states()) > 0

    def test_get_supported_states(self):
        """Test getting supported states"""
        states = self.service.get_supported_states()
        assert isinstance(states, list)
        assert len(states) > 0
        assert StateCode.CA in states  # California should be supported

    def test_get_state_info(self):
        """Test getting state information"""
        ca_info = self.service.get_state_info(StateCode.CA)
        assert ca_info is not None
        assert ca_info.name == "California"
        assert ca_info.has_income_tax is True
        assert len(ca_info.tax_rates) > 0

        # Test no income tax state
        tx_info = self.service.get_state_info(StateCode.TX)
        assert tx_info is not None
        assert tx_info.name == "Texas"
        assert tx_info.has_income_tax is False

    def test_calculate_state_tax_california(self):
        """Test California state tax calculation"""
        calculation = self.service.calculate_state_tax(
            StateCode.CA, 100000, "single", 0
        )

        assert isinstance(calculation, StateTaxCalculation)
        assert calculation.state_code == StateCode.CA
        assert calculation.taxable_income > 0
        assert calculation.tax_owed > 0
        assert calculation.effective_rate > 0

    def test_calculate_state_tax_no_income_tax(self):
        """Test state with no income tax"""
        calculation = self.service.calculate_state_tax(
            StateCode.TX, 100000, "single", 0
        )

        assert calculation.tax_owed == 0.0
        assert calculation.effective_rate == 0.0

    def test_calculate_multi_state_tax(self):
        """Test multi-state tax calculation"""
        states = [StateCode.CA, StateCode.NY, StateCode.TX]
        calculations = self.service.calculate_multi_state_tax(
            states, 100000, "single", 0
        )

        assert len(calculations) == 3
        assert StateCode.CA in calculations
        assert StateCode.NY in calculations
        assert StateCode.TX in calculations

        # California and New York should have tax, Texas should not
        assert calculations[StateCode.CA].tax_owed > 0
        assert calculations[StateCode.NY].tax_owed > 0
        assert calculations[StateCode.TX].tax_owed == 0

    def test_get_state_tax_forms(self):
        """Test getting state tax forms"""
        ca_forms = self.service.get_state_tax_forms(StateCode.CA)
        assert isinstance(ca_forms, list)
        assert len(ca_forms) > 0

        ny_forms = self.service.get_state_tax_forms(StateCode.NY)
        assert isinstance(ny_forms, list)
        assert len(ny_forms) > 0

    def test_tax_brackets_california(self):
        """Test California progressive tax brackets"""
        # Test low income
        calc_low = self.service.calculate_state_tax(StateCode.CA, 20000, "single", 0)
        assert calc_low.tax_owed > 0

        # Test high income
        calc_high = self.service.calculate_state_tax(StateCode.CA, 500000, "single", 0)
        assert calc_high.tax_owed > calc_low.tax_owed

        # Test very high income (highest bracket)
        calc_very_high = self.service.calculate_state_tax(StateCode.CA, 2000000, "single", 0)
        assert calc_very_high.tax_owed > calc_high.tax_owed

    def test_filing_status_differences(self):
        """Test tax differences by filing status"""
        income = 100000

        single_calc = self.service.calculate_state_tax(StateCode.CA, income, "single", 0)
        married_calc = self.service.calculate_state_tax(StateCode.CA, income, "married_joint", 0)

        # Married filing jointly should generally have lower effective rate
        # (This might not always be true due to standard deductions, but test the logic)
        assert single_calc.taxable_income >= married_calc.taxable_income

    def test_unsupported_state(self):
        """Test handling of unsupported state"""
        with pytest.raises(ValueError):
            # This should fail since we're not initializing all states
            self.service.calculate_state_tax(StateCode.DC, 100000, "single", 0)

    def test_zero_income(self):
        """Test tax calculation with zero income"""
        calculation = self.service.calculate_state_tax(StateCode.CA, 0, "single", 0)
        assert calculation.tax_owed == 0.0
        assert calculation.effective_rate == 0.0

    def test_credits_and_deductions(self):
        """Test tax calculation with credits and deductions"""
        base_calc = self.service.calculate_state_tax(StateCode.CA, 100000, "single", 0)

        # This is a simplified test - in real implementation, we'd pass credits/deductions
        # For now, just verify the calculation completes
        assert base_calc.tax_owed > 0