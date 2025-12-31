"""
Tax Year Service - Handle tax year selection and multi-year support

This module provides functionality for:
- Tax year selection and configuration
- Multi-year tax return management
- Year-over-year comparisons
- Carryover tracking between tax years
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import json
import os
from pathlib import Path
from config.app_config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class TaxYearConfig:
    """Configuration for a specific tax year"""
    year: int
    filing_deadline: date
    standard_deduction: Dict[str, float]  # by filing status
    personal_exemption: float
    dependent_exemption: float
    capital_gains_brackets: List[Tuple[float, float]]
    ordinary_income_brackets: List[Tuple[float, float]]
    alternative_minimum_tax: float
    earned_income_credit: Dict[str, float]
    child_tax_credit: float
    retirement_limits: Dict[str, float]
    health_savings_limits: Dict[str, float]
    education_credits: Dict[str, float]


@dataclass
class CarryoverItem:
    """Represents an item that can carry over between tax years"""
    item_type: str  # 'capital_loss', 'charitable_contribution', 'medical_expense', etc.
    description: str
    amount: float
    tax_year: int
    expiration_year: Optional[int] = None  # Some items expire
    used_amount: float = 0.0


class TaxYearService:
    """
    Service for managing tax year configurations and multi-year support.

    Handles tax year selection, configuration loading, and carryover tracking.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the tax year service.
        
        Args:
            config: Application configuration (optional)
        """
        self.config = config
        self.current_year = date.today().year
        self.supported_years = list(range(2020, self.current_year + 2))  # Support last 5 years + current + next
        self.year_configs = self._load_tax_year_configs()
        self.carryover_items: Dict[int, List[CarryoverItem]] = {}

    def _load_tax_year_configs(self) -> Dict[int, TaxYearConfig]:
        """Load tax year configurations for all supported years"""
        configs = {}

        # Load configurations for each supported year
        for year in self.supported_years:
            config = self._get_tax_year_config(year)
            if config:
                configs[year] = config

        return configs

    def _get_tax_year_config(self, year: int) -> Optional[TaxYearConfig]:
        """Get configuration for a specific tax year"""
        # This would typically load from a configuration file or database
        # For now, we'll create configurations programmatically

        # Base configuration that gets updated for each year
        base_config = {
            "standard_deduction": {
                "single": 12950,
                "married_joint": 25900,
                "head_household": 19400,
                "married_separate": 12950,
                "qualifying_widow": 25900
            },
            "personal_exemption": 0,  # Eliminated in TCJA
            "dependent_exemption": 0,  # Eliminated in TCJA
            "alternative_minimum_tax": 0.0,
            "child_tax_credit": 2000,
            "retirement_limits": {
                "traditional_ira": 6000,
                "roth_ira": 6000,
                "401k": 20500
            },
            "health_savings_limits": {
                "individual": 3550,
                "family": 7100
            }
        }

        # Adjust for specific years
        if year >= 2025:
            # 2025 tax brackets (projected)
            ordinary_brackets = [
                (0, 0.10), (11000, 0.12), (44725, 0.22), (95375, 0.24),
                (182100, 0.32), (231250, 0.35), (578125, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (44625, 0.15), (49250, 0.20)
            ]
            eic_amounts = {"single": 538, "married_joint": 538, "head_household": 538}
            # Filing deadlines are in the year following the tax year
            filing_deadline = date(year + 1, 4, 15)  # April 15 of next year

        elif year == 2024:
            ordinary_brackets = [
                (0, 0.10), (11000, 0.12), (44725, 0.22), (95375, 0.24),
                (182100, 0.32), (231250, 0.35), (578125, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (44625, 0.15), (49250, 0.20)
            ]
            eic_amounts = {"single": 538, "married_joint": 538, "head_household": 538}
            filing_deadline = date(year + 1, 4, 15)

        elif year == 2024:
            ordinary_brackets = [
                (0, 0.10), (11000, 0.12), (44725, 0.22), (95375, 0.24),
                (182100, 0.32), (231250, 0.35), (578125, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (44625, 0.15), (49250, 0.20)
            ]
            eic_amounts = {"single": 538, "married_joint": 538, "head_household": 538}
            filing_deadline = date(year + 1, 4, 15)

        elif year == 2022:
            ordinary_brackets = [
                (0, 0.10), (10275, 0.12), (41775, 0.22), (89075, 0.24),
                (170050, 0.32), (215950, 0.35), (539900, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (41675, 0.15), (45975, 0.20)
            ]
            eic_amounts = {"single": 560, "married_joint": 560, "head_household": 560}
            filing_deadline = date(year + 1, 4, 15)

        elif year == 2021:
            ordinary_brackets = [
                (0, 0.10), (9950, 0.12), (40525, 0.22), (86375, 0.24),
                (164925, 0.32), (209425, 0.35), (523600, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (40425, 0.15), (44550, 0.20)
            ]
            eic_amounts = {"single": 1502, "married_joint": 1502, "head_household": 1502}
            filing_deadline = date(year + 1, 4, 15)

        elif year == 2020:
            ordinary_brackets = [
                (0, 0.10), (9700, 0.12), (39475, 0.22), (84200, 0.24),
                (160725, 0.32), (204100, 0.35), (510300, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (39375, 0.15), (43350, 0.20)
            ]
            eic_amounts = {"single": 538, "married_joint": 538, "head_household": 538}
            filing_deadline = date(year + 1, 4, 15)

        else:
            # Default/fallback configuration
            ordinary_brackets = [
                (0, 0.10), (11000, 0.12), (44725, 0.22), (95375, 0.24),
                (182100, 0.32), (231250, 0.35), (578125, 0.37)
            ]
            capital_gains_brackets = [
                (0, 0.0), (44625, 0.15), (49250, 0.20)
            ]
            eic_amounts = {"single": 538, "married_joint": 538, "head_household": 538}
            filing_deadline = date(year + 1, 4, 15)

        return TaxYearConfig(
            year=year,
            filing_deadline=filing_deadline,
            standard_deduction=base_config["standard_deduction"],
            personal_exemption=base_config["personal_exemption"],
            dependent_exemption=base_config["dependent_exemption"],
            capital_gains_brackets=capital_gains_brackets,
            ordinary_income_brackets=ordinary_brackets,
            alternative_minimum_tax=base_config["alternative_minimum_tax"],
            earned_income_credit=eic_amounts,
            child_tax_credit=base_config["child_tax_credit"],
            retirement_limits=base_config["retirement_limits"],
            health_savings_limits=base_config["health_savings_limits"],
            education_credits={"aotc": 2500, "llc": 2000}
        )

    def get_supported_years(self) -> List[int]:
        """Get list of supported tax years"""
        return sorted(self.supported_years, reverse=True)  # Most recent first

    def get_tax_year_config(self, year: int) -> Optional[TaxYearConfig]:
        """Get configuration for a specific tax year"""
        return self.year_configs.get(year)

    def get_current_tax_year(self) -> int:
        """Get the current tax year (typically the previous calendar year)"""
        current_date = date.today()
        if current_date.month >= 4:  # After April 15
            return current_date.year
        else:
            return current_date.year - 1

    def is_tax_year_open(self, year: int) -> bool:
        """Check if a tax year is still open for filing/amending"""
        config = self.get_tax_year_config(year)
        if not config:
            return False

        # Generally, returns can be filed up to 3 years after the original deadline
        extension_deadline = date(year + 1, 10, 15)  # October 15 of next year
        return date.today() <= extension_deadline

    def create_new_tax_year(self, base_year: int, new_year: int) -> Dict[str, Any]:
        """
        Create a new tax return for a different year based on an existing return.

        Args:
            base_year: Year of the existing return
            new_year: Year for the new return

        Returns:
            New tax data structure for the specified year
        """
        # This would copy relevant data from the base year and adjust for the new year
        # For now, return a basic structure
        return {
            "personal_info": {},
            "filing_status": "single",
            "income": {},
            "deductions": {},
            "credits": {},
            "payments": {},
            "state_taxes": {"selected_states": [], "calculations": {}, "forms": [], "filings": []},
            "metadata": {
                "tax_year": new_year,
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "version": "1.0",
                "based_on_year": base_year
            }
        }

    def add_carryover_item(self, tax_year: int, item: CarryoverItem):
        """Add a carryover item for a specific tax year"""
        if tax_year not in self.carryover_items:
            self.carryover_items[tax_year] = []
        self.carryover_items[tax_year].append(item)

    def get_carryover_items(self, tax_year: int, item_type: Optional[str] = None) -> List[CarryoverItem]:
        """Get carryover items for a specific tax year"""
        items = self.carryover_items.get(tax_year, [])
        if item_type:
            items = [item for item in items if item.item_type == item_type]
        return items

    def use_carryover_amount(self, tax_year: int, item_type: str, amount: float) -> bool:
        """
        Mark a portion of carryover amount as used.

        Returns True if successful, False if insufficient carryover available.
        """
        items = self.get_carryover_items(tax_year, item_type)
        available_amount = sum(item.amount - item.used_amount for item in items)

        if available_amount >= amount:
            # Mark items as used (simplified - would need more sophisticated logic)
            remaining_to_use = amount
            for item in items:
                available = item.amount - item.used_amount
                if available > 0:
                    use_amount = min(remaining_to_use, available)
                    item.used_amount += use_amount
                    remaining_to_use -= use_amount
                    if remaining_to_use <= 0:
                        break
            return True
        return False

    def get_year_comparison_data(self, year1: int, year2: int, tax_data1: Dict, tax_data2: Dict) -> Dict[str, Any]:
        """
        Generate year-over-year comparison data.

        Args:
            year1: First tax year
            year2: Second tax year
            tax_data1: Tax data for year 1
            tax_data2: Tax data for year 2

        Returns:
            Comparison data structure
        """
        comparison = {
            "years": [year1, year2],
            "income_comparison": {},
            "deductions_comparison": {},
            "credits_comparison": {},
            "tax_comparison": {},
            "summary": {}
        }

        # Compare key metrics
        metrics = [
            ("total_income", "income", "Total Income"),
            ("total_deductions", "deductions", "Total Deductions"),
            ("taxable_income", "calculations", "Taxable Income"),
            ("total_tax", "calculations", "Total Tax"),
            ("total_credits", "credits", "Total Credits"),
            ("refund_owed", "calculations", "Refund/Owed")
        ]

        for metric_key, data_section, display_name in metrics:
            val1 = self._extract_metric_value(tax_data1, metric_key, data_section)
            val2 = self._extract_metric_value(tax_data2, metric_key, data_section)

            comparison["summary"][metric_key] = {
                "year1": val1,
                "year2": val2,
                "difference": val2 - val1,
                "percent_change": ((val2 - val1) / val1 * 100) if val1 != 0 else 0
            }

        return comparison

    def _extract_metric_value(self, tax_data: Dict, metric: str, section: str) -> float:
        """Extract a metric value from tax data"""
        try:
            if section == "calculations":
                # These are calculated values that might not be stored directly
                return tax_data.get("calculations", {}).get(metric, 0)
            else:
                return tax_data.get(section, {}).get(metric, 0)
        except (KeyError, TypeError):
            return 0

    def get_filing_deadline(self, year: int) -> Optional[date]:
        """Get the filing deadline for a tax year"""
        config = self.get_tax_year_config(year)
        return config.filing_deadline if config else None

    def get_days_until_deadline(self, year: int) -> Optional[int]:
        """Get days until filing deadline for a tax year"""
        deadline = self.get_filing_deadline(year)
        if deadline:
            today = date.today()
            if today <= deadline:
                return (deadline - today).days
            else:
                return -1 * (today - deadline).days  # Negative means past deadline
        return None

    def validate_tax_year_data(self, tax_data: Dict) -> List[str]:
        """
        Validate that tax data is appropriate for its tax year.

        Returns list of validation warnings/errors.
        """
        warnings = []
        tax_year = tax_data.get("metadata", {}).get("tax_year", self.get_current_tax_year())

        # Check if tax year is supported
        if tax_year not in self.supported_years:
            warnings.append(f"Tax year {tax_year} is not fully supported. Some calculations may be inaccurate.")

        # Check filing deadline
        days_until = self.get_days_until_deadline(tax_year)
        if days_until is not None and days_until < 0:
            warnings.append(f"Filing deadline for tax year {tax_year} has passed.")

        return warnings