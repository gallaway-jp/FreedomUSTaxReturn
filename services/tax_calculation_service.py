"""
Tax Calculation Service - Orchestrates tax calculations

This service layer separates complex calculation workflows from
the presentation layer and provides a clean API for tax operations.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from config.tax_year_config import get_tax_year_config, TaxYearConfig
from utils.tax_calculations import (
    calculate_standard_deduction,
    calculate_income_tax,
    calculate_self_employment_tax
)

logger = logging.getLogger(__name__)


@dataclass
class TaxResult:
    """Result of tax calculation with detailed breakdown"""
    
    # Income components
    total_wages: float = 0.0
    taxable_interest: float = 0.0
    tax_exempt_interest: float = 0.0
    ordinary_dividends: float = 0.0
    qualified_dividends: float = 0.0
    business_income: float = 0.0
    total_income: float = 0.0
    
    # Deductions
    standard_deduction: float = 0.0
    itemized_deduction: float = 0.0
    deduction_used: float = 0.0
    
    # Taxable income
    adjusted_gross_income: float = 0.0
    taxable_income: float = 0.0
    
    # Tax calculations
    income_tax: float = 0.0
    self_employment_tax: float = 0.0
    total_tax: float = 0.0
    
    # Payments and credits
    federal_withholding: float = 0.0
    estimated_tax_payments: float = 0.0
    total_payments: float = 0.0
    
    # Result
    refund_amount: float = 0.0
    amount_owed: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert result to dictionary for serialization"""
        return {
            'total_wages': self.total_wages,
            'taxable_interest': self.taxable_interest,
            'tax_exempt_interest': self.tax_exempt_interest,
            'ordinary_dividends': self.ordinary_dividends,
            'qualified_dividends': self.qualified_dividends,
            'business_income': self.business_income,
            'total_income': self.total_income,
            'standard_deduction': self.standard_deduction,
            'itemized_deduction': self.itemized_deduction,
            'deduction_used': self.deduction_used,
            'adjusted_gross_income': self.adjusted_gross_income,
            'taxable_income': self.taxable_income,
            'income_tax': self.income_tax,
            'self_employment_tax': self.self_employment_tax,
            'total_tax': self.total_tax,
            'federal_withholding': self.federal_withholding,
            'estimated_tax_payments': self.estimated_tax_payments,
            'total_payments': self.total_payments,
            'refund_amount': self.refund_amount,
            'amount_owed': self.amount_owed
        }


