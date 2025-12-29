"""
Form Mappers - Convert tax data to PDF field mappings

This module contains mapper classes for different IRS forms.
Each mapper follows the Mapper pattern to translate domain data
into PDF-specific field structures.
"""

import logging
from typing import Dict, Any
from constants.pdf_fields import Form1040Fields
from utils.w2_calculator import W2Calculator
from utils.tax_calculations import calculate_standard_deduction

logger = logging.getLogger(__name__)


class Form1040Mapper:
    """Maps tax data to Form 1040 PDF fields"""
    
    @staticmethod
    def map_personal_info(tax_data) -> Dict[str, str]:
        """Map personal information to Form 1040 fields"""
        fields = {}
        
        # Taxpayer information
        first_name = tax_data.get('personal_info.first_name', '')
        middle_initial = tax_data.get('personal_info.middle_initial', '')
        last_name = tax_data.get('personal_info.last_name', '')
        
        fields[Form1040Fields.FIRST_NAME] = first_name
        fields[Form1040Fields.MIDDLE_INITIAL] = middle_initial  
        fields[Form1040Fields.LAST_NAME] = last_name
        
        # SSN (format: xxx-xx-xxxx)
        ssn = tax_data.get('personal_info.ssn', '')
        if ssn:
            fields[Form1040Fields.SSN] = ssn
        
        # Address (street)
        fields[Form1040Fields.ADDRESS] = tax_data.get('personal_info.address', '')
        
        # City
        city = tax_data.get('personal_info.city', '')
        fields[Form1040Fields.CITY] = city
        
        # State (2-letter code)
        state = tax_data.get('personal_info.state', '')
        fields[Form1040Fields.STATE] = state
        
        # ZIP code
        zip_code = tax_data.get('personal_info.zip_code', '')
        fields[Form1040Fields.ZIP_CODE] = zip_code
        
        # Spouse information (if filing jointly)
        filing_status = tax_data.get('filing_status.status', '')
        if filing_status == 'Married Filing Jointly':
            spouse_first = tax_data.get('spouse_info.first_name', '')
            spouse_mi = tax_data.get('spouse_info.middle_initial', '')
            spouse_last = tax_data.get('spouse_info.last_name', '')
            
            fields[Form1040Fields.SPOUSE_FIRST_NAME] = spouse_first
            fields[Form1040Fields.SPOUSE_MIDDLE_INITIAL] = spouse_mi
            fields[Form1040Fields.SPOUSE_LAST_NAME] = spouse_last
            
            spouse_ssn = tax_data.get('spouse_info.ssn', '')
            if spouse_ssn:
                fields[Form1040Fields.SPOUSE_SSN] = spouse_ssn
        
        return fields
    
    @staticmethod
    def map_filing_status(tax_data) -> Dict[str, str]:
        """Map filing status to Form 1040 checkboxes"""
        fields = {}
        
        filing_status = tax_data.get('filing_status.status', 'Single')
        
        # Checkboxes for filing status
        if filing_status == 'Single':
            fields[Form1040Fields.FILING_STATUS_SINGLE] = Form1040Fields.CHECKBOX_CHECKED
        elif filing_status == 'Married Filing Jointly':
            fields[Form1040Fields.FILING_STATUS_MARRIED_JOINTLY] = Form1040Fields.CHECKBOX_CHECKED
        elif filing_status == 'Married Filing Separately':
            fields[Form1040Fields.FILING_STATUS_MARRIED_SEPARATELY] = Form1040Fields.CHECKBOX_CHECKED
        elif filing_status == 'Head of Household':
            fields[Form1040Fields.FILING_STATUS_HEAD_OF_HOUSEHOLD] = Form1040Fields.CHECKBOX_CHECKED
        elif filing_status in ['Qualifying Widow(er)', 'Qualifying Surviving Spouse']:
            fields[Form1040Fields.FILING_STATUS_QUALIFYING_SURVIVING_SPOUSE] = Form1040Fields.CHECKBOX_CHECKED
        
        return fields
    
    @staticmethod
    def map_income(tax_data) -> Dict[str, str]:
        """Map income items to Form 1040 fields"""
        fields = {}
        
        # Performance: Get income section once
        income_section = tax_data.get('income', {}) if hasattr(tax_data, 'get') else tax_data.data.get('income', {})
        
        # Line 1a - Total wages from all W-2 forms
        w2_forms = income_section.get('w2_forms', [])
        total_wages = W2Calculator.calculate_total_wages(w2_forms)
        
        if total_wages:
            fields[Form1040Fields.LINE_1A_WAGES] = f"{total_wages:,.2f}"
        
        # Performance: Get interest/dividend income once
        interest_income = income_section.get('interest_income', [])
        dividend_income = income_section.get('dividend_income', [])
        
        # Line 2a - Tax-exempt interest
        tax_exempt_interest = sum(item.get('amount', 0) for item in interest_income if item.get('tax_exempt', False))
        if tax_exempt_interest:
            fields[Form1040Fields.LINE_2A_TAX_EXEMPT_INTEREST] = f"{tax_exempt_interest:,.2f}"
        
        # Line 2b - Taxable interest
        taxable_interest = sum(item.get('amount', 0) for item in interest_income if not item.get('tax_exempt', False))
        if taxable_interest:
            fields[Form1040Fields.LINE_2B_TAXABLE_INTEREST] = f"{taxable_interest:,.2f}"
        
        # Line 3a - Qualified dividends
        qualified_divs = sum(item.get('qualified', 0) for item in dividend_income)
        if qualified_divs:
            fields[Form1040Fields.LINE_3A_QUALIFIED_DIVIDENDS] = f"{qualified_divs:,.2f}"
        
        # Line 3b - Ordinary dividends
        ordinary_divs = sum(item.get('ordinary', 0) for item in dividend_income)
        if ordinary_divs:
            fields[Form1040Fields.LINE_3B_ORDINARY_DIVIDENDS] = f"{ordinary_divs:,.2f}"
        
        return fields
    
    @staticmethod
    def map_deductions(tax_data) -> Dict[str, str]:
        """Map deduction fields to Form 1040"""
        fields = {}
        
        # Determine deduction method
        deduction_method = tax_data.get('deductions.method', 'standard')
        
        if deduction_method == 'standard':
            # Calculate standard deduction based on filing status
            filing_status = tax_data.get('filing_status.status', 'Single')
            tax_year = tax_data.get('basic_info.tax_year', 2025)
            
            standard_deduction = calculate_standard_deduction(
                filing_status,
                tax_year
            )
            
            # Line 12 - Standard deduction
            if standard_deduction:
                fields[Form1040Fields.LINE_12_STANDARD_DEDUCTION] = f"{standard_deduction:,.2f}"
        else:
            # Itemized deductions total (from Schedule A)
            itemized_total = (
                tax_data.get('deductions.medical_expenses', 0) +
                tax_data.get('deductions.state_local_taxes', 0) +
                tax_data.get('deductions.mortgage_interest', 0) +
                tax_data.get('deductions.charitable_contributions', 0)
            )
            if itemized_total:
                fields[Form1040Fields.LINE_12_STANDARD_DEDUCTION] = f"{itemized_total:,.2f}"
        
        return fields
    
    @staticmethod
    def map_payments(tax_data) -> Dict[str, str]:
        """Map payment and withholding information"""
        fields = {}
        
        # Get income section for W-2 withholding
        income_section = tax_data.get('income', {}) if hasattr(tax_data, 'get') else tax_data.data.get('income', {})
        w2_forms = income_section.get('w2_forms', [])
        
        # Calculate total federal withholding from W-2s
        total_withholding = sum(w2.get('federal_withholding', 0) for w2 in w2_forms)
        
        if total_withholding:
            fields[Form1040Fields.LINE_25A_FEDERAL_WITHHOLDING] = f"{total_withholding:,.2f}"
        
        # Estimated tax payments
        estimated_tax = tax_data.get('payments.estimated_tax', 0)
        if estimated_tax:
            fields[Form1040Fields.LINE_25B_2024_ESTIMATED_TAX] = f"{estimated_tax:,.2f}"
        
        return fields
    
    @staticmethod
    def get_all_fields(tax_data) -> Dict[str, str]:
        """Get all mapped fields for Form 1040"""
        fields = {}
        
        # Combine all field mappings
        fields.update(Form1040Mapper.map_personal_info(tax_data))
        fields.update(Form1040Mapper.map_filing_status(tax_data))
        fields.update(Form1040Mapper.map_income(tax_data))
        fields.update(Form1040Mapper.map_deductions(tax_data))
        fields.update(Form1040Mapper.map_payments(tax_data))
        
        return fields
