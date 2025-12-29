"""Check filing status checkbox fields"""
from pypdf import PdfReader

reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
fields = reader.get_fields()

print('Filing status related fields:')
print('=' * 80)
for name, field in fields.items():
    if 'filing' in name.lower() or 'c1_3' in name or 'c1_01' in name or 'c1_02' in name:
        field_type = field.get('/FT', 'unknown')
        print(f'{name}')
        print(f'  Type: {field_type}')
        if '/V' in field:
            print(f'  Default Value: {field["/V"]}')
        print()
