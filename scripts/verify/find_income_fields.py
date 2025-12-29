"""Find the correct income field names"""
from pypdf import PdfReader

reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
fields = reader.get_fields()

print("All text fields on Page 1 (after address fields):")
print("=" * 80)

count = 0
start_printing = False
for name, field in fields.items():
    if 'Page1[0]' in name and field.get('/FT') == '/Tx':
        # Start printing after we see address fields
        if 'f1_13' in name or start_printing:
            start_printing = True
            print(f"{name}")
            count += 1
            if count >= 30:  # Show first 30 fields after address
                break

print("\n" + "=" * 80)
print("Looking for fields starting around line numbers (f1_15 to f1_30):")
for name in fields.keys():
    if 'Page1[0]' in name and any(f'f1_{i}[0]' in name for i in range(15, 31)):
        field = fields[name]
        if field.get('/FT') == '/Tx':
            print(f"  {name}")
