#!/usr/bin/env python3
"""
Demo script for Bank Account Linking Service

This script demonstrates the key features of the bank account linking service,
including account connection, transaction synchronization, tax categorization,
and data export.

Usage:
    python demo_bank_account_linking.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.bank_account_linking_service import (
    BankAccountLinkingService,
    AccountType,
    TransactionCategory
)


def demo_bank_account_linking():
    """Demonstrate bank account linking functionality"""
    print("🏦 Bank Account Linking Service Demo")
    print("=" * 50)

    # Initialize the service
    service = BankAccountLinkingService()
    print("✅ Service initialized")

    # Demo account connection
    print("\n📋 Connecting Bank Account...")
    test_credentials = {
        'username': 'demo_user',
        'password': 'demo_pass123',
        'account_number': '1234567890'
    }

    account_id = service.connect_account(
        'Demo Bank',
        test_credentials,
        AccountType.CHECKING
    )
    print(f"✅ Account connected: {account_id}")

    # Demo account sync
    print("\n🔄 Syncing Account Transactions...")
    success = service.sync_account(account_id)
    if success:
        print("✅ Account synced successfully")
    else:
        print("❌ Account sync failed")

    # Display connected accounts
    print("\n📊 Connected Accounts:")
    accounts = service.get_accounts()
    for account in accounts:
        print(f"  • {account.institution_name} - {account.account_type.value.title()}")
        print(f"    Balance: ${account.balance:,.2f}")
        print(f"    Last Sync: {account.last_sync.strftime('%Y-%m-%d %H:%M') if account.last_sync else 'Never'}")

    # Demo transaction retrieval
    print("\n💳 Recent Transactions:")
    transactions = service.get_transactions(account_id)
    for tx in transactions[:5]:  # Show first 5
        print(f"  • {tx.date.strftime('%Y-%m-%d')}: {tx.description}")
        print(f"    Amount: ${tx.amount:,.2f} | Category: {tx.category.value if tx.category else 'Uncategorized'}")

    # Demo tax categorization
    print("\n🧾 Tax Categorization Analysis:")
    if transactions:
        results = service.categorize_for_tax(transactions[:3])  # Analyze first 3 transactions
        for result in results:
            tx = next((t for t in transactions if t.transaction_id == result.transaction_id), None)
            if tx:
                print(f"  • '{tx.description}' → {result.suggested_category.value}")
                print(f"    Confidence: {result.confidence_score:.1%}")
                if result.requires_review:
                    print("    ⚠️  Requires manual review")

    # Demo tax summary
    print("\n📈 Tax Summary (2024):")
    current_year = datetime.now().year
    summary = service.get_tax_summary(account_id, current_year)

    print(f"  Total Transactions: {summary['total_transactions']}")
    print(f"  Interest Income: ${summary['interest_income']:,.2f}")
    print(f"  Dividend Income: ${summary['dividend_income']:,.2f}")
    print(f"  Business Expenses: ${summary['business_expenses']:,.2f}")
    print(f"  Medical Expenses: ${summary['medical_expenses']:,.2f}")
    print(f"  Charitable Donations: ${summary['charitable_donations']:,.2f}")
    print(f"  Items Needing Review: {len(summary['requires_review'])}")

    # Demo data export
    print("\n📤 Exporting Data...")

    # CSV export
    csv_data = service.export_for_tax_software(account_id, 'csv')
    print("✅ CSV export completed")

    # QIF export
    qif_data = service.export_for_tax_software(account_id, 'qif')
    print("✅ QIF export completed")

    # OFX export
    ofx_data = service.export_for_tax_software(account_id, 'ofx')
    print("✅ OFX export completed")

    # Demo account disconnection
    print("\n🔌 Disconnecting Account...")
    success = service.disconnect_account(account_id)
    if success:
        print("✅ Account disconnected successfully")
    else:
        print("❌ Account disconnection failed")

    print("\n🎉 Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  • Secure account connection with encrypted credentials")
    print("  • Automatic transaction synchronization")
    print("  • AI-powered tax categorization")
    print("  • Comprehensive tax summary generation")
    print("  • Multi-format data export (CSV, QIF, OFX)")
    print("  • Secure account management")

    print("\nSecurity Features:")
    print("  • AES-256 encryption for stored credentials")
    print("  • Account number masking for display")
    print("  • Secure credential storage and retrieval")
    print("  • Audit trail of all account access")

    print("\nSupported Export Formats:")
    print("  • CSV: Compatible with spreadsheet applications")
    print("  • QIF: Quicken Interchange Format")
    print("  • OFX: Open Financial Exchange (banking software)")


if __name__ == "__main__":
    try:
        demo_bank_account_linking()
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)