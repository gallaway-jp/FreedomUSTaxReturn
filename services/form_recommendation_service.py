"""
Form Recommendation Service - Intelligent tax form suggestions

Analyzes tax data to recommend which forms should be completed based on
income, deductions, credits, and other tax situations.
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import re

from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger


class RecommendationPriority(Enum):
    """Priority levels for form recommendations"""
    CRITICAL = 10  # Must file (e.g., Form 1040)
    HIGH = 8       # Very likely needed
    MEDIUM = 6     # Probably needed
    LOW = 4        # Might be needed
    OPTIONAL = 2   # Could be beneficial


class FormType(Enum):
    """Types of tax forms"""
    INDIVIDUAL_RETURN = "individual_return"
    SCHEDULE = "schedule"
    INFORMATION_RETURN = "information_return"
    ESTIMATE = "estimate"
    AMENDMENT = "amendment"


@dataclass
class FormRecommendation:
    """Recommendation for a specific tax form"""
    form_name: str
    form_type: FormType
    priority: RecommendationPriority
    reason: str
    required_data: List[str]
    estimated_time: int  # minutes
    help_resources: List[str]
    conditional_fields: Optional[Dict[str, Any]] = None
    tax_year: Optional[int] = None


@dataclass
class RecommendationContext:
    """Context information for making recommendations"""
    tax_year: int
    filing_status: str
    has_dependents: bool
    has_spouse: bool
    total_income: float
    total_deductions: float
    total_credits: float


class FormRecommendationService:
    """
    Service for intelligently recommending tax forms based on entered data.

    Analyzes tax return data to suggest which forms and schedules are needed,
    helping users avoid missing required filings or overlooking beneficial forms.
    """

    def __init__(self, config: 'AppConfig'):
        """
        Initialize the form recommendation service.

        Args:
            config: Application configuration
        """
        self.config = config

    def analyze_tax_data(self, tax_data: 'TaxData') -> List[FormRecommendation]:
        """
        Analyze tax data and return form recommendations.

        Args:
            tax_data: The tax return data to analyze

        Returns:
            List of recommended forms with priorities and reasons
        """
        recommendations = []

        # Create analysis context
        context = self._create_analysis_context(tax_data)

        # Always recommend Form 1040 (main return)
        recommendations.append(FormRecommendation(
            form_name="Form 1040",
            form_type=FormType.INDIVIDUAL_RETURN,
            priority=RecommendationPriority.CRITICAL,
            reason="Main individual income tax return - required for all taxpayers",
            required_data=["personal_info", "filing_status"],
            estimated_time=30,
            help_resources=["IRS Form 1040 Instructions", "IRS Publication 17"]
        ))

        # Analyze income sources
        income_recs = self._analyze_income_sources(tax_data, context)
        recommendations.extend(income_recs)

        # Analyze deductions
        deduction_recs = self._analyze_deductions(tax_data, context)
        recommendations.extend(deduction_recs)

        # Analyze credits
        credit_recs = self._analyze_credits(tax_data, context)
        recommendations.extend(credit_recs)

        # Analyze business activities
        business_recs = self._analyze_business_activities(tax_data, context)
        recommendations.extend(business_recs)

        # Analyze investments
        investment_recs = self._analyze_investments(tax_data, context)
        recommendations.extend(investment_recs)

        # Analyze foreign activities
        foreign_recs = self._analyze_foreign_activities(tax_data, context)
        recommendations.extend(foreign_recs)

        # Analyze special situations
        special_recs = self._analyze_special_situations(tax_data, context)
        recommendations.extend(special_recs)

        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x.priority.value, reverse=True)

        return recommendations

    def _create_analysis_context(self, tax_data: 'TaxData') -> RecommendationContext:
        """
        Create context information for analysis.
        
        Args:
            tax_data: Tax data to analyze
            
        Returns:
            RecommendationContext with calculated totals
            
        Raises:
            InvalidInputException: If tax_data is None or missing required attributes
            DataValidationException: If calculated values are invalid
        """
        error_logger = get_error_logger()
        
        try:
            if tax_data is None:
                raise InvalidInputException(
                    field_name="tax_data",
                    details={"reason": "Tax data cannot be None"}
                )
            
            # Validate required attributes
            required_attrs = ['tax_year', 'filing_status', 'dependents', 'income', 'deductions', 'credits']
            missing_attrs = [attr for attr in required_attrs if not hasattr(tax_data, attr)]
            if missing_attrs:
                raise InvalidInputException(
                    field_name="tax_data",
                    details={"missing_attributes": missing_attrs}
                )
            
            # Calculate totals
            total_income = self._calculate_total_income(tax_data)
            total_deductions = self._calculate_total_deductions(tax_data)
            total_credits = self._calculate_total_credits(tax_data)
            
            # Validate calculated values
            if total_income < 0:
                raise DataValidationException(
                    message="Total income cannot be negative",
                    details={"total_income": total_income}
                )
            
            return RecommendationContext(
                tax_year=tax_data.tax_year,
                filing_status=tax_data.filing_status,
                has_dependents=len(tax_data.dependents) > 0,
                has_spouse=tax_data.filing_status in ['MFJ', 'MFS'],
                total_income=total_income,
                total_deductions=total_deductions,
                total_credits=total_credits
            )
        except (InvalidInputException, DataValidationException) as e:
            error_logger.log_exception(
                e,
                context="form_recommendation_service._create_analysis_context",
                extra_details={"tax_year": getattr(tax_data, 'tax_year', None)}
            )
            raise
        except Exception as e:
            error_logger.log_exception(
                e,
                context="form_recommendation_service._create_analysis_context",
                extra_details={"tax_year": getattr(tax_data, 'tax_year', None)}
            )
            raise ServiceExecutionException(
                service_name="FormRecommendationService",
                operation="create_analysis_context",
                details={"error": str(e)}
            ) from e

    def _calculate_total_income(self, tax_data: 'TaxData') -> float:
        """Calculate total income from all sources"""
        total = 0.0

        # W-2 income
        for w2 in tax_data.income.w2_forms:
            total += w2.wages_tips_other_compensation

        # Interest income
        for interest in tax_data.income.interest_income:
            total += interest.amount

        # Dividend income
        for dividend in tax_data.income.dividend_income:
            total += dividend.amount

        # Business income
        for business in tax_data.income.business_income:
            total += business.gross_income

        # Capital gains
        for gain in tax_data.income.capital_gains_losses:
            total += gain.proceeds - gain.cost_basis

        return total

    def _calculate_total_deductions(self, tax_data: 'TaxData') -> float:
        """Calculate total deductions"""
        total = 0.0

        deductions = tax_data.deductions
        total += deductions.medical_expenses
        total += deductions.state_local_taxes
        total += deductions.mortgage_interest
        total += deductions.charitable_contributions
        total += deductions.casualty_losses

        return total

    def _calculate_total_credits(self, tax_data: 'TaxData') -> float:
        """Calculate total credits"""
        total = 0.0

        credits = tax_data.credits
        total += credits.child_tax_credit
        total += credits.earned_income_credit
        total += credits.education_credits
        total += credits.energy_credits

        return total

    def _analyze_income_sources(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze income sources and recommend forms"""
        recommendations = []

        # W-2 forms
        if tax_data.income.w2_forms:
            recommendations.append(FormRecommendation(
                form_name="W-2 Wage Income",
                form_type=FormType.INFORMATION_RETURN,
                priority=RecommendationPriority.HIGH,
                reason=f"You have {len(tax_data.income.w2_forms)} W-2 form(s) to report",
                required_data=["w2_forms"],
                estimated_time=15,
                help_resources=["W-2 Instructions", "Where to find your W-2"]
            ))

        # Interest income (Schedule B)
        if tax_data.income.interest_income:
            total_interest = sum(i.amount for i in tax_data.income.interest_income)
            if total_interest > 1500:  # Threshold for Schedule B
                recommendations.append(FormRecommendation(
                    form_name="Schedule B",
                    form_type=FormType.SCHEDULE,
                    priority=RecommendationPriority.MEDIUM,
                    reason=f"Interest income of ${total_interest:,.0f} exceeds $1,500 threshold",
                    required_data=["interest_income"],
                    estimated_time=10,
                    help_resources=["Schedule B Instructions"]
                ))

        # Dividend income (Schedule B)
        if tax_data.income.dividend_income:
            total_dividends = sum(d.amount for d in tax_data.income.dividend_income)
            if total_dividends > 1500 or len(tax_data.income.dividend_income) > 1:
                recommendations.append(FormRecommendation(
                    form_name="Schedule B",
                    form_type=FormType.SCHEDULE,
                    priority=RecommendationPriority.MEDIUM,
                    reason=f"Dividend income requires Schedule B reporting",
                    required_data=["dividend_income"],
                    estimated_time=10,
                    help_resources=["Schedule B Instructions"]
                ))

        # Capital gains (Schedule D)
        if tax_data.income.capital_gains_losses:
            recommendations.append(FormRecommendation(
                form_name="Schedule D",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.HIGH,
                reason="You have capital gains or losses to report",
                required_data=["capital_gains_losses"],
                estimated_time=30,
                help_resources=["Schedule D Instructions", "IRS Publication 550"]
            ))

        # Self-employment income (Schedule C)
        if tax_data.income.business_income:
            recommendations.append(FormRecommendation(
                form_name="Schedule C",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.HIGH,
                reason="You have self-employment income to report",
                required_data=["business_income", "business_expenses"],
                estimated_time=45,
                help_resources=["Schedule C Instructions", "IRS Publication 334"]
            ))

        return recommendations

    def _analyze_deductions(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze deductions and recommend Schedule A"""
        recommendations = []

        deductions = tax_data.deductions
        deduction_types = []

        if deductions.medical_expenses > 0:
            deduction_types.append("medical expenses")
        if deductions.state_local_taxes > 0:
            deduction_types.append("state/local taxes")
        if deductions.mortgage_interest > 0:
            deduction_types.append("mortgage interest")
        if deductions.charitable_contributions > 0:
            deduction_types.append("charitable contributions")
        if deductions.casualty_losses > 0:
            deduction_types.append("casualty losses")

        if deduction_types:
            total_deductions = sum([
                deductions.medical_expenses,
                deductions.state_local_taxes,
                deductions.mortgage_interest,
                deductions.charitable_contributions,
                deductions.casualty_losses
            ])

            # Calculate standard deduction for comparison
            standard_deduction = self._get_standard_deduction(context.filing_status, context.tax_year)

            if total_deductions > standard_deduction:
                recommendations.append(FormRecommendation(
                    form_name="Schedule A",
                    form_type=FormType.SCHEDULE,
                    priority=RecommendationPriority.HIGH,
                    reason=f"Itemized deductions (${total_deductions:,.0f}) exceed standard deduction (${standard_deduction:,.0f})",
                    required_data=["itemized_deductions"],
                    estimated_time=25,
                    help_resources=["Schedule A Instructions"]
                ))

        return recommendations

    def _analyze_credits(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze credits and recommend forms"""
        recommendations = []

        credits = tax_data.credits

        # Child Tax Credit
        if credits.child_tax_credit > 0 or context.has_dependents:
            recommendations.append(FormRecommendation(
                form_name="Child Tax Credit",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.HIGH,
                reason="You may qualify for Child Tax Credit based on dependents",
                required_data=["dependents", "child_tax_credit"],
                estimated_time=10,
                help_resources=["Child Tax Credit Information"]
            ))

        # Earned Income Credit
        if context.total_income < 50000:  # Rough threshold
            recommendations.append(FormRecommendation(
                form_name="Earned Income Credit",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.MEDIUM,
                reason="You may qualify for Earned Income Credit based on income level",
                required_data=["earned_income_credit"],
                estimated_time=15,
                help_resources=["Earned Income Credit Information"]
            ))

        # Education credits
        if credits.education_credits > 0:
            recommendations.append(FormRecommendation(
                form_name="Education Credits",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.MEDIUM,
                reason="You have education expenses that may qualify for credits",
                required_data=["education_expenses"],
                estimated_time=15,
                help_resources=["Education Credit Information"]
            ))

        return recommendations

    def _analyze_business_activities(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze business activities"""
        recommendations = []

        # Schedule C (already handled in income analysis)

        # Schedule E (rental income)
        if hasattr(tax_data.income, 'rental_income') and tax_data.income.rental_income:
            recommendations.append(FormRecommendation(
                form_name="Schedule E",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.HIGH,
                reason="You have rental income to report",
                required_data=["rental_income"],
                estimated_time=30,
                help_resources=["Schedule E Instructions"]
            ))

        # Form 1065 (partnership)
        if hasattr(tax_data, 'partnership_info') and tax_data.partnership_info:
            recommendations.append(FormRecommendation(
                form_name="Form 1065",
                form_type=FormType.INDIVIDUAL_RETURN,
                priority=RecommendationPriority.HIGH,
                reason="You have partnership income to report",
                required_data=["partnership_info"],
                estimated_time=60,
                help_resources=["Form 1065 Instructions"]
            ))

        # Form 1120-S (S-Corp)
        if hasattr(tax_data, 's_corp_info') and tax_data.s_corp_info:
            recommendations.append(FormRecommendation(
                form_name="Form 1120-S",
                form_type=FormType.INDIVIDUAL_RETURN,
                priority=RecommendationPriority.HIGH,
                reason="You have S-Corporation income to report",
                required_data=["s_corp_info"],
                estimated_time=60,
                help_resources=["Form 1120-S Instructions"]
            ))

        return recommendations

    def _analyze_investments(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze investment activities"""
        recommendations = []

        # Form 8949 (sales of capital assets)
        if tax_data.income.capital_gains_losses:
            recommendations.append(FormRecommendation(
                form_name="Form 8949",
                form_type=FormType.INFORMATION_RETURN,
                priority=RecommendationPriority.HIGH,
                reason="You have capital asset sales to report",
                required_data=["capital_gains_losses"],
                estimated_time=45,
                help_resources=["Form 8949 Instructions", "IRS Publication 550"]
            ))

        return recommendations

    def _analyze_foreign_activities(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze foreign income and activities"""
        recommendations = []

        # FBAR (foreign bank accounts)
        if hasattr(tax_data, 'foreign_accounts') and tax_data.foreign_accounts:
            max_balance = max((acc.max_balance for acc in tax_data.foreign_accounts), default=0)
            if max_balance >= 10000:
                recommendations.append(FormRecommendation(
                    form_name="FBAR (FinCEN 114)",
                    form_type=FormType.INFORMATION_RETURN,
                    priority=RecommendationPriority.CRITICAL,
                    reason=f"Foreign account balance exceeded $10,000 (max: ${max_balance:,.0f})",
                    required_data=["foreign_accounts"],
                    estimated_time=30,
                    help_resources=["FBAR Instructions", "FinCEN Form 114"]
                ))

        # Form 1116 (foreign tax credit)
        if hasattr(tax_data.income, 'foreign_income') and tax_data.income.foreign_income:
            recommendations.append(FormRecommendation(
                form_name="Form 1116",
                form_type=FormType.SCHEDULE,
                priority=RecommendationPriority.MEDIUM,
                reason="You have foreign income that may qualify for foreign tax credit",
                required_data=["foreign_income"],
                estimated_time=25,
                help_resources=["Form 1116 Instructions"]
            ))

        return recommendations

    def _analyze_special_situations(self, tax_data: 'TaxData', context: RecommendationContext) -> List[FormRecommendation]:
        """Analyze special tax situations"""
        recommendations = []

        # Form 1041 (estates and trusts)
        if hasattr(tax_data, 'estate_trust_info') and tax_data.estate_trust_info:
            recommendations.append(FormRecommendation(
                form_name="Form 1041",
                form_type=FormType.INDIVIDUAL_RETURN,
                priority=RecommendationPriority.HIGH,
                reason="You have estate or trust income to report",
                required_data=["estate_trust_info"],
                estimated_time=60,
                help_resources=["Form 1041 Instructions"]
            ))

        # Estimated tax payments
        if hasattr(tax_data, 'estimated_tax_payments') and tax_data.estimated_tax_payments:
            recommendations.append(FormRecommendation(
                form_name="Form 1040-ES",
                form_type=FormType.ESTIMATE,
                priority=RecommendationPriority.MEDIUM,
                reason="You made estimated tax payments that need to be reported",
                required_data=["estimated_tax_payments"],
                estimated_time=10,
                help_resources=["Form 1040-ES Instructions"]
            ))

        return recommendations

    def _get_standard_deduction(self, filing_status: str, tax_year: int) -> int:
        """Get standard deduction amount for filing status and year"""
        # 2024 standard deductions (approximate)
        standard_deductions = {
            'single': 14600,
            'mfj': 29200,
            'mfs': 14600,
            'hoh': 21900,
            'qw': 14600
        }

        # Adjust for inflation (rough estimate)
        if tax_year > 2024:
            adjustment = 1.0 + (tax_year - 2024) * 0.02  # 2% annual increase
        else:
            adjustment = 1.0

        base_amount = standard_deductions.get(filing_status.lower(), 14600)
        return int(base_amount * adjustment)

    def get_recommendation_summary(self, recommendations: List[FormRecommendation]) -> Dict[str, Any]:
        """
        Get a summary of recommendations.

        Args:
            recommendations: List of form recommendations

        Returns:
            Summary statistics
            
        Raises:
            InvalidInputException: If recommendations is None or not a list
            DataValidationException: If recommendation data is invalid
        """
        error_logger = get_error_logger()
        
        try:
            if recommendations is None:
                raise InvalidInputException(
                    field_name="recommendations",
                    details={"reason": "Recommendations cannot be None"}
                )
            
            if not isinstance(recommendations, list):
                raise InvalidInputException(
                    field_name="recommendations",
                    details={"reason": "Recommendations must be a list"}
                )
            
            total_time = sum(rec.estimated_time for rec in recommendations)
            critical_count = sum(1 for rec in recommendations if rec.priority == RecommendationPriority.CRITICAL)
            high_count = sum(1 for rec in recommendations if rec.priority == RecommendationPriority.HIGH)

            return {
                "total_recommendations": len(recommendations),
                "critical_forms": critical_count,
                "high_priority_forms": high_count,
                "estimated_total_time": total_time,
                "forms_by_type": {
                    form_type.value: sum(1 for rec in recommendations if rec.form_type == form_type)
                    for form_type in FormType
                }
            }
        except InvalidInputException as e:
            error_logger.log_exception(
                e,
                context="form_recommendation_service.get_recommendation_summary",
                extra_details={"recommendation_count": len(recommendations) if isinstance(recommendations, list) else 0}
            )
            raise
        except Exception as e:
            error_logger.log_exception(
                e,
                context="form_recommendation_service.get_recommendation_summary",
                extra_details={"recommendation_count": len(recommendations) if isinstance(recommendations, list) else 0}
            )
            raise ServiceExecutionException(
                service_name="FormRecommendationService",
                operation="get_recommendation_summary",
                details={"error": str(e)}
            ) from e