"""
Unit tests for State Tax Integration Service

Tests cover:
- State tax data loading and management
- Tax calculations for different state types (progressive, flat, no tax)
- Multi-state return handling
- Tax form generation and validation
- State-specific tax rules and deadlines
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from services.state_tax_integration_service import (
    StateTaxIntegrationService,
    StateCode,
    FilingStatus,
    StateTaxType,
    StateTaxInfo,
    StateTaxBracket,
    StateIncome,
    StateDeductions,
    StateTaxCalculation,
    StateTaxReturn
)
from config.app_config import AppConfig
from services.encryption_service import EncryptionService


class TestStateTaxIntegrationService(unittest.TestCase):
    """Test cases for StateTaxIntegrationService"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = AppConfig.from_env()
        self.encryption = EncryptionService(self.config.key_file)
        self.service = StateTaxIntegrationService(self.config, self.encryption)

        # Test data
        self.test_tax_year = 2024
        self.test_income = StateIncome(
            wages=75000,
            interest=2000,
            dividends=5000,
            capital_gains=10000,
            business_income=25000
        )
        self.test_deductions = StateDeductions(
            standard_deduction=13850,  # Federal standard deduction for single filer
            personal_exemption=0,  # Most states don't have personal exemptions
            dependent_exemptions=0
        )

    def test_initialization(self):
        """Test service initialization"""
        self.assertIsInstance(self.service.state_tax_info, dict)
        self.assertIsInstance(self.service.tax_returns, dict)
        self.assertIsNotNone(self.service.config)
        self.assertIsNotNone(self.service.encryption)

    def test_get_state_tax_info(self):
        """Test retrieving state tax information"""
        # Test existing state
        ca_info = self.service.get_state_tax_info(StateCode.CA)
        self.assertIsNotNone(ca_info)
        self.assertEqual(ca_info.state_code, StateCode.CA)
        self.assertEqual(ca_info.state_name, "California")
        self.assertEqual(ca_info.tax_type, StateTaxType.PROGRESSIVE)

        # Test non-existent state
        nonexistent_info = self.service.get_state_tax_info(StateCode.AS)
        self.assertIsNone(nonexistent_info)

    def test_get_all_states(self):
        """Test retrieving all states"""
        states = self.service.get_all_states()
        self.assertGreater(len(states), 0)

        # Verify structure
        for state in states:
            self.assertIsInstance(state, StateTaxInfo)
            self.assertIsInstance(state.state_code, StateCode)
            self.assertIsNotNone(state.state_name)

    def test_calculate_no_income_tax_state(self):
        """Test tax calculation for states with no income tax"""
        calculation = self.service.calculate_state_tax(
            StateCode.TX, self.test_tax_year, FilingStatus.SINGLE,
            self.test_income, self.test_deductions
        )

        self.assertEqual(calculation.state_code, StateCode.TX)
        self.assertEqual(calculation.tax_year, self.test_tax_year)
        self.assertEqual(calculation.tax_amount, 0.0)
        self.assertEqual(calculation.effective_rate, 0.0)
        self.assertEqual(calculation.marginal_rate, 0.0)
        self.assertEqual(calculation.net_tax_owed, 0.0)

    def test_calculate_flat_tax_state(self):
        """Test tax calculation for flat tax states"""
        calculation = self.service.calculate_state_tax(
            StateCode.IL, self.test_tax_year, FilingStatus.SINGLE,
            self.test_income, self.test_deductions
        )

        self.assertEqual(calculation.state_code, StateCode.IL)
        self.assertGreater(calculation.tax_amount, 0)
        self.assertEqual(calculation.marginal_rate, 0.0495)  # Illinois flat rate

        # Verify calculation: taxable_income * flat_rate
        expected_taxable = self.test_income.total_income - self.test_deductions.total_deductions
        expected_tax = expected_taxable * 0.0495
        self.assertAlmostEqual(calculation.tax_amount, expected_tax, places=2)

    def test_calculate_progressive_tax_state(self):
        """Test tax calculation for progressive tax states"""
        calculation = self.service.calculate_state_tax(
            StateCode.CA, self.test_tax_year, FilingStatus.SINGLE,
            self.test_income, self.test_deductions
        )

        self.assertEqual(calculation.state_code, StateCode.CA)
        self.assertGreater(calculation.tax_amount, 0)
        self.assertGreater(calculation.effective_rate, 0)
        self.assertGreater(calculation.marginal_rate, 0)

        # Verify breakdown exists
        self.assertGreater(len(calculation.breakdown), 0)

        # Verify total tax equals sum of breakdown
        total_from_breakdown = sum(calculation.breakdown.values())
        self.assertAlmostEqual(calculation.tax_amount, total_from_breakdown, places=2)

    def test_calculate_with_credits(self):
        """Test tax calculation with tax credits"""
        credits = 1000.0

        calculation = self.service.calculate_state_tax(
            StateCode.CA, self.test_tax_year, FilingStatus.SINGLE,
            self.test_income, self.test_deductions, credits
        )

        self.assertEqual(calculation.credits, credits)
        self.assertEqual(calculation.net_tax_owed, max(0, calculation.tax_amount - credits))

    def test_calculate_negative_taxable_income(self):
        """Test tax calculation with negative taxable income"""
        # Create deductions that exceed income
        large_deductions = StateDeductions(
            standard_deduction=200000,  # Much larger than income
            personal_exemption=0,
            dependent_exemptions=0
        )

        calculation = self.service.calculate_state_tax(
            StateCode.CA, self.test_tax_year, FilingStatus.SINGLE,
            self.test_income, large_deductions
        )

        self.assertEqual(calculation.taxable_income, 0.0)
        self.assertEqual(calculation.tax_amount, 0.0)
        self.assertEqual(calculation.net_tax_owed, 0.0)

    def test_create_state_tax_return(self):
        """Test creating a state tax return"""
        taxpayer_info = {
            "taxpayer_id": "test_123",
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789"
        }

        return_id = self.service.create_state_tax_return(
            StateCode.CA, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, self.test_income, self.test_deductions
        )

        self.assertIsNotNone(return_id)
        self.assertIn(return_id, self.service.tax_returns)

        # Verify return data
        tax_return = self.service.get_state_tax_return(return_id)
        self.assertIsNotNone(tax_return)
        self.assertEqual(tax_return.state_code, StateCode.CA)
        self.assertEqual(tax_return.tax_year, self.test_tax_year)
        self.assertEqual(tax_return.filing_status, FilingStatus.SINGLE)
        self.assertEqual(tax_return.status, "draft")

    def test_get_state_tax_return(self):
        """Test retrieving a state tax return"""
        # Create a return first
        taxpayer_info = {"taxpayer_id": "test_123"}
        return_id = self.service.create_state_tax_return(
            StateCode.NY, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, self.test_income, self.test_deductions
        )

        # Retrieve it
        tax_return = self.service.get_state_tax_return(return_id)
        self.assertIsNotNone(tax_return)
        self.assertEqual(tax_return.return_id, return_id)

        # Test non-existent return
        nonexistent = self.service.get_state_tax_return("nonexistent")
        self.assertIsNone(nonexistent)

    def test_get_state_returns_for_taxpayer(self):
        """Test retrieving returns for a specific taxpayer"""
        taxpayer_id = "test_taxpayer_123"

        # Create multiple returns for same taxpayer
        taxpayer_info = {"taxpayer_id": taxpayer_id}

        return_id1 = self.service.create_state_tax_return(
            StateCode.CA, 2024, taxpayer_info, FilingStatus.SINGLE,
            self.test_income, self.test_deductions
        )

        return_id2 = self.service.create_state_tax_return(
            StateCode.NY, 2024, taxpayer_info, FilingStatus.SINGLE,
            self.test_income, self.test_deductions
        )

        # Retrieve returns
        returns = self.service.get_state_returns_for_taxpayer(taxpayer_id)
        self.assertEqual(len(returns), 2)

        return_ids = [r.return_id for r in returns]
        self.assertIn(return_id1, return_ids)
        self.assertIn(return_id2, return_ids)

        # Test with specific tax year
        returns_2024 = self.service.get_state_returns_for_taxpayer(taxpayer_id, 2024)
        self.assertEqual(len(returns_2024), 2)

        returns_2023 = self.service.get_state_returns_for_taxpayer(taxpayer_id, 2023)
        self.assertEqual(len(returns_2023), 0)

    def test_update_state_tax_return(self):
        """Test updating a state tax return"""
        # Create a return
        taxpayer_info = {"taxpayer_id": "test_123"}
        return_id = self.service.create_state_tax_return(
            StateCode.CA, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, self.test_income, self.test_deductions
        )

        # Update it
        updates = {"status": "filed", "amount_due": 1500.50}
        success = self.service.update_state_tax_return(return_id, updates)

        self.assertTrue(success)

        # Verify updates
        tax_return = self.service.get_state_tax_return(return_id)
        self.assertEqual(tax_return.status, "filed")
        self.assertEqual(tax_return.amount_due, 1500.50)
        self.assertIsNotNone(tax_return.updated_at)

    def test_delete_state_tax_return(self):
        """Test deleting a state tax return"""
        # Create a return
        taxpayer_info = {"taxpayer_id": "test_123"}
        return_id = self.service.create_state_tax_return(
            StateCode.CA, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, self.test_income, self.test_deductions
        )

        # Delete it
        success = self.service.delete_state_tax_return(return_id)
        self.assertTrue(success)

        # Verify it's gone
        tax_return = self.service.get_state_tax_return(return_id)
        self.assertIsNone(tax_return)

        # Try to delete non-existent return
        success = self.service.delete_state_tax_return("nonexistent")
        self.assertFalse(success)

    def test_generate_state_tax_form(self):
        """Test generating state tax form data"""
        # Create a return
        taxpayer_info = {
            "taxpayer_id": "test_123",
            "first_name": "John",
            "last_name": "Doe"
        }
        return_id = self.service.create_state_tax_return(
            StateCode.CA, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, self.test_income, self.test_deductions
        )

        # Generate form
        form_data = self.service.generate_state_tax_form(return_id, "1040")

        # Verify form structure
        self.assertEqual(form_data["form_type"], "CA 1040")
        self.assertEqual(form_data["tax_year"], self.test_tax_year)
        self.assertEqual(form_data["taxpayer_info"], taxpayer_info)
        self.assertEqual(form_data["filing_status"], "single")
        self.assertIn("income", form_data)
        self.assertIn("tax_calculation", form_data)
        self.assertIn("generated_at", form_data)

    def test_generate_form_nonexistent_return(self):
        """Test generating form for non-existent return"""
        with self.assertRaises(ValueError):
            self.service.generate_state_tax_form("nonexistent")

    def test_validate_state_tax_return(self):
        """Test validating a state tax return"""
        # Create a valid return
        taxpayer_info = {"taxpayer_id": "test_123"}
        return_id = self.service.create_state_tax_return(
            StateCode.CA, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, self.test_income, self.test_deductions
        )

        # Validate it
        errors = self.service.validate_state_tax_return(return_id)
        self.assertEqual(len(errors), 0)  # Should be valid

    def test_validate_nonexistent_return(self):
        """Test validating non-existent return"""
        errors = self.service.validate_state_tax_return("nonexistent")
        self.assertEqual(len(errors), 1)
        self.assertIn("Tax return not found", errors[0])

    def test_validate_no_income_tax_state_with_tax(self):
        """Test validation for no-income-tax states"""
        # Create income for Texas (no income tax)
        tx_income = StateIncome(wages=50000)
        tx_deductions = StateDeductions(standard_deduction=13850)

        # Create return with calculated tax (should be 0 for TX)
        taxpayer_info = {"taxpayer_id": "test_123"}
        return_id = self.service.create_state_tax_return(
            StateCode.TX, self.test_tax_year, taxpayer_info,
            FilingStatus.SINGLE, tx_income, tx_deductions
        )

        # Manually set a tax amount (simulating error)
        tax_return = self.service.get_state_tax_return(return_id)
        tax_return.calculation.net_tax_owed = 1000.0  # This should not happen for TX

        # Validate
        errors = self.service.validate_state_tax_return(return_id)
        self.assertGreater(len(errors), 0)  # Should have validation errors

    def test_get_state_tax_deadlines(self):
        """Test retrieving tax deadlines for all states"""
        deadlines = self.service.get_state_tax_deadlines(self.test_tax_year)

        self.assertIsInstance(deadlines, dict)
        self.assertGreater(len(deadlines), 0)

        # Check some known deadlines
        self.assertIn("CA", deadlines)
        self.assertIn("TX", deadlines)
        self.assertEqual(deadlines["TX"], "N/A")  # No income tax

    def test_get_states_by_tax_type(self):
        """Test filtering states by tax type"""
        # Get progressive tax states
        progressive_states = self.service.get_states_by_tax_type(StateTaxType.PROGRESSIVE)
        self.assertGreater(len(progressive_states), 0)

        for state in progressive_states:
            self.assertEqual(state.tax_type, StateTaxType.PROGRESSIVE)

        # Get no-income-tax states
        no_tax_states = self.service.get_states_by_tax_type(StateTaxType.NO_INCOME_TAX)
        self.assertGreater(len(no_tax_states), 0)

        for state in no_tax_states:
            self.assertEqual(state.tax_type, StateTaxType.NO_INCOME_TAX)

        # Get flat tax states
        flat_tax_states = self.service.get_states_by_tax_type(StateTaxType.FLAT)
        self.assertGreater(len(flat_tax_states), 0)

        for state in flat_tax_states:
            self.assertEqual(state.tax_type, StateTaxType.FLAT)

    def test_calculate_multi_state_tax(self):
        """Test calculating tax for multiple states"""
        states = [StateCode.CA, StateCode.TX, StateCode.FL]

        results = self.service.calculate_multi_state_tax(
            states, self.test_tax_year, FilingStatus.SINGLE,
            self.test_income, self.test_deductions
        )

        self.assertEqual(len(results), 3)
        self.assertIn("CA", results)
        self.assertIn("TX", results)
        self.assertIn("FL", results)

        # California should have tax
        ca_result = results["CA"]
        self.assertGreater(ca_result.tax_amount, 0)

        # Texas and Florida should have no tax
        tx_result = results["TX"]
        fl_result = results["FL"]
        self.assertEqual(tx_result.tax_amount, 0)
        self.assertEqual(fl_result.tax_amount, 0)

    def test_progressive_tax_calculation_logic(self):
        """Test detailed progressive tax calculation logic"""
        # Test with California brackets
        ca_info = self.service.get_state_tax_info(StateCode.CA)

        # Test income in first bracket only
        low_income = StateIncome(wages=6000)  # Increased to ensure positive taxable income
        low_deductions = StateDeductions(standard_deduction=5202)  # CA standard deduction

        calc = self.service.calculate_state_tax(
            StateCode.CA, self.test_tax_year, FilingStatus.SINGLE,
            low_income, low_deductions
        )

        # Should be in lowest bracket (1% on small positive amount)
        self.assertGreater(calc.tax_amount, 0)
        self.assertLess(calc.tax_amount, 100)  # Very small tax

        # Test income spanning multiple brackets
        high_income = StateIncome(wages=200000)
        high_deductions = StateDeductions(standard_deduction=5202)

        calc = self.service.calculate_state_tax(
            StateCode.CA, self.test_tax_year, FilingStatus.SINGLE,
            high_income, high_deductions
        )

        # Should span multiple brackets
        self.assertGreater(calc.tax_amount, 10000)  # Substantial tax
        self.assertGreater(len(calc.breakdown), 1)  # Multiple bracket entries

    def test_state_data_persistence(self):
        """Test that state data is properly loaded and saved"""
        # Get initial state count
        initial_count = len(self.service.get_all_states())

        # Add a mock state
        mock_state = StateTaxInfo(
            state_code=StateCode.AK,
            state_name="Alaska",
            tax_type=StateTaxType.NO_INCOME_TAX
        )
        self.service.state_tax_info[StateCode.AK] = mock_state

        # Save data
        self.service._save_state_tax_data()

        # Create new service instance (simulates restart)
        new_service = StateTaxIntegrationService(self.config, self.encryption)

        # Verify state was persisted
        ak_info = new_service.get_state_tax_info(StateCode.AK)
        self.assertIsNotNone(ak_info)
        self.assertEqual(ak_info.state_name, "Alaska")
        self.assertEqual(ak_info.tax_type, StateTaxType.NO_INCOME_TAX)

    def test_income_and_deduction_calculations(self):
        """Test income and deduction total calculations"""
        # Test income total
        income = StateIncome(
            wages=50000,
            interest=1000,
            dividends=2000,
            capital_gains=3000,
            business_income=10000,
            rental_income=5000,
            other_income=1000
        )
        self.assertEqual(income.total_income, 72000)

        # Test deductions total
        deductions = StateDeductions(
            standard_deduction=13850,
            itemized_deductions=5000,
            personal_exemption=0,
            dependent_exemptions=4000,
            other_deductions=1000
        )
        self.assertEqual(deductions.total_deductions, 23850)


