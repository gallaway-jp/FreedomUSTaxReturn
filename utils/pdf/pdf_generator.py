"""
PDF Generator - Main orchestrator for generating complete tax return PDFs

This module coordinates the generation of complete tax returns by:
- Determining required forms based on tax data
- Filling multiple forms with appropriate data
- Managing form dependencies and schedules
- Providing batch export functionality
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.pdf.form_filler import PDFFormFiller
from utils.pdf.form_mappers import Form1040Mapper, Form8949Mapper
from utils.plugins import PluginRegistry, PluginLoader
from utils.pdf.field_mapper import DotDict

logger = logging.getLogger(__name__)


class TaxReturnPDFGenerator:
    """
    Main orchestrator for generating complete tax return PDFs.

    This class manages the entire PDF generation process including:
    - Form determination based on tax data
    - Coordinated filling of multiple forms
    - Plugin integration for schedules
    - Batch export capabilities
    """

    def __init__(self, forms_directory: str = None, output_directory: str = None):
        """
        Initialize PDF generator.

        Args:
            forms_directory: Path to IRS form PDFs
            output_directory: Path where generated PDFs will be saved
        """
        self.form_filler = PDFFormFiller(forms_directory)

        if output_directory is None:
            # Default to output/pdf_exports
            base_dir = Path(__file__).parent.parent.parent
            self.output_directory = base_dir / "output" / "pdf_exports"
        else:
            self.output_directory = Path(output_directory)

        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize plugin registry
        self.plugin_registry = PluginRegistry()
        self._load_plugins()

    def _load_plugins(self):
        """Load plugins from the plugins directory"""
        plugins_dir = Path(__file__).parent.parent / "plugins"
        loader = PluginLoader(self.plugin_registry)
        loader.load_from_directory(plugins_dir)

    def determine_required_forms(self, tax_data: Dict[str, Any]) -> List[str]:
        """
        Determine which IRS forms are required based on tax data.

        Args:
            tax_data: Complete tax return data

        Returns:
            List of required form names
        """
        required_forms = ["Form 1040"]  # Form 1040 is always required

        # Check for income types that require additional forms
        income = tax_data.get('income', {})

        # Schedule 1 (Additional Income and Adjustments)
        has_additional_income = (
            income.get('business_income', 0) > 0 or
            income.get('rental_income', 0) > 0 or
            income.get('capital_gains', []) or
            income.get('foreign_income', 0) > 0
        )
        if has_additional_income:
            required_forms.append("Form 1040 (Schedule 1)")

        # Schedule A (Itemized Deductions)
        deductions = tax_data.get('deductions', {})
        if deductions.get('method') == 'itemized':
            required_forms.append("Form 1040 (Schedule A)")

        # Schedule C (Business Income)
        schedules = tax_data.get('schedules', {})
        if schedules.get('schedule_c'):
            required_forms.append("Form 1040 (Schedule C)")

        # Schedule D (Capital Gains/Losses)
        if income.get('capital_gains', []):
            required_forms.append("Form 1040 (Schedule D)")

        # Form 8949 (Sales and Other Dispositions of Capital Assets)
        if income.get('capital_gains', []):
            required_forms.append("Form 8949")

        # Schedule E (Supplemental Income/Loss)
        has_supplemental = (
            income.get('rental_income', 0) > 0 or
            income.get('partnership_income', 0) > 0 or
            income.get('s_corp_income', 0) > 0
        )
        if has_supplemental:
            required_forms.append("Form 1040 (Schedule E)")

        # Schedule SE (Self-Employment Tax)
        if schedules.get('schedule_c') or schedules.get('schedule_se'):
            required_forms.append("Form 1040 (Schedule SE)")

        return required_forms

    def generate_complete_return(
        self,
        tax_data: Dict[str, Any],
        flatten: bool = False,
        include_signature: bool = True
    ) -> Dict[str, str]:
        """
        Generate a complete tax return with all required forms.

        Args:
            tax_data: Complete tax return data
            flatten: Whether to flatten forms (make non-editable)
            include_signature: Whether to include signature fields

        Returns:
            Dictionary mapping form names to output file paths
        """
        # Wrap data in DotDict for consistent access
        if not isinstance(tax_data, DotDict):
            tax_data = DotDict(tax_data)

        # Determine required forms
        required_forms = self.determine_required_forms(tax_data)
        logger.info(f"Required forms: {required_forms}")

        generated_files = {}

        # Generate each form
        for form_name in required_forms:
            try:
                output_path = self._generate_single_form(
                    form_name, tax_data, flatten, include_signature
                )
                generated_files[form_name] = str(output_path)
                logger.info(f"Generated {form_name}: {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate {form_name}: {e}")
                raise

        return generated_files

    def _generate_single_form(
        self,
        form_name: str,
        tax_data: DotDict,
        flatten: bool,
        include_signature: bool
    ) -> Path:
        """
        Generate a single form.

        Args:
            form_name: Name of the form to generate
            tax_data: Tax data
            flatten: Whether to flatten the form
            include_signature: Whether to include signature

        Returns:
            Path to the generated PDF
        """
        # Get field mappings for this form
        field_mappings = self._get_field_mappings(form_name, tax_data)

        # Add signature if requested
        if include_signature:
            field_mappings.update(self._get_signature_fields(tax_data))

        # Generate output path
        output_path = self._get_output_path(form_name, tax_data)

        # Fill the form
        self.form_filler.fill_form(
            form_name=form_name,
            field_values=field_mappings,
            output_path=str(output_path),
            flatten=flatten
        )

        return output_path

    def _get_field_mappings(self, form_name: str, tax_data: DotDict) -> Dict[str, str]:
        """
        Get field mappings for a specific form.

        Args:
            form_name: Name of the form
            tax_data: Tax data

        Returns:
            Dictionary of field mappings
        """
        if form_name == "Form 1040":
            return Form1040Mapper.get_all_fields(tax_data)
        elif form_name == "Form 8949":
            return Form8949Mapper.get_all_fields(tax_data)
        elif form_name.startswith("Form 1040 (Schedule"):
            return self._get_schedule_mappings(form_name, tax_data)
        else:
            logger.warning(f"No mapper found for {form_name}, returning empty mappings")
            return {}

    def _get_schedule_mappings(self, form_name: str, tax_data: DotDict) -> Dict[str, str]:
        """
        Get field mappings for schedule forms.

        Args:
            form_name: Schedule form name
            tax_data: Tax data

        Returns:
            Dictionary of field mappings
        """
        mappings = {}

        # Use plugins for schedule-specific mappings
        if "Schedule C" in form_name:
            plugin = self.plugin_registry.get_plugin("Schedule C")
            if plugin:
                calculated_data = plugin.calculate(tax_data)
                mappings = plugin.map_to_pdf_fields(tax_data, calculated_data)
        elif "Schedule 1" in form_name:
            mappings = self._map_schedule_1(tax_data)
        elif "Schedule A" in form_name:
            mappings = self._map_schedule_a(tax_data)
        elif "Schedule D" in form_name:
            mappings = self._map_schedule_d(tax_data)
        elif "Schedule E" in form_name:
            mappings = self._map_schedule_e(tax_data)
        elif "Schedule SE" in form_name:
            mappings = self._map_schedule_se(tax_data)

        return mappings

    def _map_schedule_1(self, tax_data: DotDict) -> Dict[str, str]:
        """Map Schedule 1 (Additional Income and Adjustments)"""
        fields = {}
        income = tax_data.get('income', {})
        adjustments = tax_data.get('adjustments', {})

        # Part I: Additional Income
        # Line 1: Taxable refunds, credits, or offsets of state and local income taxes
        state_refunds = income.get('state_tax_refunds', 0)
        if state_refunds:
            fields['topmostSubform[0].Page1[0].Line1_ReadOrder[0].f1_01[0]'] = f"{state_refunds:,.2f}"

        # Line 2b: Taxable interest
        taxable_interest = sum(item.get('amount', 0) for item in income.get('interest_income', [])
                              if not item.get('tax_exempt', False))
        if taxable_interest:
            fields['topmostSubform[0].Page1[0].Line2b_ReadOrder[0].f1_02[0]'] = f"{taxable_interest:,.2f}"

        # Line 3b: Ordinary dividends
        ordinary_dividends = sum(item.get('ordinary', 0) for item in income.get('dividend_income', []))
        if ordinary_dividends:
            fields['topmostSubform[0].Page1[0].Line3b_ReadOrder[0].f1_03[0]'] = f"{ordinary_dividends:,.2f}"

        # Line 4b: IRA distributions (taxable amount)
        ira_distributions = income.get('ira_distributions', 0)
        if ira_distributions:
            fields['topmostSubform[0].Page1[0].Line4b_ReadOrder[0].f1_04[0]'] = f"{ira_distributions:,.2f}"

        # Line 5b: Pensions and annuities (taxable amount)
        pensions_annuities = income.get('pensions_annuities', 0)
        if pensions_annuities:
            fields['topmostSubform[0].Page1[0].Line5b_ReadOrder[0].f1_05[0]'] = f"{pensions_annuities:,.2f}"

        # Line 8b: Rental real estate, royalties, partnerships, S corporations, etc.
        rental_income = income.get('rental_income', 0)
        partnership_income = income.get('partnership_income', 0)
        s_corp_income = income.get('s_corp_income', 0)
        other_business_income = rental_income + partnership_income + s_corp_income
        if other_business_income:
            fields['topmostSubform[0].Page1[0].Line8b_ReadOrder[0].f1_08[0]'] = f"{other_business_income:,.2f}"

        # Part II: Adjustments to Income
        # Line 12: Educator expenses
        educator_expenses = adjustments.get('educator_expenses', 0)
        if educator_expenses:
            fields['topmostSubform[0].Page1[0].Line12_ReadOrder[0].f1_12[0]'] = f"{educator_expenses:,.2f}"

        # Line 13: Certain business income deduction
        business_deduction = adjustments.get('business_income_deduction', 0)
        if business_deduction:
            fields['topmostSubform[0].Page1[0].Line13_ReadOrder[0].f1_13[0]'] = f"{business_deduction:,.2f}"

        # Line 14: Health savings account deduction
        hsa_deduction = adjustments.get('hsa_deduction', 0)
        if hsa_deduction:
            fields['topmostSubform[0].Page1[0].Line14_ReadOrder[0].f1_14[0]'] = f"{hsa_deduction:,.2f}"

        # Line 15: Moving expenses for members of the Armed Forces
        moving_expenses = adjustments.get('moving_expenses', 0)
        if moving_expenses:
            fields['topmostSubform[0].Page1[0].Line15_ReadOrder[0].f1_15[0]'] = f"{moving_expenses:,.2f}"

        # Line 16: Self-employed SEP, SIMPLE, and qualified plans
        sep_simple_deduction = adjustments.get('sep_simple_deduction', 0)
        if sep_simple_deduction:
            fields['topmostSubform[0].Page1[0].Line16_ReadOrder[0].f1_16[0]'] = f"{sep_simple_deduction:,.2f}"

        # Line 17: Self-employed health insurance deduction
        health_insurance_deduction = adjustments.get('health_insurance_deduction', 0)
        if health_insurance_deduction:
            fields['topmostSubform[0].Page1[0].Line17_ReadOrder[0].f1_17[0]'] = f"{health_insurance_deduction:,.2f}"

        # Line 18: Penalty on early withdrawal of savings
        early_withdrawal_penalty = adjustments.get('early_withdrawal_penalty', 0)
        if early_withdrawal_penalty:
            fields['topmostSubform[0].Page1[0].Line18_ReadOrder[0].f1_18[0]'] = f"{early_withdrawal_penalty:,.2f}"

        return fields

    def _map_schedule_a(self, tax_data: DotDict) -> Dict[str, str]:
        """Map Schedule A (Itemized Deductions)"""
        fields = {}
        deductions = tax_data.get('deductions', {})

        # Part I: Medical and Dental Expenses
        # Line 1: Medical and dental expenses
        medical_expenses = deductions.get('medical_expenses', 0)
        if medical_expenses:
            fields['topmostSubform[0].Page1[0].Line1_ReadOrder[0].f1_01[0]'] = f"{medical_expenses:,.2f}"

        # Line 2: Enter amount from Form 1040, line 11
        # This would be AGI, but we'll leave it for now

        # Line 3: Multiply line 2 by 7.5% (0.075)
        # Line 4: Subtract line 3 from line 1

        # Part II: Taxes You Paid
        # Line 5: State and local income taxes
        state_local_taxes = deductions.get('state_local_taxes', 0)
        if state_local_taxes:
            fields['topmostSubform[0].Page1[0].Line5_ReadOrder[0].f1_05[0]'] = f"{state_local_taxes:,.2f}"

        # Line 6: State and local real estate taxes
        real_estate_taxes = deductions.get('real_estate_taxes', 0)
        if real_estate_taxes:
            fields['topmostSubform[0].Page1[0].Line6_ReadOrder[0].f1_06[0]'] = f"{real_estate_taxes:,.2f}"

        # Line 7: State and local personal property taxes
        personal_property_taxes = deductions.get('personal_property_taxes', 0)
        if personal_property_taxes:
            fields['topmostSubform[0].Page1[0].Line7_ReadOrder[0].f1_07[0]'] = f"{personal_property_taxes:,.2f}"

        # Line 8: Other taxes
        other_taxes = deductions.get('other_taxes', 0)
        if other_taxes:
            fields['topmostSubform[0].Page1[0].Line8_ReadOrder[0].f1_08[0]'] = f"{other_taxes:,.2f}"

        # Part III: Interest You Paid
        # Line 10: Home mortgage interest and points
        mortgage_interest = deductions.get('mortgage_interest', 0)
        if mortgage_interest:
            fields['topmostSubform[0].Page1[0].Line10_ReadOrder[0].f1_10[0]'] = f"{mortgage_interest:,.2f}"

        # Line 11: Home mortgage interest not reported to you on Form 1098
        unreported_mortgage_interest = deductions.get('unreported_mortgage_interest', 0)
        if unreported_mortgage_interest:
            fields['topmostSubform[0].Page1[0].Line11_ReadOrder[0].f1_11[0]'] = f"{unreported_mortgage_interest:,.2f}"

        # Line 12: Points not reported to you on Form 1098
        points_not_reported = deductions.get('points_not_reported', 0)
        if points_not_reported:
            fields['topmostSubform[0].Page1[0].Line12_ReadOrder[0].f1_12[0]'] = f"{points_not_reported:,.2f}"

        # Line 13: Mortgage insurance premiums
        mortgage_insurance = deductions.get('mortgage_insurance', 0)
        if mortgage_insurance:
            fields['topmostSubform[0].Page1[0].Line13_ReadOrder[0].f1_13[0]'] = f"{mortgage_insurance:,.2f}"

        # Line 14: Investment interest
        investment_interest = deductions.get('investment_interest', 0)
        if investment_interest:
            fields['topmostSubform[0].Page1[0].Line14_ReadOrder[0].f1_14[0]'] = f"{investment_interest:,.2f}"

        # Part IV: Gifts to Charity
        # Line 15: Cash contributions
        cash_contributions = deductions.get('cash_contributions', 0)
        if cash_contributions:
            fields['topmostSubform[0].Page1[0].Line15_ReadOrder[0].f1_15[0]'] = f"{cash_contributions:,.2f}"

        # Line 16: Non-cash contributions
        non_cash_contributions = deductions.get('non_cash_contributions', 0)
        if non_cash_contributions:
            fields['topmostSubform[0].Page1[0].Line16_ReadOrder[0].f1_16[0]'] = f"{non_cash_contributions:,.2f}"

        # Line 17: Carryover from prior year
        carryover_contributions = deductions.get('carryover_contributions', 0)
        if carryover_contributions:
            fields['topmostSubform[0].Page1[0].Line17_ReadOrder[0].f1_17[0]'] = f"{carryover_contributions:,.2f}"

        # Part V: Casualty and Theft Losses
        # Line 18: Casualty and theft losses
        casualty_losses = deductions.get('casualty_losses', 0)
        if casualty_losses:
            fields['topmostSubform[0].Page1[0].Line18_ReadOrder[0].f1_18[0]'] = f"{casualty_losses:,.2f}"

        # Part VI: Other Itemized Deductions
        # Line 19: Other miscellaneous deductions
        other_misc_deductions = deductions.get('other_misc_deductions', 0)
        if other_misc_deductions:
            fields['topmostSubform[0].Page1[0].Line19_ReadOrder[0].f1_19[0]'] = f"{other_misc_deductions:,.2f}"

        return fields

    def _map_schedule_d(self, tax_data: DotDict) -> Dict[str, str]:
        """Map Schedule D (Capital Gains and Losses)"""
        fields = {}
        capital_gains = tax_data.get('income', {}).get('capital_gains', [])

        if not capital_gains:
            return fields

        # Separate short-term and long-term transactions
        short_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Short-term']
        long_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Long-term']

        # Part I: Short-Term Capital Gains and Losses
        for i, transaction in enumerate(short_term[:14]):  # Schedule D has space for 14 transactions
            base_idx = i + 1

            # Column (a) - Description
            desc = transaction.get('description', '')
            if desc:
                fields[f'topmostSubform[0].Page1[0].Line1a_ReadOrder[{i}].f1_01[0]'] = desc

            # Column (b) - Date acquired
            date_acq = transaction.get('date_acquired', '')
            if date_acq:
                fields[f'topmostSubform[0].Page1[0].Line1b_ReadOrder[{i}].f1_02[0]'] = date_acq

            # Column (c) - Date sold
            date_sold = transaction.get('date_sold', '')
            if date_sold:
                fields[f'topmostSubform[0].Page1[0].Line1c_ReadOrder[{i}].f1_03[0]'] = date_sold

            # Column (d) - Sales price
            sales_price = transaction.get('sales_price', 0)
            if sales_price:
                fields[f'topmostSubform[0].Page1[0].Line1d_ReadOrder[{i}].f1_04[0]'] = f"{sales_price:,.2f}"

            # Column (e) - Cost or other basis
            cost_basis = transaction.get('cost_basis', 0)
            if cost_basis:
                fields[f'topmostSubform[0].Page1[0].Line1e_ReadOrder[{i}].f1_05[0]'] = f"{cost_basis:,.2f}"

            # Column (g) - Gain or loss
            gain_loss = transaction.get('gain_loss', 0)
            if gain_loss:
                fields[f'topmostSubform[0].Page1[0].Line1g_ReadOrder[{i}].f1_07[0]'] = f"{gain_loss:,.2f}"

        # Part II: Long-Term Capital Gains and Losses
        for i, transaction in enumerate(long_term[:14]):  # Schedule D has space for 14 transactions
            base_idx = i + 1

            # Column (a) - Description
            desc = transaction.get('description', '')
            if desc:
                fields[f'topmostSubform[0].Page1[0].Line8a_ReadOrder[{i}].f1_08[0]'] = desc

            # Column (b) - Date acquired
            date_acq = transaction.get('date_acquired', '')
            if date_acq:
                fields[f'topmostSubform[0].Page1[0].Line8b_ReadOrder[{i}].f1_09[0]'] = date_acq

            # Column (c) - Date sold
            date_sold = transaction.get('date_sold', '')
            if date_sold:
                fields[f'topmostSubform[0].Page1[0].Line8c_ReadOrder[{i}].f1_10[0]'] = date_sold

            # Column (d) - Sales price
            sales_price = transaction.get('sales_price', 0)
            if sales_price:
                fields[f'topmostSubform[0].Page1[0].Line8d_ReadOrder[{i}].f1_11[0]'] = f"{sales_price:,.2f}"

            # Column (e) - Cost or other basis
            cost_basis = transaction.get('cost_basis', 0)
            if cost_basis:
                fields[f'topmostSubform[0].Page1[0].Line8e_ReadOrder[{i}].f1_12[0]'] = f"{cost_basis:,.2f}"

            # Column (g) - Gain or loss
            gain_loss = transaction.get('gain_loss', 0)
            if gain_loss:
                fields[f'topmostSubform[0].Page1[0].Line8g_ReadOrder[{i}].f1_14[0]'] = f"{gain_loss:,.2f}"

        # Calculate totals
        if short_term:
            short_term_proceeds = sum(t.get('sales_price', 0) for t in short_term)
            short_term_basis = sum(t.get('cost_basis', 0) for t in short_term)
            short_term_gain_loss = sum(t.get('gain_loss', 0) for t in short_term)

            fields['topmostSubform[0].Page1[0].Line2_ReadOrder[0].f1_15[0]'] = f"{short_term_proceeds:,.2f}"
            fields['topmostSubform[0].Page1[0].Line3_ReadOrder[0].f1_16[0]'] = f"{short_term_basis:,.2f}"
            fields['topmostSubform[0].Page1[0].Line5_ReadOrder[0].f1_18[0]'] = f"{short_term_gain_loss:,.2f}"

        if long_term:
            long_term_proceeds = sum(t.get('sales_price', 0) for t in long_term)
            long_term_basis = sum(t.get('cost_basis', 0) for t in long_term)
            long_term_gain_loss = sum(t.get('gain_loss', 0) for t in long_term)

            fields['topmostSubform[0].Page1[0].Line9_ReadOrder[0].f1_19[0]'] = f"{long_term_proceeds:,.2f}"
            fields['topmostSubform[0].Page1[0].Line10_ReadOrder[0].f1_20[0]'] = f"{long_term_basis:,.2f}"
            fields['topmostSubform[0].Page1[0].Line12_ReadOrder[0].f1_22[0]'] = f"{long_term_gain_loss:,.2f}"

        return fields

    def _map_schedule_e(self, tax_data: DotDict) -> Dict[str, str]:
        """Map Schedule E (Supplemental Income and Loss)"""
        # TODO: Implement Schedule E mapping
        return {}

    def _map_schedule_se(self, tax_data: DotDict) -> Dict[str, str]:
        """Map Schedule SE (Self-Employment Tax)"""
        fields = {}
        schedules = tax_data.get('schedules', {})

        # Check if Schedule C or Schedule SE data exists
        schedule_c = schedules.get('schedule_c', {})
        schedule_se = schedules.get('schedule_se', {})

        if not schedule_c and not schedule_se:
            return fields

        # Part I: Self-Employment Tax
        # Line 2: Net profit from Schedule C
        net_profit_c = schedule_c.get('net_profit', 0)
        if net_profit_c:
            fields['topmostSubform[0].Page1[0].Line2_ReadOrder[0].f1_01[0]'] = f"{net_profit_c:,.2f}"

        # Line 3: Net profit from Schedule E
        # This would come from Schedule E calculations
        net_profit_e = schedule_se.get('net_profit', 0)
        if net_profit_e:
            fields['topmostSubform[0].Page1[0].Line3_ReadOrder[0].f1_02[0]'] = f"{net_profit_e:,.2f}"

        # Line 4a: Combine lines 2 and 3
        total_net_profit = net_profit_c + net_profit_e
        if total_net_profit:
            fields['topmostSubform[0].Page1[0].Line4a_ReadOrder[0].f1_03[0]'] = f"{total_net_profit:,.2f}"

        # Line 4b: Multiply line 4a by 0.9235
        se_income = total_net_profit * 0.9235
        if se_income:
            fields['topmostSubform[0].Page1[0].Line4b_ReadOrder[0].f1_04[0]'] = f"{se_income:,.2f}"

        # Line 4c: Multiply line 4b by 0.153
        se_tax = se_income * 0.153
        if se_tax:
            fields['topmostSubform[0].Page1[0].Line4c_ReadOrder[0].f1_05[0]'] = f"{se_tax:,.2f}"

        # Part II: Optional Methods to Figure Net Earnings
        # This is more complex and would require additional logic

        # For now, we'll use the simplified method (Part I)
        # Line 5a: Enter amount from line 4c
        if se_tax:
            fields['topmostSubform[0].Page1[0].Line5a_ReadOrder[0].f1_06[0]'] = f"{se_tax:,.2f}"

        # Line 5b: Enter one-half of line 5a
        deductible_se_tax = se_tax * 0.5
        if deductible_se_tax:
            fields['topmostSubform[0].Page1[0].Line5b_ReadOrder[0].f1_07[0]'] = f"{deductible_se_tax:,.2f}"

        return fields

    def _get_signature_fields(self, tax_data: DotDict) -> Dict[str, str]:
        """
        Get signature fields for forms.

        Args:
            tax_data: Tax data

        Returns:
            Dictionary of signature field mappings
        """
        fields = {}
        personal_info = tax_data.get('personal_info', {})

        # Get current date
        from datetime import datetime
        current_date = datetime.now().strftime("%m/%d/%Y")

        # Form 1040 signature fields
        # Your signature
        fields['topmostSubform[0].Page2[0].YourSignature_ReadOrder[0].f2_01[0]'] = personal_info.get('first_name', '') + ' ' + personal_info.get('last_name', '')

        # Date
        fields['topmostSubform[0].Page2[0].YourSignature_ReadOrder[0].f2_02[0]'] = current_date

        # Your occupation
        fields['topmostSubform[0].Page2[0].YourSignature_ReadOrder[0].f2_03[0]'] = personal_info.get('occupation', '')

        # Spouse signature (if married filing jointly)
        filing_status = tax_data.get('filing_status', {}).get('status', '')
        if filing_status == 'Married Filing Jointly':
            spouse_info = tax_data.get('spouse_info', {})
            spouse_name = spouse_info.get('first_name', '') + ' ' + spouse_info.get('last_name', '')
            if spouse_name.strip():
                fields['topmostSubform[0].Page2[0].SpouseSignature_ReadOrder[0].f2_04[0]'] = spouse_name
                fields['topmostSubform[0].Page2[0].SpouseSignature_ReadOrder[0].f2_05[0]'] = current_date
                fields['topmostSubform[0].Page2[0].SpouseSignature_ReadOrder[0].f2_06[0]'] = spouse_info.get('occupation', '')

        # Preparer fields (if applicable)
        preparer_info = tax_data.get('preparer_info', {})
        if preparer_info:
            fields['topmostSubform[0].Page2[0].PaidPreparer_ReadOrder[0].f2_07[0]'] = preparer_info.get('name', '')
            fields['topmostSubform[0].Page2[0].PaidPreparer_ReadOrder[0].f2_08[0]'] = preparer_info.get('ptin', '')
            fields['topmostSubform[0].Page2[0].PaidPreparer_ReadOrder[0].f2_09[0]'] = preparer_info.get('firm_name', '')
            fields['topmostSubform[0].Page2[0].PaidPreparer_ReadOrder[0].f2_10[0]'] = preparer_info.get('phone', '')
            fields['topmostSubform[0].Page2[0].PaidPreparer_ReadOrder[0].f2_11[0]'] = preparer_info.get('address', '')

            # Check if self-employed
            if preparer_info.get('self_employed', False):
                fields['topmostSubform[0].Page2[0].PaidPreparer_ReadOrder[0].c2_3[0]'] = '/1'

        return fields

    def _get_output_path(self, form_name: str, tax_data: DotDict) -> Path:
        """
        Generate output path for a form.

        Args:
            form_name: Name of the form
            tax_data: Tax data

        Returns:
            Path where the form should be saved
        """
        # Get taxpayer name for filename
        personal_info = tax_data.get('personal_info', {})
        first_name = personal_info.get('first_name', 'Unknown')
        last_name = personal_info.get('last_name', 'Unknown')
        ssn_last4 = personal_info.get('ssn', 'XXXX')[-4:]

        # Clean form name for filename
        clean_form_name = form_name.replace(" ", "_").replace("(", "").replace(")", "")

        filename = f"{last_name}_{first_name}_{ssn_last4}_{clean_form_name}.pdf"
        return self.output_directory / filename

    def generate_batch_export(
        self,
        tax_returns: List[Dict[str, Any]],
        flatten: bool = True,
        include_signature: bool = True,
        max_workers: int = 4
    ) -> List[Dict[str, str]]:
        """
        Generate PDFs for multiple tax returns in parallel.

        Args:
            tax_returns: List of tax return data dictionaries
            flatten: Whether to flatten forms
            include_signature: Whether to include signatures
            max_workers: Maximum number of parallel workers

        Returns:
            List of dictionaries mapping form names to file paths for each return
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all generation tasks
            future_to_return = {
                executor.submit(
                    self.generate_complete_return,
                    tax_return,
                    flatten,
                    include_signature
                ): tax_return for tax_return in tax_returns
            }

            # Collect results as they complete
            for future in as_completed(future_to_return):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to generate tax return: {e}")
                    results.append({})  # Empty dict for failed generation

        return results

    def validate_pdf_generation(self, tax_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that PDF generation can proceed with the given data.

        Args:
            tax_data: Tax return data

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required personal information
        personal_info = tax_data.get('personal_info', {})
        required_fields = ['first_name', 'last_name', 'ssn']

        for field in required_fields:
            if not personal_info.get(field):
                return False, f"Missing required field: {field}"

        # Check that forms directory exists
        try:
            self.form_filler.get_form_path("Form 1040")
        except FileNotFoundError:
            return False, "IRS forms directory not found or Form 1040 not available"

        return True, None