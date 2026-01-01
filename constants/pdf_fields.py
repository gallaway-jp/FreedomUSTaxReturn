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
    
    # Part I: Income
    GROSS_RECEIPTS = 'topmostSubform[0].Page1[0].Line1_ReadOrder[0].f1_01[0]'
    RETURNS_AND_ALLOWANCES = 'topmostSubform[0].Page1[0].Line2_ReadOrder[0].f1_02[0]'
    COST_OF_GOODS_SOLD = 'topmostSubform[0].Page1[0].Line4_ReadOrder[0].f1_04[0]'
    
    # Part II: Expenses
    ADVERTISING = 'topmostSubform[0].Page1[0].Line8_ReadOrder[0].f1_08[0]'
    CAR_AND_TRUCK_EXPENSES = 'topmostSubform[0].Page1[0].Line9_ReadOrder[0].f1_09[0]'
    COMMISSIONS_AND_FEES = 'topmostSubform[0].Page1[0].Line10_ReadOrder[0].f1_10[0]'
    CONTRACT_LABOR = 'topmostSubform[0].Page1[0].Line11_ReadOrder[0].f1_11[0]'
    DEPRECIATION = 'topmostSubform[0].Page1[0].Line12_ReadOrder[0].f1_12[0]'
    EMPLOYEE_BENEFIT_PROGRAMS = 'topmostSubform[0].Page1[0].Line13_ReadOrder[0].f1_13[0]'
    INSURANCE = 'topmostSubform[0].Page1[0].Line14_ReadOrder[0].f1_14[0]'
    INTEREST_MORTGAGE = 'topmostSubform[0].Page1[0].Line15_ReadOrder[0].f1_15[0]'
    INTEREST_OTHER = 'topmostSubform[0].Page1[0].Line16_ReadOrder[0].f1_16[0]'
    LEGAL_AND_PROFESSIONAL_SERVICES = 'topmostSubform[0].Page1[0].Line17_ReadOrder[0].f1_17[0]'
    OFFICE_EXPENSE = 'topmostSubform[0].Page1[0].Line18_ReadOrder[0].f1_18[0]'
    PENSION_AND_PROFIT_SHARING = 'topmostSubform[0].Page1[0].Line19_ReadOrder[0].f1_19[0]'
    RENT_OR_LEASE_VEHICLES = 'topmostSubform[0].Page1[0].Line20a_ReadOrder[0].f1_20a[0]'
    RENT_OR_LEASE_OTHER = 'topmostSubform[0].Page1[0].Line20b_ReadOrder[0].f1_20b[0]'
    REPAIRS_AND_MAINTENANCE = 'topmostSubform[0].Page1[0].Line21_ReadOrder[0].f1_21[0]'
    SUPPLIES = 'topmostSubform[0].Page1[0].Line22_ReadOrder[0].f1_22[0]'
    TAXES_AND_LICENSES = 'topmostSubform[0].Page1[0].Line23_ReadOrder[0].f1_23[0]'
    TRAVEL = 'topmostSubform[0].Page1[0].Line24a_ReadOrder[0].f1_24a[0]'
    MEALS = 'topmostSubform[0].Page1[0].Line24b_ReadOrder[0].f1_24b[0]'
    UTILITIES = 'topmostSubform[0].Page1[0].Line25_ReadOrder[0].f1_25[0]'
    WAGES = 'topmostSubform[0].Page1[0].Line26_ReadOrder[0].f1_26[0]'
    OTHER_EXPENSES = 'topmostSubform[0].Page1[0].Line27a_ReadOrder[0].f1_27a[0]'
    
    # Business Information
    BUSINESS_NAME = 'topmostSubform[0].Page1[0].BusinessName[0].f1_28[0]'
    BUSINESS_CODE = 'topmostSubform[0].Page1[0].BusinessCode[0].f1_29[0]'


