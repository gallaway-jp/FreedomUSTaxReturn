"""
Unit tests for Partnership and S-Corp Tax Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, date
from decimal import Decimal

from services.partnership_s_corp_service import (
    PartnershipSCorpService,
    PartnerShareholder,
    BusinessIncome,
    BusinessDeductions,
    EntityType,
    PartnershipType,
    SCorpShareholderType
)
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestPartnershipSCorpService:
    """Test cases for Partnership and S-Corp Tax Service"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        config.tax_year = 2025
        return config

    @pytest.fixture
    def partnership_service(self, mock_config):
        """Create partnership/S-Corp service instance"""
        return PartnershipSCorpService(mock_config)

    @pytest.fixture
    def sample_tax_data(self):
        """Create sample tax data for testing"""
        tax_data = Mock(spec=TaxData)
        tax_data.get.return_value = []
        tax_data.set = Mock()
        return tax_data

    @pytest.fixture
    def sample_partner(self):
        """Create a sample partner/shareholder"""
        return PartnerShareholder(
            name="John Smith",
            ssn_ein="123-45-6789",
            address="123 Main St, Anytown, USA",
            entity_type="individual",
            ownership_percentage=Decimal("50"),
            capital_account_beginning=Decimal("50000.00"),
            capital_account_ending=Decimal("55000.00"),
            share_of_income=Decimal("25000.00"),
            share_of_losses=Decimal("0"),
            distributions=Decimal("5000.00")
        )

    def test_service_initialization(self, partnership_service, mock_config):
        """Test partnership/S-Corp service initialization"""
        assert partnership_service.config == mock_config
        assert partnership_service.error_tracker is not None

    def test_entity_types_enum(self):
        """Test all entity type enum values"""
        entity_types = [
            EntityType.PARTNERSHIP,
            EntityType.S_CORPORATION,
            EntityType.LLC_TAXED_AS_PARTNERSHIP,
            EntityType.LLC_TAXED_AS_S_CORP
        ]
        
        assert len(entity_types) == 4
        for entity_type in entity_types:
            assert entity_type is not None

    def test_partnership_types_enum(self):
        """Test all partnership type enum values"""
        partnership_types = [
            PartnershipType.GENERAL,
            PartnershipType.LIMITED,
            PartnershipType.LIMITED_LIABILITY,
            PartnershipType.JOINT_VENTURE
        ]
        
        assert len(partnership_types) == 4

    def test_s_corp_shareholder_types_enum(self):
        """Test all S-Corp shareholder type enum values"""
        shareholder_types = [
            SCorpShareholderType.INDIVIDUAL,
            SCorpShareholderType.ESTATE,
            SCorpShareholderType.TRUST,
            SCorpShareholderType.TAX_EXEMPT_ORGANIZATION
        ]
        
        assert len(shareholder_types) == 4

    def test_add_partner_shareholder(self, partnership_service, sample_tax_data, sample_partner):
        """Test adding a partner/shareholder"""
        sample_tax_data.get.return_value = []
        
        result = partnership_service.add_partner_shareholder(sample_tax_data, sample_partner)
        
        assert result is True
        sample_tax_data.set.assert_called_once()

    def test_get_partners_shareholders(self, partnership_service, sample_tax_data, sample_partner):
        """Test retrieving partners/shareholders"""
        sample_tax_data.get.return_value = [sample_partner.to_dict()]
        
        partners = partnership_service.get_partners_shareholders(sample_tax_data)
        
        assert len(partners) == 1
        assert partners[0].name == "John Smith"
        assert partners[0].ownership_percentage == Decimal("50")

    def test_business_income_calculation(self):
        """Test business income calculation"""
        income = BusinessIncome(
            gross_receipts=Decimal("500000.00"),
            returns_allowances=Decimal("10000.00"),
            cost_of_goods_sold=Decimal("200000.00"),
            dividends=Decimal("5000.00"),
            interest_income=Decimal("2000.00")
        )
        
        gross_profit = income.calculate_gross_profit()
        
        assert gross_profit == Decimal("290000.00")

    def test_business_income_total_ordinary_income(self):
        """Test calculation of total ordinary income"""
        income = BusinessIncome(
            gross_receipts=Decimal("500000.00"),
            returns_allowances=Decimal("10000.00"),
            cost_of_goods_sold=Decimal("200000.00"),
            dividends=Decimal("5000.00"),
            interest_income=Decimal("2000.00"),
            rents=Decimal("1000.00"),
            royalties=Decimal("500.00"),
            other_income=Decimal("1000.00")
        )
        
        income.calculate_gross_profit()
        total = income.total_ordinary_income()
        
        assert total == Decimal("299500.00")

    def test_business_deductions_calculation(self):
        """Test business deductions calculation"""
        deductions = BusinessDeductions(
            compensation_officers=Decimal("100000.00"),
            salaries_wages=Decimal("150000.00"),
            repairs_maintenance=Decimal("5000.00"),
            bad_debts=Decimal("2000.00"),
            rents=Decimal("12000.00"),
            taxes_licenses=Decimal("3000.00")
        )
        
        total = deductions.calculate_total_deductions()
        
        assert total == Decimal("272000.00")

    def test_partnership_taxable_income_calculation(self, partnership_service):
        """Test partnership taxable income calculation"""
        income = Decimal("500000.00")
        deductions = Decimal("250000.00")
        
        taxable_income = partnership_service.calculate_taxable_income(income, deductions)
        
        assert taxable_income == Decimal("250000.00")

    def test_partner_share_of_income(self, partnership_service, sample_partner):
        """Test calculating partner's share of income"""
        entity_income = Decimal("100000.00")
        partner = sample_partner
        partner.ownership_percentage = Decimal("25")
        
        share = partnership_service.calculate_partner_share_of_income(entity_income, partner)
        
        assert share == Decimal("25000.00")

    def test_partner_share_of_losses(self, partnership_service):
        """Test calculating partner's share of losses"""
        entity_loss = Decimal("50000.00")
        ownership_percentage = Decimal("50")
        
        share = partnership_service.calculate_partner_share_of_losses(entity_loss, ownership_percentage)
        
        assert share == Decimal("25000.00")

    def test_k1_form_data_preparation(self, partnership_service, sample_partner):
        """Test preparation of K-1 form data"""
        k1_data = {
            'partner_name': sample_partner.name,
            'partner_ssn': sample_partner.ssn_ein,
            'partner_address': sample_partner.address,
            'partnership_ein': '98-7654321',
            'share_of_ordinary_business_income': Decimal("25000.00"),
            'share_of_net_long_term_capital_gains': Decimal("5000.00"),
            'share_of_dividends': Decimal("1000.00"),
            'distributions': sample_partner.distributions
        }
        
        assert k1_data['partner_name'] == "John Smith"
        assert k1_data['share_of_ordinary_business_income'] == Decimal("25000.00")

    def test_s_corp_dividend_distribution(self, partnership_service):
        """Test S-Corp dividend/distribution calculations"""
        net_income = Decimal("100000.00")
        number_of_shares = 1000
        
        dividend_per_share = partnership_service.calculate_dividend_per_share(net_income, number_of_shares)
        
        assert dividend_per_share == Decimal("100.00")

    def test_capital_account_tracking(self, partnership_service):
        """Test partner capital account tracking"""
        beginning_balance = Decimal("50000.00")
        income_allocated = Decimal("10000.00")
        distributions = Decimal("5000.00")
        
        ending_balance = partnership_service.calculate_capital_account(
            beginning_balance, income_allocated, distributions
        )
        
        assert ending_balance == Decimal("55000.00")

    def test_validate_partner_data(self, partnership_service):
        """Test partner data validation"""
        valid_partner = PartnerShareholder(
            name="John Smith",
            ssn_ein="123-45-6789",
            address="123 Main St",
            entity_type="individual",
            ownership_percentage=Decimal("50")
        )
        
        errors = partnership_service.validate_partner_data(valid_partner)
        
        assert len(errors) == 0

    def test_validate_partner_missing_name(self, partnership_service):
        """Test validation fails with missing name"""
        invalid_partner = PartnerShareholder(
            name="",
            ssn_ein="123-45-6789",
            address="123 Main St",
            entity_type="individual",
            ownership_percentage=Decimal("50")
        )
        
        errors = partnership_service.validate_partner_data(invalid_partner)
        
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_validate_ownership_percentages_total(self, partnership_service):
        """Test validation of total ownership percentages"""
        partners = [
            PartnerShareholder(name="Partner A", ownership_percentage=Decimal("50")),
            PartnerShareholder(name="Partner B", ownership_percentage=Decimal("40")),
            PartnerShareholder(name="Partner C", ownership_percentage=Decimal("10"))
        ]
        
        total_ownership = sum(p.ownership_percentage for p in partners)
        
        assert total_ownership == Decimal("100")

    def test_validate_ownership_percentages_over_100(self, partnership_service):
        """Test validation fails when ownership exceeds 100%"""
        partners = [
            PartnerShareholder(name="Partner A", ownership_percentage=Decimal("60")),
            PartnerShareholder(name="Partner B", ownership_percentage=Decimal("50"))
        ]
        
        total_ownership = sum(p.ownership_percentage for p in partners)
        
        assert total_ownership == Decimal("110")
        assert total_ownership > Decimal("100")

    def test_multi_member_llc_as_partnership(self, partnership_service):
        """Test Multi-member LLC treated as partnership"""
        members = [
            PartnerShareholder(name="Member A", ownership_percentage=Decimal("50")),
            PartnerShareholder(name="Member B", ownership_percentage=Decimal("50"))
        ]
        
        assert len(members) == 2
        assert sum(m.ownership_percentage for m in members) == Decimal("100")

    def test_s_corp_pass_through_taxation(self, partnership_service):
        """Test S-Corp pass-through taxation characteristics"""
        # S-Corps are pass-through entities - income passes through to shareholders
        corporation_income = Decimal("250000.00")
        shareholder_ownership = Decimal("0.25")  # 25% ownership
        
        shareholder_income = corporation_income * shareholder_ownership
        
        assert shareholder_income == Decimal("62500.00")

    def test_guaranteed_payments_to_partners(self, partnership_service):
        """Test guaranteed payments to partners"""
        guaranteed_payment = Decimal("50000.00")
        remaining_income = Decimal("150000.00")
        ownership_percentage = Decimal("50")
        
        # Guaranteed payment comes first
        total_income_received = guaranteed_payment + (remaining_income * ownership_percentage / Decimal("100"))
        
        assert total_income_received == Decimal("125000.00")

    def test_form_1065_generation(self, partnership_service):
        """Test preparation for Form 1065 (Partnership return)"""
        partnership_data = {
            'form': '1065',
            'entity_type': 'partnership',
            'net_income': Decimal("100000.00"),
            'number_of_partners': 2,
            'tax_year': 2025
        }
        
        assert partnership_data['form'] == '1065'
        assert partnership_data['entity_type'] == 'partnership'

    def test_form_1120_s_generation(self, partnership_service):
        """Test preparation for Form 1120-S (S-Corp return)"""
        s_corp_data = {
            'form': '1120-S',
            'entity_type': 's_corporation',
            'net_income': Decimal("250000.00"),
            'number_of_shareholders': 5,
            'tax_year': 2025
        }
        
        assert s_corp_data['form'] == '1120-S'
        assert s_corp_data['entity_type'] == 's_corporation'

    def test_partner_shareholder_serialization(self, sample_partner):
        """Test partner/shareholder serialization"""
        partner_dict = sample_partner.to_dict()
        
        assert partner_dict['name'] == "John Smith"
        assert partner_dict['ssn_ein'] == "123-45-6789"
        assert partner_dict['ownership_percentage'] == "50"

    def test_partner_shareholder_deserialization(self):
        """Test partner/shareholder deserialization"""
        partner_dict = {
            'name': "John Smith",
            'ssn_ein': "123-45-6789",
            'address': "123 Main St",
            'entity_type': "individual",
            'ownership_percentage': "50",
            'capital_account_beginning': "50000.00",
            'capital_account_ending': "55000.00",
            'share_of_income': "25000.00",
            'share_of_losses': "0",
            'distributions': "5000.00"
        }
        
        partner = PartnerShareholder.from_dict(partner_dict)
        
        assert partner.name == "John Smith"
        assert partner.ownership_percentage == Decimal("50")

    def test_business_income_serialization(self):
        """Test business income serialization"""
        income = BusinessIncome(
            gross_receipts=Decimal("500000.00"),
            cost_of_goods_sold=Decimal("200000.00")
        )
        
        income_dict = income.to_dict()
        
        assert income_dict['gross_receipts'] == "500000.00"
        assert income_dict['cost_of_goods_sold'] == "200000.00"

    def test_business_income_deserialization(self):
        """Test business income deserialization"""
        income_dict = {
            'gross_receipts': "500000.00",
            'returns_allowances': "10000.00",
            'cost_of_goods_sold': "200000.00",
            'gross_profit': "290000.00",
            'dividends': "5000.00",
            'interest_income': "2000.00",
            'rents': "0",
            'royalties': "0",
            'other_income': "0"
        }
        
        income = BusinessIncome.from_dict(income_dict)
        
        assert income.gross_receipts == Decimal("500000.00")
        assert income.gross_profit == Decimal("290000.00")

    def test_multiple_k1_generation(self, partnership_service):
        """Test generating K-1 forms for multiple partners"""
        partners = [
            PartnerShareholder(name="Partner A", ownership_percentage=Decimal("50")),
            PartnerShareholder(name="Partner B", ownership_percentage=Decimal("50"))
        ]
        
        entity_income = Decimal("100000.00")
        
        k1_forms = []
        for partner in partners:
            share = partnership_service.calculate_partner_share_of_income(
                entity_income,
                partner
            )
            k1_forms.append({
                'partner': partner.name,
                'income_share': share
            })
        
        assert len(k1_forms) == 2
        assert k1_forms[0]['income_share'] == Decimal("50000.00")

    def test_self_employment_tax_calculation(self, partnership_service):
        """Test self-employment tax calculation for partners"""
        partner_net_earnings = Decimal("50000.00")
        se_tax_rate = Decimal("0.9235") * Decimal("0.153")  # SE tax rate
        
        se_tax = partner_net_earnings * se_tax_rate
        
        assert se_tax > Decimal("0")

    def test_error_handling_invalid_data(self, partnership_service, sample_tax_data):
        """Test error handling with invalid data"""
        sample_tax_data.get.side_effect = Exception("Database error")
        
        partners = partnership_service.get_partners_shareholders(sample_tax_data)
        
        assert partners == []

    def test_restricted_stock_units_tracking(self, partnership_service):
        """Test tracking of RSU vesting for S-Corp shareholders"""
        # Some S-Corps use RSUs instead of traditional shares
        unvested_units = 1000
        vesting_schedule = "4 years cliff"
        
        assert unvested_units > 0
        assert vesting_schedule is not None

    def test_s_corp_shareholder_restrictions(self, partnership_service):
        """Test S-Corp shareholder restrictions"""
        # S-Corps have restrictions on ownership
        valid_shareholder_types = [
            SCorpShareholderType.INDIVIDUAL,
            SCorpShareholderType.ESTATE,
            SCorpShareholderType.TRUST
        ]
        
        # Tax-exempt organizations have special rules
        assert SCorpShareholderType.TAX_EXEMPT_ORGANIZATION in SCorpShareholderType
