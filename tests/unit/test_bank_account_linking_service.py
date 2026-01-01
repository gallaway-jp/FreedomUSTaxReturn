"""
Unit tests for Bank Account Linking Service

Tests cover:
- Account connection and disconnection
- Transaction synchronization
- Tax categorization
- Data export functionality
- Security and encryption
- Error handling
"""

import unittest
import json
from datetime import datetime, timedelta
from dataclasses import asdict
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from services.bank_account_linking_service import (
    BankAccountLinkingService,
    BankAccount,
    BankTransaction,
    AccountType,
    TransactionCategory,
    TaxCategorizationResult
)


class TestBankAccountLinkingService(unittest.TestCase):
    """Test cases for BankAccountLinkingService"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = BankAccountLinkingService()
        self.test_credentials = {
            'username': 'testuser',
            'password': 'testpass123',
            'account_number': '1234567890'
        }

    def test_initialization(self):
        """Test service initialization"""
        self.assertIsInstance(self.service.accounts, dict)
        self.assertIsInstance(self.service.transactions, dict)
        self.assertIsInstance(self.service.credentials, dict)
        self.assertIsNotNone(self.service.cipher)

    def test_connect_account(self):
        """Test connecting a new account"""
        account_id = self.service.connect_account(
            'test_bank',
            self.test_credentials,
            AccountType.CHECKING
        )

        # Verify account was created
        self.assertIn(account_id, self.service.accounts)
        account = self.service.accounts[account_id]

        self.assertEqual(account.institution_name, 'test_bank')
        self.assertEqual(account.account_type, AccountType.CHECKING)
        self.assertTrue(account.is_active)
        self.assertIsNotNone(account.created_at)

        # Verify credentials are encrypted
        self.assertIn(account_id, self.service.credentials)
        stored_creds = self.service.credentials[account_id]
        self.assertEqual(stored_creds['institution'], 'test_bank')

    def test_disconnect_account(self):
        """Test disconnecting an account"""
        # First connect an account
        account_id = self.service.connect_account('test_bank', self.test_credentials)

        # Disconnect it
        result = self.service.disconnect_account(account_id)
        self.assertTrue(result)

        # Verify it's removed
        self.assertNotIn(account_id, self.service.accounts)
        self.assertNotIn(account_id, self.service.credentials)
        self.assertNotIn(account_id, self.service.transactions)

        # Try to disconnect non-existent account
        result = self.service.disconnect_account('nonexistent')
        self.assertFalse(result)

    def test_get_accounts(self):
        """Test retrieving all accounts"""
        # Initially empty
        accounts = self.service.get_accounts()
        self.assertEqual(len(accounts), 0)

        # Add accounts
        account_id1 = self.service.connect_account('bank1', self.test_credentials)
        account_id2 = self.service.connect_account('bank2', self.test_credentials)

        accounts = self.service.get_accounts()
        self.assertEqual(len(accounts), 2)

        account_names = [acc.institution_name for acc in accounts]
        self.assertIn('bank1', account_names)
        self.assertIn('bank2', account_names)

    def test_sync_account(self):
        """Test syncing account transactions"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)

        # Sync the account
        result = self.service.sync_account(account_id)
        self.assertTrue(result)

        # Verify transactions were loaded
        self.assertIn(account_id, self.service.transactions)
        transactions = self.service.transactions[account_id]
        self.assertGreater(len(transactions), 0)

        # Verify account was updated
        account = self.service.accounts[account_id]
        self.assertIsNotNone(account.last_sync)
        self.assertIsNotNone(account.balance)

    def test_sync_nonexistent_account(self):
        """Test syncing non-existent account"""
        with self.assertRaises(ValueError):
            self.service.sync_account('nonexistent')

    def test_get_transactions(self):
        """Test retrieving transactions with filters"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)
        self.service.sync_account(account_id)

        # Get all transactions
        transactions = self.service.get_transactions(account_id)
        self.assertGreater(len(transactions), 0)

        # Test date filtering
        start_date = datetime.now() - timedelta(days=30)
        filtered_transactions = self.service.get_transactions(
            account_id, start_date=start_date
        )
        self.assertLessEqual(len(filtered_transactions), len(transactions))

        # Test category filtering
        category_transactions = self.service.get_transactions(
            account_id, category=TransactionCategory.INTEREST_INCOME
        )
        for tx in category_transactions:
            self.assertEqual(tx.category, TransactionCategory.INTEREST_INCOME)

    def test_categorize_for_tax(self):
        """Test tax categorization of transactions"""
        # Create test transactions
        transactions = [
            BankTransaction(
                transaction_id="tx1",
                account_id="acc1",
                date=datetime.now(),
                amount=25.50,
                description="Interest Payment from Bank"
            ),
            BankTransaction(
                transaction_id="tx2",
                account_id="acc1",
                date=datetime.now(),
                amount=-89.99,
                description="Office Supplies Purchase"
            ),
            BankTransaction(
                transaction_id="tx3",
                account_id="acc1",
                date=datetime.now(),
                amount=-250.00,
                description="Medical Bill Payment"
            )
        ]

        results = self.service.categorize_for_tax(transactions)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, TaxCategorizationResult)
            self.assertGreater(result.confidence_score, 0)
            self.assertIsNotNone(result.explanation)

    def test_export_csv(self):
        """Test CSV export functionality"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)
        self.service.sync_account(account_id)

        csv_data = self.service.export_for_tax_software(account_id, 'csv')

        # Verify CSV format
        lines = csv_data.strip().split('\n')
        self.assertGreater(len(lines), 1)  # Header + at least one data row

        # Check header
        self.assertEqual(lines[0], "Date,Amount,Description,Category")

        # Check data rows
        for line in lines[1:]:
            parts = line.split(',')
            self.assertEqual(len(parts), 4)

    def test_export_qif(self):
        """Test QIF export functionality"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)
        self.service.sync_account(account_id)

        qif_data = self.service.export_for_tax_software(account_id, 'qif')

        # Verify QIF format
        lines = qif_data.strip().split('\n')
        self.assertIn("!Type:Bank", lines)

        # Should contain transaction records
        self.assertGreater(len(lines), 1)

    def test_export_ofx(self):
        """Test OFX export functionality"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)
        self.service.sync_account(account_id)

        ofx_data = self.service.export_for_tax_software(account_id, 'ofx')

        # Verify OFX format
        self.assertIn("<?xml version=\"1.0\"", ofx_data)
        self.assertIn("<OFX>", ofx_data)
        self.assertIn("</OFX>", ofx_data)

    def test_export_invalid_format(self):
        """Test export with invalid format"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)

        with self.assertRaises(ValueError):
            self.service.export_for_tax_software(account_id, 'invalid')

    def test_get_tax_summary(self):
        """Test tax summary generation"""
        account_id = self.service.connect_account('test_bank', self.test_credentials)
        self.service.sync_account(account_id)

        current_year = datetime.now().year
        summary = self.service.get_tax_summary(account_id, current_year)

        # Verify summary structure
        required_keys = [
            'account_id', 'tax_year', 'total_transactions',
            'interest_income', 'dividend_income', 'business_expenses',
            'medical_expenses', 'charitable_donations', 'requires_review'
        ]

        for key in required_keys:
            self.assertIn(key, summary)

        self.assertEqual(summary['account_id'], account_id)
        self.assertEqual(summary['tax_year'], current_year)
        self.assertGreaterEqual(summary['total_transactions'], 0)

    def test_sync_all_accounts(self):
        """Test syncing all accounts"""
        # Connect multiple accounts
        account_id1 = self.service.connect_account('bank1', self.test_credentials)
        account_id2 = self.service.connect_account('bank2', self.test_credentials)

        # Sync all
        results = self.service.sync_all_accounts()

        self.assertIn(account_id1, results)
        self.assertIn(account_id2, results)
        self.assertTrue(results[account_id1])
        self.assertTrue(results[account_id2])

    def test_encryption_decryption(self):
        """Test credential encryption/decryption"""
        test_data = {'key': 'value', 'number': 123}

        # Encrypt
        encrypted = self.service._encrypt_credentials(test_data)

        # Decrypt
        decrypted = self.service._decrypt_credentials(encrypted)

        self.assertEqual(decrypted, test_data)

    def test_mask_account_number(self):
        """Test account number masking"""
        # Short number
        self.assertEqual(self.service._mask_account_number('123'), '123')

        # Long number
        self.assertEqual(self.service._mask_account_number('1234567890'), '******7890')

        # Empty
        self.assertEqual(self.service._mask_account_number(''), '')

    def test_transaction_categorization_logic(self):
        """Test detailed transaction categorization logic"""
        test_cases = [
            # Interest income
            ("Monthly Interest Payment", TransactionCategory.INTEREST_INCOME, 0.8),
            ("Dividend from Stock", TransactionCategory.DIVIDEND_INCOME, 0.9),

            # Business expenses
            ("Office Supplies Purchase", TransactionCategory.BUSINESS_EXPENSE, 0.7),

            # Medical expenses
            ("Doctor Visit Payment", TransactionCategory.MEDICAL_EXPENSE, 0.8),

            # Charitable donations
            ("Charity Donation", TransactionCategory.CHARITABLE_DONATION, 0.6),

            # Personal expenses (default)
            ("Grocery Shopping", TransactionCategory.PERSONAL_EXPENSE, 0.3),
        ]

        for description, expected_category, min_confidence in test_cases:
            transaction = BankTransaction(
                transaction_id="test_tx",
                account_id="test_acc",
                date=datetime.now(),
                amount=-50.00,
                description=description
            )

            result = self.service._categorize_transaction(transaction)

            self.assertEqual(result.suggested_category, expected_category)
            self.assertGreaterEqual(result.confidence_score, min_confidence)
            self.assertIsNotNone(result.explanation)


class TestBankAccount(unittest.TestCase):
    """Test cases for BankAccount dataclass"""

    def test_bank_account_creation(self):
        """Test BankAccount creation and defaults"""
        account = BankAccount(
            account_id="test_id",
            institution_name="Test Bank",
            account_type=AccountType.CHECKING,
            account_name="Test Checking",
            account_number_masked="****1234",
            balance=1000.50
        )

        self.assertEqual(account.account_id, "test_id")
        self.assertEqual(account.institution_name, "Test Bank")
        self.assertEqual(account.account_type, AccountType.CHECKING)
        self.assertEqual(account.balance, 1000.50)
        self.assertEqual(account.currency, "USD")
        self.assertTrue(account.is_active)
        self.assertIsNone(account.last_sync)
        self.assertIsNotNone(account.created_at)

    def test_bank_account_serialization(self):
        """Test BankAccount JSON serialization"""
        account = BankAccount(
            account_id="test_id",
            institution_name="Test Bank",
            account_type=AccountType.CHECKING,
            account_name="Test Checking",
            account_number_masked="****1234",
            balance=1000.50
        )

        # Convert to dict
        account_dict = asdict(account)

        # Verify all fields are present
        expected_fields = [
            'account_id', 'institution_name', 'account_type', 'account_name',
            'account_number_masked', 'balance', 'currency', 'is_active',
            'last_sync', 'created_at'
        ]

        for field in expected_fields:
            self.assertIn(field, account_dict)


class TestBankTransaction(unittest.TestCase):
    """Test cases for BankTransaction dataclass"""

    def test_bank_transaction_creation(self):
        """Test BankTransaction creation"""
        transaction = BankTransaction(
            transaction_id="tx_123",
            account_id="acc_456",
            date=datetime.now(),
            amount=-50.25,
            description="Test Transaction",
            category=TransactionCategory.BUSINESS_EXPENSE,
            merchant_name="Test Store",
            tax_relevant=True,
            confidence_score=0.8
        )

        self.assertEqual(transaction.transaction_id, "tx_123")
        self.assertEqual(transaction.account_id, "acc_456")
        self.assertEqual(transaction.amount, -50.25)
        self.assertEqual(transaction.description, "Test Transaction")
        self.assertEqual(transaction.category, TransactionCategory.BUSINESS_EXPENSE)
        self.assertEqual(transaction.merchant_name, "Test Store")
        self.assertTrue(transaction.tax_relevant)
        self.assertEqual(transaction.confidence_score, 0.8)
        self.assertFalse(transaction.is_pending)


if __name__ == '__main__':
    unittest.main()