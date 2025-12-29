"""Verify all filled data in the PDF"""
from pypdf import PdfReader

reader = PdfReader('output/sample_form_1040_filled.pdf')
fields = reader.get_fields()

print('TAXPAYER DATA IN PDF:')
print('=' * 80)

# Personal info
print('\nPERSONAL INFORMATION:')
name_fields = {
    'topmostSubform[0].Page1[0].f1_01[0]': 'First Name',
    'topmostSubform[0].Page1[0].f1_02[0]': 'Middle Initial',
    'topmostSubform[0].Page1[0].f1_03[0]': 'Last Name',
    'topmostSubform[0].Page1[0].f1_04[0]': 'SSN',
    'topmostSubform[0].Page1[0].f1_05[0]': 'Address',
    'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_10[0]': 'City',
    'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_11[0]': 'State',
    'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_12[0]': 'ZIP',
}

for field_name, label in name_fields.items():
    value = fields.get(field_name, {}).get('/V', '')
    if value:
        print(f'  {label}: {value}')

# Filing status
print('\nFILING STATUS:')
filing_fields = {
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]': 'Single',
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]': 'Married Filing Jointly',
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]': 'Married Filing Separately',
    'topmostSubform[0].Page1[0].c1_3[0]': 'Head of Household',
    'topmostSubform[0].Page1[0].c1_3[1]': 'Qualifying Surviving Spouse',
}

for field_name, label in filing_fields.items():
    value = fields.get(field_name, {}).get('/V', '/Off')
    if value != '/Off':
        print(f'  ✓ {label}')

# Income (look for wage fields)
print('\nINCOME:')
income_field = fields.get('topmostSubform[0].Page1[0].f1_24[0]', {}).get('/V', '')
if income_field:
    print(f'  Wages (Line 1a): ${income_field}')
else:
    print('  Wages (Line 1a): (not filled)')

# Withholding
print('\nPAYMENTS:')
withholding_field = fields.get('topmostSubform[0].Page2[0].f2_18[0]', {}).get('/V', '')
if withholding_field:
    print(f'  Federal Withholding (Line 25a): ${withholding_field}')
else:
    print('  Federal Withholding (Line 25a): (not filled)')

print('\n' + '=' * 80)
