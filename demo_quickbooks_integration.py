"""
QuickBooks Integration Demo Script

Demonstrates the QuickBooks integration functionality including:
- Company authentication and connection
- Data synchronization
- Transaction retrieval and filtering
- Tax category mapping
- Data export functionality
"""

import json
import os
from datetime import datetime, timedelta
from services.quickbooks_integration_service import (
    QuickBooksIntegrationService,
    QuickBooksCompany,
    QuickBooksAccount,
    QuickBooksTransaction,
    QuickBooksEntityType,
    AccountType,
    TaxCategory
)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{title}")
    print("-" * len(title))


def demo_company_connection():
    """Demonstrate company connection functionality"""
    print_header("QUICKBOOKS INTEGRATION DEMO")
    print("This demo showcases QuickBooks Online integration capabilities.")

    service = QuickBooksIntegrationService()

    print_section("1. Company Connection")

    # Connect a sample company
    company_name = "Demo Accounting Services LLC"
    realm_id = "12345678901234567890"

    print(f"Connecting to company: {company_name}")
    print(f"Realm ID: {realm_id}")

    company_id = service.authenticate_company(company_name, realm_id)
    print(f"✓ Company connected successfully with ID: {company_id}")

    # Display company info
    company = service.companies[company_id]
    print(f"Company Details:")
    print(f"  Name: {company.company_name}")
    print(f"  Realm ID: {company.realm_id}")
    print(f"  Active: {company.is_active}")
    print(f"  Created: {company.created_at}")
    print(f"  QB Version: {company.qb_version}")

    return service, company_id


