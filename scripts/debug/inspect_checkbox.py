"""Inspect how checkboxes work in the PDF"""
from pypdf import PdfReader

# Check the original form
reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
fields = reader.get_fields()

print('Filing Status Checkbox Details:')
print('=' * 80)

filing_fields = [
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]',
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]',
    'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]',
    'topmostSubform[0].Page1[0].c1_3[0]',
    'topmostSubform[0].Page1[0].c1_3[1]',
]

for field_name in filing_fields:
    field = fields.get(field_name)
    if field:
        print(f'\n{field_name}:')
        print(f'  Type: {field.get("/FT")}')
        print(f'  Value: {field.get("/V", "none")}')
        if '/AP' in field:
            print(f'  Appearance: {field["/AP"]}')
        if '/AS' in field:
            print(f'  Appearance State: {field["/AS"]}')
        # Check for valid values
        try:
            if hasattr(field, 'indirect_reference'):
                obj = field.get_object()
                if '/AP' in obj and '/N' in obj['/AP']:
                    print(f'  Valid values: {list(obj["/AP"]["/N"].keys())}')
        except:
            pass
