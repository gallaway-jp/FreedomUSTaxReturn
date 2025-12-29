"""
Schedule C Plugin - Profit or Loss from Business

This plugin implements Schedule C (Form 1040) for reporting business
income and expenses for sole proprietors.
"""

from typing import Dict, Any, Optional
from utils.plugins import ISchedulePlugin, PluginMetadata
import logging

logger = logging.getLogger(__name__)


class ScheduleCPlugin(ISchedulePlugin):
    """Plugin for Schedule C - Profit or Loss from Business"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Schedule C Plugin",
            version="1.0.0",
            description="Handles Schedule C - Profit or Loss from Business (Sole Proprietorship)",
            schedule_name="Schedule C",
            irs_form="f1040sc.pdf",
            author="FreedomUS Tax Return",
            requires=[]
        )
    
    def validate_data(self, tax_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that tax data contains required Schedule C fields
        """
        schedule_c = tax_data.get('schedules', {}).get('schedule_c', {})
        
        # Check if Schedule C data exists
        if not schedule_c:
            return False, "No Schedule C data found"
        
        # Required fields
        required_fields = ['business_name', 'business_code']
        for field in required_fields:
            if not schedule_c.get(field):
                return False, f"Missing required field: {field}"
        
        # Must have either income or expenses
        gross_receipts = schedule_c.get('gross_receipts', 0)
        expenses = schedule_c.get('expenses', {})
        total_expenses = sum(expenses.values()) if expenses else 0
        
        if gross_receipts == 0 and total_expenses == 0:
            return False, "No business income or expenses reported"
        
        return True, None
    
    def calculate(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Schedule C values
        
        Returns calculated gross profit, net profit, and self-employment tax
        """
        schedule_c = tax_data.get('schedules', {}).get('schedule_c', {})
        
        # Part I: Income
        gross_receipts = schedule_c.get('gross_receipts', 0)
        returns_and_allowances = schedule_c.get('returns_and_allowances', 0)
        cost_of_goods_sold = schedule_c.get('cost_of_goods_sold', 0)
        
        gross_income = gross_receipts - returns_and_allowances
        gross_profit = gross_income - cost_of_goods_sold
        
        # Part II: Expenses
        expenses = schedule_c.get('expenses', {})
        
        # Common expense categories
        advertising = expenses.get('advertising', 0)
        car_and_truck = expenses.get('car_and_truck', 0)
        commissions_and_fees = expenses.get('commissions_and_fees', 0)
        contract_labor = expenses.get('contract_labor', 0)
        depreciation = expenses.get('depreciation', 0)
        insurance = expenses.get('insurance', 0)
        interest_mortgage = expenses.get('interest_mortgage', 0)
        interest_other = expenses.get('interest_other', 0)
        legal_professional = expenses.get('legal_professional', 0)
        office_expense = expenses.get('office_expense', 0)
        rent_equipment = expenses.get('rent_equipment', 0)
        rent_property = expenses.get('rent_property', 0)
        repairs = expenses.get('repairs', 0)
        supplies = expenses.get('supplies', 0)
        taxes_licenses = expenses.get('taxes_licenses', 0)
        travel = expenses.get('travel', 0)
        meals = expenses.get('meals', 0)
        utilities = expenses.get('utilities', 0)
        wages = expenses.get('wages', 0)
        other_expenses = expenses.get('other', 0)
        
        # Calculate total expenses
        total_expenses = (
            advertising + car_and_truck + commissions_and_fees + contract_labor +
            depreciation + insurance + interest_mortgage + interest_other +
            legal_professional + office_expense + rent_equipment + rent_property +
            repairs + supplies + taxes_licenses + travel + (meals * 0.5) +  # Only 50% of meals deductible
            utilities + wages + other_expenses
        )
        
        # Calculate net profit/loss
        net_profit = gross_profit - total_expenses
        
        # Calculate self-employment tax (if applicable)
        self_employment_tax = 0
        if net_profit > 400:  # Threshold for self-employment tax
            # Self-employment tax is 15.3% on 92.35% of net profit
            self_employment_income = net_profit * 0.9235
            self_employment_tax = self_employment_income * 0.153
        
        return {
            'gross_income': gross_income,
            'gross_profit': gross_profit,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'self_employment_tax': self_employment_tax,
            'deductible_part_se_tax': self_employment_tax * 0.5  # Half of SE tax is deductible
        }
    
    def map_to_pdf_fields(self, tax_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Schedule C data to PDF form fields
        """
        schedule_c = tax_data.get('schedules', {}).get('schedule_c', {})
        personal_info = tax_data.get('personal_info', {})
        
        # Map to Schedule C PDF fields
        pdf_fields = {
            # Header
            'name': f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}",
            'ssn': personal_info.get('ssn', ''),
            'business_name': schedule_c.get('business_name', ''),
            'business_code': schedule_c.get('business_code', ''),
            'business_address': schedule_c.get('business_address', ''),
            'ein': schedule_c.get('ein', ''),
            
            # Part I: Income
            'gross_receipts': schedule_c.get('gross_receipts', 0),
            'returns_allowances': schedule_c.get('returns_and_allowances', 0),
            'gross_income': calculated_data.get('gross_income', 0),
            'cost_of_goods_sold': schedule_c.get('cost_of_goods_sold', 0),
            'gross_profit': calculated_data.get('gross_profit', 0),
            
            # Part II: Expenses
            'advertising': schedule_c.get('expenses', {}).get('advertising', 0),
            'car_truck': schedule_c.get('expenses', {}).get('car_and_truck', 0),
            'commissions': schedule_c.get('expenses', {}).get('commissions_and_fees', 0),
            'contract_labor': schedule_c.get('expenses', {}).get('contract_labor', 0),
            'depreciation': schedule_c.get('expenses', {}).get('depreciation', 0),
            'insurance': schedule_c.get('expenses', {}).get('insurance', 0),
            'interest_mortgage': schedule_c.get('expenses', {}).get('interest_mortgage', 0),
            'interest_other': schedule_c.get('expenses', {}).get('interest_other', 0),
            'legal_professional': schedule_c.get('expenses', {}).get('legal_professional', 0),
            'office_expense': schedule_c.get('expenses', {}).get('office_expense', 0),
            'rent_equipment': schedule_c.get('expenses', {}).get('rent_equipment', 0),
            'rent_property': schedule_c.get('expenses', {}).get('rent_property', 0),
            'repairs': schedule_c.get('expenses', {}).get('repairs', 0),
            'supplies': schedule_c.get('expenses', {}).get('supplies', 0),
            'taxes_licenses': schedule_c.get('expenses', {}).get('taxes_licenses', 0),
            'travel': schedule_c.get('expenses', {}).get('travel', 0),
            'meals': schedule_c.get('expenses', {}).get('meals', 0),
            'utilities': schedule_c.get('expenses', {}).get('utilities', 0),
            'wages': schedule_c.get('expenses', {}).get('wages', 0),
            'other_expenses': schedule_c.get('expenses', {}).get('other', 0),
            
            # Totals
            'total_expenses': calculated_data.get('total_expenses', 0),
            'net_profit': calculated_data.get('net_profit', 0),
        }
        
        return pdf_fields
    
    def is_applicable(self, tax_data: Dict[str, Any]) -> bool:
        """
        Schedule C is applicable if there is business income/expenses
        """
        schedule_c = tax_data.get('schedules', {}).get('schedule_c', {})
        
        # Check for any business activity
        has_receipts = schedule_c.get('gross_receipts', 0) > 0
        has_expenses = bool(schedule_c.get('expenses', {}))
        
        return has_receipts or has_expenses