class ScheduleAFields:
    """Field names for Schedule A (Itemized Deductions)"""
    
    # Part I: Medical and Dental Expenses
    MEDICAL_EXPENSES = 'topmostSubform[0].Page1[0].Line1_ReadOrder[0].f1_01[0]'
    
    # Part II: Taxes You Paid
    STATE_LOCAL_INCOME_TAXES = 'topmostSubform[0].Page1[0].Line5_ReadOrder[0].f1_05[0]'
    STATE_LOCAL_REAL_ESTATE_TAXES = 'topmostSubform[0].Page1[0].Line6_ReadOrder[0].f1_06[0]'
    STATE_LOCAL_PERSONAL_PROPERTY_TAXES = 'topmostSubform[0].Page1[0].Line7_ReadOrder[0].f1_07[0]'
    OTHER_TAXES = 'topmostSubform[0].Page1[0].Line8_ReadOrder[0].f1_08[0]'
    
    # Part III: Interest You Paid
    HOME_MORTGAGE_INTEREST = 'topmostSubform[0].Page1[0].Line10_ReadOrder[0].f1_10[0]'
    HOME_MORTGAGE_INTEREST_NOT_REPORTED = 'topmostSubform[0].Page1[0].Line11_ReadOrder[0].f1_11[0]'
    POINTS_NOT_REPORTED = 'topmostSubform[0].Page1[0].Line12_ReadOrder[0].f1_12[0]'
    MORTGAGE_INSURANCE_PREMIUMS = 'topmostSubform[0].Page1[0].Line13_ReadOrder[0].f1_13[0]'
    INVESTMENT_INTEREST = 'topmostSubform[0].Page1[0].Line14_ReadOrder[0].f1_14[0]'
    
    # Part IV: Gifts to Charity
    CASH_CONTRIBUTIONS = 'topmostSubform[0].Page1[0].Line15_ReadOrder[0].f1_15[0]'
    NON_CASH_CONTRIBUTIONS = 'topmostSubform[0].Page1[0].Line16_ReadOrder[0].f1_16[0]'
    CARRYOVER_CONTRIBUTIONS = 'topmostSubform[0].Page1[0].Line17_ReadOrder[0].f1_17[0]'
    
    # Part V: Casualty and Theft Losses
    CASUALTY_THEFT_LOSSES = 'topmostSubform[0].Page1[0].Line18_ReadOrder[0].f1_18[0]'
    
    # Part VI: Other Itemized Deductions
    OTHER_MISC_DEDUCTIONS = 'topmostSubform[0].Page1[0].Line19_ReadOrder[0].f1_19[0]'


class Form1040XFields:
    """Field names for IRS Form 1040-X (Amended Return)"""
    
    # Personal Information
    FULL_NAME = 'topmostSubform[0].Page1[0].Part1[0].Name[0].TextField[0]'
    SSN = 'topmostSubform[0].Page1[0].Part1[0].SSN[0].TextField[0]'
    ADDRESS = 'topmostSubform[0].Page1[0].Part1[0].Address[0].TextField[0]'
    CITY = 'topmostSubform[0].Page1[0].Part1[0].City[0].TextField[0]'
    STATE = 'topmostSubform[0].Page1[0].Part1[0].State[0].TextField[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].Part1[0].ZIP[0].TextField[0]'
    
    # Filing Status (checkboxes)
    FILING_STATUS_SINGLE = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[0]'
    FILING_STATUS_MARRIED_JOINT = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[1]'
    FILING_STATUS_MARRIED_SEPARATE = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[2]'
    FILING_STATUS_HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[3]'
    FILING_STATUS_QUALIFYING_SURVIVING_SPOUSE = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[4]'
    
    # Original Return Information
    ORIGINAL_FILING_DATE = 'topmostSubform[0].Page1[0].Part1[0].DateFiled[0].TextField[0]'
    
    # Reason Codes (checkboxes A-G)
    REASON_CODE_A = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[0]'  # Income
    REASON_CODE_B = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[1]'  # Deductions
    REASON_CODE_C = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[2]'  # Credits
    REASON_CODE_D = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[3]'  # Status change
    REASON_CODE_E = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[4]'  # Payments
    REASON_CODE_F = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[5]'  # Other
    REASON_CODE_G = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[6]'  # Other (continued)
    
    # Part II: Income and Deductions
    TOTAL_INCOME = 'topmostSubform[0].Page1[0].Part2[0].Line1[0].TextField[0]'
    STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].Part2[0].Line2[0].TextField[0]'
    TAXABLE_INCOME = 'topmostSubform[0].Page1[0].Part2[0].Line3[0].TextField[0]'
    
    # Part III: Tax Computation
    INCOME_TAX = 'topmostSubform[0].Page1[0].Part3[0].Line4[0].TextField[0]'
    
    # Part IV: Payments and Refundable Credits
    TOTAL_PAYMENTS = 'topmostSubform[0].Page1[0].Part4[0].Line5[0].TextField[0]'
    
    # Part V: Amount Due or Overpayment
    REFUND = 'topmostSubform[0].Page1[0].Part5[0].Line6[0].TextField[0]'
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].Part5[0].Line7[0].TextField[0]'
    
    # Explanation
    EXPLANATION = 'topmostSubform[0].Page1[0].Part6[0].Explanation[0].TextField[0]'
    
