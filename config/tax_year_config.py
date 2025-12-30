"""
Tax year specific configuration (tax brackets, deductions, thresholds)

This module centralizes all tax year specific values to make it easy
to update for new tax years without modifying calculation logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class TaxYearConfig:
    """
    Tax year specific configuration for IRS tax calculations.
    
    All amounts are based on IRS published tax year figures.
    """
    
    year: int
    
    # Standard deductions by filing status
    standard_deductions: Dict[str, float]
    
    # Tax brackets: List of (threshold, rate) tuples by filing status
    tax_brackets: Dict[str, List[Tuple[float, float]]]
    
    # Self-employment tax thresholds
    ss_wage_base: float
    medicare_threshold: float
    
    # Alternative Minimum Tax (AMT) thresholds
    amt_exemptions: Dict[str, float]
    amt_phase_out_thresholds: Dict[str, float]
    
    # Net Investment Income Tax (NIIT) thresholds
    niit_thresholds: Dict[str, float]
    
    # Retirement savings credit income limits by filing status
    retirement_savings_credit_limits: Dict[str, Dict[str, float]]
    
    # Child and dependent care credit phase-out limits
    child_dependent_care_limits: Dict[str, Dict[str, float]]
    
    # Retirement contribution limits
    retirement_limits: Dict[str, float]
    
    # IRA deductibility limits by filing status
    ira_deductibility_limits: Dict[str, Dict[str, float]]
    
    additional_medicare_rate: float = 0.009
    
    # Child tax credit amounts
    child_tax_credit_amount: float = 2000.0
    other_dependent_credit: float = 500.0
    
    # Education credits
    aotc_max_credit: float = 2500.0
    llc_max_credit: float = 2000.0
    
    # SE tax rates
    se_tax_rate: float = 0.9235
    ss_tax_rate: float = 0.124
    medicare_tax_rate: float = 0.029


# Tax Year 2025 Configuration
TAX_YEAR_2025 = TaxYearConfig(
    year=2025,
    
    standard_deductions={
        "Single": 15750.0,
        "MFJ": 31500.0,  # Married Filing Jointly
        "Married Filing Jointly": 31500.0,
        "MFS": 15750.0,  # Married Filing Separately
        "Married Filing Separately": 15750.0,
        "HOH": 23625.0,  # Head of Household
        "Head of Household": 23625.0,
        "QW": 31500.0,   # Qualifying Widow(er)
        "Qualifying Widow(er)": 31500.0,
    },
    
    tax_brackets={
        "Single": [
            (11925, 0.10),
            (48475, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250525, 0.32),
            (626350, 0.35),
            (float('inf'), 0.37)
        ],
        "MFJ": [
            (23850, 0.10),
            (96950, 0.12),
            (206700, 0.22),
            (394600, 0.24),
            (501050, 0.32),
            (751600, 0.35),
            (float('inf'), 0.37)
        ],
        "Married Filing Jointly": [  # Same as MFJ
            (23850, 0.10),
            (96950, 0.12),
            (206700, 0.22),
            (394600, 0.24),
            (501050, 0.32),
            (751600, 0.35),
            (float('inf'), 0.37)
        ],
        "MFS": [
            (11925, 0.10),
            (48475, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250525, 0.32),
            (375800, 0.35),
            (float('inf'), 0.37)
        ],
        "Married Filing Separately": [  # Same as MFS
            (11925, 0.10),
            (48475, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250525, 0.32),
            (375800, 0.35),
            (float('inf'), 0.37)
        ],
        "HOH": [
            (17000, 0.10),
            (64850, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250500, 0.32),
            (626350, 0.35),
            (float('inf'), 0.37)
        ],
        "Head of Household": [  # Same as HOH
            (17000, 0.10),
            (64850, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250500, 0.32),
            (626350, 0.35),
            (float('inf'), 0.37)
        ],
        "QW": [
            (23850, 0.10),
            (96950, 0.12),
            (206700, 0.22),
            (394600, 0.24),
            (501050, 0.32),
            (751600, 0.35),
            (float('inf'), 0.37)
        ],
        "Qualifying Widow(er)": [  # Same as QW
            (23850, 0.10),
            (96950, 0.12),
            (206700, 0.22),
            (394600, 0.24),
            (501050, 0.32),
            (751600, 0.35),
            (float('inf'), 0.37)
        ]
    },
    
    ss_wage_base=176100.0,
    medicare_threshold=200000.0,
    
    # Alternative Minimum Tax (AMT) thresholds for 2025
    amt_exemptions={
        "Single": 81300.0,
        "MFJ": 126500.0,
        "Married Filing Jointly": 126500.0,
        "MFS": 63250.0,
        "Married Filing Separately": 63250.0,
        "HOH": 81300.0,
        "Head of Household": 81300.0,
        "QW": 126500.0,
        "Qualifying Widow(er)": 126500.0,
    },
    amt_phase_out_thresholds={
        "Single": 609350.0,
        "MFJ": 1218700.0,
        "Married Filing Jointly": 1218700.0,
        "MFS": 609350.0,
        "Married Filing Separately": 609350.0,
        "HOH": 609350.0,
        "Head of Household": 609350.0,
        "QW": 1218700.0,
        "Qualifying Widow(er)": 1218700.0,
    },
    
    # Net Investment Income Tax (NIIT) thresholds for 2025
    niit_thresholds={
        "Single": 200000.0,
        "MFJ": 250000.0,
        "Married Filing Jointly": 250000.0,
        "MFS": 125000.0,
        "Married Filing Separately": 125000.0,
        "HOH": 200000.0,
        "Head of Household": 200000.0,
        "QW": 250000.0,
        "Qualifying Widow(er)": 250000.0,
    },
    
    # Retirement savings credit limits (AGI thresholds for credit percentages)
    retirement_savings_credit_limits={
        "Single": {
            "50_percent": 37500,  # 50% credit up to $37,500 AGI
            "20_percent": 41250,  # 20% credit up to $41,250 AGI
            "10_percent": 68750,  # 10% credit up to $68,750 AGI
        },
        "MFJ": {
            "50_percent": 75000,
            "20_percent": 82500,
            "10_percent": 137500,
        },
        "Married Filing Jointly": {
            "50_percent": 75000,
            "20_percent": 82500,
            "10_percent": 137500,
        },
        "MFS": {
            "50_percent": 37500,
            "20_percent": 41250,
            "10_percent": 68750,
        },
        "Married Filing Separately": {
            "50_percent": 37500,
            "20_percent": 41250,
            "10_percent": 68750,
        },
        "HOH": {
            "50_percent": 56250,
            "20_percent": 61875,
            "10_percent": 103125,
        },
        "Head of Household": {
            "50_percent": 56250,
            "20_percent": 61875,
            "10_percent": 103125,
        },
        "QW": {
            "50_percent": 75000,
            "20_percent": 82500,
            "10_percent": 137500,
        },
        "Qualifying Widow(er)": {
            "50_percent": 75000,
            "20_percent": 82500,
            "10_percent": 137500,
        },
    },
    
    # Child and dependent care credit phase-out limits
    child_dependent_care_limits={
        "Single": {
            "threshold": 15000,  # Phase out starts at $15,000 AGI
        },
        "MFJ": {
            "threshold": 30000,  # Phase out starts at $30,000 AGI
        },
        "Married Filing Jointly": {
            "threshold": 30000,
        },
        "MFS": {
            "threshold": 15000,
        },
        "Married Filing Separately": {
            "threshold": 15000,
        },
        "HOH": {
            "threshold": 15000,
        },
        "Head of Household": {
            "threshold": 15000,
        },
        "QW": {
            "threshold": 30000,
        },
        "Qualifying Widow(er)": {
            "threshold": 30000,
        },
    },
    
    # Retirement contribution limits for 2025
    retirement_limits={
        "traditional_ira": 7000.0,  # $7,000 for 2025
        "roth_ira": 7000.0,         # $7,000 for 2025
        "401k": 23000.0,            # $23,000 for 2025
        "catch_up_50_plus": 1000.0, # Additional catch-up contribution
    },
    
    # IRA deductibility limits (Modified AGI limits for Traditional IRA deductions)
    ira_deductibility_limits={
        "Single": {
            "magi_limit": 77000,  # Full deduction up to $77,000 MAGI for 2025
        },
        "MFJ": {
            "magi_limit": 123000,  # Full deduction up to $123,000 MAGI for 2025
        },
        "Married Filing Jointly": {
            "magi_limit": 123000,
        },
        "MFS": {
            "magi_limit": 10000,  # Very low limit for separate filers
        },
        "Married Filing Separately": {
            "magi_limit": 10000,
        },
        "HOH": {
            "magi_limit": 77000,
        },
        "Head of Household": {
            "magi_limit": 77000,
        },
        "QW": {
            "magi_limit": 123000,
        },
        "Qualifying Widow(er)": {
            "magi_limit": 123000,
        },
    },
)


# Tax Year 2023 Configuration (for backward compatibility)
TAX_YEAR_2023 = TaxYearConfig(
    year=2023,
    
    standard_deductions={
        "Single": 13850.0,
        "MFJ": 27700.0,
        "MFS": 13850.0,
        "HOH": 20800.0,
        "QW": 27700.0,
    },
    
    tax_brackets={
        "Single": [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (578125, 0.35),
            (float('inf'), 0.37)
        ],
        "MFJ": [
            (22000, 0.10),
            (89050, 0.12),
            (190750, 0.22),
            (364200, 0.24),
            (462500, 0.32),
            (693750, 0.35),
            (float('inf'), 0.37)
        ],
        "MFS": [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (346875, 0.35),
            (float('inf'), 0.37)
        ],
        "HOH": [
            (15700, 0.10),
            (59850, 0.12),
            (95350, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (578100, 0.35),
            (float('inf'), 0.37)
        ],
        "QW": [
            (22000, 0.10),
            (89050, 0.12),
            (190750, 0.22),
            (364200, 0.24),
            (462500, 0.32),
            (693750, 0.35),
            (float('inf'), 0.37)
        ]
    },
    
    ss_wage_base=160200.0,
    medicare_threshold=200000.0,
    
    # Alternative Minimum Tax (AMT) thresholds for 2023
    amt_exemptions={
        "Single": 75900.0,
        "MFJ": 118100.0,
        "MFS": 59050.0,
        "HOH": 75900.0,
        "QW": 118100.0,
    },
    amt_phase_out_thresholds={
        "Single": 578150.0,
        "MFJ": 1156300.0,
        "MFS": 578150.0,
        "HOH": 578150.0,
        "QW": 1156300.0,
    },
    
    # Net Investment Income Tax (NIIT) thresholds for 2023
    niit_thresholds={
        "Single": 200000.0,
        "MFJ": 250000.0,
        "MFS": 125000.0,
        "HOH": 200000.0,
        "QW": 250000.0,
    },
    
    # Retirement savings credit limits (2023 values)
    retirement_savings_credit_limits={
        "Single": {
            "50_percent": 35000,
            "20_percent": 38500,
            "10_percent": 64125,
        },
        "MFJ": {
            "50_percent": 70000,
            "20_percent": 77000,
            "10_percent": 128250,
        },
        "MFS": {
            "50_percent": 35000,
            "20_percent": 38500,
            "10_percent": 64125,
        },
        "HOH": {
            "50_percent": 52500,
            "20_percent": 57750,
            "10_percent": 96125,
        },
        "QW": {
            "50_percent": 70000,
            "20_percent": 77000,
            "10_percent": 128250,
        }
    },
    
    # Child and dependent care credit phase-out limits (2023 values)
    child_dependent_care_limits={
        "Single": {
            "threshold": 15000,
        },
        "MFJ": {
            "threshold": 30000,
        },
        "MFS": {
            "threshold": 15000,
        },
        "HOH": {
            "threshold": 15000,
        },
        "QW": {
            "threshold": 30000,
        }
    },
    
    # Retirement contribution limits for 2023
    retirement_limits={
        "traditional_ira": 6500.0,  # $6,500 for 2023
        "roth_ira": 6500.0,         # $6,500 for 2023
        "401k": 22500.0,            # $22,500 for 2023
        "catch_up_50_plus": 1000.0, # Additional catch-up contribution
    },
    
    # IRA deductibility limits (Modified AGI limits for Traditional IRA deductions)
    ira_deductibility_limits={
        "Single": {
            "magi_limit": 73000,  # Full deduction up to $73,000 MAGI for 2023
        },
        "MFJ": {
            "magi_limit": 116000,  # Full deduction up to $116,000 MAGI for 2023
        },
        "Married Filing Jointly": {
            "magi_limit": 116000,
        },
        "MFS": {
            "magi_limit": 10000,  # Very low limit for separate filers
        },
        "Married Filing Separately": {
            "magi_limit": 10000,
        },
        "HOH": {
            "magi_limit": 73000,
        },
        "Head of Household": {
            "magi_limit": 73000,
        },
        "QW": {
            "magi_limit": 116000,
        },
        "Qualifying Widow(er)": {
            "magi_limit": 116000,
        },
    },
)


# Registry of available tax year configurations
TAX_YEAR_CONFIGS = {
    2025: TAX_YEAR_2025,
    2023: TAX_YEAR_2023,
}


def get_tax_year_config(year: int = 2025) -> TaxYearConfig:
    """
    Get tax year configuration for specified year.
    
    Args:
        year: Tax year (e.g., 2025)
        
    Returns:
        TaxYearConfig for the specified year
        
    Raises:
        ValueError: If tax year configuration not available
        
    Example:
        >>> config = get_tax_year_config(2025)
        >>> config.standard_deductions['Single']
        15750.0
    """
    if year not in TAX_YEAR_CONFIGS:
        raise ValueError(
            f"Tax year {year} configuration not available. "
            f"Available years: {sorted(TAX_YEAR_CONFIGS.keys())}"
        )
    return TAX_YEAR_CONFIGS[year]
