"""Test checkbox values"""
from pypdf import PdfReader, PdfWriter

# Read original form
reader = PdfReader('IRSTaxReturnDocumentation/Form 1040.pdf')
writer = PdfWriter()
writer.append(reader)

# Try different checkbox values
test_values = ['/1', '/Yes', '/On', '1', 'Yes', 'On', '/X']

for i, test_val in enumerate(test_values):
    try:
        writer.update_page_form_field_values(
            writer.pages[0],
            {'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]': test_val}
        )
        
        # Save and check
        output_path = f'output/test_checkbox_{i}.pdf'
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Read back
        test_reader = PdfReader(output_path)
        fields = test_reader.get_fields()
        field_val = fields['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]'].get('/V', 'none')
        
        print(f'{test_val} -> Result: {field_val}')
        
        # Reset for next test
        writer = PdfWriter()
        writer.append(reader)
        
    except Exception as e:
        print(f'{test_val} -> Error: {e}')
