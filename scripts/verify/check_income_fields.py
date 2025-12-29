"""Check if income fields exist in the form"""
from pypdf import PdfReader

reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
fields = reader.get_fields()

print("Checking for income-related fields:")
print("=" * 80)

target_fields = [
    'topmostSubform[0].Page1[0].f1_24[0]',  # Wages
    'topmostSubform[0].Page2[0].f2_18[0]',  # Withholding
]

for field_name in target_fields:
    if field_name in fields:
        print(f"✓ {field_name} EXISTS")
        field = fields[field_name]
        print(f"  Type: {field.get('/FT')}")
        print(f"  Value: {field.get('/V', '(none)')}")
    else:
        print(f"✗ {field_name} NOT FOUND")

print("\nSearching for fields containing 'f1_24' or 'f2_18':")
for name in fields.keys():
    if 'f1_24' in name or 'f2_18' in name:
        print(f"  {name}")
