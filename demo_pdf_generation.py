#!/usr/bin/env python3
"""
Demo script for PDF Form Generation

This script demonstrates the new PDF form generation capabilities
added in Version 2.0 of the Freedom US Tax Return application.
"""

import json
from pathlib import Path
from utils.pdf.pdf_generator import TaxReturnPDFGenerator


def create_sample_tax_data():
    """Create sample tax data for demonstration"""
    return {
        'personal_info': {
            'first_name': 'John',
            'last_name': 'Doe',
            'middle_initial': 'Q',
            'ssn': '123-45-6789',
            'address': '123 Main Street',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'occupation': 'Software Engineer'
        },
        'filing_status': {
            'status': 'Single'
        },
        'basic_info': {
            'tax_year': 2025
        },
        'income': {
            'w2_forms': [
                {
                    'employer': 'Tech Corp',
                    'wages': 75000.00,
                    'federal_withholding': 8500.00,
                    'social_security_wages': 75000.00,
                    'social_security_withheld': 4650.00,
                    'medicare_wages': 75000.00,
                    'medicare_withheld': 1087.50
                }
            ],
            'interest_income': [
                {
                    'source': 'Bank Savings',
                    'amount': 1250.00,
                    'tax_exempt': False
                }
            ],
            'dividend_income': [
                {
                    'source': 'Stock Portfolio',
                    'ordinary': 850.00,
                    'qualified': 650.00
                }
            ],
            'capital_gains': [
                {
                    'description': 'Apple Inc. Common Stock',
                    'date_acquired': '01/15/2020',
                    'date_sold': '12/01/2025',
                    'sales_price': 15000.00,
                    'cost_basis': 12000.00,
                    'gain_loss': 3000.00,
                    'holding_period': 'Long-term'
                }
            ]
        },
        'deductions': {
            'method': 'standard'
        },
        'schedules': {
            'schedule_c': {
                'business_name': 'Freelance Consulting',
                'business_code': '541990',
                'business_address': '123 Main Street, Anytown CA 12345',
                'ein': '',
                'gross_receipts': 25000.00,
                'returns_and_allowances': 0.00,
                'cost_of_goods_sold': 0.00,
                'expenses': {
                    'advertising': 500.00,
                    'car_and_truck': 2400.00,
                    'contract_labor': 0.00,
                    'depreciation': 800.00,
                    'insurance': 1200.00,
                    'interest_mortgage': 0.00,
                    'interest_other': 0.00,
                    'legal_professional': 300.00,
                    'office_expense': 1500.00,
                    'rent_equipment': 0.00,
                    'rent_property': 0.00,
                    'repairs': 200.00,
                    'supplies': 800.00,
                    'taxes_licenses': 150.00,
                    'travel': 1200.00,
                    'meals': 600.00,
                    'utilities': 400.00,
                    'wages': 0.00,
                    'other': 100.00
                }
            }
        }
    }


def main():
    """Main demonstration function"""
    print("Freedom US Tax Return - PDF Form Generation Demo")
    print("=" * 55)

    # Create sample tax data
    tax_data = create_sample_tax_data()
    print(f"Created sample tax data for: {tax_data['personal_info']['first_name']} {tax_data['personal_info']['last_name']}")

    # Initialize PDF generator
    print("\nInitializing PDF generator...")
    generator = TaxReturnPDFGenerator()

    # Validate the data
    print("Validating tax data...")
    is_valid, error = generator.validate_pdf_generation(tax_data)
    if not is_valid:
        print(f"❌ Validation failed: {error}")
        return

    print("✅ Tax data validation passed")

    # Determine required forms
    print("\nDetermining required forms...")
    required_forms = generator.determine_required_forms(tax_data)
    print(f"Required forms: {', '.join(required_forms)}")

    # Generate the complete return
    print("\nGenerating PDF forms...")
    try:
        generated_files = generator.generate_complete_return(
            tax_data,
            flatten=True,  # Make forms non-editable for final submission
            include_signature=True
        )

        print("✅ PDF generation completed successfully!")
        print("\nGenerated files:")
        for form_name, file_path in generated_files.items():
            file_path_obj = Path(file_path)
            size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            print(f"  • {form_name}: {file_path_obj.name} ({size_mb:.2f} MB)")

        print(f"\n📁 All files saved to: {generator.output_directory}")

        # Show summary
        print("\n" + "=" * 55)
        print("SUMMARY")
        print("=" * 55)
        print(f"Taxpayer: {tax_data['personal_info']['first_name']} {tax_data['personal_info']['last_name']}")
        print(f"SSN: {tax_data['personal_info']['ssn']}")
        print(f"Tax Year: {tax_data['basic_info']['tax_year']}")
        print(f"Forms Generated: {len(generated_files)}")
        print(f"Total File Size: {sum(Path(fp).stat().st_size for fp in generated_files.values()) / (1024 * 1024):.2f} MB")

        print("\n🎉 Version 2.0 PDF Form Generation feature is working!")
        print("\nNext steps:")
        print("  • Review generated PDFs for accuracy")
        print("  • Print forms for mailing or e-filing")
        print("  • Use batch export for multiple returns")

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return


if __name__ == "__main__":
    main()