class TaxCalculationService:
    """
    Service for orchestrating tax calculations.
    
    This service provides a high-level API for tax operations and
    coordinates between multiple calculation utilities.
    """
    
    def __init__(self, tax_year: int = 2025):
        """
        Initialize tax calculation service.
        
        Args:
            tax_year: Tax year for calculations (default: 2025)
        """
        self.tax_year = tax_year
        self.config: TaxYearConfig = get_tax_year_config(tax_year)
        logger.info(f"Initialized TaxCalculationService for tax year {tax_year}")
    
    def _get_nested_value(self, data: Dict[str, Any], path: str, default=None) -> Any:
        """
        Get a nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'income.w2_forms')
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
    
    def calculate_complete_return(self, tax_data: Any) -> TaxResult:
        """
        Calculate complete tax return with all components.
        
        Args:
            tax_data: Tax data object or dictionary with taxpayer information
            
        Returns:
            TaxResult with complete calculation breakdown
        """
        result = TaxResult()
        
        # Get data accessor (handles both dict and TaxData object)
        from models.tax_data import TaxData
        if isinstance(tax_data, TaxData):
            # TaxData object
            get_value = tax_data.get
        elif isinstance(tax_data, dict):
            # Dictionary - could be old flat format or new multi-year format
            if 'years' in tax_data:
                # New multi-year format
                current_year = tax_data.get('metadata', {}).get('current_year', self.tax_year)
                year_data = tax_data['years'].get(current_year, {})
                get_value = lambda k, d=None: self._get_nested_value(year_data, k, d)
            else:
                # Old flat format
                get_value = lambda k, d=None: tax_data.get(k, d)
        else:
            raise ValueError(f"Unsupported tax_data type: {type(tax_data)}")
        
        # Calculate income components
        result.total_wages = self._calculate_total_wages(get_value)
        result.taxable_interest = self._calculate_taxable_interest(get_value)
        result.tax_exempt_interest = self._calculate_tax_exempt_interest(get_value)
        result.ordinary_dividends = self._calculate_ordinary_dividends(get_value)
        result.qualified_dividends = self._calculate_qualified_dividends(get_value)
        result.business_income = self._calculate_business_income(get_value)
        
        # Total income (AGI before adjustments)
        result.total_income = (
            result.total_wages +
            result.taxable_interest +
            result.ordinary_dividends +
            result.business_income
        )
        result.adjusted_gross_income = result.total_income  # Simplified (no adjustments yet)
        
        # Calculate deductions
        filing_status = get_value('filing_status.status', 'Single')
        result.standard_deduction = calculate_standard_deduction(filing_status, self.tax_year)
        result.itemized_deduction = self._calculate_itemized_deductions(get_value)
        
        # Use larger deduction
        deduction_method = get_value('deductions.method', 'standard')
        if deduction_method == 'itemized':
            result.deduction_used = result.itemized_deduction
        else:
            result.deduction_used = result.standard_deduction
        
        # Taxable income
        result.taxable_income = max(0, result.adjusted_gross_income - result.deduction_used)
        
        # Calculate taxes
        result.income_tax = calculate_income_tax(result.taxable_income, filing_status, self.tax_year)
        
        # Self-employment tax (if applicable)
        if result.business_income > 0:
            result.self_employment_tax = calculate_self_employment_tax(result.business_income)
        
        result.total_tax = result.income_tax + result.self_employment_tax
        
        # Calculate payments
        result.federal_withholding = self._calculate_total_withholding(get_value)
        result.estimated_tax_payments = get_value('payments.estimated_tax', 0)
        result.total_payments = result.federal_withholding + result.estimated_tax_payments
        
        # Determine refund or amount owed
        if result.total_payments > result.total_tax:
            result.refund_amount = result.total_payments - result.total_tax
            result.amount_owed = 0
        else:
            result.refund_amount = 0
            result.amount_owed = result.total_tax - result.total_payments
        
        logger.info(f"Completed tax calculation: AGI=${result.adjusted_gross_income:,.2f}, "
                   f"Tax=${result.total_tax:,.2f}, Refund=${result.refund_amount:,.2f}")
        
        return result
    
    def _calculate_total_wages(self, get_value) -> float:
        """Calculate total wages from all W-2 forms"""
        income_section = get_value('income', {})
        w2_forms = income_section.get('w2_forms', []) if isinstance(income_section, dict) else []
        return sum(w2.get('wages', 0) for w2 in w2_forms)
    
    def _calculate_taxable_interest(self, get_value) -> float:
        """Calculate total taxable interest income"""
        income_section = get_value('income', {})
        interest_income = income_section.get('interest_income', []) if isinstance(income_section, dict) else []
        return sum(item.get('amount', 0) for item in interest_income if not item.get('tax_exempt', False))
    
    def _calculate_tax_exempt_interest(self, get_value) -> float:
        """Calculate total tax-exempt interest income"""
        income_section = get_value('income', {})
        interest_income = income_section.get('interest_income', []) if isinstance(income_section, dict) else []
        return sum(item.get('amount', 0) for item in interest_income if item.get('tax_exempt', False))
    
    def _calculate_ordinary_dividends(self, get_value) -> float:
        """Calculate total ordinary dividend income"""
        income_section = get_value('income', {})
        dividend_income = income_section.get('dividend_income', []) if isinstance(income_section, dict) else []
        return sum(item.get('ordinary', 0) for item in dividend_income)
    
    def _calculate_qualified_dividends(self, get_value) -> float:
        """Calculate total qualified dividend income"""
        income_section = get_value('income', {})
        dividend_income = income_section.get('dividend_income', []) if isinstance(income_section, dict) else []
        return sum(item.get('qualified', 0) for item in dividend_income)
    
    def _calculate_business_income(self, get_value) -> float:
        """Calculate total business income (net profit)"""
        income_section = get_value('income', {})
        
        # Check for self-employment businesses (new format)
        self_employment = income_section.get('self_employment', [])
        if isinstance(self_employment, list) and self_employment:
            return sum(biz.get('net_profit', 0) for biz in self_employment)
        
        # Fallback to old format
        business_income = income_section.get('business_income', [])
        if isinstance(business_income, (int, float)):
            return float(business_income)
        elif isinstance(business_income, list):
            return sum(biz.get('net_profit', 0) for biz in business_income)
        return 0.0
    
    def _calculate_itemized_deductions(self, get_value) -> float:
        """Calculate total itemized deductions"""
        return (
            get_value('deductions.medical_expenses', 0) +
            get_value('deductions.state_local_taxes', 0) +
            get_value('deductions.mortgage_interest', 0) +
            get_value('deductions.charitable_contributions', 0)
        )
    
    def _calculate_total_withholding(self, get_value) -> float:
        """Calculate total federal withholding from all sources"""
        income_section = get_value('income', {})
        w2_forms = income_section.get('w2_forms', []) if isinstance(income_section, dict) else []
        return sum(w2.get('federal_withholding', 0) for w2 in w2_forms)
    
    def get_effective_tax_rate(self, tax_result: TaxResult) -> float:
        """
        Calculate effective tax rate.
        
        Args:
            tax_result: Completed tax calculation result
            
        Returns:
            Effective tax rate as a percentage
        """
        if tax_result.adjusted_gross_income <= 0:
            return 0.0
        return (tax_result.total_tax / tax_result.adjusted_gross_income) * 100
    
    def get_marginal_tax_rate(self, taxable_income: float, filing_status: str) -> float:
        """
        Get marginal tax rate for given income and filing status.
        
        Args:
            taxable_income: Taxable income amount
            filing_status: Filing status
            
        Returns:
            Marginal tax rate as a percentage
        """
        brackets = self.config.tax_brackets.get(filing_status, self.config.tax_brackets['Single'])
        
        for threshold, rate in brackets:
            if taxable_income <= threshold:
                return rate * 100
        
        # If we get here, use the highest bracket
        return brackets[-1][1] * 100
