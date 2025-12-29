"""Verify wages field is now filled"""
from pypdf import PdfReader

reader = PdfReader('output/sample_form_1040_filled.pdf')
fields = reader.get_fields()

print("INCOME DATA IN PDF:")
print("=" * 80)

income_field = fields.get('topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]', {}).get('/V', '')
print(f"Line 1a - Wages: {income_field if income_field else '(not filled)'}")

withholding_field = fields.get('topmostSubform[0].Page2[0].f2_18[0]', {}).get('/V', '')
print(f"Line 25a - Federal Withholding: {withholding_field if withholding_field else '(not filled)'}")
