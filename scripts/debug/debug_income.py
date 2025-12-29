"""Debug the income mapping"""
from utils.pdf_form_filler import DotDict, Form1040Mapper

# Sample data from example
sample_tax_data = {
    'personal_info.first_name': 'John',
    'filing_status.status': 'Single',
    'income.w2_forms': [
        {
            'employer_name': 'ABC Corporation',
            'wages': 75000.00,
            'federal_withholding': 8500.00,
        }
    ],
}

wrapped = DotDict(sample_tax_data)

print("Testing DotDict access:")
print(f"  wrapped.get('income.w2_forms') = {wrapped.get('income.w2_forms')}")
print(f"  Type: {type(wrapped.get('income.w2_forms'))}")

# Test the mapper
print("\nTesting Form1040Mapper.map_income():")
income_fields = Form1040Mapper.map_income(wrapped)
print(f"  Fields returned: {income_fields}")

print("\nTesting Form1040Mapper.map_payments():")
payment_fields = Form1040Mapper.map_payments(wrapped)
print(f"  Fields returned: {payment_fields}")
