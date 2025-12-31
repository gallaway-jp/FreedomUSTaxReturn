"""

TAX YEAR 2025:
This module is configured for the 2025 tax year (returns filed in 2026).
All tax brackets, standard deductions, and amounts are based on IRS
published 2025 tax year figures.
"""

from functools import lru_cache
from typing import Optional
from config.tax_year_config import get_tax_year_config

@lru_cache(maxsize=32)
def calculate_standard_deduction(filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate standard deduction based on filing status.
    
    Args:
        filing_status: Filing status code (Single, MFJ, MFS, HOH, QW)
        tax_year: Tax year for calculation (default: 2025)
        
    Returns:
        Standard deduction amount for the filing status and tax year
        
    Example:
        >>> calculate_standard_deduction('Single', 2025)
        15750.0
    """
    config = get_tax_year_config(tax_year)
    return config.standard_deductions.get(filing_status, config.standard_deductions["Single"])

@lru_cache(maxsize=128)
def calculate_income_tax(taxable_income: float, filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate federal income tax based on taxable income and filing status.
    
    Args:
        taxable_income: Amount of taxable income
        filing_status: Filing status code (Single, MFJ, MFS, HOH, QW)
        tax_year: Tax year for calculation (default: 2025)
        
    Returns:
        Calculated federal income tax amount
        
    Example:
        >>> calculate_income_tax(50000, 'Single', 2025)
        6328.0
    """
    
    config = get_tax_year_config(tax_year)
    brackets = config.tax_brackets.get(filing_status, config.tax_brackets["Single"])
    
    tax = 0.0
    prev_threshold = 0.0
    
    for threshold, rate in brackets:
        if taxable_income <= threshold:
            tax += (taxable_income - prev_threshold) * rate
            break
        else:
            tax += (threshold - prev_threshold) * rate
            prev_threshold = threshold
    
    return round(tax, 2)

def calculate_self_employment_tax(net_earnings: float) -> float:
    """
    Calculate self-employment tax (Social Security and Medicare).
    
    Args:
        net_earnings: Net earnings from self-employment
        
    Returns:
        Total self-employment tax amount
        
    Note:
        Includes Social Security (12.4%), Medicare (2.9%), and
        additional Medicare tax (0.9% over threshold)
    """
    if net_earnings <= 0:
        return 0.0
    
    config = get_tax_year_config()
    
    # 92.35% of net earnings subject to SE tax
    se_income = net_earnings * config.se_tax_rate
    
    # Social Security tax (12.4% up to wage base)
    ss_tax = min(se_income, config.ss_wage_base) * config.ss_tax_rate
    
    # Medicare tax (2.9% on all earnings)
    medicare_tax = se_income * config.medicare_tax_rate
    
    # Additional Medicare tax (0.9% over threshold)
    if se_income > config.medicare_threshold:
        additional_medicare = (se_income - config.medicare_threshold) * config.additional_medicare_rate
    else:
        additional_medicare = 0.0
    
    total_se_tax = ss_tax + medicare_tax + additional_medicare
    
    return round(total_se_tax, 2)

def calculate_child_tax_credit(num_qualifying_children: int, num_other_dependents: int, 
                               agi: float, filing_status: str) -> float:
    """
    Calculate Child Tax Credit.
    
    Args:
        num_qualifying_children: Number of qualifying children under 17
        num_other_dependents: Number of other dependents
        agi: Adjusted Gross Income
        filing_status: Filing status code
        
    Returns:
        Child tax credit amount (may be reduced by phaseout)
        
    Note:
        $2,000 per qualifying child under 17
        $500 per other dependent
    """
    if num_qualifying_children == 0 and num_other_dependents == 0:
        return 0.0
    
    config = get_tax_year_config()
    
    # Base credit amounts
    credit_per_child = config.child_tax_credit_amount
    credit_per_other = config.other_dependent_credit
    
    total_credit = (num_qualifying_children * credit_per_child + 
                   num_other_dependents * credit_per_other)
    
    # Phase-out thresholds
    thresholds = {
        "MFJ": 400000,
        "Single": 200000,
        "HOH": 200000,
        "MFS": 200000,
        "QW": 400000
    }
    
    threshold = thresholds.get(filing_status, 200000)
    
    # Phase out $50 for every $1,000 over threshold
    if agi > threshold:
        excess = agi - threshold
        reduction = (excess // 1000) * 50
        total_credit = max(0, total_credit - reduction)
    
    return round(total_credit, 2)

def calculate_earned_income_credit(earned_income, agi, num_children, filing_status):
    """
    Calculate Earned Income Credit (simplified)
    This is a complex calculation - this is a simplified version
    """
    # 2025 EIC limits
    if filing_status == "MFS":
        return 0  # Not eligible if MFS
    
    # Maximum AGI limits for 2025
    agi_limits = {
        0: {"Single": 17640, "MFJ": 24210},
        1: {"Single": 46560, "MFJ": 53120},
        2: {"Single": 52918, "MFJ": 59478},
        3: {"Single": 56838, "MFJ": 63398}
    }
    
    # Maximum credit amounts
    max_credits = {
        0: 600,
        1: 3995,
        2: 6604,
        3: 7430
    }
    
    num_children_key = min(num_children, 3)
    
    if filing_status == "MFJ":
        limit = agi_limits[num_children_key]["MFJ"]
    else:
        limit = agi_limits[num_children_key]["Single"]
    
    if agi > limit:
        return 0
    
    # Simplified calculation - actual is more complex
    max_credit = max_credits[num_children_key]
    
    # Phase in and phase out (simplified)
    if earned_income < 10000:
        credit = (earned_income / 10000) * max_credit
    else:
        credit = max_credit
    
    # Phase out based on AGI
    if agi > limit * 0.7:
        phase_out_rate = (agi - limit * 0.7) / (limit * 0.3)
        credit = credit * (1 - phase_out_rate)
    
    return round(max(0, credit), 2)

def calculate_education_credit_aotc(qualified_expenses: float, num_years_claimed: int) -> float:
    """
    Calculate American Opportunity Tax Credit (AOTC).
    
    Args:
        qualified_expenses: Qualified education expenses
        num_years_claimed: Number of years AOTC has been claimed (max 4)
        
    Returns:
        AOTC credit amount (max $2,500 per student)
        
    Note:
        100% of first $2,000 + 25% of next $2,000 in expenses
        Available for first 4 years of post-secondary education
    """
    if num_years_claimed >= 4:
        return 0.0  # Only first 4 years
    
    if qualified_expenses <= 0:
        return 0.0
    
    if qualified_expenses <= 2000:
        credit = qualified_expenses
    else:
        credit = 2000 + (min(qualified_expenses - 2000, 2000) * 0.25)
    
    return round(min(credit, 2500), 2)

def calculate_education_credit_llc(qualified_expenses: float) -> float:
    """
    Calculate Lifetime Learning Credit (LLC).
    
    Args:
        qualified_expenses: Qualified education expenses
        
    Returns:
        LLC credit amount (max $2,000)
        
    Note:
        20% of first $10,000 in qualified expenses
        No limit on number of years claimed
    """
    credit = min(qualified_expenses, 10000) * 0.20
    return round(min(credit, 2000), 2)


def calculate_retirement_savings_credit(contributions: float, agi: float, filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate Retirement Savings Contributions Credit (Saver's Credit).
    
    Args:
        contributions: Total retirement plan contributions (IRA, 401(k), etc.)
        agi: Adjusted Gross Income
        filing_status: Filing status code
        tax_year: Tax year for calculation
        
    Returns:
        Retirement savings credit amount
        
    Note:
        Credit is 50%, 20%, or 10% of contributions based on AGI
        Maximum contribution limit is $2,000 per person
        Credit phases out based on income thresholds
    """
    # Maximum credit contribution amount
    max_contribution = 2000
    
    # Limit contributions to maximum
    eligible_contributions = min(contributions, max_contribution)
    
    # Get income limits for the credit percentage
    config = get_tax_year_config(tax_year)
    income_limits = config.retirement_savings_credit_limits.get(filing_status, 
                                                               config.retirement_savings_credit_limits["Single"])
    
    # Determine credit percentage based on AGI
    if agi <= income_limits["50_percent"]:
        credit_rate = 0.50
    elif agi <= income_limits["20_percent"]:
        credit_rate = 0.20
    elif agi <= income_limits["10_percent"]:
        credit_rate = 0.10
    else:
        # No credit if AGI exceeds the 10% limit
        return 0.0
    
    credit = eligible_contributions * credit_rate
    return round(credit, 2)


def calculate_child_dependent_care_credit(expenses: float, agi: float, filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate Child and Dependent Care Credit.
    
    Args:
        expenses: Qualified child/dependent care expenses paid
        agi: Adjusted Gross Income
        filing_status: Filing status code
        tax_year: Tax year for calculation
        
    Returns:
        Child and dependent care credit amount
        
    Note:
        Credit is 35% of first $3,000 in expenses for one child/dependent
        Credit is 35% of first $6,000 in expenses for two or more children/dependents
        Credit phases out for high-income taxpayers
    """
    # Expense limits based on number of children/dependents
    # For simplicity, assume at least 2 children (most common case)
    # In a real implementation, this would be passed as a parameter
    expense_limit = 6000  # For 2+ children
    credit_rate = 0.35
    
    # Limit expenses to maximum eligible amount
    eligible_expenses = min(expenses, expense_limit)
    
    # Calculate base credit
    base_credit = eligible_expenses * credit_rate
    
    # Phase out for high income
    config = get_tax_year_config(tax_year)
    phase_out_limits = config.child_dependent_care_limits.get(filing_status,
                                                             config.child_dependent_care_limits["Single"])
    
    if agi > phase_out_limits["threshold"]:
        # Phase out $1 for every $2 of AGI over threshold
        phase_out_amount = (agi - phase_out_limits["threshold"]) / 2
        base_credit = max(0, base_credit - phase_out_amount)
    
    return round(base_credit, 2)


def calculate_residential_energy_credit(credit_amount: float) -> float:
    """
    Calculate Residential Energy Credit.
    
    Args:
        credit_amount: Amount of energy credit claimed (from Form 5695)
        
    Returns:
        Residential energy credit amount
        
    Note:
        This is a non-refundable credit for energy-efficient home improvements
        The amount is calculated on Form 5695 and entered directly
    """
    # The credit amount is calculated on IRS Form 5695
    # We just return the amount as entered by the user
    return round(credit_amount, 2)


def calculate_premium_tax_credit(credit_amount: float) -> float:
    """
    Calculate Premium Tax Credit (ACA).
    
    Args:
        credit_amount: Amount of premium tax credit from Form 1095-A
        
    Returns:
        Premium tax credit amount
        
    Note:
        This is the credit for health insurance premiums purchased through
        the Health Insurance Marketplace. The amount is calculated by the IRS
        and reported on Form 1095-A.
    """
    # The credit amount is calculated by the IRS based on income and premium costs
    # We just return the amount as entered by the user
    return round(credit_amount, 2)


def calculate_alternative_minimum_tax(agi: float, filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate Alternative Minimum Tax (AMT).
    
    Args:
        agi: Adjusted Gross Income
        filing_status: Filing status code
        tax_year: Tax year for calculation
        
    Returns:
        Alternative Minimum Tax amount
        
    Note:
        AMT is calculated using Form 6251. This is a simplified implementation
        that calculates the tentative minimum tax and compares it to regular tax.
    """
    config = get_tax_year_config(tax_year)
    
    # Get AMT exemption amount
    exemption = config.amt_exemptions.get(filing_status, config.amt_exemptions["Single"])
    
    # Phase out exemption for high income
    phase_out_threshold = config.amt_phase_out_thresholds.get(filing_status, 
                                                             config.amt_phase_out_thresholds["Single"])
    
    if agi > phase_out_threshold:
        # Exemption phases out at 25 cents per dollar over threshold
        excess = agi - phase_out_threshold
        exemption_reduction = excess * 0.25
        exemption = max(0, exemption - exemption_reduction)
    
    # AMT taxable income = AGI - exemption
    amt_taxable_income = max(0, agi - exemption)
    
    # Calculate tentative AMT using AMT tax brackets
    # AMT brackets are: 26% on first $220,700, 28% on excess
    amt_bracket_1_threshold = 220700.0
    
    if amt_taxable_income <= amt_bracket_1_threshold:
        tentative_amt = amt_taxable_income * 0.26
    else:
        tentative_amt = (amt_bracket_1_threshold * 0.26) + \
                       ((amt_taxable_income - amt_bracket_1_threshold) * 0.28)
    
    # Calculate regular tax for comparison
    regular_tax = calculate_income_tax(amt_taxable_income, filing_status, tax_year)
    
    # AMT is the excess of tentative AMT over regular tax
    amt = max(0, tentative_amt - regular_tax)
    
    return round(amt, 2)


def calculate_net_investment_income_tax(investment_income: float, agi: float, 
                                       filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate Net Investment Income Tax (NIIT).
    
    Args:
        investment_income: Net investment income (interest, dividends, capital gains, etc.)
        agi: Adjusted Gross Income
        filing_status: Filing status code
        tax_year: Tax year for calculation
        
    Returns:
        Net Investment Income Tax amount (3.8% of investment income over threshold)
        
    Note:
        NIIT applies to individuals with AGI over certain thresholds.
        The tax rate is 3.8% on the lesser of net investment income or
        the amount by which AGI exceeds the threshold.
    """
    config = get_tax_year_config(tax_year)
    
    # Get NIIT threshold
    threshold = config.niit_thresholds.get(filing_status, config.niit_thresholds["Single"])
    
    if agi <= threshold:
        return 0.0
    
    # NIIT applies to the lesser of:
    # 1. Net investment income
    # 2. AGI minus threshold
    niit_base = min(investment_income, agi - threshold)
    
    # Tax rate is 3.8%
    niit = niit_base * 0.038
    
    return round(niit, 2)


def calculate_additional_medicare_tax(wages: float, investment_income: float, 
                                    filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate Additional Medicare Tax on wages and investment income.
    
    Args:
        wages: Total wages and compensation
        investment_income: Net investment income
        filing_status: Filing status code
        tax_year: Tax year for calculation
        
    Returns:
        Additional Medicare Tax amount (0.9% on combined income over threshold)
        
    Note:
        Additional Medicare Tax applies to the combined wages and net investment 
        income that exceed $200,000 (single) or $250,000 (MFJ).
        This is separate from the additional Medicare tax on self-employment income.
    """
    config = get_tax_year_config(tax_year)
    
    # Threshold for additional Medicare tax
    threshold = config.niit_thresholds.get(filing_status, config.niit_thresholds["Single"])
    
    # Combined income subject to additional Medicare tax
    combined_income = wages + investment_income
    
    if combined_income <= threshold:
        return 0.0
    
    # Additional Medicare tax applies to the excess over threshold
    excess = combined_income - threshold
    additional_medicare_tax = excess * config.additional_medicare_rate
    
    return round(additional_medicare_tax, 2)


@lru_cache(maxsize=128)
def calculate_child_dependent_care_credit(expenses: float, agi: float, 
                                        filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate Child and Dependent Care Credit.
    
    Args:
        expenses: Qualifying child and dependent care expenses
        agi: Adjusted Gross Income
        filing_status: Filing status code
        tax_year: Tax year for calculation
        
    Returns:
        Child and dependent care credit amount
        
    Note:
        Credit is 35% of qualifying expenses up to $3,000 for one qualifying 
        individual or $6,000 for two or more. Credit phases out for high-income taxpayers.
    """
    config = get_tax_year_config(tax_year)
    
    # Maximum qualifying expenses based on number of children
    # For simplicity, assume 2+ children (most common case) - max $6,000
    max_expenses = 6000.0
    
    # Limit expenses to maximum qualifying amount
    qualifying_expenses = min(expenses, max_expenses)
    
    # Base credit rate is 35%
    credit_rate = 0.35
    
    # Check for phase-out
    phase_out_threshold = config.child_dependent_care_limits.get(filing_status, 
                                                                config.child_dependent_care_limits["Single"])["threshold"]
    
    if agi > phase_out_threshold:
        # Phase out $1 of credit for every $2 of AGI over threshold
        phase_out_amount = (agi - phase_out_threshold) / 2
        credit_rate = max(0, credit_rate - (phase_out_amount / qualifying_expenses))
    
    credit = qualifying_expenses * credit_rate
    
    return round(credit, 2)
