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
