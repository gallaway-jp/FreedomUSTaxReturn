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