class Form1040XFields:
    """Field names for IRS Form 1040-X (Amended Return)"""
    
    # Personal Information
    FULL_NAME = 'topmostSubform[0].Page1[0].Part1[0].Name[0].TextField[0]'
    SSN = 'topmostSubform[0].Page1[0].Part1[0].SSN[0].TextField[0]'
    ADDRESS = 'topmostSubform[0].Page1[0].Part1[0].Address[0].TextField[0]'
    CITY = 'topmostSubform[0].Page1[0].Part1[0].City[0].TextField[0]'
    STATE = 'topmostSubform[0].Page1[0].Part1[0].State[0].TextField[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].Part1[0].ZIP[0].TextField[0]'
    
    # Filing Status (checkboxes)
    FILING_STATUS_SINGLE = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[0]'
    FILING_STATUS_MARRIED_JOINT = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[1]'
    FILING_STATUS_MARRIED_SEPARATE = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[2]'
    FILING_STATUS_HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[3]'
    FILING_STATUS_QUALIFYING_SURVIVING_SPOUSE = 'topmostSubform[0].Page1[0].Part1[0].FilingStatus[0].c1_1[4]'
    
    # Original Return Information
    ORIGINAL_FILING_DATE = 'topmostSubform[0].Page1[0].Part1[0].DateFiled[0].TextField[0]'
    
    # Reason Codes (checkboxes A-G)
    REASON_CODE_A = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[0]'  # Income
    REASON_CODE_B = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[1]'  # Deductions
    REASON_CODE_C = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[2]'  # Credits
    REASON_CODE_D = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[3]'  # Status change
    REASON_CODE_E = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[4]'  # Payments
    REASON_CODE_F = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[5]'  # Other
    REASON_CODE_G = 'topmostSubform[0].Page1[0].Part1[0].Reason[0].c1_2[6]'  # Other (continued)
    
    # Part II: Income and Deductions
    TOTAL_INCOME = 'topmostSubform[0].Page1[0].Part2[0].Line1[0].TextField[0]'
    STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].Part2[0].Line2[0].TextField[0]'
    TAXABLE_INCOME = 'topmostSubform[0].Page1[0].Part2[0].Line3[0].TextField[0]'
    
    # Part III: Tax Computation
    INCOME_TAX = 'topmostSubform[0].Page1[0].Part3[0].Line4[0].TextField[0]'
    
    # Part IV: Payments and Refundable Credits
    TOTAL_PAYMENTS = 'topmostSubform[0].Page1[0].Part4[0].Line5[0].TextField[0]'
    
    # Part V: Amount Due or Overpayment
    REFUND = 'topmostSubform[0].Page1[0].Part5[0].Line6[0].TextField[0]'
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].Part5[0].Line7[0].TextField[0]'
    
    # Explanation
    EXPLANATION = 'topmostSubform[0].Page1[0].Part6[0].Explanation[0].TextField[0]'
    
    # Checkbox Values
    CHECKBOX_CHECKED = '/1'
    CHECKBOX_UNCHECKED = '/0'


# State Tax Form Field Constants