class TestStateTaxInfo(unittest.TestCase):
    """Test cases for StateTaxInfo dataclass"""

    def test_state_tax_info_creation(self):
        """Test StateTaxInfo creation and defaults"""
        state_info = StateTaxInfo(
            state_code=StateCode.CA,
            state_name="California",
            tax_type=StateTaxType.PROGRESSIVE
        )

        self.assertEqual(state_info.state_code, StateCode.CA)
        self.assertEqual(state_info.state_name, "California")
        self.assertEqual(state_info.tax_type, StateTaxType.PROGRESSIVE)
        self.assertIsNone(state_info.flat_rate)
        self.assertEqual(len(state_info.brackets), 0)
        self.assertEqual(len(state_info.standard_deduction), 0)
        self.assertIsNone(state_info.personal_exemption)
        self.assertIsNone(state_info.dependent_exemption)
        self.assertFalse(state_info.local_tax_supported)
        self.assertTrue(state_info.e_filing_supported)
        self.assertEqual(state_info.tax_deadline, "April 15")

    def test_state_tax_info_serialization(self):
        """Test StateTaxInfo JSON serialization"""
        state_info = StateTaxInfo(
            state_code=StateCode.TX,
            state_name="Texas",
            tax_type=StateTaxType.NO_INCOME_TAX,
            tax_deadline="N/A"
        )

        state_dict = asdict(state_info)

        expected_fields = [
            'state_code', 'state_name', 'tax_type', 'flat_rate', 'brackets',
            'standard_deduction', 'personal_exemption', 'dependent_exemption',
            'local_tax_supported', 'e_filing_supported', 'tax_deadline'
        ]

        for field in expected_fields:
            self.assertIn(field, state_dict)


