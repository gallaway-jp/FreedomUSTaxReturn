"""
Test Tax Analytics Service

Comprehensive test suite for the TaxAnalyticsService class covering:
- Effective tax rate calculations
- Tax burden analysis
- Multi-year trend analysis
- Deduction and credit utilization
- Predictive analytics and optimization insights
- Data persistence and export functionality
"""

import pytest
import json
import tempfile
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from services.tax_analytics_service import (
    TaxAnalyticsService,
    TaxAnalyticsResult,
    TaxTrendAnalysis,
    TaxOptimizationInsight
)
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService
from config.app_config import AppConfig


class TestTaxAnalyticsService:
    """Test suite for TaxAnalyticsService"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return AppConfig(
            version="1.0.0",
            safe_dir=Path(tempfile.mkdtemp()),
            key_file=Path(tempfile.mktemp()),
            tax_year=2023
        )

    @pytest.fixture
    def tax_calculation_service(self):
        """Create mock tax calculation service"""
        service = Mock()
        # Mock the tax result as an object with attributes
        tax_result = Mock()
        tax_result.total_tax_owed = Decimal('15000.00')
        tax_result.effective_rate = Decimal('15.0')
        tax_result.marginal_rate = Decimal('24.0')
        tax_result.tax_liability_breakdown = {
            'income_tax': Decimal('12000.00'),
            'social_security': Decimal('2000.00'),
            'medicare': Decimal('1000.00')
        }
        service.calculate_tax.return_value = tax_result
        service.get_marginal_tax_rate.return_value = 24.0
        service.get_standard_deduction.return_value = Decimal('13850.00')
        return service

    @pytest.fixture
    def analytics_service(self, config, tax_calculation_service):
        """Create analytics service instance"""
        return TaxAnalyticsService(config, tax_calculation_service)

    @pytest.fixture
    def sample_tax_data(self, config):
        """Create sample tax data for testing"""
        tax_data = TaxData(config)
        # Set current year to 2023 for testing
        tax_data.set_current_year(2023)
        # Set up some basic data for the current year
        current_year = 2023
        tax_data.data["years"][current_year] = {
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'ssn': '123-45-6789'
            },
            'income': {
                'wages': Decimal('75000.00'),
                'interest': Decimal('1000.00'),
                'dividends': Decimal('2000.00')
            },
            'deductions': {
                'standard_deduction': Decimal('13850.00'),
                'itemized_deductions': {}
            },
            'credits': {
                'child_tax_credit': Decimal('2000.00'),
                'education_credit': Decimal('0.00')
            },
            'payments': {
                'withholding': Decimal('12000.00'),
                'estimated_payments': Decimal('2000.00')
            },
            'filing_status': 'single'
        }
        return tax_data

    def test_initialization(self, analytics_service):
        """Test service initialization"""
        assert analytics_service.config is not None
        assert analytics_service.tax_calculation is not None
        assert analytics_service.analytics_dir.exists()

    def test_generate_comprehensive_analysis(self, analytics_service, sample_tax_data):
        """Test comprehensive analysis generation"""
        result = analytics_service.generate_comprehensive_analysis(sample_tax_data)

        assert isinstance(result, TaxAnalyticsResult)
        assert result.tax_year == 2023
        assert result.effective_tax_rate >= 0
        assert result.marginal_tax_rate >= 0
        assert result.tax_burden_percentage >= 0
        assert result.deduction_utilization >= 0
        assert result.credit_utilization >= 0
        assert isinstance(result.income_distribution, dict)
        assert isinstance(result.tax_liability_breakdown, dict)
        assert result.calculated_at is not None

    def test_calculate_effective_tax_rate(self, analytics_service, sample_tax_data):
        """Test effective tax rate calculation"""
        rate = analytics_service._calculate_effective_tax_rate(sample_tax_data)

        assert isinstance(rate, float)
        assert rate >= 0
        assert rate <= 100  # Should be a percentage

    def test_calculate_tax_burden_percentage(self, analytics_service, sample_tax_data):
        """Test tax burden percentage calculation"""
        burden = analytics_service._calculate_tax_burden_percentage(sample_tax_data)

        assert isinstance(burden, float)
        assert burden >= 0
        assert burden <= 100

    def test_analyze_income_distribution(self, analytics_service, sample_tax_data):
        """Test income distribution analysis"""
        distribution = analytics_service._analyze_income_distribution(sample_tax_data)

        assert isinstance(distribution, dict)
        assert len(distribution) > 0

        # Check that percentages sum to approximately 100%
        total_pct = sum(distribution.values())
        assert abs(total_pct - 100.0) < 1.0  # Allow small rounding error

    def test_calculate_deduction_utilization(self, analytics_service, sample_tax_data):
        """Test deduction utilization calculation"""
        utilization = analytics_service.analyze_deduction_utilization(sample_tax_data)
        
        assert isinstance(utilization, dict)
        assert 'utilization_rate' in utilization
        assert 'total_deductions' in utilization
        assert utilization['utilization_rate'] >= 0
        assert utilization['utilization_rate'] <= 100

    def test_calculate_credit_utilization(self, analytics_service, sample_tax_data):
        """Test credit utilization calculation"""
        utilization = analytics_service.analyze_credit_utilization(sample_tax_data)
        
        assert isinstance(utilization, dict)
        assert 'utilization_rate' in utilization
        assert 'total_credits' in utilization
        assert utilization['utilization_rate'] >= 0
        assert utilization['utilization_rate'] <= 100

    def test_analyze_tax_trends(self, analytics_service, config):
        """Test multi-year trend analysis"""
        # Create multiple years of tax data
        tax_returns = []
        for year in [2021, 2022, 2023]:
            tax_data = TaxData(config)
            tax_data.set_current_year(year)
            # Set up data for this year
            tax_data.data["years"][year] = {
                'personal_info': {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'ssn': '123-45-6789'
                },
                'income': {
                    'wages': Decimal('70000') + Decimal('3000') * (year - 2021),
                    'interest': Decimal('500.00')
                },
                'deductions': {
                    'standard_deduction': Decimal('12950') + Decimal('450') * (year - 2021)
                },
                'credits': {},
                'payments': {
                    'withholding': Decimal('10000') + Decimal('1000') * (year - 2021)
                }
            }
            tax_returns.append(tax_data)

        trend_analysis = analytics_service.analyze_tax_trends(tax_returns)

        assert isinstance(trend_analysis, TaxTrendAnalysis)
        assert len(trend_analysis.years_analyzed) == 3
        assert len(trend_analysis.effective_rate_trend) == 3
        assert len(trend_analysis.tax_burden_trend) == 3
        assert trend_analysis.income_growth_rate >= 0
        assert trend_analysis.tax_liability_growth_rate >= 0

    def test_save_and_load_analysis(self, analytics_service, sample_tax_data):
        """Test saving and loading analysis results"""
        # Generate analysis
        analysis = analytics_service.generate_comprehensive_analysis(sample_tax_data)

        # Save analysis
        file_path = analytics_service.save_analysis(analysis)

        assert file_path.exists()

        # Load analysis
        loaded_analysis = analytics_service.load_analysis(file_path)

        assert loaded_analysis.tax_year == analysis.tax_year
        assert loaded_analysis.effective_tax_rate == analysis.effective_tax_rate
        assert loaded_analysis.marginal_tax_rate == analysis.marginal_tax_rate

    def test_export_analysis_report(self, analytics_service, sample_tax_data):
        """Test analysis report export"""
        analysis = analytics_service.generate_comprehensive_analysis(sample_tax_data)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            file_path = Path(f.name)

        try:
            analytics_service.export_analysis_report(analysis, file_path)

            assert file_path.exists()
            assert file_path.stat().st_size > 0

            # Check content
            with open(file_path, 'r') as f:
                content = f.read()
                assert "TAX ANALYSIS REPORT" in content
                assert str(analysis.tax_year) in content
                assert "Effective Tax Rate" in content

        finally:
            file_path.unlink(missing_ok=True)

    def test_generate_tax_projections(self, analytics_service, sample_tax_data):
        """Test tax projection generation"""
        projections = analytics_service.generate_tax_projections(sample_tax_data, years_ahead=3)

        assert isinstance(projections, dict)
        assert len(projections) == 3  # 3 years of projections

        for year, projection in projections.items():
            assert isinstance(year, int)
            assert year > sample_tax_data.get_current_year()
            assert 'projected_income' in projection
            assert 'projected_tax' in projection
            assert 'projected_effective_rate' in projection

    def test_generate_optimization_insights(self, analytics_service, sample_tax_data):
        """Test tax optimization insights generation"""
        analysis = analytics_service.generate_comprehensive_analysis(sample_tax_data)
        insights = analytics_service.generate_optimization_insights(analysis)

        assert isinstance(insights, list)
        for insight in insights:
            assert isinstance(insight, TaxOptimizationInsight)
            assert insight.category in ['income', 'deductions', 'credits', 'retirement', 'investments']
            assert insight.priority in ['high', 'medium', 'low']
            assert insight.potential_savings >= 0

    def test_calculate_optimal_retirement_contributions(self, analytics_service, sample_tax_data):
        """Test optimal retirement contribution calculations"""
        optimal = analytics_service._calculate_optimal_retirement_contributions(sample_tax_data)

        assert isinstance(optimal, dict)
        assert 'traditional_ira_limit' in optimal
        assert 'roth_ira_limit' in optimal
        assert 'recommended_contribution' in optimal
        assert optimal['recommended_contribution'] >= 0

    def test_analyze_deduction_opportunities(self, analytics_service, sample_tax_data):
        """Test deduction opportunity analysis"""
        opportunities = analytics_service._analyze_deduction_opportunities(sample_tax_data)

        assert isinstance(opportunities, list)
        for opp in opportunities:
            assert 'deduction_type' in opp
            assert 'potential_savings' in opp
            assert 'feasibility' in opp

    def test_predict_future_tax_liability(self, analytics_service, sample_tax_data):
        """Test future tax liability prediction"""
        prediction = analytics_service.predict_future_tax_liability(
            sample_tax_data,
            income_growth_rate=0.03,
            years_ahead=5
        )

        assert isinstance(prediction, dict)
        assert 'current_liability' in prediction
        assert 'projected_liabilities' in prediction
        assert 'confidence_score' in prediction
        assert len(prediction['projected_liabilities']) == 5

    def test_error_handling_invalid_data(self, analytics_service, config):
        """Test error handling with invalid data"""
        invalid_data = TaxData(config)
        invalid_data.set_current_year(2023)
        # Set up invalid/empty data
        invalid_data.data["years"][2023] = {
            'personal_info': {},
            'income': {},
            'deductions': {},
            'credits': {},
            'payments': {}
        }

        # Test that the service handles invalid data gracefully
        result = analytics_service.generate_comprehensive_analysis(invalid_data)

        # Should return a result even with invalid data (graceful degradation)
        assert isinstance(result, TaxAnalyticsResult)
        assert result.tax_year == 2023
        # Check that default/safe values are used for missing data
        assert isinstance(result.effective_tax_rate, float)
        assert isinstance(result.marginal_tax_rate, float)

    def test_empty_income_distribution(self, analytics_service, config):
        """Test handling of tax data with no income"""
        empty_data = TaxData(config)
        empty_data.set_current_year(2023)
        # Set up data with no income
        empty_data.data["years"][2023] = {
            'personal_info': {'first_name': 'Test'},
            'income': {},  # No income
            'deductions': {},
            'credits': {},
            'payments': {}
        }

        distribution = analytics_service._analyze_income_distribution(empty_data)
        assert distribution == {} or len(distribution) == 0

    def test_trend_analysis_single_year(self, analytics_service, sample_tax_data):
        """Test trend analysis with single year (should handle gracefully)"""
        trend_analysis = analytics_service.analyze_tax_trends([sample_tax_data])

        assert isinstance(trend_analysis, TaxTrendAnalysis)
        assert len(trend_analysis.years_analyzed) == 1
        assert trend_analysis.income_growth_rate == 0.0
        assert trend_analysis.tax_liability_growth_rate == 0.0

    @patch('services.tax_analytics_service.datetime')
    def test_analysis_timestamp(self, mock_datetime, analytics_service, sample_tax_data):
        """Test that analysis includes correct timestamp"""
        fixed_time = datetime(2024, 1, 15, 10, 30, 45)
        mock_datetime.now.return_value = fixed_time

        analysis = analytics_service.generate_comprehensive_analysis(sample_tax_data)

        assert analysis.calculated_at == fixed_time


class TestTaxAnalyticsResult:
    """Test TaxAnalyticsResult data structure"""

    def test_initialization(self):
        """Test TaxAnalyticsResult initialization"""
        result = TaxAnalyticsResult(
            tax_year=2023,
            effective_tax_rate=15.5,
            marginal_tax_rate=22.0,
            tax_burden_percentage=12.3,
            deduction_utilization=75.0,
            credit_utilization=45.0,
            income_distribution={'wages': 85.0, 'investments': 15.0},
            tax_liability_breakdown={'income_tax': 10000, 'payroll_tax': 3000},
            calculated_at=datetime.now()
        )

        assert result.tax_year == 2023
        assert result.effective_tax_rate == 15.5
        assert result.marginal_tax_rate == 22.0
        assert result.tax_burden_percentage == 12.3
        assert result.deduction_utilization == 75.0
        assert result.credit_utilization == 45.0
        assert result.income_distribution == {'wages': 85.0, 'investments': 15.0}
        assert result.tax_liability_breakdown == {'income_tax': 10000, 'payroll_tax': 3000}
        assert isinstance(result.calculated_at, datetime)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = TaxAnalyticsResult(
            tax_year=2023,
            effective_tax_rate=15.5,
            marginal_tax_rate=22.0,
            tax_burden_percentage=12.3,
            deduction_utilization=75.0,
            credit_utilization=45.0,
            income_distribution={'wages': 85.0},
            tax_liability_breakdown={'income_tax': 10000},
            calculated_at=datetime.now()
        )

        data = result.to_dict()

        assert data['tax_year'] == 2023
        assert data['effective_tax_rate'] == 15.5
        assert data['marginal_tax_rate'] == 22.0
        assert 'calculated_at' in data

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            'tax_year': 2023,
            'effective_tax_rate': 15.5,
            'marginal_tax_rate': 22.0,
            'tax_burden_percentage': 12.3,
            'deduction_utilization': 75.0,
            'credit_utilization': 45.0,
            'income_distribution': {'wages': 85.0},
            'tax_liability_breakdown': {'income_tax': 10000},
            'calculated_at': '2024-01-15T10:30:45'
        }

        result = TaxAnalyticsResult.from_dict(data)

        assert result.tax_year == 2023
        assert result.effective_tax_rate == 15.5
        assert result.marginal_tax_rate == 22.0


class TestTaxTrendAnalysis:
    """Test TaxTrendAnalysis data structure"""

    def test_initialization(self):
        """Test TaxTrendAnalysis initialization"""
        analysis = TaxTrendAnalysis(
            years_analyzed=[2021, 2022, 2023],
            effective_rate_trend=[12.5, 14.2, 15.8],
            tax_burden_trend=[10.1, 11.5, 13.2],
            income_growth_rate=4.5,
            tax_liability_growth_rate=6.2,
            deduction_trend=[12000, 13500, 14200],
            credit_trend=[800, 950, 1100],
            analysis_period="2021-2023",
            generated_at=datetime.now()
        )

        assert analysis.years_analyzed == [2021, 2022, 2023]
        assert analysis.effective_rate_trend == [12.5, 14.2, 15.8]
        assert analysis.tax_burden_trend == [10.1, 11.5, 13.2]
        assert analysis.income_growth_rate == 4.5
        assert analysis.tax_liability_growth_rate == 6.2
        assert analysis.analysis_period == "2021-2023"

    def test_to_dict_and_from_dict(self):
        """Test serialization/deserialization"""
        original = TaxTrendAnalysis(
            years_analyzed=[2021, 2022, 2023],
            effective_rate_trend=[12.5, 14.2, 15.8],
            tax_burden_trend=[10.1, 11.5, 13.2],
            income_growth_rate=4.5,
            tax_liability_growth_rate=6.2,
            deduction_trend=[12000, 13500, 14200],
            credit_trend=[800, 950, 1100],
            analysis_period="2021-2023",
            generated_at=datetime.now()
        )

        data = original.to_dict()
        restored = TaxTrendAnalysis.from_dict(data)

        assert restored.years_analyzed == original.years_analyzed
        assert restored.effective_rate_trend == original.effective_rate_trend
        assert restored.tax_burden_trend == original.tax_burden_trend
        assert restored.income_growth_rate == original.income_growth_rate
        assert restored.tax_liability_growth_rate == original.tax_liability_growth_rate
        assert restored.analysis_period == original.analysis_period


class TestTaxOptimizationInsight:
    """Test TaxOptimizationInsight data structure"""

    def test_initialization(self):
        """Test TaxOptimizationInsight initialization"""
        insight = TaxOptimizationInsight(
            category="retirement",
            title="Increase Retirement Contributions",
            description="Consider increasing 401(k) contributions to reduce taxable income",
            potential_savings=2500.00,
            priority="high",
            implementation_steps=[
                "Contact HR to increase 401(k) contribution percentage",
                "Review investment options within retirement account"
            ],
            prerequisites=["Employer offers 401(k) matching"],
            risk_level="low"
        )

        assert insight.category == "retirement"
        assert insight.title == "Increase Retirement Contributions"
        assert insight.description == "Consider increasing 401(k) contributions to reduce taxable income"
        assert insight.potential_savings == 2500.00
        assert insight.priority == "high"
        assert len(insight.implementation_steps) == 2
        assert len(insight.prerequisites) == 1
        assert insight.risk_level == "low"

    def test_to_dict_and_from_dict(self):
        """Test serialization/deserialization"""
        original = TaxOptimizationInsight(
            category="retirement",
            title="Increase Retirement Contributions",
            description="Consider increasing 401(k) contributions",
            potential_savings=2500.00,
            priority="high",
            implementation_steps=["Step 1", "Step 2"],
            prerequisites=["Preq 1"],
            risk_level="low"
        )

        data = original.to_dict()
        restored = TaxOptimizationInsight.from_dict(data)

        assert restored.category == original.category
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.potential_savings == original.potential_savings
        assert restored.priority == original.priority
        assert restored.implementation_steps == original.implementation_steps
        assert restored.prerequisites == original.prerequisites
        assert restored.risk_level == original.risk_level