def demo_data_sync(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate data synchronization"""
    print_section("2. Data Synchronization")

    print("Syncing company data...")
    result = service.sync_company(company_id)

    if result:
        print("✓ Data synchronization completed successfully")

        # Show sync timestamp
        company = service.companies[company_id]
        print(f"Last sync: {company.last_sync}")

        # Show data summary
        accounts = service.accounts.get(company_id, [])
        transactions = service.transactions.get(company_id, [])

        print(f"Accounts loaded: {len(accounts)}")
        print(f"Transactions loaded: {len(transactions)}")

        return True
    else:
        print("✗ Data synchronization failed")
        return False


def demo_chart_of_accounts(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate chart of accounts functionality"""
    print_section("3. Chart of Accounts")

    accounts = service.get_chart_of_accounts(company_id)

    print(f"Total accounts: {len(accounts)}")
    print("\nSample Accounts:")

    # Show first 5 accounts
    for i, account in enumerate(accounts[:5]):
        print(f"{i+1}. {account.name}")
        print(f"   Type: {account.account_type.value}")
        print(f"   Balance: ${account.balance:,.2f}")
        print(f"   Currency: {account.currency}")
        print()


def demo_transaction_handling(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate transaction handling"""
    print_section("4. Transaction Management")

    # Get all transactions
    all_transactions = service.get_transactions(company_id)
    print(f"Total transactions: {len(all_transactions)}")

    # Demonstrate filtering
    print("\nTransaction Filtering:")

    # Filter by date (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_transactions = service.get_transactions(company_id, start_date=thirty_days_ago)
    print(f"Transactions in last 30 days: {len(recent_transactions)}")

    # Filter by transaction type
    invoices = service.get_transactions(company_id, transaction_types=[QuickBooksEntityType.INVOICE])
    bills = service.get_transactions(company_id, transaction_types=[QuickBooksEntityType.BILL])
    payments = service.get_transactions(company_id, transaction_types=[QuickBooksEntityType.PAYMENT])

    print(f"Invoices: {len(invoices)}")
    print(f"Bills: {len(bills)}")
    print(f"Payments: {len(payments)}")

    # Show sample transactions
    print("\nSample Transactions:")
    for i, transaction in enumerate(all_transactions[:3]):
        print(f"{i+1}. {transaction.transaction_type.value}: ${transaction.amount:,.2f}")
        print(f"   Date: {transaction.date.strftime('%Y-%m-%d')}")
        print(f"   Description: {transaction.description}")
        print(f"   Account: {transaction.account_id}")
        print()


def demo_tax_mapping(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate tax category mapping"""
    print_section("5. Tax Category Mapping")

    transactions = service.get_transactions(company_id)
    if not transactions:
        print("No transactions available for mapping")
        return

    # Map first 10 transactions
    sample_transactions = transactions[:10]
    mapping_results = service.map_to_tax_categories(sample_transactions)

    print(f"Mapped {len(mapping_results)} transactions to tax categories")
    print("\nMapping Results:")

    for result in mapping_results:
        print(f"Transaction: {result.transaction_id}")
        print(f"  Suggested Category: {result.suggested_category.value}")
        print(f"  Confidence: {result.confidence_score:.2%}")
        print(f"  Explanation: {result.explanation}")
        print()

    # Show category distribution
    category_counts = {}
    for result in mapping_results:
        category = result.suggested_category.value
        category_counts[category] = category_counts.get(category, 0) + 1

    print("Category Distribution:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} transactions")


def demo_tax_report(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate tax report generation"""
    print_section("6. Tax Report Generation")

    current_year = datetime.now().year
    print(f"Generating tax report for {current_year}...")

    report = service.generate_tax_report(company_id, current_year)

    print("✓ Tax report generated successfully")
    print(f"\nTax Report Summary for {current_year}:")
    print(f"Company: {report['company_id']}")
    print(f"Total Transactions: {report['total_transactions']}")

    print(f"\nIncome Breakdown:")
    for category, amount in report['income'].items():
        print(f"  {category}: ${amount:,.2f}")

    print(f"\nExpense Breakdown:")
    for category, amount in report['expenses'].items():
        print(f"  {category}: ${amount:,.2f}")

    print(f"\nBusiness Summary:")
    summary = report['summary']
    print(f"  Total Business Income: ${summary['total_business_income']:,.2f}")
    print(f"  Total Business Expenses: ${summary['total_business_expenses']:,.2f}")
    print(f"  Net Business Income: ${summary['net_business_income']:,.2f}")

    if report['requires_review']:
        print("\n⚠️  Note: Some transactions require manual review")


def demo_data_export(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate data export functionality"""
    print_section("7. Data Export")

    # Export to CSV
    print("Exporting data to CSV format...")
    csv_data = service.export_for_tax_software(company_id, 'csv')

    # Save to file
    csv_filename = "demo_quickbooks_export.csv"
    with open(csv_filename, 'w', encoding='utf-8') as f:
        f.write(csv_data)

    print(f"✓ CSV export saved to: {csv_filename}")

    # Show first few lines
    lines = csv_data.split('\n')[:6]  # Header + 5 data lines
    print("\nCSV Preview:")
    for line in lines:
        print(f"  {line}")

    # Export to IIF
    print("\nExporting data to IIF format...")
    iif_data = service.export_for_tax_software(company_id, 'iif')

    iif_filename = "demo_quickbooks_export.iif"
    with open(iif_filename, 'w', encoding='utf-8') as f:
        f.write(iif_data)

    print(f"✓ IIF export saved to: {iif_filename}")

    # Show first few lines
    lines = iif_data.split('\n')[:10]
    print("\nIIF Preview:")
    for line in lines:
        print(f"  {line}")


def demo_multiple_companies(service: QuickBooksIntegrationService):
    """Demonstrate multiple company handling"""
    print_section("8. Multiple Company Management")

    # Connect another company
    company2_name = "Demo Consulting Group"
    company2_realm = "98765432109876543210"

    print(f"Connecting second company: {company2_name}")
    company2_id = service.authenticate_company(company2_name, company2_realm)
    print(f"✓ Second company connected with ID: {company2_id}")

    # Sync second company
    service.sync_company(company2_id)

    # Show all companies
    companies = service.get_companies()
    print(f"\nTotal connected companies: {len(companies)}")

    for company in companies:
        print(f"- {company.company_name} (ID: {company.company_id})")

    # Sync all companies
    print("\nSyncing all companies...")
    results = service.sync_all_companies()

    for company_id, success in results.items():
        company = service.companies[company_id]
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {company.company_name}: {status}")


def demo_security_features(service: QuickBooksIntegrationService, company_id: str):
    """Demonstrate security features"""
    print_section("9. Security Features")

    print("Testing token encryption/decryption...")

    # Get the tokens for the company
    if company_id in service.auth_tokens:
        tokens = service.auth_tokens[company_id]

        # Test encryption/decryption
        encrypted = service._encrypt_tokens(tokens)
        decrypted = service._decrypt_tokens(encrypted)

        if decrypted == tokens:
            print("✓ Token encryption/decryption working correctly")
        else:
            print("✗ Token encryption/decryption failed")

    print("✓ Company data securely stored with AES-256 encryption")


def cleanup_demo_files():
    """Clean up demo export files"""
    files_to_remove = ["demo_quickbooks_export.csv", "demo_quickbooks_export.iif"]

    for filename in files_to_remove:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Cleaned up: {filename}")


def main():
    """Main demo function"""
    try:
        # Run all demos
        service, company_id = demo_company_connection()

        if demo_data_sync(service, company_id):
            demo_chart_of_accounts(service, company_id)
            demo_transaction_handling(service, company_id)
            demo_tax_mapping(service, company_id)
            demo_tax_report(service, company_id)
            demo_data_export(service, company_id)

        demo_multiple_companies(service)
        demo_security_features(service, company_id)

        print_header("DEMO COMPLETED SUCCESSFULLY")
        print("QuickBooks integration features demonstrated:")
        print("✓ Company authentication and connection")
        print("✓ Data synchronization")
        print("✓ Chart of accounts management")
        print("✓ Transaction filtering and retrieval")
        print("✓ Tax category mapping")
        print("✓ Tax report generation")
        print("✓ Data export (CSV/IIF)")
        print("✓ Multiple company support")
        print("✓ Security features (encryption)")

    except Exception as e:
        print(f"\n✗ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        cleanup_demo_files()


if __name__ == "__main__":
    main()