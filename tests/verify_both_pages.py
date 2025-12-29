"""Test filling both pages"""
from pypdf import PdfReader

# Check if both pages have the fields
reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
fields = reader.get_fields()

print("Checking if fields exist in original form:")
print("=" * 80)

test_fields = {
    'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]': 'Wages (Page 1)',
    'topmostSubform[0].Page2[0].f2_18[0]': 'Withholding (Page 2)',
}

for field_name, label in test_fields.items():
    if field_name in fields:
        print(f"✓ {label}: EXISTS")
    else:
        print(f"✗ {label}: NOT FOUND")

# Now check the filled form
print("\nChecking filled form:")
print("=" * 80)
filled_reader = PdfReader('output/sample_form_1040_filled.pdf')
filled_fields = filled_reader.get_fields()

for field_name, label in test_fields.items():
    field = filled_fields.get(field_name, {})
    value = field.get('/V', '')
    print(f"{label}: {value if value else '(empty)'}")
