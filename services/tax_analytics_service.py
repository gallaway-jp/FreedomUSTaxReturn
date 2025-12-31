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

from config.app_config import AppConfig
from models.tax_data import TaxData
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
            # Get total income
            total_income = tax_data.calculate_total_income()

            # Get tax calculation result
            tax_result = self.tax_calculation.calculate_tax(tax_data)

            if total_income <= 0:
                return 0.0

            # Calculate effective rate
            effective_rate = (tax_result.total_tax_owed / total_income) * 100

            # Ensure reasonable bounds
            return max(0.0, min(100.0, effective_rate))

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "calculate_effective_tax_rate", "tax_year": tax_data.tax_year}
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
            return self.tax_calculation.get_marginal_tax_rate(tax_data)
        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "calculate_marginal_tax_rate", "tax_year": tax_data.tax_year}
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
            total_income = tax_data.calculate_total_income()
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
            breakdown = {
                'income_tax': tax_result.income_tax,
                'self_employment_tax': tax_result.self_employment_tax,
                'additional_medicare_tax': tax_result.additional_medicare_tax,
                'net_investment_income_tax': tax_result.net_investment_income_tax,
                'alternative_minimum_tax': tax_result.alternative_minimum_tax
            }

            # Generate insights
            insights = self._generate_tax_burden_insights(
                burden_percentage, breakdown, tax_data.filing_status, total_income
            )

            return {
                'tax_burden_percentage': burden_percentage,
                'breakdown': breakdown,
                'insights': insights
            }

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_tax_burden", "tax_year": tax_data.tax_year}
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
            # Get income breakdown
            income_breakdown = tax_data.get_income_breakdown()
            total_income = sum(income_breakdown.values())

            if total_income <= 0:
                return {}

            # Calculate percentages
            distribution = {}
            for source, amount in income_breakdown.items():
                distribution[source] = (amount / total_income) * 100

            return distribution

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_income_distribution", "tax_year": tax_data.tax_year}
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
            total_income = tax_data.calculate_total_income()
            agi = tax_data.calculate_agi()
            deductions = total_income - agi if total_income > agi else 0

            # Get standard deduction for comparison
            standard_deduction = self.tax_calculation.get_standard_deduction(tax_data.filing_status)

            utilization_rate = 0.0
            if deductions > 0:
                utilization_rate = min(100.0, (deductions / max(total_income, standard_deduction)) * 100)

            # Analyze deduction sources
            deduction_sources = tax_data.get_deduction_breakdown()

            insights = []
            if deductions < standard_deduction:
                insights.append("Consider itemizing deductions if they exceed the standard deduction")
            elif deductions > standard_deduction * 1.5:
                insights.append("Strong deduction utilization - review for accuracy")

            return {
                'utilization_rate': utilization_rate,
                'total_deductions': deductions,
                'standard_deduction': standard_deduction,
                'deduction_sources': deduction_sources,
                'insights': insights
            }

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_deduction_utilization", "tax_year": tax_data.tax_year}
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
            tax_result = self.tax_calculation.calculate_tax(tax_data)
            total_credits = tax_result.total_credits

            # Estimate potential tax liability without credits
            tax_without_credits = tax_result.income_tax + tax_result.self_employment_tax + \
                                tax_result.additional_medicare_tax + tax_result.net_investment_income_tax + \
                                tax_result.alternative_minimum_tax

            utilization_rate = 0.0
            if tax_without_credits > 0:
                utilization_rate = min(100.0, (total_credits / tax_without_credits) * 100)

            # Breakdown of credits
            credit_breakdown = tax_data.get_credit_breakdown()

            insights = []
            if total_credits > tax_without_credits:
                insights.append("Credits exceed tax liability - may result in refund")
            elif total_credits > tax_without_credits * 0.5:
                insights.append("Significant credit utilization reducing tax burden")
            elif total_credits == 0:
                insights.append("No tax credits claimed - review eligibility for available credits")

            return {
                'utilization_rate': utilization_rate,
                'total_credits': total_credits,
                'credit_breakdown': credit_breakdown,
                'insights': insights
            }

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_credit_utilization", "tax_year": tax_data.tax_year}
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
            effective_rate = self.calculate_effective_tax_rate(tax_data)
            marginal_rate = self.calculate_marginal_tax_rate(tax_data)

            burden_analysis = self.analyze_tax_burden(tax_data)
            income_distribution = self.analyze_income_distribution(tax_data)
            deduction_analysis = self.analyze_deduction_utilization(tax_data)
            credit_analysis = self.analyze_credit_utilization(tax_data)

            return TaxAnalyticsResult(
                tax_year=tax_data.tax_year,
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
            self.error_tracker.track_error(
                error=e,
                context={"operation": "generate_comprehensive_analysis", "tax_year": tax_data.tax_year}
            )
            # Return minimal result on error
            return TaxAnalyticsResult(
                tax_year=tax_data.tax_year,
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
                raise ValueError("No tax returns provided for trend analysis")

            # Sort by year
            sorted_returns = sorted(tax_returns, key=lambda x: x.tax_year)
            years = [r.tax_year for r in sorted_returns]

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

                total_income = tax_data.calculate_total_income()
                incomes.append(total_income)

                tax_result = self.tax_calculation.calculate_tax(tax_data)
                tax_liabilities.append(tax_result.total_tax_owed)

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
                analysis_period=f"{min(years)}-{max(years)}",
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