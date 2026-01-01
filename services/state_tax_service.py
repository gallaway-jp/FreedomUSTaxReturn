"""
State Tax Service - Handle state-specific tax calculations and forms

This module provides functionality for:
- State tax calculations for multiple states
- State-specific tax forms and requirements
- Multi-state tax return preparation
- State tax credits and deductions
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger

logger = logging.getLogger(__name__)


class StateCode(Enum):
    """US State and Territory codes"""
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


@dataclass
class StateTaxInfo:
    """Information about a state's tax system"""
    code: StateCode
    name: str
    has_income_tax: bool
    tax_rates: List[Tuple[float, float]]  # [(min_income, rate), ...]
    standard_deduction: Dict[str, float]  # by filing status
    personal_exemption: float = 0.0
    dependent_exemption: float = 0.0
    property_tax_rate: float = 0.0  # average property tax rate
    sales_tax_rate: float = 0.0  # average sales tax rate


@dataclass
class StateTaxCalculation:
    """Result of state tax calculation"""
    state_code: StateCode
    taxable_income: float
    tax_owed: float
    effective_rate: float
    credits: float = 0.0
    deductions: float = 0.0
    withholdings: float = 0.0
    refund_or_owed: float = 0.0


class StateTaxService:
    """
    Service for calculating state income taxes and managing state tax returns.

    Supports multiple states with their specific tax rules, rates, and forms.
    """

    def __init__(self):
        self.state_info = self._initialize_state_tax_info()
        self.supported_states = list(self.state_info.keys())

    def _initialize_state_tax_info(self) -> Dict[StateCode, StateTaxInfo]:
        """Initialize tax information for all supported states"""
        return {
            # No income tax states
            StateCode.AK: StateTaxInfo(
                code=StateCode.AK, name="Alaska", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0118, sales_tax_rate=0.0
            ),
            StateCode.FL: StateTaxInfo(
                code=StateCode.FL, name="Florida", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0089, sales_tax_rate=0.06
            ),
            StateCode.NV: StateTaxInfo(
                code=StateCode.NV, name="Nevada", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0063, sales_tax_rate=0.0685
            ),
            StateCode.NH: StateTaxInfo(
                code=StateCode.NH, name="New Hampshire", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0209, sales_tax_rate=0.0
            ),
            StateCode.SD: StateTaxInfo(
                code=StateCode.SD, name="South Dakota", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0134, sales_tax_rate=0.045
            ),
            StateCode.TN: StateTaxInfo(
                code=StateCode.TN, name="Tennessee", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0069, sales_tax_rate=0.07
            ),
            StateCode.TX: StateTaxInfo(
                code=StateCode.TX, name="Texas", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0181, sales_tax_rate=0.0625
            ),
            StateCode.WA: StateTaxInfo(
                code=StateCode.WA, name="Washington", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0092, sales_tax_rate=0.065
            ),
            StateCode.WY: StateTaxInfo(
                code=StateCode.WY, name="Wyoming", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0059, sales_tax_rate=0.04
            ),

            # States with income tax - Major states first
            StateCode.CA: StateTaxInfo(
                code=StateCode.CA, name="California", has_income_tax=True,
                tax_rates=[
                    (0, 0.01), (10000, 0.02), (25000, 0.04), (40000, 0.06),
                    (55000, 0.08), (70000, 0.09), (100000, 0.10), (125000, 0.11),
                    (150000, 0.12), (200000, 0.13), (500000, 0.14), (1000000, 0.15)
                ],
                standard_deduction={"single": 5202, "married_joint": 10404, "head_household": 5202},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0074, sales_tax_rate=0.0725
            ),

            StateCode.NY: StateTaxInfo(
                code=StateCode.NY, name="New York", has_income_tax=True,
                tax_rates=[
                    (0, 0.04), (8500, 0.045), (11700, 0.0525), (13900, 0.059),
                    (21400, 0.0641), (80650, 0.0665), (215400, 0.0697), (1077550, 0.0707),
                    (2000000, 0.0718), (2500000, 0.0729)
                ],
                standard_deduction={"single": 8000, "married_joint": 16000, "head_household": 11200},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0141, sales_tax_rate=0.04
            ),

            StateCode.NJ: StateTaxInfo(
                code=StateCode.NJ, name="New Jersey", has_income_tax=True,
                tax_rates=[
                    (0, 0.014), (20000, 0.0175), (35000, 0.035), (40000, 0.055),
                    (75000, 0.0637), (500000, 0.0897), (1000000, 0.1075)
                ],
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=1000.0, dependent_exemption=1500.0,
                property_tax_rate=0.0224, sales_tax_rate=0.06625
            ),

            StateCode.IL: StateTaxInfo(
                code=StateCode.IL, name="Illinois", has_income_tax=True,
                tax_rates=[(0, 0.0495)],  # Flat rate
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0208, sales_tax_rate=0.0625
            ),

            StateCode.PA: StateTaxInfo(
                code=StateCode.PA, name="Pennsylvania", has_income_tax=True,
                tax_rates=[(0, 0.0307)],  # Flat rate
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0138, sales_tax_rate=0.06
            ),

            StateCode.MA: StateTaxInfo(
                code=StateCode.MA, name="Massachusetts", has_income_tax=True,
                tax_rates=[
                    (0, 0.05), (1000000, 0.055)
                ],
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0122, sales_tax_rate=0.0625
            ),

            # Additional major states
            StateCode.GA: StateTaxInfo(
                code=StateCode.GA, name="Georgia", has_income_tax=True,
                tax_rates=[
                    (0, 0.01), (750, 0.02), (2250, 0.03), (3750, 0.04), (5250, 0.05), (7000, 0.0575)
                ],
                standard_deduction={"single": 5400, "married_joint": 7100, "head_household": 5400},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0089, sales_tax_rate=0.04
            ),

            StateCode.MI: StateTaxInfo(
                code=StateCode.MI, name="Michigan", has_income_tax=True,
                tax_rates=[(0, 0.0425)],  # Flat rate
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0156, sales_tax_rate=0.06
            ),

            StateCode.NC: StateTaxInfo(
                code=StateCode.NC, name="North Carolina", has_income_tax=True,
                tax_rates=[
                    (0, 0.05), (12500, 0.0525)
                ],
                standard_deduction={"single": 12750, "married_joint": 25500, "head_household": 19125},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0082, sales_tax_rate=0.0475
            ),

            StateCode.MD: StateTaxInfo(
                code=StateCode.MD, name="Maryland", has_income_tax=True,
                tax_rates=[
                    (0, 0.02), (1000, 0.03), (125000, 0.04), (150000, 0.045), (250000, 0.05)
                ],
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=3200.0, dependent_exemption=3200.0,
                property_tax_rate=0.0104, sales_tax_rate=0.06
            ),

            StateCode.WA: StateTaxInfo(
                code=StateCode.WA, name="Washington", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0092, sales_tax_rate=0.065
            ),

            StateCode.AZ: StateTaxInfo(
                code=StateCode.AZ, name="Arizona", has_income_tax=True,
                tax_rates=[
                    (0, 0.0259), (27808, 0.0334), (55615, 0.0417), (83413, 0.0450)
                ],
                standard_deduction={"single": 13850, "married_joint": 27700, "head_household": 20800},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0069, sales_tax_rate=0.056
            ),

            StateCode.TN: StateTaxInfo(
                code=StateCode.TN, name="Tennessee", has_income_tax=False,
                tax_rates=[], standard_deduction={}, property_tax_rate=0.0069, sales_tax_rate=0.07
            ),

            StateCode.IN: StateTaxInfo(
                code=StateCode.IN, name="Indiana", has_income_tax=True,
                tax_rates=[(0, 0.0323)],  # Flat rate
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0084, sales_tax_rate=0.07
            ),

            StateCode.MO: StateTaxInfo(
                code=StateCode.MO, name="Missouri", has_income_tax=True,
                tax_rates=[
                    (0, 0.015), (111, 0.02), (222, 0.025), (333, 0.03), (444, 0.035),
                    (555, 0.04), (666, 0.045), (888, 0.0495), (10555, 0.054)
                ],
                standard_deduction={"single": 13850, "married_joint": 27700, "head_household": 20800},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0097, sales_tax_rate=0.04225
            ),

            StateCode.VA: StateTaxInfo(
                code=StateCode.VA, name="Virginia", has_income_tax=True,
                tax_rates=[
                    (0, 0.02), (3000, 0.03), (17000, 0.05), (50000, 0.0575)
                ],
                standard_deduction={"single": 9300, "married_joint": 18600, "head_household": 15550},
                personal_exemption=930.0, dependent_exemption=930.0,
                property_tax_rate=0.0081, sales_tax_rate=0.053
            ),

            StateCode.NJ: StateTaxInfo(
                code=StateCode.NJ, name="New Jersey", has_income_tax=True,
                tax_rates=[
                    (0, 0.014), (20000, 0.0175), (35000, 0.035), (40000, 0.055),
                    (75000, 0.0637), (500000, 0.0897), (1000000, 0.1075)
                ],
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=1000.0, dependent_exemption=1500.0,
                property_tax_rate=0.0224, sales_tax_rate=0.06625
            ),

            StateCode.CT: StateTaxInfo(
                code=StateCode.CT, name="Connecticut", has_income_tax=True,
                tax_rates=[
                    (0, 0.03), (10000, 0.05), (50000, 0.055), (100000, 0.0599),
                    (200000, 0.0635), (250000, 0.065), (500000, 0.0699)
                ],
                standard_deduction={"single": 0, "married_joint": 0, "head_household": 0},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0191, sales_tax_rate=0.0635
            ),

            StateCode.CO: StateTaxInfo(
                code=StateCode.CO, name="Colorado", has_income_tax=True,
                tax_rates=[(0, 0.0455)],  # Flat rate
                standard_deduction={"single": 13850, "married_joint": 27700, "head_household": 20800},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0051, sales_tax_rate=0.0295
            ),

            StateCode.MN: StateTaxInfo(
                code=StateCode.MN, name="Minnesota", has_income_tax=True,
                tax_rates=[
                    (0, 0.0535), (29750, 0.068), (68550, 0.0785), (101000, 0.0985), (135000, 0.108)
                ],
                standard_deduction={"single": 13825, "married_joint": 27650, "head_household": 20738},
                personal_exemption=0.0, dependent_exemption=0.0,
                property_tax_rate=0.0106, sales_tax_rate=0.06875
            ),

            StateCode.WI: StateTaxInfo(
                code=StateCode.WI, name="Wisconsin", has_income_tax=True,
                tax_rates=[
                    (0, 0.0354), (13810, 0.0465), (27630, 0.0627), (30470, 0.0765)
                ],
                standard_deduction={"single": 12760, "married_joint": 23950, "head_household": 19190},
                personal_exemption=700.0, dependent_exemption=700.0,
                property_tax_rate=0.0184, sales_tax_rate=0.05
            ),

            # Add more states as needed...
        }

    def calculate_state_tax(self, state_code: StateCode, federal_taxable_income: float,
                          filing_status: str, dependents: int = 0,
                          state_deductions: float = 0.0, state_credits: float = 0.0) -> StateTaxCalculation:
        """
        Calculate state income tax for a given state.

        Args:
            state_code: The state code
            federal_taxable_income: Federal taxable income
            filing_status: Federal filing status (single, married_joint, etc.)
            dependents: Number of dependents
            state_deductions: Additional state-specific deductions
            state_credits: State tax credits

        Returns:
            StateTaxCalculation with tax details
        """
        if state_code not in self.state_info:
            raise ValueError(f"State {state_code.value} is not supported")

        state_info = self.state_info[state_code]

        # If state has no income tax, return zero
        if not state_info.has_income_tax:
            return StateTaxCalculation(
                state_code=state_code,
                taxable_income=federal_taxable_income,
                tax_owed=0.0,
                effective_rate=0.0,
                credits=state_credits,
                deductions=state_deductions
            )

        # Calculate state taxable income
        taxable_income = self._calculate_state_taxable_income(
            federal_taxable_income, state_info, filing_status, dependents, state_deductions
        )

        # Calculate state tax owed
        tax_owed = self._calculate_tax_owed(taxable_income, state_info.tax_rates)

        # Apply credits
        net_tax = max(0, tax_owed - state_credits)

        # Calculate effective rate
        effective_rate = (net_tax / federal_taxable_income) if federal_taxable_income > 0 else 0.0

        return StateTaxCalculation(
            state_code=state_code,
            taxable_income=taxable_income,
            tax_owed=net_tax,
            effective_rate=effective_rate,
            credits=state_credits,
            deductions=state_deductions
        )

    def _calculate_state_taxable_income(self, federal_taxable_income: float,
                                      state_info: StateTaxInfo, filing_status: str,
                                      dependents: int, state_deductions: float) -> float:
        """Calculate taxable income for state tax purposes"""
        # Start with federal taxable income
        taxable_income = federal_taxable_income

        # Apply state standard deduction
        if filing_status in state_info.standard_deduction:
            taxable_income = max(0, taxable_income - state_info.standard_deduction[filing_status])

        # Apply personal exemption
        if state_info.personal_exemption > 0:
            taxable_income = max(0, taxable_income - state_info.personal_exemption)

        # Apply dependent exemptions
        if state_info.dependent_exemption > 0:
            dependent_deduction = dependents * state_info.dependent_exemption
            taxable_income = max(0, taxable_income - dependent_deduction)

        # Apply additional state deductions
        taxable_income = max(0, taxable_income - state_deductions)

        return taxable_income

    def _calculate_tax_owed(self, taxable_income: float, tax_rates: List[Tuple[float, float]]) -> float:
        """Calculate tax owed using progressive tax brackets"""
        if not tax_rates:
            return 0.0

        tax_owed = 0.0
        remaining_income = taxable_income

        # Sort tax rates by income threshold
        sorted_rates = sorted(tax_rates, key=lambda x: x[0])

        prev_threshold = 0.0
        for threshold, rate in sorted_rates:
            if remaining_income <= 0:
                break

            bracket_income = min(remaining_income, threshold - prev_threshold) if threshold > prev_threshold else remaining_income
            tax_owed += bracket_income * rate

            if threshold > prev_threshold:
                remaining_income -= bracket_income
                prev_threshold = threshold
            else:
                # Flat rate for remaining income
                break

        return tax_owed

    def get_supported_states(self) -> List[StateCode]:
        """Get list of supported states"""
        return self.supported_states.copy()

    def get_state_info(self, state_code: StateCode) -> Optional[StateTaxInfo]:
        """Get tax information for a specific state"""
        return self.state_info.get(state_code)

    def calculate_multi_state_tax(self, states: List[StateCode], federal_taxable_income: float,
                                filing_status: str, dependents: int = 0) -> Dict[StateCode, StateTaxCalculation]:
        """
        Calculate taxes for multiple states (for multi-state residents).

        Args:
            states: List of state codes
            federal_taxable_income: Federal taxable income
            filing_status: Federal filing status
            dependents: Number of dependents

        Returns:
            Dictionary mapping state codes to their tax calculations
        """
        results = {}
        for state_code in states:
            try:
                calculation = self.calculate_state_tax(
                    state_code, federal_taxable_income, filing_status, dependents
                )
                results[state_code] = calculation
            except ValueError as e:
                logger.warning(f"Could not calculate tax for {state_code.value}: {e}")

        return results

    def get_state_tax_forms(self, state_code: StateCode) -> List[str]:
        """
        Get list of required state tax forms for a given state.

        Args:
            state_code: The state code

        Returns:
            List of form names/IDs
        """
        # This would be expanded with actual state form requirements
        base_forms = {
            StateCode.CA: ["540", "540 Schedule CA", "540 Schedule D"],
            StateCode.NY: ["IT-201", "IT-201-D", "IT-196"],
            StateCode.NJ: ["NJ-1040", "NJ-1040 Schedule NJ-E"],
            StateCode.IL: ["IL-1040", "Schedule IL-E"],
            StateCode.PA: ["PA-40", "PA Schedule SP"],
            StateCode.MA: ["1", "1-NR/PY", "Schedule HC"],
        }

        return base_forms.get(state_code, ["State Income Tax Return"])