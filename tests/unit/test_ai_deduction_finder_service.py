"""
Unit tests for AI Deduction Finder Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from decimal import Decimal

from services.ai_deduction_finder_service import (
    AIDeductionFinderService,
    DeductionAnalysisResult,
    DeductionSuggestion,
    DeductionCategory,
    ConfidenceLevel
)
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestAIDeductionFinderService:
    """Test cases for AI Deduction Finder Service"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        config.tax_year = 2023
        return config

    @pytest.fixture
    def mock_tax_calculation_service(self):
        """Create a mock tax calculation service"""
        service = Mock()
        service.calculate_tax.return_value = Mock(
            total_tax=Decimal('5000.00'),
            effective_rate=Decimal('0.15')
        )
        return service

    @pytest.fixture
    def ai_service(self, mock_config, mock_tax_calculation_service):
        """Create AI deduction finder service instance"""
        return AIDeductionFinderService(mock_config, mock_tax_calculation_service)

    @pytest.fixture
    def sample_tax_data(self):
        """Create sample tax data for testing"""
        tax_data = Mock()
        
        # Mock the get method to return appropriate values
        def mock_get(path, default=None, tax_year=None):
            defaults = {
                'deductions': {},
                'income': {},
                'personal_info': {},
                'dependents': [],
                'adjustments': {},
                'credits': {},
            }
            return {
                'deductions.medical_expenses': Decimal('2000.00'),
                'deductions.charitable_contributions': Decimal('1500.00'),
                'deductions.business_expenses': Decimal('3000.00'),
                'deductions.state_local_taxes': Decimal('2500.00'),
                'income.w2_income': [{'wages': Decimal('70000.00'), 'federal_tax_withheld': Decimal('8000.00')}],
                'income.business_income': [{'description': 'Consulting', 'gross_income': Decimal('10000.00'), 'expenses': Decimal('3000.00')}],
                'personal_info.date_of_birth': '01/15/1980',
                'personal_info.first_name': 'John',
                'dependents': [{'relationship': 'child'}, {'relationship': 'spouse'}],
                'filing_status.status': 'single',
                'adjustments.ira_deduction': Decimal('2000.00'),
                'adjustments.student_loan_interest': Decimal('1500.00'),
                'credits.residential_energy.amount': Decimal('800.00'),
            }.get(path, default if default is not None else defaults.get(path.split('.')[0], []))
        
        tax_data.get.side_effect = mock_get
        
        tax_data.get_current_year.return_value = 2023
        
        # Mock methods that the service calls
        tax_data.calculate_agi = Mock(return_value=Decimal('65000.00'))
        tax_data.calculate_total_income = Mock(return_value=Decimal('75000.00'))
        
        # Mock other methods that might be called
        tax_data.get_section.side_effect = lambda section, tax_year=None: {
            'income': {'w2_income': [{'wages': Decimal('70000.00')}], 'business_income': [{'gross_income': Decimal('10000.00'), 'expenses': Decimal('3000.00')}]},
            'deductions': {'medical_expenses': Decimal('2000.00'), 'charitable_contributions': Decimal('1500.00'), 'state_local_taxes': Decimal('2500.00')},
            'personal_info': {'date_of_birth': '01/15/1980', 'first_name': 'John'},
            'dependents': [{'relationship': 'child'}],
            'adjustments': {'ira_deduction': Decimal('2000.00'), 'student_loan_interest': Decimal('1500.00')},
            'credits': {'residential_energy': {'amount': Decimal('800.00')}},
        }.get(section, {})
        
        return tax_data
        
        # Mock other methods that might be called
        tax_data.get_section.side_effect = lambda section, tax_year=None: {
            'income': {'w2_income': [{'wages': Decimal('70000.00')}], 'business_income': [{'gross_income': Decimal('10000.00'), 'expenses': Decimal('3000.00')}]},
            'deductions': {'medical_expenses': Decimal('2000.00'), 'charitable_contributions': Decimal('1500.00'), 'state_local_taxes': Decimal('2500.00')},
            'personal_info': {'date_of_birth': '01/15/1980', 'first_name': 'John'},
            'dependents': [{'relationship': 'child'}],
            'adjustments': {'ira_deduction': Decimal('2000.00'), 'student_loan_interest': Decimal('1500.00')},
            'credits': {'residential_energy': {'amount': Decimal('800.00')}},
        }.get(section, {})
        
        return tax_data

    def test_service_initialization(self, ai_service):
        """Test that the service initializes correctly"""
        assert ai_service is not None
        assert ai_service.config is not None
        assert ai_service.tax_calculation is not None

    def test_analyze_deductions_basic(self, ai_service, sample_tax_data):
        """Test basic deduction analysis functionality"""
        result = ai_service.analyze_deductions(sample_tax_data)

        assert isinstance(result, DeductionAnalysisResult)
        assert result.analysis_date <= datetime.now()
        assert isinstance(result.suggestions, list)
        assert isinstance(result.analyzed_categories, list)
        assert result.total_potential_savings >= 0
        assert result.tax_year == 2023
        assert 0 <= result.data_completeness_score <= 100

    def test_medical_deductions_analysis(self, ai_service, sample_tax_data):
        """Test medical deductions analysis"""
        suggestions = ai_service._analyze_medical_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.MEDICAL
            assert suggestion.potential_savings >= 0

    def test_charitable_deductions_analysis(self, ai_service, sample_tax_data):
        """Test charitable deductions analysis"""
        suggestions = ai_service._analyze_charitable_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.CHARITABLE
            assert suggestion.potential_savings >= 0

    def test_business_deductions_analysis(self, ai_service, sample_tax_data):
        """Test business deductions analysis"""
        suggestions = ai_service._analyze_business_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.BUSINESS
            assert suggestion.potential_savings >= 0

    def test_education_deductions_analysis(self, ai_service, sample_tax_data):
        """Test education deductions analysis"""
        suggestions = ai_service._analyze_education_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.EDUCATION
            assert suggestion.potential_savings >= 0

    def test_home_office_deductions_analysis(self, ai_service, sample_tax_data):
        """Test home office deductions analysis"""
        suggestions = ai_service._analyze_home_office_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.HOME_OFFICE
            assert suggestion.potential_savings >= 0

    def test_vehicle_deductions_analysis(self, ai_service, sample_tax_data):
        """Test vehicle deductions analysis"""
        suggestions = ai_service._analyze_vehicle_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.VEHICLE
            assert suggestion.potential_savings >= 0

    def test_retirement_deductions_analysis(self, ai_service, sample_tax_data):
        """Test retirement deductions analysis"""
        suggestions = ai_service._analyze_retirement_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.RETIREMENT
            assert suggestion.potential_savings >= 0

    def test_state_local_deductions_analysis(self, ai_service, sample_tax_data):
        """Test state/local tax deductions analysis"""
        suggestions = ai_service._analyze_state_local_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.STATE_LOCAL
            assert suggestion.potential_savings >= 0

    def test_energy_deductions_analysis(self, ai_service, sample_tax_data):
        """Test energy deductions analysis"""
        suggestions = ai_service._analyze_energy_deductions(sample_tax_data)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, DeductionSuggestion)
            assert suggestion.category == DeductionCategory.ENERGY
            assert suggestion.potential_savings >= 0

    def test_confidence_levels(self, ai_service, sample_tax_data):
        """Test that suggestions have appropriate confidence levels"""
        result = ai_service.analyze_deductions(sample_tax_data)

        for suggestion in result.suggestions:
            assert isinstance(suggestion.confidence, ConfidenceLevel)

    def test_priority_scoring(self, ai_service, sample_tax_data):
        """Test that suggestions are properly prioritized"""
        result = ai_service.analyze_deductions(sample_tax_data)

        # Check that priority is within expected range
        for suggestion in result.suggestions:
            assert 1 <= suggestion.priority <= 10

    def test_category_summaries(self, ai_service, sample_tax_data):
        """Test that analyzed categories are tracked"""
        result = ai_service.analyze_deductions(sample_tax_data)

        assert len(result.analyzed_categories) > 0
        assert "medical" in result.analyzed_categories

    def test_empty_tax_data_handling(self, ai_service):
        """Test handling of empty or minimal tax data"""
        empty_tax_data = Mock(spec=TaxData)
        empty_tax_data.filing_status = "single"
        empty_tax_data.gross_income = Decimal('0.00')
        empty_tax_data.adjusted_gross_income = Decimal('0.00')
        empty_tax_data.total_deductions = Decimal('0.00')
        empty_tax_data.total_credits = Decimal('0.00')
        empty_tax_data.taxable_income = Decimal('0.00')
        empty_tax_data.w2_income = []
        empty_tax_data.income_1099 = []

        # Set all expense fields to zero
        for attr in ['medical_expenses', 'charitable_contributions', 'business_expenses',
                     'education_expenses', 'home_office_expenses', 'vehicle_expenses',
                     'retirement_contributions', 'state_tax_paid', 'energy_credits']:
            setattr(empty_tax_data, attr, Decimal('0.00'))

        result = ai_service.analyze_deductions(empty_tax_data)

        assert isinstance(result, DeductionAnalysisResult)
        # Should still generate some suggestions even with no data
        assert isinstance(result.suggestions, list)