class California540Fields:
    """Field names for California Form 540 (Individual Income Tax Return)"""

    # Personal Information
    SSN = 'topmostSubform[0].Page1[0].SSN[0]'
    FIRST_NAME = 'topmostSubform[0].Page1[0].FirstName[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].MI[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].LastName[0]'

    # Address
    ADDRESS = 'topmostSubform[0].Page1[0].Address[0]'
    CITY = 'topmostSubform[0].Page1[0].City[0]'
    STATE = 'topmostSubform[0].Page1[0].State[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].ZIP[0]'

    # Filing Status
    SINGLE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'
    MARRIED_FILING_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'
    MARRIED_FILING_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[2]'
    HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[3]'
    QUALIFYING_WIDOW = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[4]'

    # Income
    FEDERAL_ADJUSTED_GROSS_INCOME = 'topmostSubform[0].Page1[0].AGI[0]'
    ADDITIONS_TO_INCOME = 'topmostSubform[0].Page1[0].Additions[0]'
    SUBTRACTIONS_FROM_INCOME = 'topmostSubform[0].Page1[0].Subtractions[0]'
    CALIFORNIA_ADJUSTED_GROSS_INCOME = 'topmostSubform[0].Page1[0].CA_AGI[0]'

    # Deductions
    STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].StdDed[0]'
    ITEMIZED_DEDUCTIONS = 'topmostSubform[0].Page1[0].ItemDed[0]'

    # Tax and Credits
    TAX = 'topmostSubform[0].Page1[0].Tax[0]'
    TAX_CREDITS = 'topmostSubform[0].Page1[0].Credits[0]'
    NET_TAX = 'topmostSubform[0].Page1[0].NetTax[0]'

    # Payments
    WITHHOLDING = 'topmostSubform[0].Page1[0].Withholding[0]'
    ESTIMATED_PAYMENTS = 'topmostSubform[0].Page1[0].Estimated[0]'
    OTHER_PAYMENTS = 'topmostSubform[0].Page1[0].OtherPayments[0]'

    # Amount Due or Refund
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].AmountDue[0]'
    OVERPAID = 'topmostSubform[0].Page1[0].Overpaid[0]'


class NewYorkIT201Fields:
    """Field names for New York Form IT-201 (Resident Income Tax Return)"""

    # Personal Information
    SSN = 'topmostSubform[0].Page1[0].SSN[0]'
    FIRST_NAME = 'topmostSubform[0].Page1[0].FirstName[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].MI[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].LastName[0]'

    # Address
    ADDRESS = 'topmostSubform[0].Page1[0].Address[0]'
    CITY = 'topmostSubform[0].Page1[0].City[0]'
    STATE = 'topmostSubform[0].Page1[0].State[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].ZIP[0]'

    # Filing Status
    SINGLE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'
    MARRIED_FILING_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'
    MARRIED_FILING_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[2]'
    HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[3]'

    # Income
    FEDERAL_AGI = 'topmostSubform[0].Page1[0].FederalAGI[0]'
    NEW_YORK_ADDITIONS = 'topmostSubform[0].Page1[0].NYAdditions[0]'
    NEW_YORK_SUBTRACTIONS = 'topmostSubform[0].Page1[0].NYSubtractions[0]'
    NEW_YORK_AGI = 'topmostSubform[0].Page1[0].NY_AGI[0]'

    # Standard Deduction
    STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].StdDed[0]'

    # Tax Computation
    TAXABLE_INCOME = 'topmostSubform[0].Page1[0].TaxableIncome[0]'
    TAX_BEFORE_CREDITS = 'topmostSubform[0].Page1[0].TaxBeforeCredits[0]'
    TAX_CREDITS = 'topmostSubform[0].Page1[0].TaxCredits[0]'
    TAX_AFTER_CREDITS = 'topmostSubform[0].Page1[0].TaxAfterCredits[0]'

    # Other Taxes
    HOUSEHOLD_CREDIT = 'topmostSubform[0].Page1[0].HouseholdCredit[0]'
    INCOME_PERCENTAGE_TAX = 'topmostSubform[0].Page1[0].IncomePercentageTax[0]'

    # Payments
    WITHHOLDING = 'topmostSubform[0].Page1[0].Withholding[0]'
    ESTIMATED_PAYMENTS = 'topmostSubform[0].Page1[0].Estimated[0]'

    # Amount Due or Overpayment
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].AmountDue[0]'
    OVERPAID = 'topmostSubform[0].Page1[0].Overpaid[0]'


