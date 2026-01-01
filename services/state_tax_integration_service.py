"""
State Tax Integration Service

Handles state tax return preparation, calculations, and e-filing for all 50 states.
Provides state-specific tax forms, calculations, and multi-state return support.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

from services.encryption_service import EncryptionService
from config.app_config import AppConfig


class StateCode(Enum):
    """US State and Territory Codes"""
    AL = "AL"  # Alabama
    AK = "AK"  # Alaska
    AZ = "AZ"  # Arizona
    AR = "AR"  # Arkansas
    CA = "CA"  # California
    CO = "CO"  # Colorado
    CT = "CT"  # Connecticut
    DE = "DE"  # Delaware
    FL = "FL"  # Florida
    GA = "GA"  # Georgia
    HI = "HI"  # Hawaii
    ID = "ID"  # Idaho
    IL = "IL"  # Illinois
    IN = "IN"  # Indiana
    IA = "IA"  # Iowa
    KS = "KS"  # Kansas
    KY = "KY"  # Kentucky
    LA = "LA"  # Louisiana
    ME = "ME"  # Maine
    MD = "MD"  # Maryland
    MA = "MA"  # Massachusetts
    MI = "MI"  # Michigan
    MN = "MN"  # Minnesota
    MS = "MS"  # Mississippi
    MO = "MO"  # Missouri
    MT = "MT"  # Montana
    NE = "NE"  # Nebraska
    NV = "NV"  # Nevada
    NH = "NH"  # New Hampshire
    NJ = "NJ"  # New Jersey
    NM = "NM"  # New Mexico
    NY = "NY"  # New York
    NC = "NC"  # North Carolina
    ND = "ND"  # North Dakota
    OH = "OH"  # Ohio
    OK = "OK"  # Oklahoma
    OR = "OR"  # Oregon
    PA = "PA"  # Pennsylvania
    RI = "RI"  # Rhode Island
    SC = "SC"  # South Carolina
    SD = "SD"  # South Dakota
    TN = "TN"  # Tennessee
    TX = "TX"  # Texas
    UT = "UT"  # Utah
    VT = "VT"  # Vermont
    VA = "VA"  # Virginia
    WA = "WA"  # Washington
    WV = "WV"  # West Virginia
    WI = "WI"  # Wisconsin
    WY = "WY"  # Wyoming
    DC = "DC"  # District of Columbia
    PR = "PR"  # Puerto Rico
    VI = "VI"  # US Virgin Islands
    GU = "GU"  # Guam
    MP = "MP"  # Northern Mariana Islands
    AS = "AS"  # American Samoa


class FilingStatus(Enum):
    """State tax filing status options"""
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"
    QUALIFYING_WIDOW = "qualifying_widow"


class StateTaxType(Enum):
    """Types of state income tax systems"""
    PROGRESSIVE = "progressive"  # Progressive tax brackets
    FLAT = "flat"                # Flat tax rate
    NO_INCOME_TAX = "no_income_tax"  # No state income tax
    TERRITORIAL = "territorial"  # US territories


@dataclass
class StateTaxBracket:
    """Tax bracket for a specific state"""
    min_income: float
    max_income: Optional[float]  # None for highest bracket
    rate: float
    filing_status: FilingStatus


@dataclass
class StateTaxInfo:
    """Tax information for a specific state"""
    state_code: StateCode
    state_name: str
    tax_type: StateTaxType
    flat_rate: Optional[float] = None  # For flat tax states
    brackets: List[StateTaxBracket] = field(default_factory=list)
    standard_deduction: Dict[FilingStatus, float] = field(default_factory=dict)
    personal_exemption: Optional[float] = None
    dependent_exemption: Optional[float] = None
    local_tax_supported: bool = False
    e_filing_supported: bool = True
    tax_deadline: str = "April 15"  # Default deadline


@dataclass
class StateIncome:
    """Income sources for state tax purposes"""
    wages: float = 0.0
    interest: float = 0.0
    dividends: float = 0.0
    capital_gains: float = 0.0
    business_income: float = 0.0
    rental_income: float = 0.0
    other_income: float = 0.0

    @property
    def total_income(self) -> float:
        """Calculate total income"""
        return (self.wages + self.interest + self.dividends +
                self.capital_gains + self.business_income +
                self.rental_income + self.other_income)


@dataclass
class StateDeductions:
    """Deductions for state tax purposes"""
    standard_deduction: float = 0.0
    itemized_deductions: float = 0.0
    personal_exemption: float = 0.0
    dependent_exemptions: float = 0.0
    other_deductions: float = 0.0

    @property
    def total_deductions(self) -> float:
        """Calculate total deductions"""
        return (self.standard_deduction + self.itemized_deductions +
                self.personal_exemption + self.dependent_exemptions +
                self.other_deductions)


@dataclass
class StateTaxCalculation:
    """State tax calculation result"""
    state_code: StateCode
    tax_year: int
    filing_status: FilingStatus
    gross_income: float
    taxable_income: float
    tax_amount: float
    effective_rate: float
    marginal_rate: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    credits: float = 0.0
    net_tax_owed: float = 0.0


@dataclass
class StateTaxReturn:
    """Complete state tax return data"""
    return_id: str
    state_code: StateCode
    tax_year: int
    taxpayer_info: Dict[str, Any]
    filing_status: FilingStatus
    income: StateIncome
    deductions: StateDeductions
    calculation: StateTaxCalculation
    payments: List[Dict[str, Any]] = field(default_factory=list)
    refund_amount: float = 0.0
    amount_due: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"  # draft, filed, accepted, rejected


class StateTaxIntegrationService:
    """Main service for state tax integration"""

    def __init__(self, config: AppConfig, encryption_service: EncryptionService):
        self.config = config
        self.encryption = encryption_service
        self.logger = logging.getLogger(__name__)

        # Initialize state tax data
        self.state_tax_info: Dict[StateCode, StateTaxInfo] = {}
        self.tax_returns: Dict[str, StateTaxReturn] = {}
        self.state_data_file = os.path.join(config.safe_dir, "state_tax_data.json")

        # Load state tax information
        self._load_state_tax_data()

    def _load_state_tax_data(self):
        """Load state tax information from data file"""
        try:
            if os.path.exists(self.state_data_file):
                with open(self.state_data_file, 'r') as f:
                    data = json.load(f)
                    for state_code, state_data in data.items():
                        self.state_tax_info[StateCode(state_code)] = StateTaxInfo(**state_data)
            else:
                # Initialize with default state data
                self._initialize_default_state_data()
                self._save_state_tax_data()
        except Exception as e:
            self.logger.error(f"Failed to load state tax data: {e}")
            self._initialize_default_state_data()

    def _initialize_default_state_data(self):
        """Initialize default state tax data for major states"""
        # California (Progressive)
        ca_brackets = [
            StateTaxBracket(0, 10099, 0.01, FilingStatus.SINGLE),
            StateTaxBracket(10099, 23942, 0.02, FilingStatus.SINGLE),
            StateTaxBracket(23942, 37788, 0.04, FilingStatus.SINGLE),
            StateTaxBracket(37788, 52455, 0.06, FilingStatus.SINGLE),
            StateTaxBracket(52455, 66295, 0.08, FilingStatus.SINGLE),
            StateTaxBracket(66295, 349137, 0.09, FilingStatus.SINGLE),
            StateTaxBracket(349137, 590742, 0.10, FilingStatus.SINGLE),
            StateTaxBracket(590742, 1000000, 0.11, FilingStatus.SINGLE),
            StateTaxBracket(1000000, None, 0.13, FilingStatus.SINGLE),
        ]

        self.state_tax_info[StateCode.CA] = StateTaxInfo(
            state_code=StateCode.CA,
            state_name="California",
            tax_type=StateTaxType.PROGRESSIVE,
            brackets=ca_brackets,
            standard_deduction={
                FilingStatus.SINGLE: 5202,
                FilingStatus.MARRIED_FILING_JOINTLY: 10404,
                FilingStatus.MARRIED_FILING_SEPARATELY: 5202,
                FilingStatus.HEAD_OF_HOUSEHOLD: 5202,
            },
            personal_exemption=144.55,
            dependent_exemption=408.07,
            local_tax_supported=True,
            tax_deadline="April 15"
        )

        # Texas (No Income Tax)
        self.state_tax_info[StateCode.TX] = StateTaxInfo(
            state_code=StateCode.TX,
            state_name="Texas",
            tax_type=StateTaxType.NO_INCOME_TAX,
            tax_deadline="N/A"
        )

        # Florida (No Income Tax)
        self.state_tax_info[StateCode.FL] = StateTaxInfo(
            state_code=StateCode.FL,
            state_name="Florida",
            tax_type=StateTaxType.NO_INCOME_TAX,
            tax_deadline="N/A"
        )

        # Alaska (No Income Tax)
        self.state_tax_info[StateCode.AK] = StateTaxInfo(
            state_code=StateCode.AK,
            state_name="Alaska",
            tax_type=StateTaxType.NO_INCOME_TAX,
            tax_deadline="N/A"
        )

        # New York (Progressive)
        ny_brackets = [
            StateTaxBracket(0, 8500, 0.04, FilingStatus.SINGLE),
            StateTaxBracket(8500, 11700, 0.045, FilingStatus.SINGLE),
            StateTaxBracket(11700, 13900, 0.0525, FilingStatus.SINGLE),
            StateTaxBracket(13900, 21400, 0.059, FilingStatus.SINGLE),
            StateTaxBracket(21400, 80650, 0.0597, FilingStatus.SINGLE),
            StateTaxBracket(80650, 215400, 0.0633, FilingStatus.SINGLE),
            StateTaxBracket(215400, 1077550, 0.0685, FilingStatus.SINGLE),
            StateTaxBracket(1077550, None, 0.0882, FilingStatus.SINGLE),
        ]

        self.state_tax_info[StateCode.NY] = StateTaxInfo(
            state_code=StateCode.NY,
            state_name="New York",
            tax_type=StateTaxType.PROGRESSIVE,
            brackets=ny_brackets,
            standard_deduction={
                FilingStatus.SINGLE: 8000,
                FilingStatus.MARRIED_FILING_JOINTLY: 16050,
                FilingStatus.MARRIED_FILING_SEPARATELY: 8000,
                FilingStatus.HEAD_OF_HOUSEHOLD: 11200,
            },
            local_tax_supported=True,
            tax_deadline="April 15"
        )

        # Illinois (Flat Rate)
        self.state_tax_info[StateCode.IL] = StateTaxInfo(
            state_code=StateCode.IL,
            state_name="Illinois",
            tax_type=StateTaxType.FLAT,
            flat_rate=0.0495,
            standard_deduction={
                FilingStatus.SINGLE: 0,  # Illinois has no standard deduction
                FilingStatus.MARRIED_FILING_JOINTLY: 0,
            },
            personal_exemption=242,
            dependent_exemption=242,
            tax_deadline="April 15"
        )

    def _save_state_tax_data(self):
        """Save state tax data to file"""
        try:
            data = {}
            for state_code, state_info in self.state_tax_info.items():
                data[state_code.value] = asdict(state_info)

            with open(self.state_data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save state tax data: {e}")

    def get_state_tax_info(self, state_code: StateCode) -> Optional[StateTaxInfo]:
        """Get tax information for a specific state"""
        return self.state_tax_info.get(state_code)

    def get_all_states(self) -> List[StateTaxInfo]:
        """Get tax information for all states"""
        return list(self.state_tax_info.values())

    def calculate_state_tax(self, state_code: StateCode, tax_year: int,
                          filing_status: FilingStatus, income: StateIncome,
                          deductions: StateDeductions, credits: float = 0.0) -> StateTaxCalculation:
        """
        Calculate state income tax for given parameters

        Args:
            state_code: The state to calculate tax for
            tax_year: Tax year (e.g., 2024)
            filing_status: Filing status
            income: Income sources
            deductions: Deductions and exemptions
            credits: Tax credits

        Returns:
            StateTaxCalculation with detailed tax breakdown
        """
        state_info = self.get_state_tax_info(state_code)
        if not state_info:
            raise ValueError(f"State tax information not available for {state_code.value}")

        # Calculate gross income
        gross_income = income.total_income

        # Calculate taxable income
        taxable_income = max(0, gross_income - deductions.total_deductions)

        # Calculate tax based on state tax type
        if state_info.tax_type == StateTaxType.NO_INCOME_TAX:
            tax_amount = 0.0
            marginal_rate = 0.0
            breakdown = {}

        elif state_info.tax_type == StateTaxType.FLAT:
            tax_amount = taxable_income * state_info.flat_rate
            marginal_rate = state_info.flat_rate
            breakdown = {f"Flat rate ({state_info.flat_rate:.2%})": tax_amount}

        elif state_info.tax_type == StateTaxType.PROGRESSIVE:
            tax_amount, marginal_rate, breakdown = self._calculate_progressive_tax(
                taxable_income, state_info.brackets, filing_status
            )

        else:
            raise ValueError(f"Unsupported tax type: {state_info.tax_type}")

        # Calculate effective rate
        effective_rate = tax_amount / gross_income if gross_income > 0 else 0.0

        # Apply credits
        net_tax_owed = max(0, tax_amount - credits)

        return StateTaxCalculation(
            state_code=state_code,
            tax_year=tax_year,
            filing_status=filing_status,
            gross_income=gross_income,
            taxable_income=taxable_income,
            tax_amount=tax_amount,
            effective_rate=effective_rate,
            marginal_rate=marginal_rate,
            breakdown=breakdown,
            credits=credits,
            net_tax_owed=net_tax_owed
        )

    def _calculate_progressive_tax(self, taxable_income: float,
                                 brackets: List[StateTaxBracket],
                                 filing_status: FilingStatus) -> tuple[float, float, Dict[str, float]]:
        """
        Calculate progressive tax using tax brackets

        Returns:
            Tuple of (total_tax, marginal_rate, breakdown_dict)
        """
        total_tax = 0.0
        breakdown = {}
        marginal_rate = 0.0

        # Filter brackets for filing status
        status_brackets = [b for b in brackets if b.filing_status == filing_status]

        for bracket in sorted(status_brackets, key=lambda b: b.min_income):
            if taxable_income <= bracket.min_income:
                break

            # Calculate tax for this bracket
            bracket_start = bracket.min_income
            bracket_end = bracket.max_income if bracket.max_income else taxable_income

            if taxable_income > bracket_start:
                taxable_in_bracket = min(taxable_income, bracket_end) - bracket_start
                tax_in_bracket = taxable_in_bracket * bracket.rate
                total_tax += tax_in_bracket

                if bracket.max_income is None or taxable_income >= bracket_end:
                    marginal_rate = bracket.rate

                # Add to breakdown
                if bracket.max_income:
                    range_desc = f"${bracket.min_income:,.0f} - ${bracket.max_income:,.0f}"
                else:
                    range_desc = f"${bracket.min_income:,.0f}+"

                breakdown[f"{range_desc} ({bracket.rate:.1%})"] = tax_in_bracket

        return total_tax, marginal_rate, breakdown

    def create_state_tax_return(self, state_code: StateCode, tax_year: int,
                              taxpayer_info: Dict[str, Any], filing_status: FilingStatus,
                              income: StateIncome, deductions: StateDeductions,
                              credits: float = 0.0) -> str:
        """
        Create a new state tax return

        Returns:
            Return ID for the created return
        """
        # Calculate tax
        calculation = self.calculate_state_tax(
            state_code, tax_year, filing_status, income, deductions, credits
        )

        # Create return
        return_id = f"state_{state_code.value}_{tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        tax_return = StateTaxReturn(
            return_id=return_id,
            state_code=state_code,
            tax_year=tax_year,
            taxpayer_info=taxpayer_info,
            filing_status=filing_status,
            income=income,
            deductions=deductions,
            calculation=calculation
        )

        self.tax_returns[return_id] = tax_return
        return return_id

    def get_state_tax_return(self, return_id: str) -> Optional[StateTaxReturn]:
        """Get a state tax return by ID"""
        return self.tax_returns.get(return_id)

    def get_state_returns_for_taxpayer(self, taxpayer_id: str, tax_year: Optional[int] = None) -> List[StateTaxReturn]:
        """Get all state returns for a taxpayer"""
        returns = []
        for tax_return in self.tax_returns.values():
            if tax_return.taxpayer_info.get('taxpayer_id') == taxpayer_id:
                if tax_year is None or tax_return.tax_year == tax_year:
                    returns.append(tax_return)
        return returns

    def update_state_tax_return(self, return_id: str, updates: Dict[str, Any]) -> bool:
        """Update a state tax return"""
        tax_return = self.get_state_tax_return(return_id)
        if not tax_return:
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(tax_return, key):
                setattr(tax_return, key, value)

        tax_return.updated_at = datetime.now()
        return True

    def delete_state_tax_return(self, return_id: str) -> bool:
        """Delete a state tax return"""
        if return_id in self.tax_returns:
            del self.tax_returns[return_id]
            return True
        return False

    def generate_state_tax_form(self, return_id: str, form_type: str = "1040") -> Dict[str, Any]:
        """
        Generate state tax form data for e-filing or printing

        Args:
            return_id: The return ID
            form_type: Type of form to generate (1040, 1040EZ, etc.)

        Returns:
            Form data dictionary ready for e-filing
        """
        tax_return = self.get_state_tax_return(return_id)
        if not tax_return:
            raise ValueError(f"Tax return not found: {return_id}")

        state_info = self.get_state_tax_info(tax_return.state_code)
        if not state_info:
            raise ValueError(f"State information not available for {tax_return.state_code.value}")

        # Generate form data based on state and form type
        form_data = {
            "form_type": f"{state_info.state_code.value} {form_type}",
            "tax_year": tax_return.tax_year,
            "taxpayer_info": tax_return.taxpayer_info,
            "filing_status": tax_return.filing_status.value,
            "income": asdict(tax_return.income),
            "deductions": asdict(tax_return.deductions),
            "tax_calculation": asdict(tax_return.calculation),
            "payments": tax_return.payments,
            "refund_amount": tax_return.refund_amount,
            "amount_due": tax_return.amount_due,
            "generated_at": datetime.now().isoformat()
        }

        return form_data

    def validate_state_tax_return(self, return_id: str) -> List[str]:
        """
        Validate a state tax return for completeness and accuracy

        Returns:
            List of validation error messages (empty if valid)
        """
        tax_return = self.get_state_tax_return(return_id)
        if not tax_return:
            return ["Tax return not found"]

        errors = []

        # Basic validation
        if tax_return.calculation.gross_income < 0:
            errors.append("Gross income cannot be negative")

        if tax_return.calculation.taxable_income < 0:
            errors.append("Taxable income cannot be negative")

        if tax_return.calculation.net_tax_owed < 0:
            errors.append("Net tax owed cannot be negative")

        # State-specific validation
        state_info = self.get_state_tax_info(tax_return.state_code)
        if state_info and state_info.tax_type == StateTaxType.NO_INCOME_TAX:
            if tax_return.calculation.net_tax_owed > 0:
                errors.append(f"{state_info.state_name} has no income tax")

        return errors

    def get_state_tax_deadlines(self, tax_year: int) -> Dict[str, str]:
        """Get tax deadlines for all states"""
        deadlines = {}
        for state_info in self.get_all_states():
            deadlines[state_info.state_code.value] = state_info.tax_deadline
        return deadlines

    def get_states_by_tax_type(self, tax_type: StateTaxType) -> List[StateTaxInfo]:
        """Get all states with a specific tax type"""
        return [state for state in self.get_all_states() if state.tax_type == tax_type]

    def calculate_multi_state_tax(self, states: List[StateCode], tax_year: int,
                                filing_status: FilingStatus, income: StateIncome,
                                deductions: StateDeductions, credits: float = 0.0) -> Dict[str, StateTaxCalculation]:
        """
        Calculate tax for multiple states

        Returns:
            Dictionary mapping state codes to tax calculations
        """
        results = {}
        for state_code in states:
            try:
                calculation = self.calculate_state_tax(
                    state_code, tax_year, filing_status, income, deductions, credits
                )
                results[state_code.value] = calculation
            except Exception as e:
                self.logger.error(f"Failed to calculate tax for {state_code.value}: {e}")

        return results