"""
Unit tests for QuickBooks Integration Service

Tests cover:
- Company authentication and connection
- Data synchronization
- Transaction retrieval and filtering
- Tax category mapping
- Data export functionality
- Error handling and security
"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from dataclasses import asdict

from services.quickbooks_integration_service import (
    QuickBooksIntegrationService,
    QuickBooksCompany,
    QuickBooksAccount,
    QuickBooksTransaction,
    QuickBooksEntityType,
    AccountType,
    TaxCategory,
    TaxMappingResult
)


class TestQuickBooksIntegrationService(unittest.TestCase):
    """Test cases for QuickBooksIntegrationService"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = QuickBooksIntegrationService()
        self.test_realm_id = "12345678901234567890"
        self.test_company_name = "Test Company LLC"

    def test_initialization(self):
        """Test service initialization"""
        self.assertIsInstance(self.service.companies, dict)
        self.assertIsInstance(self.service.accounts, dict)
        self.assertIsInstance(self.service.transactions, dict)
        self.assertIsInstance(self.service.auth_tokens, dict)
        self.assertIsNotNone(self.service.cipher)
        self.assertEqual(self.service.environment, "sandbox")

    def test_authenticate_company(self):
        """Test company authentication"""
        company_id = self.service.authenticate_company(
            self.test_company_name,
            self.test_realm_id
        )

        # Verify company was created
        self.assertIn(company_id, self.service.companies)
        company = self.service.companies[company_id]

        self.assertEqual(company.company_name, self.test_company_name)
        self.assertEqual(company.realm_id, self.test_realm_id)
        self.assertTrue(company.is_active)
        self.assertIsNotNone(company.created_at)
        self.assertEqual(company.qb_version, "Online")

    def test_disconnect_company(self):
        """Test company disconnection"""
        # First connect a company
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)

        # Disconnect it
        result = self.service.disconnect_company(company_id)
        self.assertTrue(result)

        # Verify it's removed
        self.assertNotIn(company_id, self.service.companies)
        self.assertNotIn(company_id, self.service.auth_tokens)
        self.assertNotIn(company_id, self.service.accounts)
        self.assertNotIn(company_id, self.service.transactions)

        # Try to disconnect non-existent company
        result = self.service.disconnect_company('nonexistent')
        self.assertFalse(result)

    def test_get_companies(self):
        """Test retrieving all companies"""
        # Initially empty
        companies = self.service.get_companies()
        self.assertEqual(len(companies), 0)

        # Add companies
        company_id1 = self.service.authenticate_company("Company 1", "realm1")
        company_id2 = self.service.authenticate_company("Company 2", "realm2")

        companies = self.service.get_companies()
        self.assertEqual(len(companies), 2)

        company_names = [comp.company_name for comp in companies]
        self.assertIn("Company 1", company_names)
        self.assertIn("Company 2", company_names)

    def test_sync_company(self):
        """Test syncing company data"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)

        # Sync the company
        result = self.service.sync_company(company_id)
        self.assertTrue(result)

        # Verify data was loaded
        self.assertIn(company_id, self.service.accounts)
        self.assertIn(company_id, self.service.transactions)

        accounts = self.service.accounts[company_id]
        transactions = self.service.transactions[company_id]

        self.assertGreater(len(accounts), 0)
        self.assertGreater(len(transactions), 0)

        # Verify company was updated
        company = self.service.companies[company_id]
        self.assertIsNotNone(company.last_sync)

    def test_sync_nonexistent_company(self):
        """Test syncing non-existent company"""
        with self.assertRaises(ValueError):
            self.service.sync_company('nonexistent')

    def test_get_chart_of_accounts(self):
        """Test retrieving chart of accounts"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)
        self.service.sync_company(company_id)

        accounts = self.service.get_chart_of_accounts(company_id)
        self.assertGreater(len(accounts), 0)

        # Verify account structure
        for account in accounts:
            self.assertIsInstance(account, QuickBooksAccount)
            self.assertIsNotNone(account.account_id)
            self.assertIsNotNone(account.name)
            self.assertIsInstance(account.account_type, AccountType)

    def test_get_transactions(self):
        """Test retrieving transactions with filters"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)
        self.service.sync_company(company_id)

        # Get all transactions
        transactions = self.service.get_transactions(company_id)
        self.assertGreater(len(transactions), 0)

        # Test date filtering
        start_date = datetime.now() - timedelta(days=30)
        filtered_transactions = self.service.get_transactions(
            company_id, start_date=start_date
        )
        self.assertLessEqual(len(filtered_transactions), len(transactions))

        # Test transaction type filtering
        invoice_transactions = self.service.get_transactions(
            company_id, transaction_types=[QuickBooksEntityType.INVOICE]
        )
        for tx in invoice_transactions:
            self.assertEqual(tx.transaction_type, QuickBooksEntityType.INVOICE)

    def test_map_to_tax_categories(self):
        """Test tax category mapping"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)
        self.service.sync_company(company_id)

        transactions = self.service.get_transactions(company_id)
        results = self.service.map_to_tax_categories(transactions[:3])  # Test first 3

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, TaxMappingResult)
            self.assertIsInstance(result.suggested_category, TaxCategory)
            self.assertGreaterEqual(result.confidence_score, 0.0)
            self.assertLessEqual(result.confidence_score, 1.0)
            self.assertIsNotNone(result.explanation)

    def test_generate_tax_report(self):
        """Test tax report generation"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)
        self.service.sync_company(company_id)

        current_year = datetime.now().year
        report = self.service.generate_tax_report(company_id, current_year)

        # Verify report structure
        required_keys = ['company_id', 'tax_year', 'total_transactions', 'income', 'expenses', 'summary', 'requires_review']
        for key in required_keys:
            self.assertIn(key, report)

        self.assertEqual(report['company_id'], company_id)
        self.assertEqual(report['tax_year'], current_year)
        self.assertGreaterEqual(report['total_transactions'], 0)

        # Verify summary calculations
        summary = report['summary']
        expected_summary_keys = ['total_business_income', 'total_business_expenses', 'net_business_income']
        for key in expected_summary_keys:
            self.assertIn(key, summary)

    def test_export_csv(self):
        """Test CSV export functionality"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)
        self.service.sync_company(company_id)

        csv_data = self.service.export_for_tax_software(company_id, 'csv')

        # Verify CSV format
        lines = csv_data.strip().split('\n')
        self.assertGreater(len(lines), 1)  # Header + at least one data row

        # Check header
        self.assertEqual(lines[0], "Date,Type,Amount,Description,Account,Tax Amount")

        # Check data rows
        for line in lines[1:]:
            parts = line.split(',')
            self.assertEqual(len(parts), 6)

    def test_export_iif(self):
        """Test IIF export functionality"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)
        self.service.sync_company(company_id)

        iif_data = self.service.export_for_tax_software(company_id, 'iif')

        # Verify IIF format
        lines = iif_data.strip().split('\n')
        self.assertIn("!TRNS", lines[0])
        self.assertIn("!SPL", lines[1])
        self.assertIn("!ENDTRNS", lines[2])

    def test_export_invalid_format(self):
        """Test export with invalid format"""
        company_id = self.service.authenticate_company(self.test_company_name, self.test_realm_id)

        with self.assertRaises(ValueError):
            self.service.export_for_tax_software(company_id, 'invalid')

    def test_sync_all_companies(self):
        """Test syncing all companies"""
        # Connect multiple companies
        company_id1 = self.service.authenticate_company("Company 1", "realm1")
        company_id2 = self.service.authenticate_company("Company 2", "realm2")

        # Sync all
        results = self.service.sync_all_companies()

        self.assertIn(company_id1, results)
        self.assertIn(company_id2, results)
        self.assertTrue(results[company_id1])
        self.assertTrue(results[company_id2])

    def test_encryption_decryption(self):
        """Test token encryption/decryption"""
        test_tokens = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_at': datetime.now().isoformat(),
            'realm_id': 'test_realm_id'
        }

        # Encrypt
        encrypted = self.service._encrypt_tokens(test_tokens)

        # Decrypt
        decrypted = self.service._decrypt_tokens(encrypted)

        self.assertEqual(decrypted, test_tokens)

    def test_tax_mapping_logic(self):
        """Test detailed tax mapping logic"""
        # Create test accounts
        accounts = [
            QuickBooksAccount("acc1", "Service Revenue", AccountType.INCOME),
            QuickBooksAccount("acc2", "Office Rent", AccountType.EXPENSE),
            QuickBooksAccount("acc3", "Vehicle Expense", AccountType.EXPENSE),
            QuickBooksAccount("acc4", "Meals and Entertainment", AccountType.EXPENSE),
            QuickBooksAccount("acc5", "Cost of Goods Sold", AccountType.COST_OF_GOODS_SOLD),
        ]

        # Create test transactions
        transactions = [
            QuickBooksTransaction("tx_test_company_1", QuickBooksEntityType.INVOICE, datetime.now(), 1000, "Service", "acc1"),
            QuickBooksTransaction("tx_test_company_2", QuickBooksEntityType.BILL, datetime.now(), -500, "Rent", "acc2"),
            QuickBooksTransaction("tx_test_company_3", QuickBooksEntityType.BILL, datetime.now(), -300, "Gas", "acc3"),
            QuickBooksTransaction("tx_test_company_4", QuickBooksEntityType.BILL, datetime.now(), -200, "Dinner", "acc4"),
            QuickBooksTransaction("tx_test_company_5", QuickBooksEntityType.BILL, datetime.now(), -150, "COGS", "acc5"),
        ]

        # Mock accounts in service
        company_id = "test"
        self.service.accounts[company_id] = accounts

        # Test mapping
        results = self.service.map_to_tax_categories(transactions)

        self.assertEqual(len(results), 5)

        # Verify specific mappings
        income_result = next(r for r in results if r.transaction_id == "tx_test_company_1")
        self.assertEqual(income_result.suggested_category, TaxCategory.BUSINESS_INCOME)
        self.assertGreaterEqual(income_result.confidence_score, 0.8)

        rent_result = next(r for r in results if r.transaction_id == "tx_test_company_2")
        self.assertEqual(rent_result.suggested_category, TaxCategory.OFFICE_EXPENSE)
        self.assertGreaterEqual(rent_result.confidence_score, 0.7)

        vehicle_result = next(r for r in results if r.transaction_id == "tx_test_company_3")
        self.assertEqual(vehicle_result.suggested_category, TaxCategory.VEHICLE_EXPENSE)
        self.assertGreaterEqual(vehicle_result.confidence_score, 0.8)

        meals_result = next(r for r in results if r.transaction_id == "tx_test_company_4")
        self.assertEqual(meals_result.suggested_category, TaxCategory.MEALS_ENTERTAINMENT)
        self.assertGreaterEqual(meals_result.confidence_score, 0.6)

        cogs_result = next(r for r in results if r.transaction_id == "tx_test_company_5")
        self.assertEqual(cogs_result.suggested_category, TaxCategory.COST_OF_GOODS_SOLD)
        self.assertGreaterEqual(cogs_result.confidence_score, 0.8)


class TestQuickBooksCompany(unittest.TestCase):
    """Test cases for QuickBooksCompany dataclass"""

    def test_company_creation(self):
        """Test QuickBooksCompany creation and defaults"""
        company = QuickBooksCompany(
            company_id="test_id",
            company_name="Test Company",
            realm_id="123456789"
        )

        self.assertEqual(company.company_id, "test_id")
        self.assertEqual(company.company_name, "Test Company")
        self.assertEqual(company.realm_id, "123456789")
        self.assertTrue(company.is_active)
        self.assertIsNone(company.last_sync)
        self.assertIsNotNone(company.created_at)
        self.assertEqual(company.qb_version, "Online")

    def test_company_serialization(self):
        """Test QuickBooksCompany JSON serialization"""
        company = QuickBooksCompany(
            company_id="test_id",
            company_name="Test Company",
            realm_id="123456789"
        )

        company_dict = asdict(company)

        expected_fields = [
            'company_id', 'company_name', 'realm_id', 'is_active',
            'last_sync', 'created_at', 'qb_version'
        ]

        for field in expected_fields:
            self.assertIn(field, company_dict)


class TestQuickBooksAccount(unittest.TestCase):
    """Test cases for QuickBooksAccount dataclass"""

    def test_account_creation(self):
        """Test QuickBooksAccount creation"""
        account = QuickBooksAccount(
            account_id="acc_123",
            name="Test Account",
            account_type=AccountType.ASSET,
            account_sub_type="Bank",
            balance=1000.50,
            currency="USD",
            is_active=True
        )

        self.assertEqual(account.account_id, "acc_123")
        self.assertEqual(account.name, "Test Account")
        self.assertEqual(account.account_type, AccountType.ASSET)
        self.assertEqual(account.account_sub_type, "Bank")
        self.assertEqual(account.balance, 1000.50)
        self.assertEqual(account.currency, "USD")
        self.assertTrue(account.is_active)


class TestQuickBooksTransaction(unittest.TestCase):
    """Test cases for QuickBooksTransaction dataclass"""

    def test_transaction_creation(self):
        """Test QuickBooksTransaction creation"""
        transaction = QuickBooksTransaction(
            transaction_id="tx_123",
            transaction_type=QuickBooksEntityType.INVOICE,
            date=datetime.now(),
            amount=500.00,
            description="Test Invoice",
            account_id="acc_456",
            tax_amount=40.00,
            is_taxable=True
        )

        self.assertEqual(transaction.transaction_id, "tx_123")
        self.assertEqual(transaction.transaction_type, QuickBooksEntityType.INVOICE)
        self.assertEqual(transaction.amount, 500.00)
        self.assertEqual(transaction.description, "Test Invoice")
        self.assertEqual(transaction.account_id, "acc_456")
        self.assertEqual(transaction.tax_amount, 40.00)
        self.assertTrue(transaction.is_taxable)
        self.assertIsNotNone(transaction.line_items)
        self.assertEqual(len(transaction.line_items), 0)


if __name__ == '__main__':
    unittest.main()