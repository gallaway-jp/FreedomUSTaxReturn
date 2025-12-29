"""
PDF Field Name Constants for IRS Forms

This module centralizes all PDF field names to avoid magic strings
throughout the codebase and make field references easier to maintain.
"""


class Form1040Fields:
    """Field names for IRS Form 1040 (2025)"""
    
    # Personal Information
    FIRST_NAME = 'topmostSubform[0].Page1[0].f1_01[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].f1_02[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].f1_03[0]'
    SSN = 'topmostSubform[0].Page1[0].f1_04[0]'
    ADDRESS = 'topmostSubform[0].Page1[0].f1_05[0]'
    CITY = 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_10[0]'
    STATE = 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_11[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_12[0]'
    
    # Spouse Information (if married filing jointly)
    SPOUSE_FIRST_NAME = 'topmostSubform[0].Page1[0].f1_06[0]'
    SPOUSE_MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].f1_07[0]'
    SPOUSE_LAST_NAME = 'topmostSubform[0].Page1[0].f1_08[0]'
    SPOUSE_SSN = 'topmostSubform[0].Page1[0].f1_09[0]'
    
    # Filing Status (checkboxes)
    FILING_STATUS_SINGLE = 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]'
    FILING_STATUS_MARRIED_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]'
    FILING_STATUS_MARRIED_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]'
    FILING_STATUS_HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].c1_3[0]'
    FILING_STATUS_QUALIFYING_SURVIVING_SPOUSE = 'topmostSubform[0].Page1[0].c1_3[1]'
    
    # Income Section (Lines 1-9)
    LINE_1A_WAGES = 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]'
    LINE_2A_TAX_EXEMPT_INTEREST = 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_48[0]'
    LINE_2B_TAXABLE_INTEREST = 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_49[0]'
    LINE_3A_QUALIFIED_DIVIDENDS = 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_50[0]'
    LINE_3B_ORDINARY_DIVIDENDS = 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_51[0]'
    
    # Deductions Section
    LINE_12_STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].f1_37[0]'
    
    # Payments Section (Page 2)
    LINE_25A_FEDERAL_WITHHOLDING = 'topmostSubform[0].Page2[0].f2_18[0]'
    LINE_25B_2024_ESTIMATED_TAX = 'topmostSubform[0].Page2[0].f2_19[0]'
    LINE_25C_EITC = 'topmostSubform[0].Page2[0].f2_20[0]'
    LINE_25D_OTHER_PAYMENTS = 'topmostSubform[0].Page2[0].f2_21[0]'
    
    # Checkbox Values
    CHECKBOX_CHECKED = '/1'
    CHECKBOX_UNCHECKED = '/0'


class ScheduleCFields:
    """Field names for Schedule C (Profit or Loss from Business)"""
    # TODO: Add Schedule C field names when implementing
    pass


class ScheduleAFields:
    """Field names for Schedule A (Itemized Deductions)"""
    # TODO: Add Schedule A field names when implementing
    pass