class NewJersey1040Fields:
    """Field names for New Jersey Form NJ-1040 (Gross Income Tax Return)"""

    # Personal Information
    SSN = 'topmostSubform[0].Page1[0].SSN[0]'
    FIRST_NAME = 'topmostSubform[0].Page1[0].FirstName[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].MI[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].LastName[0]'

    # Address
    ADDRESS = 'topmostSubform[0].Page1[0].Address[0]'
    CITY = 'topmostSubform[0].Page1[0].City[0]'
    STATE = 'topmostSubform[0].Page1[0].State[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].ZIP[0]'

    # Filing Status
    SINGLE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'
    MARRIED_FILING_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'
    MARRIED_FILING_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[2]'
    CIVIL_UNION_COUPLE_JOINT = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[3]'
    CIVIL_UNION_COUPLE_SEPARATE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[4]'
    HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[5]'

    # Gross Income
    WAGES = 'topmostSubform[0].Page1[0].Wages[0]'
    INTEREST = 'topmostSubform[0].Page1[0].Interest[0]'
    DIVIDENDS = 'topmostSubform[0].Page1[0].Dividends[0]'
    BUSINESS_INCOME = 'topmostSubform[0].Page1[0].BusinessIncome[0]'
    OTHER_INCOME = 'topmostSubform[0].Page1[0].OtherIncome[0]'
    TOTAL_GROSS_INCOME = 'topmostSubform[0].Page1[0].TotalGrossIncome[0]'

    # Deductions
    STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].StdDed[0]'

    # Exemptions
    PERSONAL_EXEMPTION = 'topmostSubform[0].Page1[0].PersonalExemption[0]'
    DEPENDENT_EXEMPTIONS = 'topmostSubform[0].Page1[0].DependentExemptions[0]'

    # Taxable Income
    TAXABLE_INCOME = 'topmostSubform[0].Page1[0].TaxableIncome[0]'

    # Tax
    TAX_DUE = 'topmostSubform[0].Page1[0].TaxDue[0]'

    # Credits
    TAX_CREDITS = 'topmostSubform[0].Page1[0].TaxCredits[0]'

    # Payments
    WITHHOLDING = 'topmostSubform[0].Page1[0].Withholding[0]'
    ESTIMATED_PAYMENTS = 'topmostSubform[0].Page1[0].Estimated[0]'

    # Amount Due or Refund
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].AmountDue[0]'
    OVERPAID = 'topmostSubform[0].Page1[0].Overpaid[0]'


class IllinoisIL1040Fields:
    """Field names for Illinois Form IL-1040 (Individual Income Tax Return)"""

    # Personal Information
    SSN = 'topmostSubform[0].Page1[0].SSN[0]'
    FIRST_NAME = 'topmostSubform[0].Page1[0].FirstName[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].MI[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].LastName[0]'

    # Address
    ADDRESS = 'topmostSubform[0].Page1[0].Address[0]'
    CITY = 'topmostSubform[0].Page1[0].City[0]'
    STATE = 'topmostSubform[0].Page1[0].State[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].ZIP[0]'

    # Filing Status
    SINGLE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'
    MARRIED_FILING_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'
    MARRIED_FILING_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[2]'
    HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[3]'

    # Federal Adjusted Gross Income
    FEDERAL_AGI = 'topmostSubform[0].Page1[0].FederalAGI[0]'

    # Illinois Additions
    ILLINOIS_ADDITIONS = 'topmostSubform[0].Page1[0].ILAdditions[0]'

    # Illinois Subtractions
    ILLINOIS_SUBTRACTIONS = 'topmostSubform[0].Page1[0].ILSubtractions[0]'

    # Illinois Base Income
    ILLINOIS_BASE_INCOME = 'topmostSubform[0].Page1[0].ILBaseIncome[0]'

    # Exemptions
    EXEMPTIONS = 'topmostSubform[0].Page1[0].Exemptions[0]'

    # Net Income
    NET_INCOME = 'topmostSubform[0].Page1[0].NetIncome[0]'

    # Tax
    TAX_DUE = 'topmostSubform[0].Page1[0].TaxDue[0]'

    # Credits
    TAX_CREDITS = 'topmostSubform[0].Page1[0].TaxCredits[0]'

    # Payments
    WITHHOLDING = 'topmostSubform[0].Page1[0].Withholding[0]'
    ESTIMATED_PAYMENTS = 'topmostSubform[0].Page1[0].Estimated[0]'

    # Amount Due or Refund
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].AmountDue[0]'
    OVERPAID = 'topmostSubform[0].Page1[0].Overpaid[0]'


