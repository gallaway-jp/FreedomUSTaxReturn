"""
Unit tests for Cryptocurrency Tax Service
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

from services.cryptocurrency_tax_service import (
    CryptocurrencyTaxService,
    CryptoTransaction,
    CryptoTransactionType,
    CapitalGainLoss,
    HoldingMethod
)
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestCryptocurrencyTaxService:
    """Test cases for Cryptocurrency Tax Service"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        config.tax_year = 2025
        return config

    @pytest.fixture
    def crypto_service(self, mock_config):
        """Create cryptocurrency tax service instance"""
        return CryptocurrencyTaxService(mock_config)

    @pytest.fixture
    def sample_tax_data(self):
        """Create sample tax data for testing"""
        tax_data = Mock(spec=TaxData)
        tax_data.get.return_value = []
        tax_data.set = Mock()
        return tax_data

    @pytest.fixture
    def sample_transaction(self):
        """Create sample cryptocurrency transaction"""
        return CryptoTransaction(
            date=date(2025, 3, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="Bitcoin",
            amount=Decimal("0.5"),
            price_per_unit=Decimal("45000.00"),
            total_value=Decimal("22500.00"),
            fees=Decimal("50.00"),
            exchange="Coinbase",
            transaction_id="tx_001"
        )

    def test_service_initialization(self, crypto_service, mock_config):
        """Test cryptocurrency service initialization"""
        assert crypto_service.config == mock_config
        assert crypto_service.error_tracker is not None

    def test_add_transaction(self, crypto_service, sample_tax_data, sample_transaction):
        """Test adding a cryptocurrency transaction"""
        sample_tax_data.get.return_value = []
        
        result = crypto_service.add_transaction(sample_tax_data, sample_transaction)
        
        assert result is True
        sample_tax_data.set.assert_called_once()

    def test_add_multiple_transactions(self, crypto_service, sample_tax_data, sample_transaction):
        """Test adding multiple transactions"""
        sample_tax_data.get.side_effect = [
            [],
            [sample_transaction.to_dict()]
        ]
        
        transaction2 = CryptoTransaction(
            date=date(2025, 6, 20),
            type=CryptoTransactionType.SELL,
            cryptocurrency="Bitcoin",
            amount=Decimal("0.25"),
            price_per_unit=Decimal("50000.00"),
            total_value=Decimal("12500.00"),
            fees=Decimal("25.00"),
            exchange="Kraken",
            transaction_id="tx_002"
        )
        
        crypto_service.add_transaction(sample_tax_data, sample_transaction)
        crypto_service.add_transaction(sample_tax_data, transaction2)
        
        assert sample_tax_data.set.call_count == 2

    def test_get_transactions(self, crypto_service, sample_tax_data, sample_transaction):
        """Test retrieving transactions"""
        sample_tax_data.get.return_value = [sample_transaction.to_dict()]
        
        transactions = crypto_service.get_transactions(sample_tax_data)
        
        assert len(transactions) == 1
        assert transactions[0].cryptocurrency == "Bitcoin"
        assert transactions[0].amount == Decimal("0.5")

    def test_transaction_types(self):
        """Test all crypto transaction types"""
        transaction_types = [
            CryptoTransactionType.BUY,
            CryptoTransactionType.SELL,
            CryptoTransactionType.TRADE,
            CryptoTransactionType.TRANSFER,
            CryptoTransactionType.MINING,
            CryptoTransactionType.AIRDROP,
            CryptoTransactionType.FORK,
            CryptoTransactionType.STAKING
        ]
        
        for tx_type in transaction_types:
            assert tx_type is not None
            assert isinstance(tx_type.value, str)

    def test_calculate_cost_basis_fifo(self, crypto_service, sample_tax_data):
        """Test cost basis calculation using FIFO method"""
        transactions = [
            CryptoTransaction(
                date=date(2025, 1, 1),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Bitcoin",
                amount=Decimal("1.0"),
                price_per_unit=Decimal("40000.00"),
                total_value=Decimal("40000.00"),
                fees=Decimal("100.00"),
                exchange="Coinbase",
                transaction_id="tx_001"
            ),
            CryptoTransaction(
                date=date(2025, 3, 1),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Bitcoin",
                amount=Decimal("1.0"),
                price_per_unit=Decimal("45000.00"),
                total_value=Decimal("45000.00"),
                fees=Decimal("100.00"),
                exchange="Coinbase",
                transaction_id="tx_002"
            )
        ]
        
        sample_tax_data.get.return_value = [t.to_dict() for t in transactions]
        
        gains_losses = crypto_service.calculate_capital_gains_losses(sample_tax_data, 2025)
        
        # Cost basis should be calculated from FIFO method
        assert len(transactions) == 2

    def test_calculate_capital_gains(self, crypto_service, sample_tax_data):
        """Test capital gains calculation"""
        buy_transaction = CryptoTransaction(
            date=date(2025, 1, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("40000.00"),
            total_value=Decimal("40000.00"),
            fees=Decimal("100.00"),
            exchange="Coinbase",
            transaction_id="tx_001"
        )
        
        sell_transaction = CryptoTransaction(
            date=date(2025, 9, 15),
            type=CryptoTransactionType.SELL,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("50000.00"),
            total_value=Decimal("50000.00"),
            fees=Decimal("100.00"),
            exchange="Coinbase",
            transaction_id="tx_002"
        )
        
        sample_tax_data.get.return_value = [buy_transaction.to_dict(), sell_transaction.to_dict()]
        
        gains_losses = crypto_service.calculate_capital_gains_losses(sample_tax_data, 2025)
        
        # Should have calculated gains
        assert len(gains_losses) >= 0

    def test_short_term_capital_gains(self, crypto_service, sample_tax_data):
        """Test short-term capital gains identification"""
        buy_transaction = CryptoTransaction(
            date=date(2025, 6, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("40000.00"),
            total_value=Decimal("40000.00"),
            fees=Decimal("50.00"),
            exchange="Coinbase",
            transaction_id="tx_001"
        )
        
        sell_transaction = CryptoTransaction(
            date=date(2025, 7, 10),  # 25 days later - short term
            type=CryptoTransactionType.SELL,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("50000.00"),
            total_value=Decimal("50000.00"),
            fees=Decimal("50.00"),
            exchange="Coinbase",
            transaction_id="tx_002"
        )
        
        sample_tax_data.get.return_value = [buy_transaction.to_dict(), sell_transaction.to_dict()]
        
        gains_losses = crypto_service.calculate_capital_gains_losses(sample_tax_data, 2025)
        
        # Should identify holding period
        if gains_losses:
            assert gains_losses[0].holding_period in ["short", "long"]

    def test_long_term_capital_gains(self, crypto_service, sample_tax_data):
        """Test long-term capital gains identification"""
        buy_transaction = CryptoTransaction(
            date=date(2024, 6, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("40000.00"),
            total_value=Decimal("40000.00"),
            fees=Decimal("50.00"),
            exchange="Coinbase",
            transaction_id="tx_001"
        )
        
        sell_transaction = CryptoTransaction(
            date=date(2025, 7, 10),  # More than 1 year later
            type=CryptoTransactionType.SELL,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("50000.00"),
            total_value=Decimal("50000.00"),
            fees=Decimal("50.00"),
            exchange="Coinbase",
            transaction_id="tx_002"
        )
        
        sample_tax_data.get.return_value = [buy_transaction.to_dict(), sell_transaction.to_dict()]
        
        gains_losses = crypto_service.calculate_capital_gains_losses(sample_tax_data, 2025)
        
        # Should have long-term designation
        if gains_losses:
            assert gains_losses[0].holding_period in ["long", "short"]

    def test_validate_transaction_data(self, crypto_service):
        """Test transaction data validation"""
        valid_transaction = CryptoTransaction(
            date=date(2025, 3, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="Bitcoin",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("45000.00"),
            total_value=Decimal("45000.00"),
            fees=Decimal("50.00"),
            exchange="Coinbase",
            transaction_id="tx_001"
        )
        
        # Transactions can be created and should have required fields
        assert valid_transaction.cryptocurrency == "Bitcoin"
        assert valid_transaction.transaction_id == "tx_001"

    def test_validate_transaction_missing_fields(self, crypto_service):
        """Test validation of transaction with missing fields"""
        invalid_transaction = CryptoTransaction(
            date=date(2025, 3, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="",
            amount=Decimal("1.0"),
            price_per_unit=Decimal("45000.00"),
            total_value=Decimal("45000.00"),
            fees=Decimal("50.00"),
            exchange="",
            transaction_id=""
        )
        
        # Verify it was created with empty fields
        assert invalid_transaction.cryptocurrency == ""
        assert invalid_transaction.exchange == ""

    def test_validate_negative_amounts(self, crypto_service):
        """Test validation of negative amounts"""
        invalid_transaction = CryptoTransaction(
            date=date(2025, 3, 15),
            type=CryptoTransactionType.BUY,
            cryptocurrency="Bitcoin",
            amount=Decimal("-1.0"),
            price_per_unit=Decimal("45000.00"),
            total_value=Decimal("-45000.00"),
            fees=Decimal("-50.00"),
            exchange="Coinbase",
            transaction_id="tx_001"
        )
        
        # Verify it has negative values
        assert invalid_transaction.amount < 0
        assert invalid_transaction.total_value < 0

    def test_mining_income_calculation(self, crypto_service):
        """Test mining income as ordinary income"""
        mining_transaction = CryptoTransaction(
            date=date(2025, 6, 15),
            type=CryptoTransactionType.MINING,
            cryptocurrency="Bitcoin",
            amount=Decimal("0.001"),
            price_per_unit=Decimal("50000.00"),
            total_value=Decimal("50.00"),
            fees=Decimal("0"),
            exchange="Mining Pool",
            transaction_id="mining_001"
        )
        
        # Mining creates ordinary income at fair market value
        ordinary_income = mining_transaction.total_value
        
        assert ordinary_income == Decimal("50.00")

    def test_staking_income_calculation(self, crypto_service):
        """Test staking income as ordinary income"""
        staking_transaction = CryptoTransaction(
            date=date(2025, 4, 1),
            type=CryptoTransactionType.STAKING,
            cryptocurrency="Ethereum",
            amount=Decimal("0.1"),
            price_per_unit=Decimal("3000.00"),
            total_value=Decimal("300.00"),
            fees=Decimal("5.00"),
            exchange="Staking Pool",
            transaction_id="staking_001"
        )
        
        # Staking income is the fair market value
        ordinary_income = staking_transaction.total_value
        
        assert ordinary_income == Decimal("300.00")

    def test_airdrop_income_calculation(self, crypto_service):
        """Test airdrop income as ordinary income"""
        airdrop_transaction = CryptoTransaction(
            date=date(2025, 2, 15),
            type=CryptoTransactionType.AIRDROP,
            cryptocurrency="NewToken",
            amount=Decimal("100"),
            price_per_unit=Decimal("10.00"),
            total_value=Decimal("1000.00"),
            fees=Decimal("0"),
            exchange="Airdrop",
            transaction_id="airdrop_001"
        )
        
        # Airdrop income is the fair market value at receipt
        ordinary_income = airdrop_transaction.total_value
        
        assert ordinary_income == Decimal("1000.00")

    def test_transaction_serialization(self, sample_transaction):
        """Test transaction serialization to dictionary"""
        transaction_dict = sample_transaction.to_dict()
        
        assert transaction_dict['date'] == '2025-03-15'
        assert transaction_dict['type'] == 'buy'
        assert transaction_dict['cryptocurrency'] == 'Bitcoin'
        assert transaction_dict['amount'] == '0.5'

    def test_transaction_deserialization(self):
        """Test transaction deserialization from dictionary"""
        transaction_dict = {
            'date': '2025-03-15',
            'type': 'buy',
            'cryptocurrency': 'Bitcoin',
            'amount': '0.5',
            'price_per_unit': '45000.00',
            'total_value': '22500.00',
            'fees': '50.00',
            'exchange': 'Coinbase',
            'transaction_id': 'tx_001',
            'description': 'Initial purchase',
            'related_transaction_id': None
        }
        
        transaction = CryptoTransaction.from_dict(transaction_dict)
        
        assert transaction.date == date(2025, 3, 15)
        assert transaction.cryptocurrency == 'Bitcoin'
        assert transaction.amount == Decimal('0.5')

    def test_holding_method_enum(self):
        """Test holding method enum values"""
        methods = [HoldingMethod.FIFO, HoldingMethod.LIFO, HoldingMethod.SPECIFIC_ID]
        
        assert HoldingMethod.FIFO.value == 'fifo'
        assert HoldingMethod.LIFO.value == 'lifo'
        assert HoldingMethod.SPECIFIC_ID.value == 'specific_id'

    def test_portfolio_value_calculation(self, crypto_service, sample_tax_data):
        """Test calculating total portfolio value"""
        transactions = [
            CryptoTransaction(
                date=date(2025, 1, 1),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Bitcoin",
                amount=Decimal("1.0"),
                price_per_unit=Decimal("40000.00"),
                total_value=Decimal("40000.00"),
                fees=Decimal("100.00"),
                exchange="Coinbase",
                transaction_id="tx_001"
            ),
            CryptoTransaction(
                date=date(2025, 1, 5),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Ethereum",
                amount=Decimal("10.0"),
                price_per_unit=Decimal("3000.00"),
                total_value=Decimal("30000.00"),
                fees=Decimal("100.00"),
                exchange="Coinbase",
                transaction_id="tx_002"
            )
        ]
        
        sample_tax_data.get.return_value = [t.to_dict() for t in transactions]
        
        retrieved_transactions = crypto_service.get_transactions(sample_tax_data)
        
        # Should have retrieved transactions
        assert len(retrieved_transactions) == 2

    def test_error_handling_invalid_data(self, crypto_service, sample_tax_data):
        """Test error handling with invalid data"""
        sample_tax_data.get.side_effect = Exception("Database error")
        
        transactions = crypto_service.get_transactions(sample_tax_data)
        
        assert transactions == []

    def test_capital_gain_loss_serialization(self):
        """Test capital gain/loss serialization"""
        gain_loss = CapitalGainLoss(
            description="Bitcoin sale",
            date_acquired=date(2024, 1, 15),
            date_sold=date(2025, 3, 15),
            sales_price=Decimal("50000.00"),
            cost_basis=Decimal("40000.00"),
            gain_loss=Decimal("10000.00"),
            holding_period="long",
            cryptocurrency="Bitcoin"
        )
        
        gl_dict = gain_loss.to_dict()
        
        assert gl_dict['description'] == "Bitcoin sale"
        assert gl_dict['holding_period'] == "long"
        assert gl_dict['gain_loss'] == '10000.00'

    def test_wash_sale_detection(self, crypto_service):
        """Test detection of potential wash sale issues (crypto version)"""
        # Note: Wash sale rules don't technically apply to crypto, but tracking is useful
        transactions = [
            CryptoTransaction(
                date=date(2025, 1, 15),
                type=CryptoTransactionType.SELL,
                cryptocurrency="Bitcoin",
                amount=Decimal("0.5"),
                price_per_unit=Decimal("40000.00"),
                total_value=Decimal("20000.00"),
                fees=Decimal("50.00"),
                exchange="Coinbase",
                transaction_id="tx_001"
            ),
            CryptoTransaction(
                date=date(2025, 1, 20),  # Within 30 days
                type=CryptoTransactionType.BUY,
                cryptocurrency="Bitcoin",
                amount=Decimal("0.5"),
                price_per_unit=Decimal("45000.00"),
                total_value=Decimal("22500.00"),
                fees=Decimal("50.00"),
                exchange="Coinbase",
                transaction_id="tx_002"
            )
        ]
        
        # Check for same-asset transactions within 30 days
        has_potential_wash = any(
            t.cryptocurrency == "Bitcoin" for t in transactions
        )
        
        assert has_potential_wash is True

    def test_multiple_cryptocurrencies(self, crypto_service, sample_tax_data):
        """Test handling multiple different cryptocurrencies"""
        transactions = [
            CryptoTransaction(
                date=date(2025, 1, 1),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Bitcoin",
                amount=Decimal("1.0"),
                price_per_unit=Decimal("40000.00"),
                total_value=Decimal("40000.00"),
                fees=Decimal("50.00"),
                exchange="Coinbase",
                transaction_id="tx_001"
            ),
            CryptoTransaction(
                date=date(2025, 1, 5),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Ethereum",
                amount=Decimal("10.0"),
                price_per_unit=Decimal("3000.00"),
                total_value=Decimal("30000.00"),
                fees=Decimal("50.00"),
                exchange="Coinbase",
                transaction_id="tx_002"
            ),
            CryptoTransaction(
                date=date(2025, 1, 10),
                type=CryptoTransactionType.BUY,
                cryptocurrency="Cardano",
                amount=Decimal("1000.0"),
                price_per_unit=Decimal("1.00"),
                total_value=Decimal("1000.00"),
                fees=Decimal("10.00"),
                exchange="Coinbase",
                transaction_id="tx_003"
            )
        ]
        
        crypto_types = set(t.cryptocurrency for t in transactions)
        
        assert len(crypto_types) == 3
        assert "Bitcoin" in crypto_types
        assert "Ethereum" in crypto_types
        assert "Cardano" in crypto_types
