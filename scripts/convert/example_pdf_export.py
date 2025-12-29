"""
Example: How to use the PDF Form Filler
This demonstrates filling IRS Form 1040 with sample data
"""

import sys
from utils.pdf_form_filler import TaxReturnPDFExporter, PDFFormFiller
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'backslashreplace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'backslashreplace')


def example_fill_form_1040():
    """Example: Fill Form 1040 with sample taxpayer data"""
    
    print("="*80)
    print("Example: Filling IRS Form 1040 with Sample Data")
    print("="*80)
    
    # Sample tax data using TaxData structure
    sample_tax_data = {
        # Personal Information
        'personal_info.first_name': 'John',
        'personal_info.middle_initial': 'Q',
        'personal_info.last_name': 'Taxpayer',
        'personal_info.ssn': '123-45-6789',
        'personal_info.address': '123 Main Street',
        'personal_info.city': 'Anytown',
        'personal_info.state': 'CA',
        'personal_info.zip_code': '90210',
        
        # Filing Status
        'filing_status.status': 'Single',
        
        # Income (W-2 forms as list)
        'income.w2_forms': [
            {
                'employer_name': 'ABC Corporation',
                'wages': 75000.00,
                'federal_withholding': 8500.00,
            }
        ],
        
        # Deductions
        'deductions.method': 'standard',
        
        # Tax Year
        'metadata.tax_year': '2025',
    }
    
    # Create exporter
    exporter = TaxReturnPDFExporter()
    
    # Define output path
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "sample_form_1040_filled.pdf"
    
    print(f"\nFilling Form 1040...")
    print(f"Output: {output_file}")
    
    # Export Form 1040 only
    try:
        success = exporter.export_1040_only(sample_tax_data, str(output_file))
        
        if success:
            print(f"\n✓ SUCCESS: Form filled and saved to {output_file}")
            print(f"  File size: {output_file.stat().st_size:,} bytes")
        else:
            print("\n✗ FAILED: Could not fill form")
            
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
        print("  Make sure the IRSTaxReturnDocumentation folder contains Form 1040.pdf")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print("="*80)


def example_inspect_form_fields():
    """Example: Inspect what fields are available in Form 1040"""
    
    print("\n" + "="*80)
    print("Example: Inspecting Form 1040 Fields")
    print("="*80)
    
    try:
        filler = PDFFormFiller()
        fields = filler.get_form_fields("Form 1040")
        
        print(f"\nTotal fields in Form 1040: {len(fields)}")
        print("\nFirst 20 fields:")
        
        for i, (field_name, field_info) in enumerate(list(fields.items())[:20], 1):
            field_type = field_info.get('type', 'unknown')
            print(f"  {i:2d}. {field_name}")
            print(f"      Type: {field_type}")
        
        print(f"\n... and {len(fields) - 20} more fields")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print("="*80)


def example_complete_return():
    """Example: Export complete tax return with all schedules"""
    
    print("\n" + "="*80)
    print("Example: Exporting Complete Tax Return")
    print("="*80)
    
    # Sample tax data with multiple income sources
    sample_tax_data = {
        'personal_info.first_name': 'Jane',
        'personal_info.middle_initial': 'A',
        'personal_info.last_name': 'Freelancer',
        'personal_info.ssn': '987-65-4321',
        'personal_info.address': '456 Oak Avenue',
        'personal_info.city': 'Portland',
        'personal_info.state': 'OR',
        'personal_info.zip_code': '97201',
        
        'filing_status.status': 'Single',
        
        # W-2 Income
        'income.w2_forms': [
            {
                'employer_name': 'XYZ Company',
                'wages': 50000.00,
                'federal_withholding': 5000.00,
            }
        ],
        
        # Self-Employment Income (requires Schedule C and SE)
        'income.self_employment': 25000.00,
        
        # Unemployment (requires Schedule 1)
        'income.unemployment': 3000.00,
        
        # Student Loan Interest (Schedule 1 adjustment)
        'adjustments.student_loan_interest': 2500.00,
        
        'metadata.tax_year': '2025',
    }
    
    exporter = TaxReturnPDFExporter()
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "complete_tax_return.pdf"
    
    print(f"\nExporting complete tax return...")
    print(f"Output: {output_file}")
    
    try:
        success = exporter.export_complete_return(sample_tax_data, str(output_file))
        
        if success:
            print(f"\n✓ SUCCESS: Complete return saved to {output_file}")
            print(f"  File size: {output_file.stat().st_size:,} bytes")
            print("\nIncluded forms:")
            print("  - Form 1040 (main form)")
            print("  - Schedule 1 (additional income and adjustments)")
            print("  - Schedule C (self-employment income)")
            print("  - Schedule SE (self-employment tax)")
        else:
            print("\n✗ FAILED: Could not export complete return")
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print("="*80)


def main():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("PDF FORM FILLER EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate how to fill IRS PDF forms")
    print("using the actual PDF files from the IRSTaxReturnDocumentation folder.\n")
    
    # Example 1: Fill Form 1040 only
    example_fill_form_1040()
    
    # Example 2: Inspect form fields
    example_inspect_form_fields()
    
    # Example 3: Export complete return with schedules
    example_complete_return()
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)
    print("\nCheck the 'output' folder for generated PDFs.")
    print("="*80)


if __name__ == "__main__":
    main()