class PennsylvaniaPA40Fields:
    """Field names for Pennsylvania Form PA-40 (Income Tax Return)"""

    # Personal Information
    SSN = 'topmostSubform[0].Page1[0].SSN[0]'
    FIRST_NAME = 'topmostSubform[0].Page1[0].FirstName[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].MI[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].LastName[0]'

    # Address
    ADDRESS = 'topmostSubform[0].Page1[0].Address[0]'
    CITY = 'topmostSubform[0].Page1[0].City[0]'
    STATE = 'topmostSubform[0].Page1[0].State[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].ZIP[0]'

    # Filing Status
    SINGLE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'
    MARRIED_FILING_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'
    MARRIED_FILING_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[2]'

    # Income
    FEDERAL_GROSS_INCOME = 'topmostSubform[0].Page1[0].FederalGrossIncome[0]'
    PENNSYLVANIA_ADDITIONS = 'topmostSubform[0].Page1[0].PAAdditions[0]'
    PENNSYLVANIA_SUBTRACTIONS = 'topmostSubform[0].Page1[0].PASubtractions[0]'

    # Taxable Income
    TAXABLE_INCOME = 'topmostSubform[0].Page1[0].TaxableIncome[0]'

    # Tax
    TAX_DUE = 'topmostSubform[0].Page1[0].TaxDue[0]'

    # Credits
    TAX_CREDITS = 'topmostSubform[0].Page1[0].TaxCredits[0]'

    # Payments
    WITHHOLDING = 'topmostSubform[0].Page1[0].Withholding[0]'
    ESTIMATED_PAYMENTS = 'topmostSubform[0].Page1[0].Estimated[0]'

    # Amount Due or Refund
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].AmountDue[0]'
    OVERPAID = 'topmostSubform[0].Page1[0].Overpaid[0]'


class Massachusetts1Fields:
    """Field names for Massachusetts Form 1 (Individual Income Tax Return)"""

    # Personal Information
    SSN = 'topmostSubform[0].Page1[0].SSN[0]'
    FIRST_NAME = 'topmostSubform[0].Page1[0].FirstName[0]'
    MIDDLE_INITIAL = 'topmostSubform[0].Page1[0].MI[0]'
    LAST_NAME = 'topmostSubform[0].Page1[0].LastName[0]'

    # Address
    ADDRESS = 'topmostSubform[0].Page1[0].Address[0]'
    CITY = 'topmostSubform[0].Page1[0].City[0]'
    STATE = 'topmostSubform[0].Page1[0].State[0]'
    ZIP_CODE = 'topmostSubform[0].Page1[0].ZIP[0]'

    # Filing Status
    SINGLE = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[0]'
    MARRIED_FILING_JOINTLY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[1]'
    MARRIED_FILING_SEPARATELY = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[2]'
    HEAD_OF_HOUSEHOLD = 'topmostSubform[0].Page1[0].FilingStatus[0].c1_1[3]'

    # Part 1: Income
    WAGES = 'topmostSubform[0].Page1[0].Wages[0]'
    INTEREST = 'topmostSubform[0].Page1[0].Interest[0]'
    DIVIDENDS = 'topmostSubform[0].Page1[0].Dividends[0]'
    BUSINESS_INCOME = 'topmostSubform[0].Page1[0].BusinessIncome[0]'
    OTHER_INCOME = 'topmostSubform[0].Page1[0].OtherIncome[0]'

    # Part 2: Adjustments to Income
    ADJUSTMENTS = 'topmostSubform[0].Page1[0].Adjustments[0]'

    # Part 3: Massachusetts Adjusted Gross Income
    MA_ADJUSTED_GROSS_INCOME = 'topmostSubform[0].Page1[0].MA_AGI[0]'

    # Part 4: Deductions
    STANDARD_DEDUCTION = 'topmostSubform[0].Page1[0].StdDed[0]'
    ITEMIZED_DEDUCTIONS = 'topmostSubform[0].Page1[0].ItemDed[0]'

    # Part 5: Taxable Income
    TAXABLE_INCOME = 'topmostSubform[0].Page1[0].TaxableIncome[0]'

    # Part 6: Tax
    TAX_DUE = 'topmostSubform[0].Page1[0].TaxDue[0]'

    # Part 7: Credits
    TAX_CREDITS = 'topmostSubform[0].Page1[0].TaxCredits[0]'

    # Part 8: Payments
    WITHHOLDING = 'topmostSubform[0].Page1[0].Withholding[0]'
    ESTIMATED_PAYMENTS = 'topmostSubform[0].Page1[0].Estimated[0]'

    # Part 9: Amount Due or Refund
    AMOUNT_DUE = 'topmostSubform[0].Page1[0].AmountDue[0]'
    OVERPAID = 'topmostSubform[0].Page1[0].Overpaid[0]'
