"""
Comprehensive PDF Data Verification
Shows all filled data in the generated PDF
"""
from pypdf import PdfReader

reader = PdfReader('output/sample_form_1040_filled.pdf')
fields = reader.get_fields()

print("=" * 80)
print("COMPREHENSIVE PDF VERIFICATION")
print("=" * 80)

# Personal Information
print("\n✓ PERSONAL INFORMATION:")
personal_fields = {
    'topmostSubform[0].Page1[0].f1_01[0]': '  First Name',
    'topmostSubform[0].Page1[0].f1_02[0]': '  Middle Initial',
    'topmostSubform[0].Page1[0].f1_03[0]': '  Last Name',
    'topmostSubform[0].Page1[0].f1_04[0]': '  SSN',
    'topmostSubform[0].Page1[0].f1_05[0]': '  Address',
    'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_10[0]': '  City',
    'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_11[0]': '  State',
    'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_12[0]': '  ZIP',
}

for field_name, label in personal_fields.items():
    value = fields.get(field_name, {}).get('/V', '')
    if value:
        print(f'{label}: {value}')

# Filing Status
print("\n✓ FILING STATUS:")
filing_fields = {
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]': '  Single',
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]': '  Married Filing Jointly',
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]': '  Married Filing Separately',
    'topmostSubform[0].Page1[0].c1_3[0]': '  Head of Household',
    'topmostSubform[0].Page1[0].c1_3[1]': '  Qualifying Surviving Spouse',
}

for field_name, label in filing_fields.items():
    value = fields.get(field_name, {}).get('/V', '/Off')
    if value == '/1':
        print(f'{label} [X]')

# Income
print("\n✓ INCOME:")
income_fields = {
    'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]': '  Line 1a - Wages',
}

for field_name, label in income_fields.items():
    value = fields.get(field_name, {}).get('/V', '')
    if value:
        print(f'{label}: ${value}')
    else:
        print(f'{label}: (not filled)')

# Payments
print("\n✓ PAYMENTS:")
payment_fields = {
    'topmostSubform[0].Page2[0].f2_18[0]': '  Line 25a - Federal Withholding',
}

for field_name, label in payment_fields.items():
    value = fields.get(field_name, {}).get('/V', '')
    if value:
        print(f'{label}: ${value}')
    else:
        print(f'{label}: (not filled)')

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
