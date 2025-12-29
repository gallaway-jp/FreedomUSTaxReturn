"""Quick script to check if data was filled in the PDF"""
from pypdf import PdfReader

reader = PdfReader('output/sample_form_1040_filled.pdf')
fields = reader.get_fields()

print('Sample of filled field values:')
print('=' * 80)
count = 0
for name, field in fields.items():
    value = field.get('/V', '')
    if value and str(value).strip():  # Only show fields with values
        print(f'{name}: {value}')
        count += 1
        if count >= 20:
            break

if count == 0:
    print("No filled fields found - PDF is empty!")
else:
    print(f'\n{count} filled fields shown (may be more)')
