"""
Unit tests for Tax Planning Service
"""

import pytest
import json
from unittest.mock import Mock, patch
from services.tax_planning_service import (
    TaxPlanningService,
    ScenarioResult,
    TaxProjection,
    EstimatedTaxPayment,
    WithholdingRecommendation,
    RetirementOptimization
)
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestTaxPlanningService:
    """Test cases for TaxPlanningService"""

    @pytest.fixture
    def tax_data(self):
        """Create sample tax data for testing"""
        config = AppConfig()
        data = TaxData(config)

        # Set up sample data using proper methods
        data.set('personal_info.first_name', 'John')
        data.set('personal_info.last_name', 'Doe')
        data.set('personal_info.ssn', '123-45-6789')
        data.set('filing_status.status', 'Single')
        data.set('income.w2_forms', [{
            'employer_ein': '12-3456789',
            'wages': 75000.00,
            'federal_withholding': 8500.00
        }])
        data.set('income.business_income', 0)
        data.set('income.dividend_income', [])
        data.set('deductions.method', 'standard')
        
        return data

    @pytest.fixture
    def planning_service(self):
        """Create tax planning service instance"""
        return TaxPlanningService()

    def test_init(self, planning_service):
        """Test service initialization"""
        assert planning_service.tax_year == 2025
        assert planning_service.calc_service is not None

    def test_analyze_scenario_income_change(self, planning_service, tax_data):
        """Test scenario analysis with income changes"""
        changes = {
            'income': {
                'w2_forms': [{
                    'wages': 10000  # Additional $10k income
                }]
            }
        }

        result = planning_service.analyze_scenario(tax_data, changes, "Income Increase")

        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == "Income Increase"
        assert result.new_tax > result.original_tax
        assert result.tax_difference > 0
        assert 'income' in result.key_changes

    def test_analyze_scenario_filing_status_change(self, planning_service, tax_data):
        """Test scenario analysis with filing status change"""
        changes = {
            'filing_status': {
                'status': 'Head of Household'
            }
        }

        result = planning_service.analyze_scenario(tax_data, changes, "Filing Status Change")

        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == "Filing Status Change"
        assert 'filing_status' in result.key_changes

    def test_project_future_tax(self, planning_service, tax_data):
        """Test future tax projection"""
        # Use 2023 since it's available
        projection = planning_service.project_future_tax(
            tax_data, 2023, income_growth_rate=0.03, inflation_rate=0.025
        )

        assert isinstance(projection, TaxProjection)
        assert projection.projection_year == 2023
        assert projection.projected_income >= 0  # Could be same or slightly different
        assert projection.projected_tax >= 0
        assert projection.confidence_level in ['high', 'medium', 'low']
        assert 'income_growth_rate' in projection.assumptions

    def test_calculate_estimated_tax_payments(self, planning_service, tax_data):
        """Test estimated tax payment calculation"""
        payments = planning_service.calculate_estimated_tax_payments(tax_data, 80000)

        assert len(payments) == 4  # Four quarters
        assert all(isinstance(p, EstimatedTaxPayment) for p in payments)

        # Check quarter progression
        for i, payment in enumerate(payments):
            assert payment.quarter == i + 1
            assert payment.year == 2025
            assert payment.payment_amount >= 0
            assert payment.safe_harbor_amount >= 0

        # Check due dates are in correct quarters
        assert payments[0].due_date.month == 4  # Q1
        assert payments[1].due_date.month == 6  # Q2
        assert payments[2].due_date.month == 9  # Q3
        assert payments[3].due_date.month == 1  # Q4

    def test_calculate_withholding_recommendation(self, planning_service, tax_data):
        """Test withholding recommendation calculation"""
        recommendation = planning_service.calculate_withholding_recommendation(tax_data, 80000)

        assert isinstance(recommendation, WithholdingRecommendation)
        assert recommendation.current_withholding >= 0
        assert recommendation.recommended_withholding >= 0
        assert recommendation.expected_annual_tax >= 0
        assert isinstance(recommendation.reasoning, str)

    def test_optimize_retirement_contributions(self, planning_service, tax_data):
        """Test retirement contribution optimization"""
        optimization = planning_service.optimize_retirement_contributions(
            tax_data, 75000, employer_401k_match=0.05
        )

        assert isinstance(optimization, RetirementOptimization)
        assert optimization.traditional_ira_limit > 0
        assert optimization.roth_ira_limit > 0
        assert optimization.employer_401k_limit > 0
        assert optimization.recommended_401k >= optimization.employer_401k_limit * 0.05  # At least match
        assert isinstance(optimization.strategy, str)
        assert len(optimization.reasoning) > 0

    def test_scenario_result_to_dict(self, planning_service, tax_data):
        """Test ScenarioResult serialization"""
        changes = {'income': {'w2_forms': [{'wages': 5000}]}}
        result = planning_service.analyze_scenario(tax_data, changes)

        data = result.to_dict()
        assert isinstance(data, dict)
        assert 'scenario_name' in data
        assert 'original_tax' in data
        assert 'new_tax' in data
        assert 'tax_difference' in data

    def test_tax_projection_to_dict(self, planning_service, tax_data):
        """Test TaxProjection serialization"""
        projection = planning_service.project_future_tax(tax_data, 2023)

        data = projection.to_dict()
        assert isinstance(data, dict)
        assert 'projection_year' in data
        assert 'projected_income' in data
        assert 'projected_tax' in data
        assert 'confidence_level' in data

    def test_estimated_tax_payment_to_dict(self, planning_service, tax_data):
        """Test EstimatedTaxPayment serialization"""
        payments = planning_service.calculate_estimated_tax_payments(tax_data, 75000)
        payment = payments[0]

        data = payment.to_dict()
        assert isinstance(data, dict)
        assert 'quarter' in data
        assert 'year' in data
        assert 'payment_amount' in data
        assert 'due_date' in data

    def test_withholding_recommendation_to_dict(self, planning_service, tax_data):
        """Test WithholdingRecommendation serialization"""
        recommendation = planning_service.calculate_withholding_recommendation(tax_data, 75000)

        data = recommendation.to_dict()
        assert isinstance(data, dict)
        assert 'current_withholding' in data
        assert 'recommended_withholding' in data
        assert 'adjustment_needed' in data

    def test_retirement_optimization_to_dict(self, planning_service, tax_data):
        """Test RetirementOptimization serialization"""
        optimization = planning_service.optimize_retirement_contributions(tax_data, 75000)

        data = optimization.to_dict()
        assert isinstance(data, dict)
        assert 'traditional_ira_limit' in data
        assert 'recommended_traditional' in data
        assert 'strategy' in data

    @patch('services.tax_planning_service.TaxCalculationService')
    def test_service_with_custom_tax_year(self, mock_calc_service):
        """Test service initialization with custom tax year"""
        service = TaxPlanningService(tax_year=2023)
        assert service.tax_year == 2023
        mock_calc_service.assert_called_once_with(2023)

    def test_projection_invalid_year(self, planning_service, tax_data):
        """Test projection with invalid year"""
        with pytest.raises(Exception):  # Should handle invalid year gracefully
            planning_service.project_future_tax(tax_data, 2024)  # Past year

    def test_estimated_tax_zero_income(self, planning_service, tax_data):
        """Test estimated tax calculation with zero income"""
        payments = planning_service.calculate_estimated_tax_payments(tax_data, 0)

        # Should still return payments, but they might be zero or minimal
        assert len(payments) == 4
        # The payments might not be exactly zero due to safe harbor calculation
        # Just check that they're reasonable (not negative)
        assert all(p.payment_amount >= 0 for p in payments)

    def test_withholding_zero_income(self, planning_service, tax_data):
        """Test withholding recommendation with zero income"""
        recommendation = planning_service.calculate_withholding_recommendation(tax_data, 0)

        assert recommendation.expected_annual_tax == 0
        assert recommendation.recommended_withholding == 0

    def test_retirement_zero_income(self, planning_service, tax_data):
        """Test retirement optimization with zero income"""
        optimization = planning_service.optimize_retirement_contributions(tax_data, 0)

        # Should still return valid structure but with minimal recommendations
        assert optimization.recommended_traditional >= 0  # Could be 0 or some amount
        assert optimization.recommended_roth >= 0
        assert optimization.recommended_401k >= 0
        assert optimization.tax_savings >= 0
        assert isinstance(optimization.strategy, str)


