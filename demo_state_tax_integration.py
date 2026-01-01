#!/usr/bin/env python3
"""
State Tax Integration Demo Script

Demonstrates the comprehensive state tax integration functionality including:
- Single state tax calculations for different tax systems
- Multi-state tax calculations
- State tax return management
- Tax form generation and validation
- State comparison features

This script showcases the StateTaxIntegrationService capabilities across
all supported states and territories.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.state_tax_integration_service import (
    StateTaxIntegrationService,
    StateCode,
    FilingStatus,
    StateTaxType,
    StateIncome,
    StateDeductions,
    StateTaxCalculation
)
from config.app_config import AppConfig
from services.encryption_service import EncryptionService


class MockConfig:
    """Mock configuration for demo purposes"""

    def __init__(self):
        self.safe_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.safe_dir, exist_ok=True)

    def get_data_directory(self):
        return self.data_dir


class MockEncryptionService:
    """Mock encryption service for demo purposes"""

    def encrypt_data(self, data):
        return data  # No encryption for demo

    def decrypt_data(self, data):
        return data  # No decryption for demo


class StateTaxDemo:
    """Demo class for showcasing state tax integration features"""

    def __init__(self):
        """Initialize the demo with sample data"""
        # Initialize mock services
        mock_config = MockConfig()
        mock_encryption = MockEncryptionService()

        self.service = StateTaxIntegrationService(mock_config, mock_encryption)

        # Sample taxpayer data
        self.sample_taxpayer = {
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "taxpayer_id": "123456789_CA"
        }

        # Sample income data (moderate income scenario)
        self.sample_income = StateIncome(
            wages=75000.00,
            interest=2500.00,
            dividends=1500.00,
            capital_gains=5000.00,
            business_income=0.00,
            rental_income=12000.00,
            other_income=500.00
        )

        # Sample deductions
        self.sample_deductions = StateDeductions(
            standard_deduction=12950.00,  # Single filer standard deduction
            itemized_deductions=0.00,
            personal_exemption=0.00,  # Most states eliminated personal exemptions
            dependent_exemptions=0.00
        )

        self.current_year = datetime.now().year

    def run_demo(self):
        """Run the complete state tax integration demo"""
        print("=" * 80)
        print("STATE TAX INTEGRATION DEMO")
        print("=" * 80)
        print(f"Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tax Year: {self.current_year}")
        print()

        # Demo 1: Single State Calculations
        self.demo_single_state_calculations()

        # Demo 2: Multi-State Calculations
        self.demo_multi_state_calculations()

        # Demo 3: State Tax Return Management
        self.demo_return_management()

        # Demo 4: State Comparison
        self.demo_state_comparison()

        # Demo 5: Tax Form Generation
        self.demo_form_generation()

        # Demo 6: Validation Features
        self.demo_validation()

        print("\n" + "=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 80)

    def demo_single_state_calculations(self):
        """Demonstrate single state tax calculations"""
        print("\n1. SINGLE STATE TAX CALCULATIONS")
        print("-" * 40)

        # Test different tax systems
        test_states = [
            (StateCode.CA, "Progressive Tax State"),
            (StateCode.FL, "No Income Tax State"),
            (StateCode.PA, "Flat Tax State"),
            (StateCode.TX, "No Income Tax State"),
            (StateCode.NY, "High Progressive Tax State")
        ]

        for state_code, description in test_states:
            print(f"\n{description}: {state_code.value}")
            print("-" * 30)

            try:
                calculation = self.service.calculate_state_tax(
                    state_code, self.current_year, FilingStatus.SINGLE,
                    self.sample_income, self.sample_deductions
                )

                self._print_calculation_results(calculation)

            except Exception as e:
                print(f"Error calculating tax for {state_code.value}: {str(e)}")

    def demo_multi_state_calculations(self):
        """Demonstrate multi-state tax calculations"""
        print("\n\n2. MULTI-STATE TAX CALCULATIONS")
        print("-" * 40)

        # Test different combinations
        multi_state_scenarios = [
            ([StateCode.CA, StateCode.NY, StateCode.FL], "High Tax + No Tax States"),
            ([StateCode.TX, StateCode.NV, StateCode.WA], "No Income Tax States"),
            ([StateCode.CA, StateCode.TX, StateCode.NY], "Cross-Country Scenario")
        ]

        for state_codes, description in multi_state_scenarios:
            print(f"\n{description}")
            print("-" * 30)

            try:
                results = self.service.calculate_multi_state_tax(
                    state_codes, self.current_year, FilingStatus.SINGLE,
                    self.sample_income, self.sample_deductions
                )

                total_tax = 0
                for state_code, calculation in results.items():
                    print(f"{state_code}: ${calculation.net_tax_owed:,.2f} "
                          f"(Effective: {calculation.effective_rate:.2%})")
                    total_tax += calculation.net_tax_owed

                print(f"Total Tax Owed: ${total_tax:,.2f}")

            except Exception as e:
                print(f"Error in multi-state calculation: {str(e)}")

    def demo_return_management(self):
        """Demonstrate state tax return management"""
        print("\n\n3. STATE TAX RETURN MANAGEMENT")
        print("-" * 40)

        # Create returns for different states
        states_to_create = [StateCode.CA, StateCode.NY, StateCode.FL, StateCode.TX]

        created_returns = []

        for state_code in states_to_create:
            try:
                return_id = self.service.create_state_tax_return(
                    state_code, self.current_year, self.sample_taxpayer,
                    FilingStatus.SINGLE, self.sample_income, self.sample_deductions
                )
                created_returns.append(return_id)
                print(f"Created return for {state_code.value}: {return_id}")

            except Exception as e:
                print(f"Error creating return for {state_code.value}: {str(e)}")

        # List all returns
        print(f"\nTotal returns created: {len(created_returns)}")

        # Get return details
        if created_returns:
            return_id = created_returns[0]
            tax_return = self.service.get_state_tax_return(return_id)
            if tax_return:
                print(f"\nReturn Details for {return_id}:")
                print(f"  State: {tax_return.state_code.value}")
                print(f"  Year: {tax_return.tax_year}")
                print(f"  Status: {tax_return.status}")
                print(f"  Tax Owed: ${tax_return.calculation.net_tax_owed:,.2f}")

    def demo_state_comparison(self):
        """Demonstrate state tax comparison features"""
        print("\n\n4. STATE TAX COMPARISON")
        print("-" * 40)

        # Compare tax burdens across states
        comparison_states = [StateCode.CA, StateCode.NY, StateCode.TX, StateCode.FL, StateCode.PA]

        print("Tax Comparison for $75,000 Income (Single Filer):")
        print("-" * 50)

        comparisons = []
        for state_code in comparison_states:
            try:
                calculation = self.service.calculate_state_tax(
                    state_code, self.current_year, FilingStatus.SINGLE,
                    self.sample_income, self.sample_deductions
                )

                # Get state info separately
                state_info = self.service.get_state_tax_info(state_code)

                comparisons.append({
                    'state': state_code.value,
                    'tax_owed': calculation.net_tax_owed,
                    'effective_rate': calculation.effective_rate,
                    'tax_type': state_info.tax_type.value if state_info else 'Unknown'
                })

            except Exception as e:
                print(f"Error calculating for {state_code.value}: {str(e)}")

        # Sort by tax owed
        comparisons.sort(key=lambda x: x['tax_owed'])

        print("<15")
        print("-" * 50)

        for comp in comparisons:
            print("<15")

        # Find best and worst states
        if comparisons:
            best_state = min(comparisons, key=lambda x: x['tax_owed'])
            worst_state = max(comparisons, key=lambda x: x['tax_owed'])

            print(f"\nLowest Tax Burden: {best_state['state']} (${best_state['tax_owed']:,.2f})")
            print(f"Highest Tax Burden: {worst_state['state']} (${worst_state['tax_owed']:,.2f})")
            print(f"Tax Difference: ${worst_state['tax_owed'] - best_state['tax_owed']:,.2f}")

    def demo_form_generation(self):
        """Demonstrate tax form generation"""
        print("\n\n5. TAX FORM GENERATION")
        print("-" * 40)

        # Create a return first
        try:
            return_id = self.service.create_state_tax_return(
                StateCode.CA, self.current_year, self.sample_taxpayer,
                FilingStatus.SINGLE, self.sample_income, self.sample_deductions
            )

            # Generate form data
            form_data = self.service.generate_state_tax_form(return_id)

            print("Generated Form Data for California:")
            print("-" * 30)
            print(f"Form Type: {form_data.get('form_type', 'N/A')}")
            print(f"Tax Year: {form_data.get('tax_year', 'N/A')}")
            print(f"Taxpayer: {form_data.get('taxpayer_name', 'N/A')}")
            print(f"Total Income: ${form_data.get('total_income', 0):,.2f}")
            print(f"Tax Owed: ${form_data.get('tax_owed', 0):,.2f}")

            # Show form sections
            if 'form_sections' in form_data:
                print(f"\nForm Sections: {len(form_data['form_sections'])}")
                for section in form_data['form_sections']:
                    print(f"  - {section}")

        except Exception as e:
            print(f"Error in form generation: {str(e)}")

    def demo_validation(self):
        """Demonstrate validation features"""
        print("\n\n6. VALIDATION FEATURES")
        print("-" * 40)

        # Create a return and validate it
        try:
            return_id = self.service.create_state_tax_return(
                StateCode.CA, self.current_year, self.sample_taxpayer,
                FilingStatus.SINGLE, self.sample_income, self.sample_deductions
            )

            # Validate the return
            errors = self.service.validate_state_tax_return(return_id)

            if not errors:
                print("✓ Return validation passed - no errors found")
            else:
                print(f"✗ Return validation failed - {len(errors)} error(s):")
                for error in errors:
                    print(f"  - {error}")

        except Exception as e:
            print(f"Error in validation: {str(e)}")

        # Test state tax deadlines
        print(f"\nState Tax Deadlines for {self.current_year}:")
        deadlines = self.service.get_state_tax_deadlines(self.current_year)
        for state, deadline in sorted(list(deadlines.items())[:5]):  # Show first 5
            print(f"  {state}: {deadline}")

    def _print_calculation_results(self, calculation: StateTaxCalculation):
        """Print formatted calculation results"""
        print(f"Gross Income: ${calculation.gross_income:,.2f}")
        print(f"Taxable Income: ${calculation.taxable_income:,.2f}")
        print(f"Tax Amount: ${calculation.tax_amount:,.2f}")
        print(f"Effective Rate: {calculation.effective_rate:.2%}")
        print(f"Marginal Rate: {calculation.marginal_rate:.2%}")
        if calculation.credits > 0:
            print(f"Tax Credits: ${calculation.credits:,.2f}")
        print(f"Net Tax Owed: ${calculation.net_tax_owed:,.2f}")

        if calculation.breakdown:
            print("Tax Breakdown:")
            for bracket, amount in calculation.breakdown.items():
                print(f"  {bracket}: ${amount:,.2f}")


def main():
    """Main demo function"""
    try:
        demo = StateTaxDemo()
        demo.run_demo()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()