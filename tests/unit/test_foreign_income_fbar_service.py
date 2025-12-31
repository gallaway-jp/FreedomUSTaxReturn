"""
Unit tests for Foreign Income and FBAR Service
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import date, datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.foreign_income_fbar_service import (
    ForeignIncomeFBARService,
    ForeignAccount,
    ForeignIncome,
    ForeignAccountType,
    FBARThreshold
)


class TestForeignIncomeFBARService:
    """Test cases for Foreign Income FBAR Service"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return AppConfig()

    @pytest.fixture
    def tax_data(self):
        """Create test tax data"""
        return TaxData()

    @pytest.fixture
    def service(self, config):
        """Create service instance"""
        return ForeignIncomeFBARService(config)

    def test_service_initialization(self, service):
        """Test service initializes correctly"""
        assert service is not None
        assert service.config is not None

    def test_fbar_thresholds(self, service):
        """Test FBAR threshold values"""
        # Test 2025 threshold for single filer
        threshold_single = FBARThreshold.SINGLE_2025.value
        assert threshold_single == 10000

        # Test 2025 threshold for married filer
        threshold_married = FBARThreshold.MARRIED_2025.value
        assert threshold_married == 20000

    def test_validate_foreign_account_data(self, service):
        """Test foreign account data validation"""
        # Valid account
        valid_account = ForeignAccount(
            account_number="123456789",
            institution_name="Test Bank",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="Canada",
            currency="CAD",
            max_value_during_year=Decimal("15000.00"),
            year_end_value=Decimal("12000.00"),
            was_closed=False
        )

        errors = service.validate_foreign_account_data(valid_account)
        assert len(errors) == 0

        # Invalid account - missing required fields
        invalid_account = ForeignAccount(
            account_number="",
            institution_name="",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="",
            currency="USD",
            max_value_during_year=Decimal("5000.00"),
            year_end_value=Decimal("4000.00"),
            was_closed=False
        )

        errors = service.validate_foreign_account_data(invalid_account)
        assert len(errors) > 0
        assert any("account number" in error.lower() for error in errors)
        assert any("institution name" in error.lower() for error in errors)
        assert any("country" in error.lower() for error in errors)

    def test_is_fbar_required(self, service, tax_data):
        """Test FBAR requirement determination"""
        tax_year = 2025

        # No accounts - FBAR not required
        required, reason = service.is_fbar_required(tax_data, tax_year)
        assert not required
        assert "below" in reason.lower() and "threshold" in reason.lower()

        # Add account below threshold
        account = ForeignAccount(
            account_number="123456789",
            institution_name="Test Bank",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="Canada",
            currency="CAD",
            max_value_during_year=Decimal("5000.00"),
            year_end_value=Decimal("4000.00"),
            was_closed=False
        )

        service.add_foreign_account(tax_data, account)

        required, reason = service.is_fbar_required(tax_data, tax_year)
        assert not required
        assert "below" in reason.lower() and "threshold" in reason.lower()

        # Add account above threshold
        large_account = ForeignAccount(
            account_number="987654321",
            institution_name="Big Bank",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="Switzerland",
            currency="CHF",
            max_value_during_year=Decimal("20000.00"),
            year_end_value=Decimal("18000.00"),
            was_closed=False
        )

        service.add_foreign_account(tax_data, large_account)

        required, reason = service.is_fbar_required(tax_data, tax_year)
        assert required
        assert "exceeds" in reason.lower() and "threshold" in reason.lower()

    def test_calculate_foreign_tax_credit(self, service, tax_data):
        """Test foreign tax credit calculation"""
        tax_year = 2024

        # Add foreign income with withholding
        income = ForeignIncome(
            source_type="dividends",
            country="Germany",
            amount_usd=Decimal("10000.00"),
            amount_foreign=Decimal("8500.00"),
            currency="EUR",
            withholding_tax=Decimal("500.00"),
            description="German dividends"
        )

        service.add_foreign_income(tax_data, income)

        credit_info = service.calculate_foreign_tax_credit(tax_data, tax_year)

        assert credit_info is not None
        assert credit_info['total_foreign_income'] == Decimal("10000.00")
        assert credit_info['total_withholding_tax'] == Decimal("500.00")
        assert 'foreign_tax_credit_limit' in credit_info
        assert 'available_credit' in credit_info

    def test_generate_fbar_summary(self, service, tax_data):
        """Test FBAR summary generation"""
        tax_year = 2025

        # Add accounts
        account1 = ForeignAccount(
            account_number="111111111",
            institution_name="Bank A",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="Canada",
            currency="CAD",
            max_value_during_year=Decimal("15000.00"),
            year_end_value=Decimal("12000.00"),
            was_closed=False
        )

        account2 = ForeignAccount(
            account_number="222222222",
            institution_name="Bank B",
            account_type=ForeignAccountType.SECURITIES_ACCOUNT,
            country="UK",
            currency="GBP",
            max_value_during_year=Decimal("25000.00"),
            year_end_value=Decimal("22000.00"),
            was_closed=False
        )

        service.add_foreign_account(tax_data, account1)
        service.add_foreign_account(tax_data, account2)

        summary = service.generate_fbar_summary(tax_data, tax_year)

        assert summary is not None
        assert summary['total_accounts'] == 2
        assert summary['total_max_value'] == Decimal("40000.00")
        assert summary['total_year_end_value'] == Decimal("34000.00")
        assert summary['fbar_required'] is True
        assert len(summary['accounts_by_country']) == 2
        assert 'Canada' in summary['accounts_by_country']
        assert 'UK' in summary['accounts_by_country']

    def test_get_fbar_filing_instructions(self, service):
        """Test FBAR filing instructions"""
        instructions = service.get_fbar_filing_instructions()

        assert instructions is not None
        assert len(instructions) > 0
        assert "FBAR" in instructions
        assert "foreign financial account" in instructions.lower()

    def test_add_and_get_foreign_accounts(self, service, tax_data):
        """Test adding and retrieving foreign accounts"""
        # Initially empty
        accounts = service.get_foreign_accounts(tax_data)
        assert len(accounts) == 0

        # Add account
        account = ForeignAccount(
            account_number="123456789",
            institution_name="Test Bank",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="Canada",
            currency="CAD",
            max_value_during_year=Decimal("10000.00"),
            year_end_value=Decimal("8000.00"),
            was_closed=False
        )

        success = service.add_foreign_account(tax_data, account)
        assert success

        # Retrieve accounts
        accounts = service.get_foreign_accounts(tax_data)
        assert len(accounts) == 1
        assert accounts[0].account_number == "123456789"
        assert accounts[0].institution_name == "Test Bank"

    def test_add_and_get_foreign_income(self, service, tax_data):
        """Test adding and retrieving foreign income"""
        # Initially empty
        income_list = service.get_foreign_income(tax_data)
        assert len(income_list) == 0

        # Add income
        income = ForeignIncome(
            source_type="interest",
            country="Germany",
            amount_usd=Decimal("2000.00"),
            amount_foreign=Decimal("1700.00"),
            currency="EUR",
            withholding_tax=Decimal("100.00"),
            description="Savings interest"
        )

        success = service.add_foreign_income(tax_data, income)
        assert success

        # Retrieve income
        income_list = service.get_foreign_income(tax_data)
        assert len(income_list) == 1
        assert income_list[0].source_type == "interest"
        assert income_list[0].country == "Germany"
        assert income_list[0].amount_usd == Decimal("2000.00")

    def test_duplicate_account_prevention(self, service, tax_data):
        """Test that duplicate accounts are prevented"""
        account = ForeignAccount(
            account_number="123456789",
            institution_name="Test Bank",
            account_type=ForeignAccountType.BANK_ACCOUNT,
            country="Canada",
            currency="CAD",
            max_value_during_year=Decimal("10000.00"),
            year_end_value=Decimal("8000.00"),
            was_closed=False
        )

        # Add first time - should succeed
        success1 = service.add_foreign_account(tax_data, account)
        assert success1

        # Add second time - should fail
        success2 = service.add_foreign_account(tax_data, account)
        assert not success2

    def test_account_type_enum_values(self):
        """Test ForeignAccountType enum values"""
        assert ForeignAccountType.BANK_ACCOUNT.value == "bank_account"
        assert ForeignAccountType.SECURITIES_ACCOUNT.value == "securities_account"
        assert ForeignAccountType.MUTUAL_FUND.value == "mutual_fund"
        assert ForeignAccountType.TRUST.value == "trust"

    def test_fbar_threshold_enum_values(self):
        """Test FBARThreshold enum values"""
        assert FBARThreshold.SINGLE_2025.value == 10000
        assert FBARThreshold.MARRIED_2025.value == 20000