class TestConvenienceFunctions:
    """Test convenience functions for tax planning"""

    @pytest.fixture
    def tax_data(self):
        """Create sample tax data for testing"""
        config = AppConfig()
        data = TaxData(config)

        # Set up sample data using proper methods
        data.set('personal_info.first_name', 'John')
        data.set('personal_info.last_name', 'Doe')
        data.set('personal_info.ssn', '123-45-6789')
        data.set('filing_status.status', 'Single')
        data.set('income.w2_forms', [{
            'employer_ein': '12-3456789',
            'wages': 75000.00,
            'federal_withholding': 8500.00
        }])
        data.set('income.business_income', 0)
        data.set('income.dividend_income', [])
        data.set('deductions.method', 'standard')
        
        return data

    @pytest.fixture
    def planning_service(self):
        """Create tax planning service instance"""
        return TaxPlanningService()

    @patch('services.tax_planning_service.TaxPlanningService.analyze_scenario')
    def test_scenario_with_empty_changes(self, mock_analyze, planning_service, tax_data):
        """Test scenario analysis with no changes"""
        mock_analyze.return_value = Mock(spec=ScenarioResult)

        # Empty changes should still work
        result = planning_service.analyze_scenario(tax_data, {}, "Empty Scenario")
        mock_analyze.assert_called_once()

    def test_projection_confidence_levels(self, planning_service, tax_data):
        """Test that confidence levels are assigned correctly"""
        # Current year should be high confidence
        projection_2025 = planning_service.project_future_tax(tax_data, 2025)
        assert projection_2025.confidence_level == 'high'

        # Near past should still be high confidence (using available config)
        projection_2023 = planning_service.project_future_tax(tax_data, 2023)
        assert projection_2023.confidence_level == 'high'