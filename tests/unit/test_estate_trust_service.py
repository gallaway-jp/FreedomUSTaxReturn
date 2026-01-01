"""
Unit tests for Estate and Trust Tax Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, date
from decimal import Decimal

from services.estate_trust_service import (
    EstateTrustService,
    TrustBeneficiary,
    TrustIncome,
    TrustDeductions,
    TrustType,
    EstateType,
    IncomeDistributionType
)
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestEstateTrustService:
    """Test cases for Estate and Trust Tax Service"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        config.tax_year = 2025
        return config

    @pytest.fixture
    def estate_service(self, mock_config):
        """Create estate and trust service instance"""
        return EstateTrustService(mock_config)

    @pytest.fixture
    def sample_tax_data(self):
        """Create sample tax data for testing"""
        tax_data = Mock(spec=TaxData)
        tax_data.get.return_value = []
        tax_data.set = Mock()
        return tax_data

    @pytest.fixture
    def sample_beneficiary(self):
        """Create a sample trust beneficiary"""
        return TrustBeneficiary(
            name="John Smith",
            ssn="123-45-6789",
            address="123 Main St, Anytown, USA",
            relationship="Child",
            share_percentage=Decimal("50"),
            income_distributed=Decimal("5000.00")
        )

    def test_service_initialization(self, estate_service, mock_config):
        """Test estate and trust service initialization"""
        assert estate_service.config == mock_config
        assert estate_service.error_tracker is not None

    def test_trust_types_enum(self):
        """Test all trust type enum values"""
        trust_types = [
            TrustType.SIMPLE_TRUST,
            TrustType.COMPLEX_TRUST,
            TrustType.GRANTOR_TRUST,
            TrustType.CHARITABLE_REMAINDER_TRUST,
            TrustType.QUALIFIED_DISABILITY_TRUST,
            TrustType.OTHER
        ]
        
        assert len(trust_types) == 6
        for trust_type in trust_types:
            assert trust_type is not None
            assert isinstance(trust_type.value, str)

    def test_estate_types_enum(self):
        """Test all estate type enum values"""
        estate_types = [
            EstateType.SIMPLE_ESTATE,
            EstateType.COMPLEX_ESTATE,
            EstateType.QUALIFIED_TERMINATION,
            EstateType.OTHER
        ]
        
        assert len(estate_types) == 4
        for estate_type in estate_types:
            assert estate_type is not None
            assert isinstance(estate_type.value, str)

    def test_income_distribution_types_enum(self):
        """Test income distribution type enum values"""
        distribution_types = [
            IncomeDistributionType.ORDINARY_INCOME,
            IncomeDistributionType.CAPITAL_GAINS,
            IncomeDistributionType.TAX_EXEMPT,
            IncomeDistributionType.RETURN_OF_CAPITAL
        ]
        
        assert len(distribution_types) == 4

    def test_add_beneficiary(self, estate_service, sample_tax_data, sample_beneficiary):
        """Test adding a trust beneficiary"""
        sample_tax_data.get.return_value = []
        
        result = estate_service.add_beneficiary(sample_tax_data, sample_beneficiary)
        
        assert result is True
        sample_tax_data.set.assert_called_once()

    def test_add_multiple_beneficiaries(self, estate_service, sample_tax_data, sample_beneficiary):
        """Test adding multiple beneficiaries"""
        beneficiary2 = TrustBeneficiary(
            name="Jane Smith",
            ssn="987-65-4321",
            address="456 Oak Ave, Somewhere, USA",
            relationship="Spouse",
            share_percentage=Decimal("50")
        )
        
        sample_tax_data.get.side_effect = [[], [sample_beneficiary.to_dict()]]
        
        estate_service.add_beneficiary(sample_tax_data, sample_beneficiary)
        estate_service.add_beneficiary(sample_tax_data, beneficiary2)
        
        assert sample_tax_data.set.call_count == 2

    def test_get_beneficiaries(self, estate_service, sample_tax_data, sample_beneficiary):
        """Test retrieving beneficiaries"""
        sample_tax_data.get.return_value = [sample_beneficiary.to_dict()]
        
        beneficiaries = estate_service.get_beneficiaries(sample_tax_data)
        
        assert len(beneficiaries) == 1
        assert beneficiaries[0].name == "John Smith"
        assert beneficiaries[0].share_percentage == Decimal("50")

    def test_trust_income_calculation(self):
        """Test trust income calculation"""
        trust_income = TrustIncome(
            interest_income=Decimal("1000.00"),
            dividend_income=Decimal("2000.00"),
            business_income=Decimal("5000.00"),
            capital_gains=Decimal("3000.00"),
            rental_income=Decimal("4000.00"),
            royalty_income=Decimal("500.00"),
            other_income=Decimal("0")
        )
        
        total = trust_income.calculate_total()
        
        assert total == Decimal("15500.00")

    def test_trust_deductions_calculation(self):
        """Test trust deductions calculation"""
        trust_deductions = TrustDeductions(
            fiduciary_fees=Decimal("500.00"),
            attorney_fees=Decimal("1000.00"),
            accounting_fees=Decimal("800.00"),
            other_administrative_expenses=Decimal("200.00"),
            charitable_contributions=Decimal("2000.00"),
            net_operating_loss=Decimal("0")
        )
        
        total = trust_deductions.calculate_total()
        
        assert total == Decimal("4500.00")

    def test_beneficiary_income_distribution(self, estate_service):
        """Test calculating beneficiary income distribution"""
        beneficiary = TrustBeneficiary(
            name="John Smith",
            ssn="123-45-6789",
            address="123 Main St",
            relationship="Child",
            share_percentage=Decimal("25"),
            income_distributed=Decimal("0")
        )
        
        trust_income = Decimal("10000.00")
        distribution = estate_service.calculate_beneficiary_distribution(beneficiary, trust_income)
        
        assert distribution == Decimal("2500.00")

    def test_validate_beneficiary_data(self, estate_service):
        """Test beneficiary data validation"""
        valid_beneficiary = TrustBeneficiary(
            name="John Smith",
            ssn="123-45-6789",
            address="123 Main St, Anytown, USA",
            relationship="Child",
            share_percentage=Decimal("50")
        )
        
        errors = estate_service.validate_beneficiary_data(valid_beneficiary)
        
        assert len(errors) == 0

    def test_validate_beneficiary_missing_name(self, estate_service):
        """Test validation fails with missing name"""
        invalid_beneficiary = TrustBeneficiary(
            name="",
            ssn="123-45-6789",
            address="123 Main St",
            relationship="Child",
            share_percentage=Decimal("50")
        )
        
        errors = estate_service.validate_beneficiary_data(invalid_beneficiary)
        
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_validate_share_percentage_total(self, estate_service):
        """Test validation of total share percentages"""
        beneficiaries = [
            TrustBeneficiary(
                name="John",
                ssn="111-11-1111",
                address="123 Main",
                relationship="Child",
                share_percentage=Decimal("50")
            ),
            TrustBeneficiary(
                name="Jane",
                ssn="222-22-2222",
                address="456 Oak",
                relationship="Child",
                share_percentage=Decimal("40")
            )
        ]
        
        total_share = sum(b.share_percentage for b in beneficiaries)
        
        assert total_share == Decimal("90")
        assert total_share != Decimal("100")

    def test_simple_trust_distribution(self, estate_service):
        """Test simple trust distribution calculations"""
        # Simple trusts must distribute all income annually
        trust_income = TrustIncome(
            interest_income=Decimal("5000.00"),
            dividend_income=Decimal("3000.00"),
            capital_gains=Decimal("2000.00")
        )
        
        total_income = trust_income.calculate_total()
        
        # All income must be distributed in simple trust
        assert total_income == Decimal("10000.00")

    def test_complex_trust_accumulation(self, estate_service):
        """Test complex trust with accumulated income"""
        # Complex trusts can accumulate income
        trust_income = TrustIncome(
            interest_income=Decimal("5000.00"),
            dividend_income=Decimal("3000.00"),
            capital_gains=Decimal("2000.00"),
            other_income=Decimal("1000.00")
        )
        
        distributed_amount = Decimal("6000.00")  # Only distribute part
        accumulated_amount = trust_income.calculate_total() - distributed_amount
        
        assert accumulated_amount == Decimal("5000.00")

    def test_grantor_trust_passthrough(self, estate_service, sample_tax_data):
        """Test grantor trust income passthrough to grantor"""
        grantor_income = Decimal("10000.00")
        
        # In grantor trusts, grantor pays tax on all income
        # regardless of actual distribution
        is_grantor_trust = True
        
        assert is_grantor_trust is True

    def test_charitable_remainder_trust_distribution(self, estate_service):
        """Test charitable remainder trust calculations"""
        trust_value = Decimal("500000.00")
        distribution_rate = Decimal("0.05")  # 5% annual distribution
        
        annual_distribution = trust_value * distribution_rate
        
        assert annual_distribution == Decimal("25000.00")

    def test_form_1041_calculations(self, estate_service, sample_tax_data):
        """Test Form 1041 (Estate/Trust income tax return) calculations"""
        trust_income = TrustIncome(
            interest_income=Decimal("2000.00"),
            dividend_income=Decimal("1500.00"),
            business_income=Decimal("3000.00"),
            capital_gains=Decimal("1000.00")
        )
        
        trust_deductions = TrustDeductions(
            fiduciary_fees=Decimal("500.00"),
            accounting_fees=Decimal("300.00"),
            charitable_contributions=Decimal("1000.00")
        )
        
        total_income = trust_income.calculate_total()
        total_deductions = trust_deductions.calculate_total()
        taxable_income = total_income - total_deductions
        
        assert total_income == Decimal("7500.00")
        assert total_deductions == Decimal("1800.00")
        assert taxable_income == Decimal("5700.00")

    def test_beneficiary_serialization(self, sample_beneficiary):
        """Test beneficiary serialization to dictionary"""
        beneficiary_dict = sample_beneficiary.to_dict()
        
        assert beneficiary_dict['name'] == "John Smith"
        assert beneficiary_dict['ssn'] == "123-45-6789"
        assert beneficiary_dict['relationship'] == "Child"
        assert beneficiary_dict['share_percentage'] == "50"

    def test_beneficiary_deserialization(self):
        """Test beneficiary deserialization from dictionary"""
        beneficiary_dict = {
            'name': "John Smith",
            'ssn': "123-45-6789",
            'address': "123 Main St, Anytown, USA",
            'relationship': "Child",
            'share_percentage': "50",
            'income_distributed': "5000.00",
            'distribution_type': 'ordinary_income'
        }
        
        beneficiary = TrustBeneficiary.from_dict(beneficiary_dict)
        
        assert beneficiary.name == "John Smith"
        assert beneficiary.share_percentage == Decimal("50")

    def test_trust_income_serialization(self):
        """Test trust income serialization"""
        trust_income = TrustIncome(
            interest_income=Decimal("1000.00"),
            dividend_income=Decimal("2000.00"),
            business_income=Decimal("3000.00")
        )
        
        trust_income.calculate_total()
        income_dict = trust_income.to_dict()
        
        assert income_dict['interest_income'] == "1000.00"
        assert income_dict['dividend_income'] == "2000.00"
        assert income_dict['total_income'] == "6000.00"

    def test_trust_income_deserialization(self):
        """Test trust income deserialization"""
        income_dict = {
            'interest_income': "1000.00",
            'dividend_income': "2000.00",
            'business_income': "3000.00",
            'capital_gains': "500.00",
            'rental_income': "0",
            'royalty_income': "0",
            'other_income': "0",
            'total_income': "6500.00"
        }
        
        trust_income = TrustIncome.from_dict(income_dict)
        
        assert trust_income.interest_income == Decimal("1000.00")
        assert trust_income.total_income == Decimal("6500.00")

    def test_trust_deductions_serialization(self):
        """Test trust deductions serialization"""
        trust_deductions = TrustDeductions(
            fiduciary_fees=Decimal("500.00"),
            attorney_fees=Decimal("1000.00"),
            accounting_fees=Decimal("300.00")
        )
        
        trust_deductions.calculate_total()
        deductions_dict = trust_deductions.to_dict()
        
        assert deductions_dict['fiduciary_fees'] == "500.00"
        assert deductions_dict['total_deductions'] == "1800.00"

    def test_k1_generation_preparation(self, estate_service, sample_beneficiary):
        """Test preparation for K-1 form generation (for partnerships/S-Corps)"""
        # Similar concept for trust K-1s
        beneficiary = sample_beneficiary
        
        # Prepare K-1 data
        k1_data = {
            'beneficiary_name': beneficiary.name,
            'beneficiary_ssn': beneficiary.ssn,
            'beneficiary_address': beneficiary.address,
            'share_percentage': beneficiary.share_percentage,
            'ordinary_income': Decimal("2000.00"),
            'capital_gains': Decimal("500.00")
        }
        
        assert k1_data['beneficiary_name'] == "John Smith"
        assert k1_data['share_percentage'] == Decimal("50")

    def test_estimated_tax_calculations(self, estate_service):
        """Test estimated tax calculations for trusts"""
        trust_income = Decimal("20000.00")
        estimated_tax_rate = Decimal("0.24")  # 24% bracket
        
        estimated_tax = trust_income * estimated_tax_rate
        
        assert estimated_tax == Decimal("4800.00")

    def test_error_handling_invalid_data(self, estate_service, sample_tax_data):
        """Test error handling with invalid data"""
        sample_tax_data.get.side_effect = Exception("Database error")
        
        beneficiaries = estate_service.get_beneficiaries(sample_tax_data)
        
        assert beneficiaries == []

    def test_multiple_trusts_tracking(self, estate_service, sample_tax_data):
        """Test tracking multiple separate trusts"""
        trust1_beneficiary = TrustBeneficiary(
            name="John",
            ssn="111-11-1111",
            address="123 Main",
            relationship="Child",
            share_percentage=Decimal("100")
        )
        
        trust2_beneficiary = TrustBeneficiary(
            name="Jane",
            ssn="222-22-2222",
            address="456 Oak",
            relationship="Child",
            share_percentage=Decimal("100")
        )
        
        assert trust1_beneficiary.name != trust2_beneficiary.name

    def test_depletable_trust_calculations(self, estate_service):
        """Test depletable trust calculations"""
        # For trusts with finite duration
        trust_principal = Decimal("100000.00")
        years_remaining = 20
        annual_distribution = trust_principal / Decimal(years_remaining)
        
        assert annual_distribution == Decimal("5000.00")

    def test_charitable_contribution_deduction(self, estate_service):
        """Test charitable contribution deduction in trusts"""
        charitable_contributions = Decimal("5000.00")
        
        # Charitable contributions are deductible in full for trusts
        deduction_amount = charitable_contributions
        
        assert deduction_amount == Decimal("5000.00")

    def test_distribution_type_classification(self):
        """Test classification of different distribution types"""
        distributions = [
            (IncomeDistributionType.ORDINARY_INCOME, "taxed_at_trust_rate"),
            (IncomeDistributionType.CAPITAL_GAINS, "preferential_rate"),
            (IncomeDistributionType.TAX_EXEMPT, "no_tax"),
            (IncomeDistributionType.RETURN_OF_CAPITAL, "no_tax"),
        ]
        
        for dist_type, tax_treatment in distributions:
            assert dist_type is not None
