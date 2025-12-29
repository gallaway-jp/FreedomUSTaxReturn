"""Map out the income section fields"""
from pypdf import PdfReader

reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
fields = reader.get_fields()

print("Income section fields (Line4a-11_ReadOrder):")
print("=" * 80)
for name in sorted(fields.keys()):
    if 'Line4a-11_ReadOrder' in name and fields[name].get('/FT') == '/Tx':
        print(f"{name}")

print("\nFields directly under Page1[0] in f1_32-60 range:")
print("=" * 80)
for i in range(32, 61):
    field_name = f'topmostSubform[0].Page1[0].f1_{i}[0]'
    if field_name in fields:
        print(f"{field_name}")
