"""
Tax Planning Service - Advanced tax planning and optimization tools

This service provides sophisticated tax planning capabilities including:
- What-if scenario analysis
- Tax projections for future years
- Estimated tax payment calculations
- Withholding optimization
- Retirement contribution optimization
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
from config.tax_year_config import get_tax_year_config, TaxYearConfig
from services.tax_calculation_service import TaxCalculationService, TaxResult
from utils.tax_calculations import calculate_income_tax, calculate_standard_deduction

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    """Result of a what-if scenario analysis"""

    scenario_name: str
    original_tax: float
    new_tax: float
    tax_difference: float
    refund_difference: float
    effective_rate_change: float
    key_changes: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'scenario_name': self.scenario_name,
            'original_tax': self.original_tax,
            'new_tax': self.new_tax,
            'tax_difference': self.tax_difference,
            'refund_difference': self.refund_difference,
            'effective_rate_change': self.effective_rate_change,
            'key_changes': self.key_changes
        }


@dataclass
class TaxProjection:
    """Tax projection for a future year"""

    projection_year: int
    projected_income: float
    projected_deductions: float
    projected_taxable_income: float
    projected_tax: float
    confidence_level: str  # 'high', 'medium', 'low'
    assumptions: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'projection_year': self.projection_year,
            'projected_income': self.projected_income,
            'projected_deductions': self.projected_deductions,
            'projected_taxable_income': self.projected_taxable_income,
            'projected_tax': self.projected_tax,
            'confidence_level': self.confidence_level,
            'assumptions': self.assumptions
        }


@dataclass
class EstimatedTaxPayment:
    """Quarterly estimated tax payment calculation"""

    quarter: int
    year: int
    payment_amount: float
    due_date: date
    safe_harbor_amount: float
    annualized_income_method: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'quarter': self.quarter,
            'year': self.year,
            'payment_amount': self.payment_amount,
            'due_date': self.due_date.isoformat(),
            'safe_harbor_amount': self.safe_harbor_amount,
            'annualized_income_method': self.annualized_income_method,
            'reasoning': self.reasoning
        }


@dataclass
class WithholdingRecommendation:
    """W-4 withholding recommendation"""

    current_withholding: float
    recommended_withholding: float
    adjustment_needed: float
    expected_annual_tax: float
    expected_annual_refund: float
    w4_adjustments: Dict[str, Any]
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'current_withholding': self.current_withholding,
            'recommended_withholding': self.recommended_withholding,
            'adjustment_needed': self.adjustment_needed,
            'expected_annual_tax': self.expected_annual_tax,
            'expected_annual_refund': self.expected_annual_refund,
            'w4_adjustments': self.w4_adjustments,
            'reasoning': self.reasoning
        }


@dataclass
class RetirementOptimization:
    """Retirement contribution optimization"""

    traditional_ira_limit: float
    roth_ira_limit: float
    employer_401k_limit: float
    recommended_traditional: float
    recommended_roth: float
    recommended_401k: float
    tax_savings: float
    net_benefit: float
    strategy: str
    reasoning: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'traditional_ira_limit': self.traditional_ira_limit,
            'roth_ira_limit': self.roth_ira_limit,
            'employer_401k_limit': self.employer_401k_limit,
            'recommended_traditional': self.recommended_traditional,
            'recommended_roth': self.recommended_roth,
            'recommended_401k': self.recommended_401k,
            'tax_savings': self.tax_savings,
            'net_benefit': self.net_benefit,
            'strategy': self.strategy,
            'reasoning': self.reasoning
        }


class TaxPlanningService:
    """
    Advanced tax planning service providing scenario analysis,
    projections, and optimization recommendations.
    """

    def __init__(self, tax_year: int = 2025):
        """
        Initialize tax planning service.

        Args:
            tax_year: Current tax year for planning (default: 2025)
        """
        self.tax_year = tax_year
        self.config: TaxYearConfig = get_tax_year_config(tax_year)
        self.calc_service = TaxCalculationService(tax_year)
        logger.info(f"Initialized TaxPlanningService for tax year {tax_year}")

    def analyze_scenario(self, current_tax_data: Any, scenario_changes: Dict[str, Any],
                        scenario_name: str = "Custom Scenario") -> ScenarioResult:
        """
        Analyze a what-if scenario by applying changes to current tax data.

        Args:
            current_tax_data: Current tax data (dict or TaxData object)
            scenario_changes: Dictionary of changes to apply
            scenario_name: Name for the scenario

        Returns:
            ScenarioResult with comparison of original vs new tax situation
        """
        # Calculate original tax
        original_result = self.calc_service.calculate_complete_return(current_tax_data)

        # Create modified tax data
        modified_data = self._apply_scenario_changes(current_tax_data, scenario_changes)

        # Calculate new tax
        new_result = self.calc_service.calculate_complete_return(modified_data)

        # Calculate differences
        tax_difference = new_result.total_tax - original_result.total_tax
        refund_difference = (new_result.refund_amount - new_result.amount_owed) - \
                           (original_result.refund_amount - original_result.amount_owed)

        # Calculate effective rate change
        if original_result.taxable_income > 0:
            original_rate = original_result.total_tax / original_result.taxable_income
            new_rate = new_result.total_tax / new_result.taxable_income if new_result.taxable_income > 0 else 0
            effective_rate_change = new_rate - original_rate
        else:
            effective_rate_change = 0.0

        return ScenarioResult(
            scenario_name=scenario_name,
            original_tax=original_result.total_tax,
            new_tax=new_result.total_tax,
            tax_difference=tax_difference,
            refund_difference=refund_difference,
            effective_rate_change=effective_rate_change,
            key_changes=scenario_changes
        )

    def project_future_tax(self, current_tax_data: Any, projection_year: int,
                          income_growth_rate: float = 0.03,
                          inflation_rate: float = 0.025) -> TaxProjection:
        """
        Project tax liability for a future year based on current data and growth assumptions.

        Args:
            current_tax_data: Current tax data
            projection_year: Year to project for
            income_growth_rate: Expected annual income growth rate (default: 3%)
            inflation_rate: Expected inflation rate (default: 2.5%)

        Returns:
            TaxProjection with estimated future tax liability
        """
        # Get current income
        current_result = self.calc_service.calculate_complete_return(current_tax_data)
        years_ahead = projection_year - self.tax_year

        # Project income growth
        projected_income = current_result.total_income * ((1 + income_growth_rate) ** years_ahead)

        # Project deductions (adjusted for inflation)
        current_deductions = current_result.deduction_used
        projected_deductions = current_deductions * ((1 + inflation_rate) ** years_ahead)

        # Get filing status
        get_value = current_tax_data.get if hasattr(current_tax_data, 'get') else \
                   lambda k, d=None: current_tax_data.data.get(k, d)
        filing_status = get_value('filing_status.status', 'Single')

        # Get future tax config
        future_config = get_tax_year_config(projection_year)
        future_standard_deduction = future_config.standard_deductions.get(filing_status,
                                                                         future_config.standard_deductions["Single"])

        # Use the higher of projected or future standard deduction
        projected_deductions = max(projected_deductions, future_standard_deduction)

        # Calculate projected taxable income
        projected_taxable_income = max(0, projected_income - projected_deductions)

        # Calculate projected tax
        projected_tax = calculate_income_tax(projected_taxable_income, filing_status, projection_year)

        # Determine confidence level
        confidence_level = 'high' if years_ahead <= 2 else 'medium' if years_ahead <= 5 else 'low'

        assumptions = {
            'income_growth_rate': income_growth_rate,
            'inflation_rate': inflation_rate,
            'years_ahead': years_ahead,
            'current_income': current_result.total_income,
            'current_deductions': current_deductions,
            'filing_status': filing_status
        }

        return TaxProjection(
            projection_year=projection_year,
            projected_income=projected_income,
            projected_deductions=projected_deductions,
            projected_taxable_income=projected_taxable_income,
            projected_tax=projected_tax,
            confidence_level=confidence_level,
            assumptions=assumptions
        )

    def calculate_estimated_tax_payments(self, current_tax_data: Any,
                                       annual_income_projection: float) -> List[EstimatedTaxPayment]:
        """
        Calculate quarterly estimated tax payments for the current year.

        Args:
            current_tax_data: Current tax data
            annual_income_projection: Projected annual income for the year

        Returns:
            List of EstimatedTaxPayment objects for each quarter
        """
        # Get filing status and calculate expected annual tax
        get_value = current_tax_data.get if hasattr(current_tax_data, 'get') else \
                   lambda k, d=None: current_tax_data.data.get(k, d)
        filing_status = get_value('filing_status.status', 'Single')

        # Calculate standard deduction for the year
        standard_deduction = calculate_standard_deduction(filing_status, self.tax_year)
        taxable_income = max(0, annual_income_projection - standard_deduction)
        annual_tax = calculate_income_tax(taxable_income, filing_status, self.tax_year)

        # Calculate safe harbor amount (100% of prior year tax)
        prior_year_result = self.calc_service.calculate_complete_return(current_tax_data)
        safe_harbor_amount = prior_year_result.total_tax

        # Calculate payments using annualized income method
        payments = []
        quarter_dates = [
            date(self.tax_year, 4, 15),   # Q1
            date(self.tax_year, 6, 15),   # Q2
            date(self.tax_year, 9, 15),   # Q3
            date(self.tax_year + 1, 1, 15) # Q4
        ]

        cumulative_income = 0
        cumulative_tax = 0

        for quarter in range(1, 5):
            # Assume equal quarterly income (simplified)
            quarterly_income = annual_income_projection / 4
            cumulative_income += quarterly_income

            # Calculate annualized income tax
            annualized_taxable = max(0, cumulative_income - standard_deduction)
            annualized_tax = calculate_income_tax(annualized_taxable, filing_status, self.tax_year)
            annualized_tax *= (quarter / 4)  # Adjust for quarter

            quarterly_tax = annualized_tax - cumulative_tax
            cumulative_tax = annualized_tax

            # Use the higher of safe harbor or annualized income method
            payment_amount = max(quarterly_tax, safe_harbor_amount / 4)

            reasoning = f"Quarter {quarter}: Using {'safe harbor' if payment_amount == safe_harbor_amount / 4 else 'annualized income'} method"

            payments.append(EstimatedTaxPayment(
                quarter=quarter,
                year=self.tax_year,
                payment_amount=payment_amount,
                due_date=quarter_dates[quarter - 1],
                safe_harbor_amount=safe_harbor_amount / 4,
                annualized_income_method=quarterly_tax,
                reasoning=reasoning
            ))

        return payments

    def calculate_withholding_recommendation(self, current_tax_data: Any,
                                           expected_annual_income: float) -> WithholdingRecommendation:
        """
        Calculate recommended W-4 withholding adjustments.

        Args:
            current_tax_data: Current tax data
            expected_annual_income: Expected annual income

        Returns:
            WithholdingRecommendation with W-4 adjustment suggestions
        """
        # Calculate expected annual tax
        get_value = current_tax_data.get if hasattr(current_tax_data, 'get') else \
                   lambda k, d=None: current_tax_data.data.get(k, d)
        filing_status = get_value('filing_status.status', 'Single')

        standard_deduction = calculate_standard_deduction(filing_status, self.tax_year)
        taxable_income = max(0, expected_annual_income - standard_deduction)
        expected_annual_tax = calculate_income_tax(taxable_income, filing_status, self.tax_year)

        # Get current withholding (assume from W-2 data)
        current_withholding = 0
        w2_forms = get_value('income.w2_forms', [])
        for w2 in w2_forms:
            current_withholding += w2.get('federal_withholding', 0)

        # Calculate recommended withholding (assume bi-weekly pay periods)
        pay_periods_per_year = 26  # Bi-weekly
        recommended_withholding = expected_annual_tax / pay_periods_per_year

        adjustment_needed = recommended_withholding - (current_withholding / pay_periods_per_year)

        # Calculate expected refund/amount owed
        expected_annual_refund = current_withholding - expected_annual_tax
        if expected_annual_refund < 0:
            expected_annual_refund = 0  # Amount owed instead

        # Generate W-4 adjustment recommendations
        w4_adjustments = {}

        if abs(adjustment_needed) > 10:  # More than $10 per pay period
            if adjustment_needed > 0:
                w4_adjustments['extra_withholding'] = adjustment_needed
                reasoning = f"Increase withholding by ${adjustment_needed:.2f} per pay period to avoid underpayment penalties"
            else:
                w4_adjustments['reduce_withholding'] = abs(adjustment_needed)
                reasoning = f"Reduce withholding by ${abs(adjustment_needed):.2f} per pay period to increase take-home pay"
        else:
            reasoning = "Current withholding is adequate - no changes needed"

        return WithholdingRecommendation(
            current_withholding=current_withholding,
            recommended_withholding=recommended_withholding * pay_periods_per_year,
            adjustment_needed=adjustment_needed,
            expected_annual_tax=expected_annual_tax,
            expected_annual_refund=expected_annual_refund,
            w4_adjustments=w4_adjustments,
            reasoning=reasoning
        )

    def optimize_retirement_contributions(self, current_tax_data: Any,
                                        current_income: float,
                                        employer_401k_match: float = 0.0) -> RetirementOptimization:
        """
        Optimize retirement contributions for maximum tax benefits.

        Args:
            current_tax_data: Current tax data
            current_income: Current annual income
            employer_401k_match: Employer 401(k) match percentage (default: 0%)

        Returns:
            RetirementOptimization with contribution recommendations
        """
        # Get contribution limits for the year
        traditional_ira_limit = self.config.retirement_limits.get('traditional_ira', 7000)
        roth_ira_limit = self.config.retirement_limits.get('roth_ira', 7000)
        employer_401k_limit = self.config.retirement_limits.get('401k', 23000)

        # Get filing status and calculate current tax situation
        get_value = current_tax_data.get if hasattr(current_tax_data, 'get') else \
                   lambda k, d=None: current_tax_data.data.get(k, d)
        filing_status = get_value('filing_status.status', 'Single')

        # Calculate current tax without retirement contributions
        standard_deduction = calculate_standard_deduction(filing_status, self.tax_year)
        current_taxable = max(0, current_income - standard_deduction)
        current_tax = calculate_income_tax(current_taxable, filing_status, self.tax_year)

        # Determine eligibility and optimal contributions
        reasoning = []

        # Traditional 401(k) - always beneficial for tax deduction
        recommended_401k = employer_401k_match * current_income  # At least match employer contribution
        if recommended_401k > employer_401k_limit:
            recommended_401k = employer_401k_limit
        reasoning.append(f"Contribute at least ${recommended_401k:.0f} to 401(k) to get employer match")

        # Traditional IRA - deductible if income below certain limits
        income_limits = self.config.ira_deductibility_limits.get(filing_status, {})
        magi_limit = income_limits.get('magi_limit', 0)

        if current_income <= magi_limit or magi_limit == 0:
            recommended_traditional = traditional_ira_limit
            reasoning.append(f"Contribute ${traditional_ira_limit:.0f} to Traditional IRA for tax deduction")
        else:
            recommended_traditional = 0
            reasoning.append("Income too high for Traditional IRA deduction - consider Roth IRA")

        # Roth IRA - after-tax but tax-free growth
        recommended_roth = roth_ira_limit if recommended_traditional == 0 else 0

        # Calculate tax savings
        total_contributions = recommended_traditional + recommended_roth + recommended_401k
        reduced_taxable_income = max(0, current_income - total_contributions - standard_deduction)
        new_tax = calculate_income_tax(reduced_taxable_income, filing_status, self.tax_year)
        tax_savings = current_tax - new_tax

        # Calculate net benefit (accounting for Roth being after-tax)
        net_benefit = tax_savings  # Simplified - doesn't account for future tax-free growth

        # Determine strategy
        if recommended_traditional > 0:
            strategy = "Maximize Traditional IRA and 401(k) for immediate tax benefits"
        elif recommended_roth > 0:
            strategy = "Use Roth IRA for tax-free future growth"
        else:
            strategy = "Focus on employer 401(k) match first"

        return RetirementOptimization(
            traditional_ira_limit=traditional_ira_limit,
            roth_ira_limit=roth_ira_limit,
            employer_401k_limit=employer_401k_limit,
            recommended_traditional=recommended_traditional,
            recommended_roth=recommended_roth,
            recommended_401k=recommended_401k,
            tax_savings=tax_savings,
            net_benefit=net_benefit,
            strategy=strategy,
            reasoning=reasoning
        )

    def _apply_scenario_changes(self, tax_data: Any, changes: Dict[str, Any]) -> Any:
        """
        Apply scenario changes to tax data.

        Args:
            tax_data: Original tax data
            changes: Dictionary of changes to apply

        Returns:
            Modified tax data object
        """
        # If it's a TaxData object, create a copy and modify its data
        if hasattr(tax_data, 'data'):
            # Create a deep copy of the TaxData object
            import copy
            modified_tax_data = copy.deepcopy(tax_data)
            
            # Apply changes to the copied data
            def apply_nested_changes(target: Dict[str, Any], changes: Dict[str, Any]):
                for key, value in changes.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        apply_nested_changes(target[key], value)
                    elif isinstance(value, list) and key in target and isinstance(target[key], list):
                        # Handle list modifications (like w2_forms)
                        if key == 'w2_forms' and target[key] and isinstance(target[key][0], dict):
                            # Modify existing W-2 form
                            for change_key, change_value in value[0].items():
                                if change_key in target[key][0]:
                                    if isinstance(change_value, (int, float)):
                                        target[key][0][change_key] += change_value
                                    else:
                                        target[key][0][change_key] = change_value
                    else:
                        target[key] = value

            apply_nested_changes(modified_tax_data.data, changes)
            # Clear any caching to ensure fresh calculation
            if hasattr(modified_tax_data, '_calculation_cache'):
                modified_tax_data._calculation_cache = {}
            if hasattr(modified_tax_data, '_cache_timestamp'):
                modified_tax_data._cache_timestamp = None
            return modified_tax_data

        # For plain dictionaries, work with copies
        else:
            import copy
            data = copy.deepcopy(tax_data)

            # Apply changes recursively
            def apply_nested_changes(target: Dict[str, Any], changes: Dict[str, Any]):
                for key, value in changes.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        apply_nested_changes(target[key], value)
                    else:
                        target[key] = value

            apply_nested_changes(data, changes)
            return data