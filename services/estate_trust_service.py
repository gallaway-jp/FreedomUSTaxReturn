"""
Estate and Trust Tax Return Service

Handles estate and trust tax return preparation and calculations.
Supports Form 1041 (U.S. Income Tax Return for Estates and Trusts).
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from config.app_config import AppConfig
from models.tax_data import TaxData
from utils.error_tracker import get_error_tracker
from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger

logger = logging.getLogger(__name__)


class TrustType(Enum):
    """Types of trusts for tax purposes"""
    SIMPLE_TRUST = "simple_trust"
    COMPLEX_TRUST = "complex_trust"
    GRANTOR_TRUST = "grantor_trust"
    CHARITABLE_REMAINDER_TRUST = "charitable_remainder_trust"
    QUALIFIED_DISABILITY_TRUST = "qualified_disability_trust"
    OTHER = "other"


class EstateType(Enum):
    """Types of estates for tax purposes"""
    SIMPLE_ESTATE = "simple_estate"
    COMPLEX_ESTATE = "complex_estate"
    QUALIFIED_TERMINATION = "qualified_termination"
    OTHER = "other"


class IncomeDistributionType(Enum):
    """Types of income distributions"""
    ORDINARY_INCOME = "ordinary_income"
    CAPITAL_GAINS = "capital_gains"
    TAX_EXEMPT = "tax_exempt"
    RETURN_OF_CAPITAL = "return_of_capital"


@dataclass
class TrustBeneficiary:
    """A trust beneficiary"""
    name: str
    ssn: str
    address: str
    relationship: str
    share_percentage: Decimal
    income_distributed: Decimal = Decimal('0')
    distribution_type: IncomeDistributionType = IncomeDistributionType.ORDINARY_INCOME

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'name': self.name,
            'ssn': self.ssn,
            'address': self.address,
            'relationship': self.relationship,
            'share_percentage': str(self.share_percentage),
            'income_distributed': str(self.income_distributed),
            'distribution_type': self.distribution_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustBeneficiary':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            ssn=data['ssn'],
            address=data['address'],
            relationship=data['relationship'],
            share_percentage=Decimal(data['share_percentage']),
            income_distributed=Decimal(data.get('income_distributed', '0')),
            distribution_type=IncomeDistributionType(data.get('distribution_type', 'ordinary_income')),
        )


@dataclass
class TrustIncome:
    """Trust income sources"""
    interest_income: Decimal = Decimal('0')
    dividend_income: Decimal = Decimal('0')
    business_income: Decimal = Decimal('0')
    capital_gains: Decimal = Decimal('0')
    rental_income: Decimal = Decimal('0')
    royalty_income: Decimal = Decimal('0')
    other_income: Decimal = Decimal('0')
    total_income: Decimal = Decimal('0')

    def calculate_total(self) -> Decimal:
        """Calculate total income"""
        self.total_income = (
            self.interest_income + self.dividend_income + self.business_income +
            self.capital_gains + self.rental_income + self.royalty_income + self.other_income
        )
        return self.total_income

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'interest_income': str(self.interest_income),
            'dividend_income': str(self.dividend_income),
            'business_income': str(self.business_income),
            'capital_gains': str(self.capital_gains),
            'rental_income': str(self.rental_income),
            'royalty_income': str(self.royalty_income),
            'other_income': str(self.other_income),
            'total_income': str(self.total_income),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustIncome':
        """Create from dictionary"""
        return cls(
            interest_income=Decimal(data.get('interest_income', '0')),
            dividend_income=Decimal(data.get('dividend_income', '0')),
            business_income=Decimal(data.get('business_income', '0')),
            capital_gains=Decimal(data.get('capital_gains', '0')),
            rental_income=Decimal(data.get('rental_income', '0')),
            royalty_income=Decimal(data.get('royalty_income', '0')),
            other_income=Decimal(data.get('other_income', '0')),
            total_income=Decimal(data.get('total_income', '0')),
        )


@dataclass
class TrustDeductions:
    """Trust deductions"""
    fiduciary_fees: Decimal = Decimal('0')
    attorney_fees: Decimal = Decimal('0')
    accounting_fees: Decimal = Decimal('0')
    other_administrative_expenses: Decimal = Decimal('0')
    charitable_contributions: Decimal = Decimal('0')
    net_operating_loss: Decimal = Decimal('0')
    total_deductions: Decimal = Decimal('0')

    def calculate_total(self) -> Decimal:
        """Calculate total deductions"""
        self.total_deductions = (
            self.fiduciary_fees + self.attorney_fees + self.accounting_fees +
            self.other_administrative_expenses + self.charitable_contributions + self.net_operating_loss
        )
        return self.total_deductions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'fiduciary_fees': str(self.fiduciary_fees),
            'attorney_fees': str(self.attorney_fees),
            'accounting_fees': str(self.accounting_fees),
            'other_administrative_expenses': str(self.other_administrative_expenses),
            'charitable_contributions': str(self.charitable_contributions),
            'net_operating_loss': str(self.net_operating_loss),
            'total_deductions': str(self.total_deductions),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustDeductions':
        """Create from dictionary"""
        return cls(
            fiduciary_fees=Decimal(data.get('fiduciary_fees', '0')),
            attorney_fees=Decimal(data.get('attorney_fees', '0')),
            accounting_fees=Decimal(data.get('accounting_fees', '0')),
            other_administrative_expenses=Decimal(data.get('other_administrative_expenses', '0')),
            charitable_contributions=Decimal(data.get('charitable_contributions', '0')),
            net_operating_loss=Decimal(data.get('net_operating_loss', '0')),
            total_deductions=Decimal(data.get('total_deductions', '0')),
        )


@dataclass
class EstateTrustReturn:
    """Estate or Trust tax return data"""
    tax_year: int
    entity_type: str  # "estate" or "trust"
    entity_name: str
    ein: str  # Employer Identification Number
    fiduciary_name: str
    fiduciary_address: str
    fiduciary_phone: str

    # Entity-specific data
    trust_type: Optional[TrustType] = None
    estate_type: Optional[EstateType] = None

    # Dates
    date_entity_created: Optional[date] = None
    tax_year_begin: Optional[date] = None
    tax_year_end: Optional[date] = None

    # Financial data
    income: TrustIncome = field(default_factory=TrustIncome)
    deductions: TrustDeductions = field(default_factory=TrustDeductions)
    beneficiaries: List[TrustBeneficiary] = field(default_factory=list)

    # Tax calculations
    taxable_income: Decimal = Decimal('0')
    tax_due: Decimal = Decimal('0')
    payments_credits: Decimal = Decimal('0')
    balance_due: Decimal = Decimal('0')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'tax_year': self.tax_year,
            'entity_type': self.entity_type,
            'entity_name': self.entity_name,
            'ein': self.ein,
            'fiduciary_name': self.fiduciary_name,
            'fiduciary_address': self.fiduciary_address,
            'fiduciary_phone': self.fiduciary_phone,
            'trust_type': self.trust_type.value if self.trust_type else None,
            'estate_type': self.estate_type.value if self.estate_type else None,
            'date_entity_created': self.date_entity_created.isoformat() if self.date_entity_created else None,
            'tax_year_begin': self.tax_year_begin.isoformat() if self.tax_year_begin else None,
            'tax_year_end': self.tax_year_end.isoformat() if self.tax_year_end else None,
            'income': self.income.to_dict(),
            'deductions': self.deductions.to_dict(),
            'beneficiaries': [b.to_dict() for b in self.beneficiaries],
            'taxable_income': str(self.taxable_income),
            'tax_due': str(self.tax_due),
            'payments_credits': str(self.payments_credits),
            'balance_due': str(self.balance_due),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EstateTrustReturn':
        """Create from dictionary"""
        return cls(
            tax_year=data['tax_year'],
            entity_type=data['entity_type'],
            entity_name=data['entity_name'],
            ein=data['ein'],
            fiduciary_name=data['fiduciary_name'],
            fiduciary_address=data['fiduciary_address'],
            fiduciary_phone=data['fiduciary_phone'],
            trust_type=TrustType(data['trust_type']) if data.get('trust_type') else None,
            estate_type=EstateType(data['estate_type']) if data.get('estate_type') else None,
            date_entity_created=date.fromisoformat(data['date_entity_created']) if data.get('date_entity_created') else None,
            tax_year_begin=date.fromisoformat(data['tax_year_begin']) if data.get('tax_year_begin') else None,
            tax_year_end=date.fromisoformat(data['tax_year_end']) if data.get('tax_year_end') else None,
            income=TrustIncome.from_dict(data.get('income', {})),
            deductions=TrustDeductions.from_dict(data.get('deductions', {})),
            beneficiaries=[TrustBeneficiary.from_dict(b) for b in data.get('beneficiaries', [])],
            taxable_income=Decimal(data.get('taxable_income', '0')),
            tax_due=Decimal(data.get('tax_due', '0')),
            payments_credits=Decimal(data.get('payments_credits', '0')),
            balance_due=Decimal(data.get('balance_due', '0')),
        )


class EstateTrustService:
    """
    Service for managing estate and trust tax returns.

    Handles Form 1041 preparation and calculations for estates and trusts.
    """

    def __init__(self, config: AppConfig):
        """
        Initialize estate and trust service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.error_tracker = get_error_tracker()

    def create_estate_trust_return(self, tax_data: TaxData, entity_type: str, tax_year: int) -> EstateTrustReturn:
        """
        Create a new estate or trust tax return.

        Args:
            tax_data: Tax data model
            entity_type: "estate" or "trust"
            tax_year: Tax year

        Returns:
            EstateTrustReturn: New return object
        """
        return EstateTrustReturn(
            tax_year=tax_year,
            entity_type=entity_type,
            entity_name="",
            ein="",
            fiduciary_name="",
            fiduciary_address="",
            fiduciary_phone="",
        )

    def save_estate_trust_return(self, tax_data: TaxData, return_data: EstateTrustReturn) -> bool:
        """
        Save estate/trust return data to tax data model.

        Args:
            tax_data: Tax data model
            return_data: Estate/trust return data

        Returns:
            bool: True if successful
        """
        try:
            # Save to tax data under estate_trust_returns
            existing_returns = tax_data.get("estate_trust_returns", [])
            existing_returns = [r for r in existing_returns if not (
                r.get('tax_year') == return_data.tax_year and
                r.get('entity_type') == return_data.entity_type and
                r.get('ein') == return_data.ein
            )]

            existing_returns.append(return_data.to_dict())
            tax_data.set("estate_trust_returns", existing_returns)

            logger.info(f"Saved {return_data.entity_type} return for EIN {return_data.ein}, tax year {return_data.tax_year}")
            return True

        except Exception as e:
            logger.error(f"Failed to save estate/trust return: {e}")
            self.error_tracker.log_error("estate_trust_save", str(e))
            return False

    def load_estate_trust_returns(self, tax_data: TaxData) -> List[EstateTrustReturn]:
        """
        Load all estate/trust returns from tax data.

        Args:
            tax_data: Tax data model

        Returns:
            List[EstateTrustReturn]: List of returns
        """
        try:
            return_dicts = tax_data.get("estate_trust_returns", [])
            return [EstateTrustReturn.from_dict(r) for r in return_dicts]
        except Exception as e:
            logger.error(f"Failed to load estate/trust returns: {e}")
            return []

    def calculate_tax(self, return_data: EstateTrustReturn) -> Dict[str, Any]:
        """
        Calculate tax for estate/trust return.

        Args:
            return_data: Estate/trust return data

        Returns:
            Dict containing tax calculation results
        """
        try:
            # Calculate total income
            total_income = return_data.income.calculate_total()

            # Calculate total deductions
            total_deductions = return_data.deductions.calculate_total()

            # Calculate taxable income
            taxable_income = max(Decimal('0'), total_income - total_deductions)

            # Calculate tax using trust tax rates
            tax_due = self._calculate_trust_tax(taxable_income, return_data.tax_year)

            # Calculate balance due
            balance_due = max(Decimal('0'), tax_due - return_data.payments_credits)

            # Update return data
            return_data.taxable_income = taxable_income
            return_data.tax_due = tax_due
            return_data.balance_due = balance_due

            return {
                'total_income': total_income,
                'total_deductions': total_deductions,
                'taxable_income': taxable_income,
                'tax_due': tax_due,
                'balance_due': balance_due,
                'success': True
            }

        except Exception as e:
            logger.error(f"Failed to calculate estate/trust tax: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_trust_tax(self, taxable_income: Decimal, tax_year: int) -> Decimal:
        """
        Calculate trust tax using IRS tax brackets.

        Args:
            taxable_income: Taxable income
            tax_year: Tax year

        Returns:
            Decimal: Tax amount
        """
        # Simplified trust tax calculation (estates and trusts use same rates as individuals)
        # In practice, this would use the actual IRS tax tables for the specific year

        if tax_year >= 2024:
            # 2024 tax brackets for trusts (simplified)
            brackets = [
                (Decimal('0'), Decimal('100'), Decimal('0.10')),
                (Decimal('100'), Decimal('1100'), Decimal('0.12')),
                (Decimal('1100'), Decimal('4475'), Decimal('0.22')),
                (Decimal('4475'), Decimal('9575'), Decimal('0.24')),
                (Decimal('9575'), Decimal('18200'), Decimal('0.32')),
                (Decimal('18200'), Decimal('23175'), Decimal('0.35')),
                (Decimal('23175'), Decimal('57875'), Decimal('0.37')),
            ]
        else:
            # Default brackets
            brackets = [
                (Decimal('0'), Decimal('100'), Decimal('0.10')),
                (Decimal('100'), Decimal('1100'), Decimal('0.12')),
                (Decimal('1100'), Decimal('10000'), Decimal('0.22')),
                (Decimal('10000'), Decimal('100000'), Decimal('0.24')),
            ]

        tax = Decimal('0')
        remaining_income = taxable_income

        for min_amount, max_amount, rate in brackets:
            if remaining_income <= 0:
                break

            bracket_amount = min(remaining_income, max_amount - min_amount)
            tax += bracket_amount * rate
            remaining_income -= bracket_amount

        # Apply 37% rate to remaining income
        if remaining_income > 0:
            tax += remaining_income * Decimal('0.37')

        return tax

    def add_beneficiary(self, tax_data: TaxData, beneficiary: TrustBeneficiary) -> bool:
        """
        Add a trust beneficiary to the tax data.

        Args:
            tax_data: Tax data model
            beneficiary: Beneficiary to add

        Returns:
            bool: True if successful
        """
        try:
            beneficiaries = self.get_beneficiaries(tax_data)
            
            # Check for duplicate SSN
            if any(b.ssn == beneficiary.ssn for b in beneficiaries):
                logger.warning(f"Duplicate beneficiary SSN: {beneficiary.ssn}")
                return False
            
            beneficiaries.append(beneficiary)
            beneficiary_dicts = [b.to_dict() for b in beneficiaries]
            tax_data.set("estate_trust.beneficiaries", beneficiary_dicts)
            
            logger.info(f"Added beneficiary: {beneficiary.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add beneficiary: {e}")
            self.error_tracker.log_error("estate_add_beneficiary", str(e))
            return False

    def get_beneficiaries(self, tax_data: TaxData) -> List[TrustBeneficiary]:
        """
        Get all beneficiaries from tax data.

        Args:
            tax_data: Tax data model

        Returns:
            List[TrustBeneficiary]: List of beneficiaries
        """
        try:
            beneficiary_dicts = tax_data.get("estate_trust.beneficiaries", [])
            return [TrustBeneficiary.from_dict(b) for b in beneficiary_dicts]
        except Exception as e:
            logger.error(f"Failed to load beneficiaries: {e}")
            return []

    def calculate_beneficiary_distribution(self, beneficiary: TrustBeneficiary, trust_income: Decimal) -> Decimal:
        """
        Calculate income distribution to a specific beneficiary.

        Args:
            beneficiary: Beneficiary to calculate for
            trust_income: Total trust income to distribute

        Returns:
            Decimal: Amount distributed to beneficiary
        """
        return trust_income * (beneficiary.share_percentage / Decimal('100'))

    def validate_beneficiary_data(self, beneficiary: TrustBeneficiary) -> List[str]:
        """
        Validate beneficiary data.

        Args:
            beneficiary: Beneficiary to validate

        Returns:
            List of validation error messages
        """
        errors = []
        
        if not beneficiary.name.strip():
            errors.append("Beneficiary name is required")
        
        if not beneficiary.ssn.strip():
            errors.append("Beneficiary SSN is required")
        
        if not beneficiary.address.strip():
            errors.append("Beneficiary address is required")
        
        if beneficiary.share_percentage < 0 or beneficiary.share_percentage > 100:
            errors.append("Share percentage must be between 0 and 100")
        
        return errors

    def validate_estate_trust_data(self, return_data: EstateTrustReturn) -> List[str]:
        """
        Validate estate/trust return data.

        Args:
            return_data: Return data to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Required fields
        if not return_data.entity_name.strip():
            errors.append("Entity name is required")

        if not return_data.ein.strip():
            errors.append("EIN is required")

        if not return_data.fiduciary_name.strip():
            errors.append("Fiduciary name is required")

        # EIN format validation (XX-XXXXXXX)
        import re
        if return_data.ein and not re.match(r'^\d{2}-\d{7}$', return_data.ein):
            errors.append("EIN must be in XX-XXXXXXX format")

        # Entity type specific validation
        if return_data.entity_type == "trust" and not return_data.trust_type:
            errors.append("Trust type must be specified for trusts")

        if return_data.entity_type == "estate" and not return_data.estate_type:
            errors.append("Estate type must be specified for estates")

        # Date validation
        if return_data.date_entity_created and return_data.date_entity_created > date.today():
            errors.append("Entity creation date cannot be in the future")

        # Financial validation
        if return_data.income.total_income < 0:
            errors.append("Total income cannot be negative")

        if return_data.deductions.total_deductions < 0:
            errors.append("Total deductions cannot be negative")

        # Beneficiary validation
        total_shares = sum(b.share_percentage for b in return_data.beneficiaries)
        if return_data.beneficiaries and abs(total_shares - Decimal('100')) > Decimal('0.01'):
            errors.append("Beneficiary share percentages must total 100%")

        return errors

    def generate_form_1041(self, return_data: EstateTrustReturn) -> Dict[str, Any]:
        """
        Generate Form 1041 data for IRS submission.

        Args:
            return_data: Estate/trust return data

        Returns:
            Dict containing Form 1041 data
        """
        try:
            form_data = {
                'form_type': '1041',
                'tax_year': return_data.tax_year,
                'entity_name': return_data.entity_name,
                'ein': return_data.ein,
                'fiduciary_name': return_data.fiduciary_name,
                'fiduciary_address': return_data.fiduciary_address,

                # Part I - Income
                'interest_income': return_data.income.interest_income,
                'dividends': return_data.income.dividend_income,
                'business_income': return_data.income.business_income,
                'capital_gains': return_data.income.capital_gains,
                'rental_income': return_data.income.rental_income,
                'royalties': return_data.income.royalty_income,
                'other_income': return_data.income.other_income,
                'total_income': return_data.income.total_income,

                # Part II - Deductions
                'fiduciary_fees': return_data.deductions.fiduciary_fees,
                'attorney_fees': return_data.deductions.attorney_fees,
                'accounting_fees': return_data.deductions.accounting_fees,
                'other_expenses': return_data.deductions.other_administrative_expenses,
                'charitable_contributions': return_data.deductions.charitable_contributions,
                'total_deductions': return_data.deductions.total_deductions,

                # Tax calculations
                'taxable_income': return_data.taxable_income,
                'tax_due': return_data.tax_due,
                'payments_and_credits': return_data.payments_credits,
                'balance_due': return_data.balance_due,

                # Beneficiaries
                'beneficiaries': [b.to_dict() for b in return_data.beneficiaries],
            }

            return form_data

        except Exception as e:
            logger.error(f"Failed to generate Form 1041: {e}")
            return {}

    def get_filing_instructions(self) -> str:
        """
        Get filing instructions for Form 1041.

        Returns:
            String containing filing instructions
        """
        return """
Form 1041 (U.S. Income Tax Return for Estates and Trusts) Filing Instructions:

1. **Who Must File:**
   - Estates of decedents
   - Trusts (simple, complex, grantor, etc.)
   - Bankruptcy estates
   - Qualified disability trusts

2. **When to File:**
   - Due date: 4th month after end of tax year (April 15 for calendar year)
   - Extensions: Available to 9.5 months after tax year end

3. **Income Types Reported:**
   - Interest and dividends
   - Business income
   - Capital gains/losses
   - Rental income
   - Royalties
   - Other income

4. **Deductions:**
   - Fiduciary fees
   - Attorney and accounting fees
   - Charitable contributions
   - Administrative expenses
   - Net operating losses

5. **Tax Rates:**
   - Estates and trusts use compressed tax brackets
   - Top rate of 37% reached at lower income levels than individuals

6. **Beneficiary Reporting:**
   - Income distributed to beneficiaries
   - K-1 forms issued to beneficiaries
   - Character of income preserved for beneficiaries

Important: Consult a tax professional for complex estate and trust tax situations.
        """