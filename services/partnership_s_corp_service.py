"""
Partnership and S-Corp Tax Return Service

Handles partnership (Form 1065) and S-Corp (Form 1120-S) tax return preparation.
Supports both pass-through entities with K-1 generation and tax calculations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from decimal import Decimal
from datetime import datetime, date
from enum import Enum

from config.app_config import AppConfig
from utils.error_tracker import get_error_tracker


class EntityType(Enum):
    """Types of business entities"""
    PARTNERSHIP = "partnership"
    S_CORPORATION = "s_corporation"
    LLC_TAXED_AS_PARTNERSHIP = "llc_partnership"
    LLC_TAXED_AS_S_CORP = "llc_s_corp"


class PartnershipType(Enum):
    """Types of partnerships"""
    GENERAL = "general"
    LIMITED = "limited"
    LIMITED_LIABILITY = "limited_liability"
    JOINT_VENTURE = "joint_venture"


class SCorpShareholderType(Enum):
    """Types of S-Corp shareholders"""
    INDIVIDUAL = "individual"
    ESTATE = "estate"
    TRUST = "trust"
    TAX_EXEMPT_ORGANIZATION = "tax_exempt"


@dataclass
class PartnerShareholder:
    """Represents a partner or shareholder in the entity"""
    name: str = ""
    ssn_ein: str = ""  # SSN for individuals, EIN for entities
    address: str = ""
    entity_type: str = "individual"  # individual, partnership, corporation, estate, trust
    ownership_percentage: Decimal = Decimal("0.00")
    capital_account_beginning: Decimal = Decimal("0.00")
    capital_account_ending: Decimal = Decimal("0.00")
    share_of_income: Decimal = Decimal("0.00")
    share_of_losses: Decimal = Decimal("0.00")
    distributions: Decimal = Decimal("0.00")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'name': self.name,
            'ssn_ein': self.ssn_ein,
            'address': self.address,
            'entity_type': self.entity_type,
            'ownership_percentage': str(self.ownership_percentage),
            'capital_account_beginning': str(self.capital_account_beginning),
            'capital_account_ending': str(self.capital_account_ending),
            'share_of_income': str(self.share_of_income),
            'share_of_losses': str(self.share_of_losses),
            'distributions': str(self.distributions),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PartnerShareholder':
        """Create from dictionary"""
        return cls(
            name=data.get('name', ''),
            ssn_ein=data.get('ssn_ein', ''),
            address=data.get('address', ''),
            entity_type=data.get('entity_type', 'individual'),
            ownership_percentage=Decimal(data.get('ownership_percentage', '0')),
            capital_account_beginning=Decimal(data.get('capital_account_beginning', '0')),
            capital_account_ending=Decimal(data.get('capital_account_ending', '0')),
            share_of_income=Decimal(data.get('share_of_income', '0')),
            share_of_losses=Decimal(data.get('share_of_losses', '0')),
            distributions=Decimal(data.get('distributions', '0')),
        )


@dataclass
class BusinessIncome:
    """Business income and revenue"""
    gross_receipts: Decimal = Decimal("0.00")
    returns_allowances: Decimal = Decimal("0.00")
    cost_of_goods_sold: Decimal = Decimal("0.00")
    gross_profit: Decimal = Decimal("0.00")

    # Ordinary business income
    dividends: Decimal = Decimal("0.00")
    interest_income: Decimal = Decimal("0.00")
    rents: Decimal = Decimal("0.00")
    royalties: Decimal = Decimal("0.00")
    other_income: Decimal = Decimal("0.00")

    def calculate_gross_profit(self) -> Decimal:
        """Calculate gross profit"""
        self.gross_profit = self.gross_receipts - self.returns_allowances - self.cost_of_goods_sold
        return self.gross_profit

    def total_ordinary_income(self) -> Decimal:
        """Calculate total ordinary income"""
        return self.gross_profit + self.dividends + self.interest_income + self.rents + self.royalties + self.other_income

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'gross_receipts': str(self.gross_receipts),
            'returns_allowances': str(self.returns_allowances),
            'cost_of_goods_sold': str(self.cost_of_goods_sold),
            'gross_profit': str(self.gross_profit),
            'dividends': str(self.dividends),
            'interest_income': str(self.interest_income),
            'rents': str(self.rents),
            'royalties': str(self.royalties),
            'other_income': str(self.other_income),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessIncome':
        """Create from dictionary"""
        return cls(
            gross_receipts=Decimal(data.get('gross_receipts', '0')),
            returns_allowances=Decimal(data.get('returns_allowances', '0')),
            cost_of_goods_sold=Decimal(data.get('cost_of_goods_sold', '0')),
            gross_profit=Decimal(data.get('gross_profit', '0')),
            dividends=Decimal(data.get('dividends', '0')),
            interest_income=Decimal(data.get('interest_income', '0')),
            rents=Decimal(data.get('rents', '0')),
            royalties=Decimal(data.get('royalties', '0')),
            other_income=Decimal(data.get('other_income', '0')),
        )


@dataclass
class BusinessDeductions:
    """Business deductions and expenses"""
    compensation_officers: Decimal = Decimal("0.00")
    salaries_wages: Decimal = Decimal("0.00")
    repairs_maintenance: Decimal = Decimal("0.00")
    bad_debts: Decimal = Decimal("0.00")
    rents: Decimal = Decimal("0.00")
    taxes_licenses: Decimal = Decimal("0.00")
    charitable_contributions: Decimal = Decimal("0.00")
    advertising: Decimal = Decimal("0.00")
    pension_plans: Decimal = Decimal("0.00")
    employee_benefits: Decimal = Decimal("0.00")
    utilities: Decimal = Decimal("0.00")
    supplies: Decimal = Decimal("0.00")
    other_expenses: Decimal = Decimal("0.00")

    def total_deductions(self) -> Decimal:
        """Calculate total deductions"""
        return (
            self.compensation_officers + self.salaries_wages + self.repairs_maintenance +
            self.bad_debts + self.rents + self.taxes_licenses + self.charitable_contributions +
            self.advertising + self.pension_plans + self.employee_benefits + self.utilities +
            self.supplies + self.other_expenses
        )

    def calculate_total_deductions(self) -> Decimal:
        """Calculate total deductions (alias for total_deductions)"""
        return self.total_deductions()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'compensation_officers': str(self.compensation_officers),
            'salaries_wages': str(self.salaries_wages),
            'repairs_maintenance': str(self.repairs_maintenance),
            'bad_debts': str(self.bad_debts),
            'rents': str(self.rents),
            'taxes_licenses': str(self.taxes_licenses),
            'charitable_contributions': str(self.charitable_contributions),
            'advertising': str(self.advertising),
            'pension_plans': str(self.pension_plans),
            'employee_benefits': str(self.employee_benefits),
            'utilities': str(self.utilities),
            'supplies': str(self.supplies),
            'other_expenses': str(self.other_expenses),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessDeductions':
        """Create from dictionary"""
        return cls(
            compensation_officers=Decimal(data.get('compensation_officers', '0')),
            salaries_wages=Decimal(data.get('salaries_wages', '0')),
            repairs_maintenance=Decimal(data.get('repairs_maintenance', '0')),
            bad_debts=Decimal(data.get('bad_debts', '0')),
            rents=Decimal(data.get('rents', '0')),
            taxes_licenses=Decimal(data.get('taxes_licenses', '0')),
            charitable_contributions=Decimal(data.get('charitable_contributions', '0')),
            advertising=Decimal(data.get('advertising', '0')),
            pension_plans=Decimal(data.get('pension_plans', '0')),
            employee_benefits=Decimal(data.get('employee_benefits', '0')),
            utilities=Decimal(data.get('utilities', '0')),
            supplies=Decimal(data.get('supplies', '0')),
            other_expenses=Decimal(data.get('other_expenses', '0')),
        )


@dataclass
class PartnershipSCorpReturn:
    """Partnership (1065) or S-Corp (1120-S) tax return data"""
    tax_year: int
    entity_type: EntityType
    entity_name: str
    ein: str  # Employer Identification Number
    business_address: str
    business_description: str

    # Entity-specific data
    partnership_type: Optional[PartnershipType] = None
    s_corp_shareholder_type: Optional[SCorpShareholderType] = None

    # Principal business activity
    principal_business_activity: str = ""
    business_activity_code: str = ""

    # Accounting method
    accounting_method: str = "cash"  # cash, accrual

    # Business dates
    business_start_date: Optional[date] = None
    tax_year_begin: Optional[date] = None
    tax_year_end: Optional[date] = None

    # Financial data
    income: BusinessIncome = field(default_factory=BusinessIncome)
    deductions: BusinessDeductions = field(default_factory=BusinessDeductions)
    partners_shareholders: List[PartnerShareholder] = field(default_factory=list)

    # Tax calculations
    ordinary_business_income: Decimal = Decimal("0.00")
    net_income_loss: Decimal = Decimal("0.00")

    # For S-Corps: distributions and AAA
    distributions: Decimal = Decimal("0.00")
    accumulated_adjustments_account: Decimal = Decimal("0.00")

    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'tax_year': self.tax_year,
            'entity_type': self.entity_type.value,
            'entity_name': self.entity_name,
            'ein': self.ein,
            'business_address': self.business_address,
            'business_description': self.business_description,
            'partnership_type': self.partnership_type.value if self.partnership_type else None,
            's_corp_shareholder_type': self.s_corp_shareholder_type.value if self.s_corp_shareholder_type else None,
            'principal_business_activity': self.principal_business_activity,
            'business_activity_code': self.business_activity_code,
            'accounting_method': self.accounting_method,
            'business_start_date': self.business_start_date.isoformat() if self.business_start_date else None,
            'tax_year_begin': self.tax_year_begin.isoformat() if self.tax_year_begin else None,
            'tax_year_end': self.tax_year_end.isoformat() if self.tax_year_end else None,
            'income': self.income.to_dict(),
            'deductions': self.deductions.to_dict(),
            'partners_shareholders': [p.to_dict() for p in self.partners_shareholders],
            'ordinary_business_income': str(self.ordinary_business_income),
            'net_income_loss': str(self.net_income_loss),
            'distributions': str(self.distributions),
            'accumulated_adjustments_account': str(self.accumulated_adjustments_account),
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PartnershipSCorpReturn':
        """Create from dictionary"""
        return cls(
            tax_year=data['tax_year'],
            entity_type=EntityType(data['entity_type']),
            entity_name=data['entity_name'],
            ein=data['ein'],
            business_address=data['business_address'],
            business_description=data['business_description'],
            partnership_type=PartnershipType(data['partnership_type']) if data.get('partnership_type') else None,
            s_corp_shareholder_type=SCorpShareholderType(data['s_corp_shareholder_type']) if data.get('s_corp_shareholder_type') else None,
            principal_business_activity=data.get('principal_business_activity', ''),
            business_activity_code=data.get('business_activity_code', ''),
            accounting_method=data.get('accounting_method', 'cash'),
            business_start_date=date.fromisoformat(data['business_start_date']) if data.get('business_start_date') else None,
            tax_year_begin=date.fromisoformat(data['tax_year_begin']) if data.get('tax_year_begin') else None,
            tax_year_end=date.fromisoformat(data['tax_year_end']) if data.get('tax_year_end') else None,
            income=BusinessIncome.from_dict(data.get('income', {})),
            deductions=BusinessDeductions.from_dict(data.get('deductions', {})),
            partners_shareholders=[PartnerShareholder.from_dict(p) for p in data.get('partners_shareholders', [])],
            ordinary_business_income=Decimal(data.get('ordinary_business_income', '0')),
            net_income_loss=Decimal(data.get('net_income_loss', '0')),
            distributions=Decimal(data.get('distributions', '0')),
            accumulated_adjustments_account=Decimal(data.get('accumulated_adjustments_account', '0')),
            created_date=datetime.fromisoformat(data.get('created_date', datetime.now().isoformat())),
            modified_date=datetime.fromisoformat(data.get('modified_date', datetime.now().isoformat())),
        )


class PartnershipSCorpService:
    """
    Service for managing partnership and S-Corp tax returns.

    Handles:
    - Form 1065 (Partnership returns)
    - Form 1120-S (S-Corp returns)
    - K-1 generation for partners/shareholders
    - Tax calculations and allocations
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.error_tracker = get_error_tracker()

    def create_partnership_s_corp_return(
        self,
        tax_year: int,
        entity_type: EntityType,
        entity_name: str,
        ein: str
    ) -> PartnershipSCorpReturn:
        """
        Create a new partnership or S-Corp return

        Args:
            tax_year: Tax year for the return
            entity_type: Type of entity (partnership or s_corp)
            entity_name: Legal name of the entity
            ein: Employer Identification Number

        Returns:
            PartnershipSCorpReturn: New return object
        """
        return_obj = PartnershipSCorpReturn(
            tax_year=tax_year,
            entity_type=entity_type,
            entity_name=entity_name,
            ein=ein,
            business_address="",
            business_description="",
        )

        # Set default tax year dates
        return_obj.tax_year_begin = date(tax_year, 1, 1)
        return_obj.tax_year_end = date(tax_year, 12, 31)

        return return_obj

    def calculate_business_income(self, return_data: PartnershipSCorpReturn) -> Decimal:
        """
        Calculate ordinary business income

        Args:
            return_data: The return data

        Returns:
            Decimal: Ordinary business income amount
        """
        # Calculate gross profit
        return_data.income.calculate_gross_profit()

        # Calculate total ordinary income
        ordinary_income = return_data.income.total_ordinary_income()

        # Subtract deductions
        total_deductions = return_data.deductions.total_deductions()

        # Net income/loss
        return_data.net_income_loss = ordinary_income - total_deductions
        return_data.ordinary_business_income = return_data.net_income_loss

        return return_data.ordinary_business_income

    def allocate_income_to_partners(
        self,
        return_data: PartnershipSCorpReturn
    ) -> List[Dict[str, Any]]:
        """
        Allocate income/loss to partners based on ownership percentages

        Args:
            return_data: The return data

        Returns:
            List[Dict]: Allocation details for each partner
        """
        if not return_data.partners_shareholders:
            return []

        total_ownership = sum(p.ownership_percentage for p in return_data.partners_shareholders)
        if total_ownership == 0:
            return []

        allocations = []
        for partner in return_data.partners_shareholders:
            if partner.ownership_percentage > 0:
                share_percentage = partner.ownership_percentage / total_ownership
                income_share = return_data.net_income_loss * share_percentage

                partner.share_of_income = max(Decimal("0"), income_share)
                partner.share_of_losses = max(Decimal("0"), -income_share)

                allocations.append({
                    'partner_name': partner.name,
                    'ownership_percentage': partner.ownership_percentage,
                    'share_percentage': share_percentage,
                    'income_share': partner.share_of_income,
                    'loss_share': partner.share_of_losses,
                })

        return allocations

    def generate_k1_forms(self, return_data: PartnershipSCorpReturn) -> List[Dict[str, Any]]:
        """
        Generate K-1 forms for partners/shareholders

        Args:
            return_data: The return data

        Returns:
            List[Dict]: K-1 form data for each partner/shareholder
        """
        k1_forms = []

        for partner in return_data.partners_shareholders:
            k1_data = {
                'tax_year': return_data.tax_year,
                'entity_name': return_data.entity_name,
                'entity_ein': return_data.ein,
                'partner_name': partner.name,
                'partner_ssn_ein': partner.ssn_ein,
                'partner_address': partner.address,
                'ownership_percentage': partner.ownership_percentage,
                'ordinary_income': partner.share_of_income,
                'ordinary_loss': partner.share_of_losses,
                'distributions': partner.distributions,
                'beginning_capital': partner.capital_account_beginning,
                'ending_capital': partner.capital_account_ending,
            }
            k1_forms.append(k1_data)

        return k1_forms

    def validate_partnership_s_corp_data(self, return_data: PartnershipSCorpReturn) -> List[str]:
        """
        Validate partnership/S-Corp return data

        Args:
            return_data: The return data to validate

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        # Required fields
        if not return_data.entity_name.strip():
            errors.append("Entity name is required")

        if not return_data.ein.strip():
            errors.append("EIN is required")

        if not return_data.business_description.strip():
            errors.append("Business description is required")

        # EIN format validation (should be XX-XXXXXXX)
        import re
        if return_data.ein and not re.match(r'^\d{2}-\d{7}$', return_data.ein):
            errors.append("EIN must be in XX-XXXXXXX format")

        # Business activity code validation
        if return_data.business_activity_code and not return_data.business_activity_code.isdigit():
            errors.append("Business activity code must be numeric")

        # Partnership-specific validations
        if return_data.entity_type in [EntityType.PARTNERSHIP, EntityType.LLC_TAXED_AS_PARTNERSHIP]:
            if not return_data.partnership_type:
                errors.append("Partnership type must be specified")

        # S-Corp specific validations
        elif return_data.entity_type in [EntityType.S_CORPORATION, EntityType.LLC_TAXED_AS_S_CORP]:
            if not return_data.s_corp_shareholder_type:
                errors.append("S-Corp shareholder type must be specified")

        # Partner/Shareholder validations
        total_ownership = sum(p.ownership_percentage for p in return_data.partners_shareholders)
        if return_data.partners_shareholders and total_ownership == 0:
            errors.append("At least one partner/shareholder must have ownership percentage > 0")

        for i, partner in enumerate(return_data.partners_shareholders):
            if not partner.name.strip():
                errors.append(f"Partner/Shareholder {i+1}: Name is required")

            if not partner.ssn_ein.strip():
                errors.append(f"Partner/Shareholder {i+1}: SSN/EIN is required")

            # SSN format for individuals (XXX-XX-XXXX)
            if partner.entity_type == "individual" and partner.ssn_ein:
                if not re.match(r'^\d{3}-\d{2}-\d{4}$', partner.ssn_ein):
                    errors.append(f"Partner/Shareholder {i+1}: SSN must be in XXX-XX-XXXX format")

            # EIN format for entities (XX-XXXXXXX)
            elif partner.entity_type != "individual" and partner.ssn_ein:
                if not re.match(r'^\d{2}-\d{7}$', partner.ssn_ein):
                    errors.append(f"Partner/Shareholder {i+1}: EIN must be in XX-XXXXXXX format")

        return errors

    def save_partnership_s_corp_return(
        self,
        tax_data: Any,
        return_data: PartnershipSCorpReturn
    ) -> bool:
        """
        Save the partnership/S-Corp return to tax data

        Args:
            tax_data: The main tax data object
            return_data: The return data to save

        Returns:
            bool: True if saved successfully
        """
        try:
            # Get the current year data
            year_data = tax_data.get_year_data(return_data.tax_year)
            if not year_data:
                year_data = {}
                tax_data.data["years"][str(return_data.tax_year)] = year_data

            # Save to partnership_s_corp section
            if "partnership_s_corp" not in year_data:
                year_data["partnership_s_corp"] = []

            # Find existing return or add new one
            existing_index = None
            for i, existing in enumerate(year_data["partnership_s_corp"]):
                if existing.get("ein") == return_data.ein:
                    existing_index = i
                    break

            return_dict = return_data.to_dict()

            if existing_index is not None:
                year_data["partnership_s_corp"][existing_index] = return_dict
            else:
                year_data["partnership_s_corp"].append(return_dict)

            return True

        except Exception as e:
            self.logger.error(f"Failed to save partnership/S-Corp return: {e}")
            return False

    def load_partnership_s_corp_returns(self, tax_data: Any) -> List[PartnershipSCorpReturn]:
        """
        Load all partnership/S-Corp returns from tax data

        Args:
            tax_data: The main tax data object

        Returns:
            List[PartnershipSCorpReturn]: List of return objects
        """
        returns = []

        try:
            current_year = tax_data.get_current_year()
            year_data = tax_data.get_year_data(current_year)

            if year_data and "partnership_s_corp" in year_data:
                for return_dict in year_data["partnership_s_corp"]:
                    try:
                        return_obj = PartnershipSCorpReturn.from_dict(return_dict)
                        returns.append(return_obj)
                    except Exception as e:
                        self.logger.error(f"Failed to load partnership/S-Corp return: {e}")

        except Exception as e:
            self.logger.error(f"Failed to load partnership/S-Corp returns: {e}")

        return returns

    def generate_form_1065(self, return_data: PartnershipSCorpReturn) -> Dict[str, Any]:
        """
        Generate Form 1065 data for partnerships

        Args:
            return_data: The return data

        Returns:
            Dict: Form 1065 data
        """
        if return_data.entity_type not in [EntityType.PARTNERSHIP, EntityType.LLC_TAXED_AS_PARTNERSHIP]:
            raise ValueError("Form 1065 is only for partnerships")

        form_data = {
            'form_type': '1065',
            'tax_year': return_data.tax_year,
            'entity_name': return_data.entity_name,
            'ein': return_data.ein,
            'business_address': return_data.business_address,
            'business_description': return_data.business_description,
            'partnership_type': return_data.partnership_type.value if return_data.partnership_type else '',
            'principal_business_activity': return_data.principal_business_activity,
            'business_activity_code': return_data.business_activity_code,
            'accounting_method': return_data.accounting_method,

            # Income section
            'gross_receipts': return_data.income.gross_receipts,
            'returns_allowances': return_data.income.returns_allowances,
            'cost_of_goods_sold': return_data.income.cost_of_goods_sold,
            'gross_profit': return_data.income.gross_profit,
            'ordinary_income': return_data.ordinary_business_income,
            'net_income_loss': return_data.net_income_loss,

            # Partners
            'number_of_partners': len(return_data.partners_shareholders),
            'partners': [p.to_dict() for p in return_data.partners_shareholders],
        }

        return form_data

    def generate_form_1120s(self, return_data: PartnershipSCorpReturn) -> Dict[str, Any]:
        """
        Generate Form 1120-S data for S-Corporations

        Args:
            return_data: The return data

        Returns:
            Dict: Form 1120-S data
        """
        if return_data.entity_type not in [EntityType.S_CORPORATION, EntityType.LLC_TAXED_AS_S_CORP]:
            raise ValueError("Form 1120-S is only for S-Corporations")

        form_data = {
            'form_type': '1120-S',
            'tax_year': return_data.tax_year,
            'entity_name': return_data.entity_name,
            'ein': return_data.ein,
            'business_address': return_data.business_address,
            'business_description': return_data.business_description,
            'shareholder_type': return_data.s_corp_shareholder_type.value if return_data.s_corp_shareholder_type else '',
            'principal_business_activity': return_data.principal_business_activity,
            'business_activity_code': return_data.business_activity_code,
            'accounting_method': return_data.accounting_method,

            # Income section
            'gross_receipts': return_data.income.gross_receipts,
            'returns_allowances': return_data.income.returns_allowances,
            'cost_of_goods_sold': return_data.income.cost_of_goods_sold,
            'gross_profit': return_data.income.gross_profit,
            'ordinary_income': return_data.ordinary_business_income,
            'net_income_loss': return_data.net_income_loss,

            # Distributions and AAA
            'distributions': return_data.distributions,
            'accumulated_adjustments_account': return_data.accumulated_adjustments_account,

            # Shareholders
            'number_of_shareholders': len(return_data.partners_shareholders),
            'shareholders': [p.to_dict() for p in return_data.partners_shareholders],
        }

        return form_data

    def add_partner_shareholder(self, tax_data: Any, partner: PartnerShareholder) -> bool:
        """
        Add a partner or shareholder to the entity.

        Args:
            tax_data: Tax data model
            partner: Partner/shareholder to add

        Returns:
            bool: True if successful
        """
        try:
            partners = self.get_partners_shareholders(tax_data)
            
            # Check for duplicate SSN/EIN
            if any(p.ssn_ein == partner.ssn_ein for p in partners):
                self.logger.warning(f"Duplicate partner SSN/EIN: {partner.ssn_ein}")
                return False
            
            partners.append(partner)
            partner_dicts = [p.to_dict() for p in partners]
            
            # Save to tax_data
            tax_data.set("partnership_s_corp.partners", partner_dicts)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add partner/shareholder: {e}")
            self.error_tracker.log_error("partnership_add_partner", str(e))
            return False

    def get_partners_shareholders(self, tax_data: Any) -> List[PartnerShareholder]:
        """
        Get all partners/shareholders from tax data.

        Args:
            tax_data: Tax data model

        Returns:
            List[PartnerShareholder]: List of partners/shareholders
        """
        try:
            partner_dicts = tax_data.get("partnership_s_corp.partners", [])
            return [PartnerShareholder.from_dict(p) for p in partner_dicts]
        except Exception as e:
            self.logger.error(f"Failed to load partners/shareholders: {e}")
            return []

    def calculate_taxable_income(self, income: Decimal, deductions: Decimal) -> Decimal:
        """
        Calculate taxable income for the entity.

        Args:
            income: Total income
            deductions: Total deductions

        Returns:
            Decimal: Taxable income
        """
        return income - deductions

    def calculate_partner_share_of_income(self, entity_income: Decimal, partner: PartnerShareholder) -> Decimal:
        """
        Calculate a partner's share of entity income.

        Args:
            entity_income: Total entity income
            partner: Partner to calculate for

        Returns:
            Decimal: Partner's share of income
        """
        return entity_income * (partner.ownership_percentage / Decimal('100'))

    def calculate_partner_share_of_losses(self, entity_loss: Decimal, ownership_percentage: Decimal) -> Decimal:
        """
        Calculate a partner's share of entity losses.

        Args:
            entity_loss: Total entity loss
            ownership_percentage: Partner's ownership percentage

        Returns:
            Decimal: Partner's share of loss
        """
        return entity_loss * (ownership_percentage / Decimal('100'))

    def calculate_dividend_per_share(self, net_income: Decimal, number_of_shares: int) -> Decimal:
        """
        Calculate dividend per share for S-Corp.

        Args:
            net_income: Net income available for distribution
            number_of_shares: Total number of shares outstanding

        Returns:
            Decimal: Dividend per share
        """
        if number_of_shares == 0:
            return Decimal('0')
        return net_income / Decimal(number_of_shares)

    def calculate_capital_account(self, beginning_balance: Decimal, income_allocated: Decimal, distributions: Decimal) -> Decimal:
        """
        Calculate partner's capital account balance.

        Args:
            beginning_balance: Beginning capital account balance
            income_allocated: Income allocated to partner
            distributions: Distributions made to partner

        Returns:
            Decimal: Ending capital account balance
        """
        return beginning_balance + income_allocated - distributions

    def validate_partner_data(self, partner: PartnerShareholder) -> List[str]:
        """
        Validate partner/shareholder data.

        Args:
            partner: Partner to validate

        Returns:
            List of validation error messages
        """
        errors = []
        
        if not partner.name.strip():
            errors.append("Partner/shareholder name is required")
        
        if not partner.ssn_ein.strip():
            errors.append("Partner/shareholder SSN or EIN is required")
        
        if not partner.address.strip():
            errors.append("Partner/shareholder address is required")
        
        if partner.ownership_percentage < 0 or partner.ownership_percentage > 100:
            errors.append("Ownership percentage must be between 0 and 100")
        
        return errors

    def get_filing_instructions(self) -> str:
        """
        Get filing instructions for partnership/S-Corp returns

        Returns:
            str: Filing instructions
        """
        return """
Partnership and S-Corporation Tax Return Filing Instructions:

FORMS:
- Form 1065: U.S. Return of Partnership Income (for partnerships)
- Form 1120-S: U.S. Income Tax Return for an S Corporation (for S-Corps)
- Schedule K-1: Partner's/Shareholder's Share of Income, Deductions, Credits

FILING DEADLINES:
- Calendar year: 15th day of 4th month after year-end (April 15 for calendar year)
- Fiscal year: 15th day of 4th month after year-end

REQUIRED INFORMATION:
- Employer Identification Number (EIN)
- Business address and description
- Principal business activity code
- Names, addresses, and ownership percentages of all partners/shareholders
- SSN or EIN for each partner/shareholder

IMPORTANT NOTES:
- Pass-through entities don't pay tax at the entity level
- Income/loss flows through to partners/shareholders
- K-1 forms must be provided to each partner/shareholder
- Extensions available using Form 7004
"""