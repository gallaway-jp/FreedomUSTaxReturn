"""
Foreign Income and FBAR Service

Handles foreign income reporting and FBAR (Foreign Bank Account Report) requirements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from config.app_config import AppConfig
from models.tax_data import TaxData
from utils.error_tracker import get_error_tracker

logger = logging.getLogger(__name__)


class FBARThreshold(Enum):
    """FBAR reporting thresholds"""
    SINGLE_2025 = 10000  # $10,000 for single filers in 2025
    MARRIED_2025 = 20000  # $20,000 for married filing jointly in 2025


class ForeignAccountType(Enum):
    """Types of foreign financial accounts"""
    BANK_ACCOUNT = "bank_account"
    SECURITIES_ACCOUNT = "securities_account"
    MUTUAL_FUND = "mutual_fund"
    TRUST = "trust"
    INSURANCE_POLICY = "insurance_policy"
    ANNUITY = "annuity"
    OTHER = "other"


@dataclass
class ForeignAccount:
    """A foreign financial account for FBAR reporting"""

    account_number: str
    institution_name: str
    account_type: ForeignAccountType
    country: str
    currency: str
    max_value_during_year: Decimal
    year_end_value: Decimal
    was_closed: bool
    closed_date: Optional[date] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'account_number': self.account_number,
            'institution_name': self.institution_name,
            'account_type': self.account_type.value,
            'country': self.country,
            'currency': self.currency,
            'max_value_during_year': str(self.max_value_during_year),
            'year_end_value': str(self.year_end_value),
            'was_closed': self.was_closed,
            'closed_date': self.closed_date.isoformat() if self.closed_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForeignAccount':
        """Create from dictionary"""
        return cls(
            account_number=data['account_number'],
            institution_name=data['institution_name'],
            account_type=ForeignAccountType(data['account_type']),
            country=data['country'],
            currency=data['currency'],
            max_value_during_year=Decimal(data['max_value_during_year']),
            year_end_value=Decimal(data['year_end_value']),
            was_closed=data['was_closed'],
            closed_date=date.fromisoformat(data['closed_date']) if data.get('closed_date') else None,
        )


@dataclass
class ForeignIncome:
    """Foreign income source"""

    source_type: str  # "dividends", "interest", "rental", "business", etc.
    country: str
    amount_usd: Decimal
    amount_foreign: Decimal
    currency: str
    withholding_tax: Decimal
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'source_type': self.source_type,
            'country': self.country,
            'amount_usd': str(self.amount_usd),
            'amount_foreign': str(self.amount_foreign),
            'currency': self.currency,
            'withholding_tax': str(self.withholding_tax),
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForeignIncome':
        """Create from dictionary"""
        return cls(
            source_type=data['source_type'],
            country=data['country'],
            amount_usd=Decimal(data['amount_usd']),
            amount_foreign=Decimal(data['amount_foreign']),
            currency=data['currency'],
            withholding_tax=Decimal(data['withholding_tax']),
            description=data['description'],
        )


class ForeignIncomeFBARService:
    """
    Service for handling foreign income reporting and FBAR requirements.

    Features:
    - Foreign account tracking and FBAR determination
    - Foreign income reporting
    - Tax treaty benefit calculations
    - FBAR form generation assistance
    """

    def __init__(self, config: AppConfig):
        """
        Initialize foreign income and FBAR service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.error_tracker = get_error_tracker()

    def add_foreign_account(self, tax_data: TaxData, account: ForeignAccount) -> bool:
        """
        Add a foreign account to the tax data.

        Args:
            tax_data: Tax data model
            account: Foreign account to add

        Returns:
            bool: True if successful
        """
        try:
            # Get existing accounts
            accounts = self.get_foreign_accounts(tax_data)

            # Check for duplicate account numbers
            if any(a.account_number == account.account_number for a in accounts):
                logger.warning(f"Duplicate account number: {account.account_number}")
                return False

            # Add account
            accounts.append(account)

            # Save back to tax data
            account_dicts = [a.to_dict() for a in accounts]
            tax_data.set("foreign_accounts", account_dicts)

            logger.info(f"Added foreign account: {account.account_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to add foreign account: {e}")
            self.error_tracker.log_error("foreign_add_account", str(e))
            return False

    def get_foreign_accounts(self, tax_data: TaxData) -> List[ForeignAccount]:
        """
        Get all foreign accounts from tax data.

        Args:
            tax_data: Tax data model

        Returns:
            List[ForeignAccount]: List of foreign accounts
        """
        try:
            account_dicts = tax_data.get("foreign_accounts", [])
            return [ForeignAccount.from_dict(a) for a in account_dicts]
        except Exception as e:
            logger.error(f"Failed to load foreign accounts: {e}")
            return []

    def add_foreign_income(self, tax_data: TaxData, income: ForeignIncome) -> bool:
        """
        Add foreign income to the tax data.

        Args:
            tax_data: Tax data model
            income: Foreign income to add

        Returns:
            bool: True if successful
        """
        try:
            # Get existing income sources
            incomes = self.get_foreign_income(tax_data)

            # Add income
            incomes.append(income)

            # Save back to tax data
            income_dicts = [i.to_dict() for i in incomes]
            tax_data.set("foreign_income", income_dicts)

            logger.info(f"Added foreign income: {income.description}")
            return True

        except Exception as e:
            logger.error(f"Failed to add foreign income: {e}")
            self.error_tracker.log_error("foreign_add_income", str(e))
            return False

    def get_foreign_income(self, tax_data: TaxData) -> List[ForeignIncome]:
        """
        Get all foreign income from tax data.

        Args:
            tax_data: Tax data model

        Returns:
            List[ForeignIncome]: List of foreign income sources
        """
        try:
            income_dicts = tax_data.get("foreign_income", [])
            return [ForeignIncome.from_dict(i) for i in income_dicts]
        except Exception as e:
            logger.error(f"Failed to load foreign income: {e}")
            return []

    def is_fbar_required(self, tax_data: TaxData, tax_year: int) -> Tuple[bool, str]:
        """
        Determine if FBAR filing is required based on foreign account values.

        Args:
            tax_data: Tax data model
            tax_year: Tax year to check

        Returns:
            Tuple of (is_required, reason)
        """
        try:
            accounts = self.get_foreign_accounts(tax_data)

            # Get threshold based on filing status
            filing_status = tax_data.get("filing_status.status", "Single")
            threshold = FBARThreshold.MARRIED_2025.value if filing_status in ["MFJ", "MFS"] else FBARThreshold.SINGLE_2025.value

            total_max_value = sum(account.max_value_during_year for account in accounts)

            if total_max_value >= threshold:
                return True, f"Total foreign account value (${total_max_value:,.0f}) exceeds FBAR threshold (${threshold:,.0f})"

            return False, f"Total foreign account value (${total_max_value:,.0f}) is below FBAR threshold (${threshold:,.0f})"

        except Exception as e:
            logger.error(f"Failed to determine FBAR requirement: {e}")
            return False, "Error determining FBAR requirement"

    def calculate_foreign_tax_credit(self, tax_data: TaxData, tax_year: int) -> Dict[str, Any]:
        """
        Calculate foreign tax credit based on foreign income and withholding taxes.

        Args:
            tax_data: Tax data model
            tax_year: Tax year to calculate for

        Returns:
            Dict containing foreign tax credit information
        """
        try:
            foreign_income = self.get_foreign_income(tax_data)
            total_withholding = sum(income.withholding_tax for income in foreign_income)
            total_foreign_income = sum(income.amount_usd for income in foreign_income)

            # Simplified foreign tax credit calculation
            # In reality, this involves complex limitations based on US tax liability
            us_tax_liability = self._calculate_us_tax_liability(tax_data, tax_year)
            foreign_tax_credit_limit = min(total_withholding, us_tax_liability * Decimal('0.8'))  # 80% limit

            return {
                'total_foreign_income': total_foreign_income,
                'total_withholding_tax': total_withholding,
                'foreign_tax_credit_limit': foreign_tax_credit_limit,
                'available_credit': min(total_withholding, foreign_tax_credit_limit),
                'tax_year': tax_year
            }

        except Exception as e:
            logger.error(f"Failed to calculate foreign tax credit: {e}")
            return {}

    def _calculate_us_tax_liability(self, tax_data: TaxData, tax_year: int) -> Decimal:
        """
        Calculate US tax liability (simplified calculation).

        Args:
            tax_data: Tax data model
            tax_year: Tax year

        Returns:
            Estimated US tax liability
        """
        # This would integrate with the main tax calculation service
        # For now, return a placeholder
        return Decimal('10000')  # Placeholder

    def generate_fbar_summary(self, tax_data: TaxData, tax_year: int) -> Dict[str, Any]:
        """
        Generate FBAR filing summary for IRS Form 114.

        Args:
            tax_data: Tax data model
            tax_year: Tax year

        Returns:
            Dict containing FBAR summary data
        """
        try:
            accounts = self.get_foreign_accounts(tax_data)
            fbar_required, reason = self.is_fbar_required(tax_data, tax_year)

            summary = {
                'tax_year': tax_year,
                'fbar_required': fbar_required,
                'reason': reason,
                'total_accounts': len(accounts),
                'accounts_by_country': {},
                'total_max_value': Decimal('0'),
                'total_year_end_value': Decimal('0'),
            }

            for account in accounts:
                # Group by country
                if account.country not in summary['accounts_by_country']:
                    summary['accounts_by_country'][account.country] = []
                summary['accounts_by_country'][account.country].append(account.to_dict())

                summary['total_max_value'] += account.max_value_during_year
                summary['total_year_end_value'] += account.year_end_value

            return summary

        except Exception as e:
            logger.error(f"Failed to generate FBAR summary: {e}")
            return {}

    def get_fbar_filing_instructions(self) -> str:
        """
        Get FBAR filing instructions and requirements.

        Returns:
            String containing FBAR filing instructions
        """
        return """
FBAR (Foreign Bank Account Report) Filing Requirements:

1. FBAR must be filed if you had a financial interest in or signature authority over foreign financial accounts with an aggregate value exceeding $10,000 at any point during the calendar year.

2. Filing deadline: April 15 following the calendar year (or the tax return due date if later).

3. Form: FinCEN Form 114 (filed electronically through BSA E-Filing System).

4. Penalties for non-filing: Up to $10,000 per violation, or 50% of account balance, whichever is greater.

5. Extensions: Available through August 15 with Form 114a.

Important: FBAR is separate from Form 8938 (Statement of Specified Foreign Financial Assets) which has different thresholds and requirements.
        """

    def validate_foreign_account_data(self, account: ForeignAccount) -> List[str]:
        """
        Validate foreign account data.

        Args:
            account: Foreign account to validate

        Returns:
            List of validation error messages
        """
        errors = []

        if not account.account_number.strip():
            errors.append("Account number is required")

        if not account.institution_name.strip():
            errors.append("Institution name is required")

        if not account.country.strip():
            errors.append("Country is required")

        if account.max_value_during_year < 0:
            errors.append("Maximum value cannot be negative")

        if account.year_end_value < 0:
            errors.append("Year-end value cannot be negative")

        if account.was_closed and not account.closed_date:
            errors.append("Closed date is required if account was closed")

        return errors