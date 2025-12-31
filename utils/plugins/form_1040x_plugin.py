"""
Form 1040-X Plugin - Amended U.S. Individual Income Tax Return

This plugin implements Form 1040-X for amending previously filed tax returns.
It calculates the differences between original and amended returns.
"""

from typing import Dict, Any, Optional, List
from utils.plugins import ISchedulePlugin, PluginMetadata
from constants.pdf_fields import Form1040XFields
import logging

logger = logging.getLogger(__name__)


class Form1040XPlugin(ISchedulePlugin):
    """Plugin for Form 1040-X - Amended U.S. Individual Income Tax Return"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Form 1040-X Plugin",
            version="1.0.0",
            description="Handles Form 1040-X - Amended U.S. Individual Income Tax Return",
            schedule_name="Form 1040-X",
            irs_form="f1040x.pdf",
            author="FreedomUS Tax Return",
            requires=[]
        )

    def validate_data(self, tax_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that tax data contains required Form 1040-X fields
        """
        # Check if this is an amended return
        metadata = tax_data.get('metadata', {})
        if metadata.get('return_type') != 'amended':
            return False, "This is not an amended return"

        amended_info = metadata.get('amended_info', {})
        if not amended_info:
            return False, "Missing amended return information"

        # Check required amended info
        if not amended_info.get('original_filing_date'):
            return False, "Original filing date is required"

        if not amended_info.get('reason_codes'):
            return False, "At least one reason code is required"

        return True, None

    def calculate(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Form 1040-X values - differences between original and amended returns

        For amended returns, we need to compare the current (amended) data
        with the original return data. Since we don't store the original return
        separately in this implementation, we'll assume the "original" values
        are embedded in the amended return data.
        """
        # For now, we'll calculate based on the current tax data
        # In a full implementation, we'd compare against stored original return

        # Get tax calculations for the amended return
        from utils.tax_calculations import (
            calculate_income_tax,
            calculate_self_employment_tax,
            calculate_standard_deduction
        )

        # Basic income and deduction calculations
        filing_status = tax_data.get('filing_status', {}).get('status', 'Single')
        tax_year = tax_data.get('metadata', {}).get('tax_year', 2025)

        # Calculate total income
        income = tax_data.get('income', {})
        w2_income = sum(w2.get('wages', 0) for w2 in income.get('w2_forms', []))
        interest_income = sum(int_inc.get('amount', 0) for int_inc in income.get('interest_income', []))
        dividend_income = sum(div_inc.get('amount', 0) for div_inc in income.get('dividend_income', []))

        total_income = w2_income + interest_income + dividend_income

        # Calculate deductions
        deductions = tax_data.get('deductions', {})
        if deductions.get('method') == 'standard':
            standard_deduction = calculate_standard_deduction(filing_status, tax_year)
        else:
            # Itemized deductions would be calculated here
            standard_deduction = 0

        # Calculate taxable income
        taxable_income = max(0, total_income - standard_deduction)

        # Calculate tax
        income_tax = calculate_income_tax(taxable_income, filing_status, tax_year)

        # Calculate payments/credits
        payments = tax_data.get('payments', {})
        withholding = payments.get('federal_withholding', 0)
        estimated_payments = sum(payments.get('estimated_payments', []))
        total_payments = withholding + estimated_payments

        # Calculate refund or amount due
        tax_owed = income_tax
        if total_payments > tax_owed:
            refund = total_payments - tax_owed
            amount_due = 0
        else:
            refund = 0
            amount_due = tax_owed - total_payments

        return {
            'total_income': total_income,
            'standard_deduction': standard_deduction,
            'taxable_income': taxable_income,
            'income_tax': income_tax,
            'total_payments': total_payments,
            'refund': refund,
            'amount_due': amount_due,
        }

    def map_to_pdf_fields(self, tax_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Form 1040-X data to PDF form fields
        """
        personal_info = tax_data.get('personal_info', {})
        metadata = tax_data.get('metadata', {})
        amended_info = metadata.get('amended_info', {})

        # Build full name
        first_name = personal_info.get('first_name', '')
        middle_initial = personal_info.get('middle_initial', '')
        last_name = personal_info.get('last_name', '')
        full_name = f"{first_name} {middle_initial} {last_name}".strip()

        # Map to Form 1040-X PDF fields
        pdf_fields = {
            # Part I: Amended Return Information
            Form1040XFields.FULL_NAME: full_name,
            Form1040XFields.SSN: personal_info.get('ssn', ''),
            Form1040XFields.ADDRESS: personal_info.get('address', ''),
            Form1040XFields.CITY: personal_info.get('city', ''),
            Form1040XFields.STATE: personal_info.get('state', ''),
            Form1040XFields.ZIP_CODE: personal_info.get('zip_code', ''),

            # Filing status (checkboxes)
            Form1040XFields.FILING_STATUS_SINGLE: Form1040XFields.CHECKBOX_CHECKED if tax_data.get('filing_status', {}).get('status') == 'Single' else Form1040XFields.CHECKBOX_UNCHECKED,
            Form1040XFields.FILING_STATUS_MARRIED_JOINT: Form1040XFields.CHECKBOX_CHECKED if tax_data.get('filing_status', {}).get('status') == 'Married Filing Jointly' else Form1040XFields.CHECKBOX_UNCHECKED,
            Form1040XFields.FILING_STATUS_MARRIED_SEPARATE: Form1040XFields.CHECKBOX_CHECKED if tax_data.get('filing_status', {}).get('status') == 'Married Filing Separately' else Form1040XFields.CHECKBOX_UNCHECKED,
            Form1040XFields.FILING_STATUS_HEAD_OF_HOUSEHOLD: Form1040XFields.CHECKBOX_CHECKED if tax_data.get('filing_status', {}).get('status') == 'Head of Household' else Form1040XFields.CHECKBOX_UNCHECKED,
            Form1040XFields.FILING_STATUS_QUALIFYING_SURVIVING_SPOUSE: Form1040XFields.CHECKBOX_CHECKED if tax_data.get('filing_status', {}).get('status') == 'Qualifying Surviving Spouse' else Form1040XFields.CHECKBOX_UNCHECKED,

            # Original return information
            Form1040XFields.ORIGINAL_FILING_DATE: amended_info.get('original_filing_date', ''),

            # Reason codes (checkboxes A-G)
            Form1040XFields.REASON_CODE_A: Form1040XFields.CHECKBOX_CHECKED if 'A' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Income
            Form1040XFields.REASON_CODE_B: Form1040XFields.CHECKBOX_CHECKED if 'B' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Deductions
            Form1040XFields.REASON_CODE_C: Form1040XFields.CHECKBOX_CHECKED if 'C' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Credits
            Form1040XFields.REASON_CODE_D: Form1040XFields.CHECKBOX_CHECKED if 'D' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Status change
            Form1040XFields.REASON_CODE_E: Form1040XFields.CHECKBOX_CHECKED if 'E' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Payments
            Form1040XFields.REASON_CODE_F: Form1040XFields.CHECKBOX_CHECKED if 'F' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Other
            Form1040XFields.REASON_CODE_G: Form1040XFields.CHECKBOX_CHECKED if 'G' in amended_info.get('reason_codes', []) else Form1040XFields.CHECKBOX_UNCHECKED,  # Other (continued)

            # Part II: Income and Deductions
            Form1040XFields.TOTAL_INCOME: calculated_data.get('total_income', 0),
            Form1040XFields.STANDARD_DEDUCTION: calculated_data.get('standard_deduction', 0),
            Form1040XFields.TAXABLE_INCOME: calculated_data.get('taxable_income', 0),

            # Part III: Tax Computation
            Form1040XFields.INCOME_TAX: calculated_data.get('income_tax', 0),

            # Part IV: Payments and Refundable Credits
            Form1040XFields.TOTAL_PAYMENTS: calculated_data.get('total_payments', 0),

            # Part V: Amount Due or Overpayment
            Form1040XFields.REFUND: calculated_data.get('refund', 0),
            Form1040XFields.AMOUNT_DUE: calculated_data.get('amount_due', 0),

            # Explanation
            Form1040XFields.EXPLANATION: amended_info.get('explanation', ''),
        }

        return pdf_fields

    def is_applicable(self, tax_data: Dict[str, Any]) -> bool:
        """
        Form 1040-X is applicable for amended returns
        """
        metadata = tax_data.get('metadata', {})
        return metadata.get('return_type') == 'amended'