class TestStateTaxCalculation(unittest.TestCase):
    """Test cases for StateTaxCalculation dataclass"""

    def test_tax_calculation_creation(self):
        """Test StateTaxCalculation creation"""
        breakdown = {"Bracket 1 (10%)": 1000.0, "Bracket 2 (12%)": 1200.0}

        calculation = StateTaxCalculation(
            state_code=StateCode.CA,
            tax_year=2024,
            filing_status=FilingStatus.SINGLE,
            gross_income=100000,
            taxable_income=75000,
            tax_amount=2200.0,
            effective_rate=0.022,
            marginal_rate=0.12,
            breakdown=breakdown,
            credits=200.0,
            net_tax_owed=2000.0
        )

        self.assertEqual(calculation.state_code, StateCode.CA)
        self.assertEqual(calculation.tax_year, 2024)
        self.assertEqual(calculation.filing_status, FilingStatus.SINGLE)
        self.assertEqual(calculation.gross_income, 100000)
        self.assertEqual(calculation.taxable_income, 75000)
        self.assertEqual(calculation.tax_amount, 2200.0)
        self.assertEqual(calculation.effective_rate, 0.022)
        self.assertEqual(calculation.marginal_rate, 0.12)
        self.assertEqual(calculation.breakdown, breakdown)
        self.assertEqual(calculation.credits, 200.0)
        self.assertEqual(calculation.net_tax_owed, 2000.0)


if __name__ == '__main__':
    unittest.main()