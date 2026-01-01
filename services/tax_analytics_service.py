"""
Tax Analytics Service - Advanced tax analysis and reporting

Provides comprehensive tax analytics including effective tax rates,
tax burden analysis, deduction utilization, and multi-year trends.
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from dataclasses import dataclass, asdict
from pathlib import Path
from decimal import Decimal

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger
from services.tax_calculation_service import TaxCalculationService
from utils.error_tracker import get_error_tracker


@dataclass
class TaxAnalyticsResult:
    """Result of tax analytics calculations"""
    tax_year: int
    effective_tax_rate: float
    marginal_tax_rate: float
    tax_burden_percentage: float
    deduction_utilization: float
    credit_utilization: float
    income_distribution: Dict[str, float]
    tax_liability_breakdown: Dict[str, float]
    calculated_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['calculated_at'] = self.calculated_at.isoformat()
        # Convert any Decimal objects to float for JSON serialization
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, Decimal):
                        value[sub_key] = float(sub_value)
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxAnalyticsResult':
        """Create from dictionary"""
        data['calculated_at'] = datetime.fromisoformat(data['calculated_at'])
        return cls(**data)


@dataclass
class TaxTrendAnalysis:
    """Multi-year tax trend analysis"""
    years_analyzed: List[int]
    effective_rate_trend: List[float]
    tax_burden_trend: List[float]
    income_growth_rate: float
    tax_liability_growth_rate: float
    deduction_trend: List[float]
    credit_trend: List[float]
    analysis_period: str
    generated_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxTrendAnalysis':
        """Create from dictionary"""
        data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)


@dataclass
class TaxOptimizationInsight:
    """Tax optimization insight with actionable recommendations"""
    category: str  # "deductions", "credits", "retirement", "income", "planning"
    title: str
    description: str
    potential_savings: float
    priority: str  # "high", "medium", "low"
    implementation_steps: List[str]
    prerequisites: List[str]
    risk_level: str  # "low", "medium", "high"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxOptimizationInsight':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class TaxProjectionScenario:
    """Tax projection scenario with assumptions and results"""
    scenario_name: str
    projection_year: int
    base_year: int
    assumptions: Dict[str, Any]
    projected_income: float
    projected_tax_liability: float
    projected_effective_rate: float
    confidence_level: str  # "High", "Medium", "Low"
    risk_factors: List[str]
    calculated_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['calculated_at'] = self.calculated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxProjectionScenario':
        """Create from dictionary"""
        data['calculated_at'] = datetime.fromisoformat(data['calculated_at'])
        return cls(**data)


@dataclass
class TaxProjectionResult:
    """Complete tax projection analysis"""
    base_tax_year: int
    scenarios: List[TaxProjectionScenario]
    summary_insights: List[str]
    recommended_actions: List[str]
    calculated_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['scenarios'] = [s.to_dict() for s in self.scenarios]
        data['calculated_at'] = self.calculated_at.isoformat()
        return data
    """Tax optimization recommendation"""
    category: str  # 'income', 'deductions', 'credits', 'retirement', 'investments'
    title: str
    description: str
    potential_savings: float
    priority: str  # 'high', 'medium', 'low'
    implementation_steps: List[str]
    prerequisites: List[str]
    risk_level: str  # 'low', 'medium', 'high'

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxOptimizationInsight':
        """Create from dictionary"""
        return cls(**data)


class TaxAnalyticsService:
    """
    Service for advanced tax analytics and reporting.

    Provides comprehensive analysis of tax situations including:
    - Effective tax rate calculations
    - Tax burden analysis
    - Deduction and credit utilization
    - Multi-year trend analysis
    - Tax optimization insights
    """

    def __init__(self, config: AppConfig, tax_calculation_service: TaxCalculationService):
        """
        Initialize tax analytics service.

        Args:
            config: Application configuration
            tax_calculation_service: Service for tax calculations
        """
        self.config = config
        self.tax_calculation = tax_calculation_service
        self.error_tracker = get_error_tracker()

        # Analytics storage
        self.analytics_dir = Path(config.safe_dir) / "analytics"
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

    def calculate_effective_tax_rate(self, tax_data: TaxData) -> float:
        """
        Calculate the effective tax rate for a tax return.

        Effective tax rate = Total tax liability / Total income

        Args:
            tax_data: Tax data to analyze

        Returns:
            Effective tax rate as a percentage (0-100)
        """
        try:
            # Get current tax year
            tax_year = tax_data.get_current_year()
            
            # Get total income from the year's data
            income_data = tax_data.get_section('income', tax_year)
            total_income = sum(Decimal(str(v)) for v in income_data.values() if v)

            # Get tax calculation result
            tax_result = self.tax_calculation.calculate_tax(tax_data)

            if total_income <= 0:
                return 0.0

            # Calculate effective rate
            effective_rate = (tax_result.total_tax_owed / total_income) * 100

            # Ensure reasonable bounds
            return max(0.0, min(100.0, float(effective_rate)))

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "calculate_effective_tax_rate", "tax_year": tax_year}
            )
            return 0.0

    def calculate_marginal_tax_rate(self, tax_data: TaxData) -> float:
        """
        Calculate the marginal tax rate (tax rate on the last dollar earned).

        Args:
            tax_data: Tax data to analyze

        Returns:
            Marginal tax rate as a percentage
        """
        try:
            tax_year = tax_data.get_current_year()
            return self.tax_calculation.get_marginal_tax_rate(tax_data)
        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "calculate_marginal_tax_rate", "tax_year": tax_year}
            )
            return 0.0

    def analyze_tax_burden(self, tax_data: TaxData) -> Dict[str, Any]:
        """
        Analyze the overall tax burden and its components.

        Args:
            tax_data: Tax data to analyze

        Returns:
            Dictionary with tax burden analysis
        """
        try:
            tax_year = tax_data.get_current_year()
            income_data = tax_data.get_section('income', tax_year)
            total_income = sum(Decimal(str(v)) for v in income_data.values() if v)
            
            tax_result = self.tax_calculation.calculate_tax(tax_data)

            if total_income <= 0:
                return {
                    'tax_burden_percentage': 0.0,
                    'breakdown': {},
                    'insights': ['No taxable income']
                }

            # Calculate burden percentage
            burden_percentage = (tax_result.total_tax_owed / total_income) * 100

            # Breakdown by tax type
            breakdown = tax_result.tax_liability_breakdown

            # Generate insights
            filing_status = tax_data.get('filing_status', tax_year)
            insights = self._generate_tax_burden_insights(
                burden_percentage, breakdown, filing_status, total_income
            )

            return {
                'tax_burden_percentage': burden_percentage,
                'breakdown': breakdown,
                'insights': insights
            }

        except Exception as e:
            tax_year = tax_data.get_current_year()
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_tax_burden", "tax_year": tax_year}
            )
            return {
                'tax_burden_percentage': 0.0,
                'breakdown': {},
                'insights': ['Analysis failed due to error']
            }

    def analyze_income_distribution(self, tax_data: TaxData) -> Dict[str, float]:
        """
        Analyze the distribution of income sources.

        Args:
            tax_data: Tax data to analyze

        Returns:
            Dictionary with income source percentages
        """
        try:
            tax_year = tax_data.get_current_year()
            # Get income breakdown
            income_data = tax_data.get_section('income', tax_year)
            total_income = sum(Decimal(str(v)) for v in income_data.values() if v)

            if total_income <= 0:
                return {}

            # Calculate percentages
            distribution = {}
            for source, amount in income_data.items():
                if amount and amount > 0:
                    percentage = (Decimal(str(amount)) / total_income) * 100
                    distribution[source] = float(percentage)

            return distribution

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_income_distribution", "tax_year": tax_year}
            )
            return {}

    def analyze_deduction_utilization(self, tax_data: TaxData) -> Dict[str, Any]:
        """
        Analyze how effectively deductions are being utilized.

        Args:
            tax_data: Tax data to analyze

        Returns:
            Dictionary with deduction utilization analysis
        """
        try:
            tax_year = tax_data.get_current_year()
            income_data = tax_data.get_section('income', tax_year)
            deduction_data = tax_data.get_section('deductions', tax_year)
            
            total_income = sum(Decimal(str(v)) for v in income_data.values() if v)
            total_deductions = sum(Decimal(str(v)) for v in deduction_data.values() if v)
            
            filing_status = tax_data.get('filing_status', tax_year)

            # Get standard deduction for comparison
            standard_deduction = self.tax_calculation.get_standard_deduction(filing_status)

            utilization_rate = 0.0
            if total_deductions > 0:
                utilization_rate = min(100.0, (total_deductions / max(total_income, standard_deduction)) * 100)

            insights = []
            if total_deductions < standard_deduction:
                insights.append("Consider itemizing deductions if they exceed the standard deduction")
            elif total_deductions > standard_deduction * Decimal('1.5'):
                insights.append("Strong deduction utilization - review for accuracy")

            return {
                'utilization_rate': utilization_rate,
                'total_deductions': float(total_deductions),
                'standard_deduction': float(standard_deduction),
                'deduction_sources': deduction_data,
                'insights': insights
            }

        except Exception as e:
            tax_year = tax_data.get_current_year()
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_deduction_utilization", "tax_year": tax_year}
            )
            return {
                'utilization_rate': 0.0,
                'total_deductions': 0.0,
                'standard_deduction': 0.0,
                'deduction_sources': {},
                'insights': ['Analysis failed due to error']
            }

    def analyze_credit_utilization(self, tax_data: TaxData) -> Dict[str, Any]:
        """
        Analyze tax credit utilization and potential savings.

        Args:
            tax_data: Tax data to analyze

        Returns:
            Dictionary with credit utilization analysis
        """
        try:
            tax_year = tax_data.get_current_year()
            tax_result = self.tax_calculation.calculate_tax(tax_data)
            
            # Get credits from tax data
            credit_data = tax_data.get_section('credits', tax_year)
            total_credits = sum(Decimal(str(v)) for v in credit_data.values() if v)

            # Estimate potential tax liability without credits
            tax_without_credits = sum(tax_result.tax_liability_breakdown.values())

            utilization_rate = 0.0
            if tax_without_credits > 0:
                utilization_rate = min(100.0, (total_credits / tax_without_credits) * 100)

            insights = []
            if total_credits > tax_without_credits:
                insights.append("Credits exceed tax liability - may result in refund")
            elif total_credits > tax_without_credits * Decimal('0.5'):
                insights.append("Significant credit utilization reducing tax burden")
            elif total_credits == 0:
                insights.append("No tax credits claimed - review eligibility for available credits")

            return {
                'utilization_rate': float(utilization_rate),
                'total_credits': float(total_credits),
                'credit_breakdown': credit_data,
                'insights': insights
            }

        except Exception as e:
            tax_year = tax_data.get_current_year()
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_credit_utilization", "tax_year": tax_year}
            )
            return {
                'utilization_rate': 0.0,
                'total_credits': 0.0,
                'credit_breakdown': {},
                'insights': ['Analysis failed due to error']
            }

    def generate_comprehensive_analysis(self, tax_data: TaxData) -> TaxAnalyticsResult:
        """
        Generate comprehensive tax analytics for a tax return.

        Args:
            tax_data: Tax data to analyze

        Returns:
            Comprehensive analytics result
        """
        try:
            tax_year = tax_data.get_current_year()
            effective_rate = self.calculate_effective_tax_rate(tax_data)
            marginal_rate = self.calculate_marginal_tax_rate(tax_data)

            burden_analysis = self.analyze_tax_burden(tax_data)
            income_distribution = self.analyze_income_distribution(tax_data)
            deduction_analysis = self.analyze_deduction_utilization(tax_data)
            credit_analysis = self.analyze_credit_utilization(tax_data)

            return TaxAnalyticsResult(
                tax_year=tax_year,
                effective_tax_rate=effective_rate,
                marginal_tax_rate=marginal_rate,
                tax_burden_percentage=burden_analysis['tax_burden_percentage'],
                deduction_utilization=deduction_analysis['utilization_rate'],
                credit_utilization=credit_analysis['utilization_rate'],
                income_distribution=income_distribution,
                tax_liability_breakdown=burden_analysis['breakdown'],
                calculated_at=datetime.now()
            )

        except Exception as e:
            tax_year = tax_data.get_current_year()
            self.error_tracker.track_error(
                error=e,
                context={"operation": "generate_comprehensive_analysis", "tax_year": tax_year}
            )
            # Return minimal result on error
            return TaxAnalyticsResult(
                tax_year=tax_year,
                effective_tax_rate=0.0,
                marginal_tax_rate=0.0,
                tax_burden_percentage=0.0,
                deduction_utilization=0.0,
                credit_utilization=0.0,
                income_distribution={},
                tax_liability_breakdown={},
                calculated_at=datetime.now()
            )

    def analyze_tax_trends(self, tax_returns: List[TaxData]) -> TaxTrendAnalysis:
        """
        Analyze tax trends across multiple years.

        Args:
            tax_returns: List of tax data objects for different years

        Returns:
            Multi-year trend analysis
        """
        try:
            if not tax_returns:
                return TaxTrendAnalysis(
                    years_analyzed=[],
                    effective_rate_trend=[],
                    tax_burden_trend=[],
                    income_growth_rate=0.0,
                    tax_liability_growth_rate=0.0,
                    deduction_trend=[],
                    credit_trend=[],
                    analysis_period="N/A",
                    generated_at=datetime.now()
                )

            # Sort by year - need to get current year for each
            sorted_returns = sorted(tax_returns, key=lambda x: x.get_current_year())
            years = [r.get_current_year() for r in sorted_returns]

            # Calculate metrics for each year
            effective_rates = []
            tax_burdens = []
            incomes = []
            tax_liabilities = []
            deductions = []
            credits = []

            for tax_data in sorted_returns:
                analysis = self.generate_comprehensive_analysis(tax_data)

                effective_rates.append(analysis.effective_tax_rate)
                tax_burdens.append(analysis.tax_burden_percentage)

                # Get total income
                tax_year = tax_data.get_current_year()
                income_data = tax_data.get_section('income', tax_year)
                total_income = sum(Decimal(str(v)) for v in income_data.values() if v)
                incomes.append(float(total_income))

                tax_result = self.tax_calculation.calculate_tax(tax_data)
                tax_liabilities.append(float(tax_result.total_tax_owed))

                deduction_analysis = self.analyze_deduction_utilization(tax_data)
                deductions.append(deduction_analysis['total_deductions'])

                credit_analysis = self.analyze_credit_utilization(tax_data)
                credits.append(credit_analysis['total_credits'])

            # Calculate growth rates
            income_growth = self._calculate_average_growth_rate(incomes) if len(incomes) > 1 else 0.0
            tax_growth = self._calculate_average_growth_rate(tax_liabilities) if len(tax_liabilities) > 1 else 0.0

            return TaxTrendAnalysis(
                years_analyzed=years,
                effective_rate_trend=effective_rates,
                tax_burden_trend=tax_burdens,
                income_growth_rate=income_growth,
                tax_liability_growth_rate=tax_growth,
                deduction_trend=deductions,
                credit_trend=credits,
                analysis_period=f"{min(years)}-{max(years)}" if years else "N/A",
                generated_at=datetime.now()
            )

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_tax_trends", "num_returns": len(tax_returns) if tax_returns else 0}
            )
            # Return minimal result on error
            return TaxTrendAnalysis(
                years_analyzed=[],
                effective_rate_trend=[],
                tax_burden_trend=[],
                income_growth_rate=0.0,
                tax_liability_growth_rate=0.0,
                deduction_trend=[],
                credit_trend=[],
                analysis_period="N/A",
                generated_at=datetime.now()
            )

    def _calculate_average_growth_rate(self, values: List[float]) -> float:
        """Calculate average annual growth rate"""
        if len(values) < 2:
            return 0.0

        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                rate = ((values[i] - values[i-1]) / values[i-1]) * 100
                growth_rates.append(rate)

        return sum(growth_rates) / len(growth_rates) if growth_rates else 0.0

    def _generate_tax_burden_insights(self, burden_pct: float, breakdown: Dict[str, float],
                                    filing_status: str, total_income: float) -> List[str]:
        """Generate insights about tax burden"""
        insights = []

        # Burden level assessment
        if burden_pct < 5:
            insights.append("Very low tax burden - review income reporting accuracy")
        elif burden_pct < 15:
            insights.append("Moderate tax burden - typical for most taxpayers")
        elif burden_pct < 25:
            insights.append("Higher tax burden - consider tax planning strategies")
        else:
            insights.append("Very high tax burden - consult tax professional for optimization")

        # Filing status specific insights
        if filing_status == "Single" and total_income > 200000:
            insights.append("High income single filer - consider marriage or retirement planning")
        elif filing_status in ["MFJ", "MFS"] and burden_pct > 20:
            insights.append("Married filing status - review joint vs separate filing options")

        # Tax type breakdown insights
        if breakdown.get('self_employment_tax', 0) > breakdown.get('income_tax', 0):
            insights.append("Self-employment tax is significant - consider retirement contributions")

        return insights

    def project_future_tax_liability(self, tax_data: TaxData, 
                                   projection_years: int = 5,
                                   income_growth_rate: float = 0.03,
                                   inflation_rate: float = 0.025) -> TaxProjectionResult:
        """
        Project future tax liability based on current tax situation.

        This method creates multiple scenarios for future tax planning:
        1. Base case: Current income with moderate growth
        2. Conservative: Lower income growth
        3. Aggressive: Higher income growth
        4. Retirement: Reduced income scenario

        Args:
            tax_data: Current tax data to base projections on
            projection_years: Number of years to project (default: 5)
            income_growth_rate: Expected annual income growth rate (default: 3%)
            inflation_rate: Expected annual inflation rate (default: 2.5%)

        Returns:
            TaxProjectionResult with multiple scenarios and insights
        """
        try:
            base_year = tax_data.get_current_year()
            scenarios = []
            summary_insights = []
            recommended_actions = []

            # Get current income data
            current_income_data = tax_data.get_section('income', base_year)
            current_total_income = sum(Decimal(str(v)) for v in current_income_data.values() if v)

            if current_total_income <= 0:
                return TaxProjectionResult(
                    base_tax_year=base_year,
                    scenarios=[],
                    summary_insights=["Cannot project taxes without current income data"],
                    recommended_actions=["Complete income section first"],
                    calculated_at=datetime.now()
                )

            # Scenario 1: Base Case (Moderate Growth)
            base_scenario = self._create_projection_scenario(
                tax_data, base_year, projection_years,
                income_growth_rate, inflation_rate,
                "Base Case", "Medium"
            )
            scenarios.append(base_scenario)

            # Scenario 2: Conservative (Lower Growth)
            conservative_scenario = self._create_projection_scenario(
                tax_data, base_year, projection_years,
                max(income_growth_rate * 0.5, 0.01), inflation_rate,
                "Conservative", "High"
            )
            scenarios.append(conservative_scenario)

            # Scenario 3: Aggressive (Higher Growth)
            aggressive_scenario = self._create_projection_scenario(
                tax_data, base_year, projection_years,
                income_growth_rate * 1.5, inflation_rate,
                "Aggressive", "Low"
            )
            scenarios.append(aggressive_scenario)

            # Scenario 4: Retirement (Reduced Income)
            retirement_scenario = self._create_projection_scenario(
                tax_data, base_year, projection_years,
                -0.02, inflation_rate,  # 2% annual reduction
                "Retirement", "Medium"
            )
            scenarios.append(retirement_scenario)

            # Generate summary insights
            summary_insights = self._generate_projection_insights(scenarios, base_year)

            # Generate recommended actions
            recommended_actions = self._generate_projection_actions(scenarios, tax_data)

            return TaxProjectionResult(
                base_tax_year=base_year,
                scenarios=scenarios,
                summary_insights=summary_insights,
                recommended_actions=recommended_actions,
                calculated_at=datetime.now()
            )

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "project_future_tax_liability", "base_year": tax_data.get_current_year()}
            )
            # Return minimal result on error
            return TaxProjectionResult(
                base_tax_year=tax_data.get_current_year(),
                scenarios=[],
                summary_insights=["Projection failed due to error"],
                recommended_actions=["Contact support if issue persists"],
                calculated_at=datetime.now()
            )

    def _create_projection_scenario(self, tax_data: TaxData, base_year: int, 
                                  projection_years: int, income_growth: float,
                                  inflation: float, scenario_name: str, 
                                  confidence: str) -> TaxProjectionScenario:
        """Create a single projection scenario"""
        # Calculate projected income for the target year
        projection_year = base_year + projection_years
        
        current_income_data = tax_data.get_section('income', base_year)
        current_total_income = sum(Decimal(str(v)) for v in current_income_data.values() if v)
        
        # Project income with compound growth
        projected_income = float(current_total_income * (1 + income_growth) ** projection_years)
        
        # Adjust for inflation (tax brackets and deductions are inflation-adjusted)
        inflation_factor = (1 + inflation) ** projection_years
        
        # Create projected tax data (simplified - only income changes)
        projected_tax_data = tax_data.clone()
        projected_tax_data.set_current_year(projection_year)
        
        # Scale income sources proportionally
        if current_total_income > 0:
            income_ratio = projected_income / float(current_total_income)
            for income_type, amount in current_income_data.items():
                if amount:
                    projected_tax_data.set(f'income.{income_type}', 
                                         float(amount) * income_ratio, projection_year)
        
        # Calculate projected tax liability
        tax_result = self.tax_calculation.calculate_tax(projected_tax_data)
        projected_tax_liability = float(tax_result.total_tax_owed)
        
        # Calculate effective rate
        effective_rate = (projected_tax_liability / projected_income) * 100 if projected_income > 0 else 0
        
        # Determine risk factors
        risk_factors = []
        if income_growth > 0.05:
            risk_factors.append("High income growth assumption")
        if projection_years > 10:
            risk_factors.append("Long projection horizon increases uncertainty")
        if scenario_name == "Retirement" and projected_income < 40000:
            risk_factors.append("Projected retirement income below poverty threshold")
        
        return TaxProjectionScenario(
            scenario_name=scenario_name,
            projection_year=projection_year,
            base_year=base_year,
            assumptions={
                'income_growth_rate': income_growth,
                'inflation_rate': inflation,
                'projection_years': projection_years
            },
            projected_income=projected_income,
            projected_tax_liability=projected_tax_liability,
            projected_effective_rate=effective_rate,
            confidence_level=confidence,
            risk_factors=risk_factors,
            calculated_at=datetime.now()
        )

    def _generate_projection_insights(self, scenarios: List[TaxProjectionScenario], 
                                    base_year: int) -> List[str]:
        """Generate insights from projection scenarios"""
        insights = []
        
        if not scenarios:
            return ["No projection scenarios available"]
        
        # Compare scenarios
        base_case = next((s for s in scenarios if s.scenario_name == "Base Case"), None)
        conservative = next((s for s in scenarios if s.scenario_name == "Conservative"), None)
        aggressive = next((s for s in scenarios if s.scenario_name == "Aggressive"), None)
        retirement = next((s for s in scenarios if s.scenario_name == "Retirement"), None)
        
        if base_case and conservative and aggressive:
            # Tax liability range
            min_tax = min(s.projected_tax_liability for s in scenarios)
            max_tax = max(s.projected_tax_liability for s in scenarios)
            tax_range = max_tax - min_tax
            
            insights.append(f"Projected tax liability in {base_case.projection_year} ranges from ${min_tax:,.0f} to ${max_tax:,.0f}")
            
            if tax_range > base_case.projected_tax_liability * 0.5:
                insights.append("Wide range of possible tax outcomes - consider tax planning strategies")
            
            # Effective rate trends
            if aggressive.projected_effective_rate > base_case.projected_effective_rate * 1.2:
                insights.append("Aggressive growth scenario may push you into higher tax brackets")
        
        if retirement:
            if retirement.projected_tax_liability < 1000:
                insights.append("Retirement scenario shows very low tax liability - maximize retirement contributions")
            elif retirement.projected_tax_liability > 50000:
                insights.append("Retirement income may still result in significant tax liability")
        
        return insights

    def _generate_projection_actions(self, scenarios: List[TaxProjectionScenario], 
                                   tax_data: TaxData) -> List[str]:
        """Generate recommended actions based on projections"""
        actions = []
        
        if not scenarios:
            return ["Complete tax return to enable projections"]
        
        base_case = next((s for s in scenarios if s.scenario_name == "Base Case"), None)
        
        if base_case:
            # Tax planning actions based on projected liability
            if base_case.projected_effective_rate > 30:
                actions.append("Consider tax-advantaged retirement contributions to reduce future tax burden")
                actions.append("Review investment choices for tax efficiency")
            
            if base_case.projected_tax_liability > 50000:
                actions.append("Consult tax professional for advanced planning strategies")
            
            # Income growth planning
            if any(s.projected_income > base_case.projected_income * 1.5 for s in scenarios):
                actions.append("Consider tax implications of significant income growth")
        
        # General actions
        actions.extend([
            "Review and update retirement contribution limits annually",
            "Consider tax-loss harvesting opportunities",
            "Keep detailed records for all deductible expenses"
        ])
        
        return actions

    def save_analytics_result(self, result: TaxAnalyticsResult, filename: Optional[str] = None) -> Path:
        """
        Save analytics result to file.

        Args:
            result: Analytics result to save
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        try:
            if not filename:
                filename = f"tax_analytics_{result.tax_year}_{int(result.calculated_at.timestamp())}.json"

            filepath = self.analytics_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

            return filepath

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "save_analytics_result", "filename": filename}
            )
            raise

    def load_analytics_result(self, filepath: Path) -> TaxAnalyticsResult:
        """
        Load analytics result from file.

        Args:
            filepath: Path to analytics file

        Returns:
            Loaded analytics result
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return TaxAnalyticsResult.from_dict(data)

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "load_analytics_result", "filepath": str(filepath)}
            )
            raise

    def save_trend_analysis(self, analysis: TaxTrendAnalysis, filename: Optional[str] = None) -> Path:
        """
        Save trend analysis to file.

        Args:
            analysis: Trend analysis to save
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        try:
            if not filename:
                filename = f"tax_trends_{analysis.analysis_period.replace('-', '_')}_{int(analysis.generated_at.timestamp())}.json"

            filepath = self.analytics_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis.to_dict(), f, indent=2, ensure_ascii=False)

            return filepath

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "save_trend_analysis", "filename": filename}
            )
            raise

    def generate_tax_projections(self, tax_data: TaxData, years_ahead: int = 3) -> Dict[int, Dict[str, Any]]:
        """
        Generate tax projections for future years.

        Args:
            tax_data: Current tax data
            years_ahead: Number of years to project

        Returns:
            Dictionary with projected tax data by year
        """
        try:
            projections = {}
            tax_year = tax_data.get_current_year()
            income_data = tax_data.get_section('income', tax_year)
            deduction_data = tax_data.get_section('deductions', tax_year)
            credit_data = tax_data.get_section('credits', tax_year)
            
            base_income = sum(Decimal(str(v)) for v in income_data.values() if v)
            base_deductions = sum(Decimal(str(v)) for v in deduction_data.values() if v)
            base_credits = sum(Decimal(str(v)) for v in credit_data.values() if v)

            # Assume 3% annual income growth, 2% deduction growth
            for i in range(1, years_ahead + 1):
                year = tax_year + i
                projected_income = base_income * (Decimal('1.03') ** i)
                projected_deductions = base_deductions * (Decimal('1.02') ** i)
                projected_credits = base_credits * (Decimal('1.01') ** i)  # Credits grow slower

                # Estimate taxable income
                taxable_income = max(0, projected_income - projected_deductions)

                # Simple tax calculation (rough estimate)
                if taxable_income <= 11000:
                    tax_rate = 0.10
                elif taxable_income <= 44725:
                    tax_rate = 0.12
                elif taxable_income <= 95375:
                    tax_rate = 0.22
                else:
                    tax_rate = 0.24

                projected_tax = taxable_income * Decimal(str(tax_rate)) - projected_credits
                projected_tax = max(Decimal('0'), projected_tax)

                projections[year] = {
                    'projected_income': projected_income,
                    'projected_deductions': projected_deductions,
                    'projected_credits': projected_credits,
                    'projected_taxable_income': taxable_income,
                    'projected_tax': projected_tax,
                    'projected_effective_rate': (projected_tax / projected_income * 100) if projected_income > 0 else 0
                }

            return projections

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "generate_tax_projections", "years_ahead": years_ahead}
            )
            raise

    def generate_optimization_insights(self, analysis: TaxAnalyticsResult) -> List[TaxOptimizationInsight]:
        """
        Generate tax optimization insights based on analysis.

        Args:
            analysis: Tax analysis result

        Returns:
            List of optimization insights
        """
        try:
            insights = []

            # High priority insights
            if analysis.deduction_utilization < 70:
                insights.append(TaxOptimizationInsight(
                    category="deductions",
                    title="Increase Deduction Utilization",
                    description="You're not fully utilizing available deductions. Consider itemizing or contributing to retirement accounts.",
                    potential_savings=2000.00,  # Rough estimate
                    priority="high",
                    implementation_steps=[
                        "Review all possible deductions (medical, charitable, home office)",
                        "Consider bunching deductions if close to itemizing threshold",
                        "Consult tax professional for comprehensive review"
                    ],
                    prerequisites=["Gather all expense receipts"],
                    risk_level="low"
                ))

            if analysis.effective_tax_rate > 20:
                insights.append(TaxOptimizationInsight(
                    category="retirement",
                    title="Maximize Retirement Contributions",
                    description="High effective tax rate suggests opportunity to reduce taxable income through retirement contributions.",
                    potential_savings=3000.00,  # Rough estimate
                    priority="high",
                    implementation_steps=[
                        "Maximize 401(k) contributions (up to $23,000 in 2024)",
                        "Consider IRA contributions if eligible",
                        "Review employer matching programs"
                    ],
                    prerequisites=["Check retirement account contribution limits"],
                    risk_level="low"
                ))

            # Medium priority insights
            if analysis.credit_utilization < 50:
                insights.append(TaxOptimizationInsight(
                    category="credits",
                    title="Explore Additional Tax Credits",
                    description="You may be eligible for additional tax credits that could reduce your tax liability.",
                    potential_savings=1500.00,  # Rough estimate
                    priority="medium",
                    implementation_steps=[
                        "Check eligibility for Education Credits",
                        "Review energy efficiency credits",
                        "Consider child and dependent care credit if applicable"
                    ],
                    prerequisites=["Gather supporting documentation"],
                    risk_level="low"
                ))

            if analysis.tax_burden_percentage > 20:
                insights.append(TaxOptimizationInsight(
                    category="investments",
                    title="Tax-Loss Harvesting",
                    description="Consider tax-loss harvesting to offset capital gains and reduce overall tax burden.",
                    potential_savings=1000.00,  # Rough estimate
                    priority="medium",
                    implementation_steps=[
                        "Review investment portfolio for losses",
                        "Sell losing investments to offset gains",
                        "Be mindful of wash sale rules"
                    ],
                    prerequisites=["Consult investment advisor"],
                    risk_level="medium"
                ))

            # Low priority insights
            insights.append(TaxOptimizationInsight(
                category="income",
                title="Income Shifting Strategies",
                description="Consider income shifting strategies for future tax years to optimize overall tax situation.",
                potential_savings=500.00,  # Rough estimate
                priority="low",
                implementation_steps=[
                    "Plan major income events strategically",
                    "Consider deferred compensation options",
                    "Review business structure if self-employed"
                ],
                prerequisites=["Consult tax advisor"],
                risk_level="medium"
            ))

            return insights

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "generate_optimization_insights"}
            )
            raise

    def predict_future_tax_liability(self, tax_data: TaxData, income_growth_rate: float = 0.03,
                                   years_ahead: int = 5) -> Dict[str, Any]:
        """
        Predict future tax liability based on growth assumptions.

        Args:
            tax_data: Current tax data
            income_growth_rate: Expected annual income growth rate
            years_ahead: Number of years to predict

        Returns:
            Dictionary with current and projected liabilities
        """
        try:
            current_analysis = self.generate_comprehensive_analysis(tax_data)
            projections = self.generate_tax_projections(tax_data, years_ahead)

            projected_liabilities = {}
            for year, projection in projections.items():
                projected_liabilities[year] = projection['projected_tax']

            return {
                'current_liability': sum(current_analysis.tax_liability_breakdown.values()),
                'projected_liabilities': projected_liabilities,
                'confidence_score': 0.75,  # Rough confidence score
                'assumptions': {
                    'income_growth_rate': income_growth_rate,
                    'projection_method': 'simple_growth_model'
                }
            }

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "predict_future_tax_liability", "years_ahead": years_ahead}
            )
            raise

    def _calculate_optimal_retirement_contributions(self, tax_data: TaxData) -> Dict[str, Any]:
        """
        Calculate optimal retirement account contributions.

        Args:
            tax_data: Tax data

        Returns:
            Dictionary with contribution recommendations
        """
        try:
            # Simplified calculation - in reality this would be more complex
            tax_year = tax_data.get_current_year()
            income_data = tax_data.get_section('income', tax_year)
            current_income = sum(Decimal(str(v)) for v in income_data.values() if v)

            # 2024 limits (would need to be updated annually)
            traditional_ira_limit = 7000
            roth_ira_limit = 7000
            four01k_limit = 23000

            # Recommend based on income level
            if current_income < Decimal('50000'):
                recommended = min(traditional_ira_limit, current_income * Decimal('0.1'))
            elif current_income < Decimal('100000'):
                recommended = min(traditional_ira_limit, current_income * Decimal('0.08'))
            else:
                recommended = min(traditional_ira_limit, current_income * Decimal('0.06'))

            return {
                'traditional_ira_limit': traditional_ira_limit,
                'roth_ira_limit': roth_ira_limit,
                'four01k_limit': four01k_limit,
                'recommended_contribution': recommended
            }

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "_calculate_optimal_retirement_contributions"}
            )
            raise

    def _analyze_deduction_opportunities(self, tax_data: TaxData) -> List[Dict[str, Any]]:
        """
        Analyze potential deduction opportunities.

        Args:
            tax_data: Tax data

        Returns:
            List of deduction opportunities
        """
        try:
            opportunities = []
            tax_year = tax_data.get_current_year()
            deduction_data = tax_data.get_section('deductions', tax_year)
            income_data = tax_data.get_section('income', tax_year)

            # Check for common missed deductions
            current_deductions = sum(Decimal(str(v)) for v in deduction_data.values() if v)

            # Home office deduction (simplified check)
            if 'home_office' not in deduction_data and 'wages' in income_data:
                opportunities.append({
                    'deduction_type': 'home_office',
                    'potential_savings': 500.00,  # Rough estimate
                    'feasibility': 'medium',
                    'description': 'If you work from home, you may qualify for home office deduction'
                })

            # Medical expense deduction (simplified)
            if 'medical' not in deduction_data:
                opportunities.append({
                    'deduction_type': 'medical_expenses',
                    'potential_savings': 1000.00,  # Rough estimate
                    'feasibility': 'low',
                    'description': 'Medical expenses over 7.5% of AGI may be deductible'
                })

            # Charitable contributions
            if 'charitable' not in deduction_data:
                opportunities.append({
                    'deduction_type': 'charitable_contributions',
                    'potential_savings': 750.00,  # Rough estimate
                    'feasibility': 'high',
                    'description': 'Cash contributions to qualified charities are deductible'
                })

            return opportunities

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "_analyze_deduction_opportunities"}
            )
            raise

    # Alias methods for backward compatibility with tests
    def _calculate_effective_tax_rate(self, tax_data: TaxData) -> float:
        """Alias for calculate_effective_tax_rate"""
        return self.calculate_effective_tax_rate(tax_data)

    def _calculate_tax_burden_percentage(self, tax_data: TaxData) -> float:
        """Alias for analyzing tax burden and returning percentage"""
        burden_analysis = self.analyze_tax_burden(tax_data)
        return burden_analysis.get('burden_percentage', 0.0)

    def _analyze_income_distribution(self, tax_data: TaxData) -> Dict[str, float]:
        """Alias for analyze_income_distribution"""
        return self.analyze_income_distribution(tax_data)

    def save_analysis(self, result: TaxAnalyticsResult, filename: Optional[str] = None) -> Path:
        """Alias for save_analytics_result"""
        return self.save_analytics_result(result, filename)

    def load_analysis(self, filepath: Path) -> TaxAnalyticsResult:
        """Alias for load_analytics_result"""
        return self.load_analytics_result(filepath)

    def export_analysis_report(self, analysis: TaxAnalyticsResult, file_path: Path) -> None:
        """
        Export analysis report to text file.

        Args:
            analysis: Analysis to export
            file_path: Path to export file
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("TAX ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Tax Year: {analysis.tax_year}\n")
                f.write(f"Analysis Date: {analysis.calculated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("KEY METRICS:\n")
                f.write(f"Effective Tax Rate: {analysis.effective_tax_rate:.1f}%\n")
                f.write(f"Marginal Tax Rate: {analysis.marginal_tax_rate:.1f}%\n")
                f.write(f"Tax Burden: {analysis.tax_burden_percentage:.1f}%\n")
                f.write(f"Deduction Utilization: {analysis.deduction_utilization:.1f}%\n")
                f.write(f"Credit Utilization: {analysis.credit_utilization:.1f}%\n\n")

                f.write("INCOME DISTRIBUTION:\n")
                for source, pct in analysis.income_distribution.items():
                    f.write(f"• {source}: {pct:.1f}%\n")

                f.write("\nTAX LIABILITY BREAKDOWN:\n")
                for tax_type, amount in analysis.tax_liability_breakdown.items():
                    f.write(f"• {tax_type}: ${amount:,.2f}\n")

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "export_analysis_report", "file_path": str(file_path)}
            )
            raise