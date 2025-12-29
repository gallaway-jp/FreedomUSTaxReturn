# PDF Form Export Feature

## Overview

The PDF Form Export feature fills **actual IRS PDF forms** from the `IRSTaxReturnDocumentation` folder with your tax data. This creates professional, official tax documents that can be printed or e-filed.

## Key Features

✅ **Uses Official IRS Forms** - Fills the actual PDF forms downloaded from IRS.gov  
✅ **Maintains Form Integrity** - Preserves all form formatting, instructions, and layout  
✅ **Field Mapping** - Automatically maps your tax data to the correct form fields  
✅ **Multi-Form Support** - Combines multiple schedules into a single PDF  
✅ **Print-Ready Output** - Generated PDFs can be printed and mailed to the IRS

## How It Works

### Architecture

```
User Tax Data → Field Mapper → PDF Form Filler → Filled PDF
                     ↓
              (Form 1040 Mapper)
                     ↓
         Maps data to IRS field names
```

### Components

1. **PDFFormFiller** (`utils/pdf_form_filler.py`)
   - Low-level PDF form manipulation
   - Reads and writes PDF form fields
   - Combines multiple forms into one PDF

2. **Form1040Mapper** (`utils/pdf_form_filler.py`)
   - Maps tax data to Form 1040 field names
   - Handles personal info, income, deductions, credits, etc.
   - Calculates which schedules are needed

3. **TaxReturnPDFExporter** (`utils/pdf_form_filler.py`)
   - High-level export interface
   - Determines required forms based on tax situation
   - Orchestrates the export process

4. **PDFFieldInspector** (`utils/pdf_field_inspector.py`)
   - Discovers field names in IRS PDF forms
   - Helps developers add support for new forms
   - Debugging tool for field mapping

## Usage

### From the GUI

1. Complete your tax return in the application
2. Navigate to the "Form Viewer" page
3. Click "Export to PDF"
4. Choose save location
5. Your filled forms are saved as a PDF!

### Programmatic Usage

```python
from utils.pdf_form_filler import TaxReturnPDFExporter

# Your tax data
tax_data = {
    'personal.first_name': 'John',
    'personal.last_name': 'Doe',
    'personal.ssn': '123-45-6789',
    'filing_status': 'Single',
    'w2.total_wages': 75000.00,
    # ... more fields
}

# Export Form 1040 only
exporter = TaxReturnPDFExporter()
exporter.export_1040_only(tax_data, "my_1040.pdf")

# Export complete return with all schedules
exporter.export_complete_return(tax_data, "complete_return.pdf")
```

## Field Mapping

### Form 1040 Field Names

IRS PDF forms use specific internal field names. Here's how common data maps to Form 1040:

| Application Data | Form 1040 Field Name | Description |
|-----------------|---------------------|-------------|
| `personal.first_name` | `topmostSubform[0].Page1[0].f1_01[0]` | First name |
| `personal.last_name` | `topmostSubform[0].Page1[0].f1_03[0]` | Last name |
| `personal.ssn` | `topmostSubform[0].Page1[0].f1_04[0]` | Social Security Number |
| `w2.total_wages` | `topmostSubform[0].Page1[0].f1_11[0]` | Line 1a - Wages |
| `deductions.standard_deduction` | `topmostSubform[0].Page1[0].f1_22[0]` | Line 12 - Standard deduction |
| `calculations.total_tax` | `topmostSubform[0].Page2[0].f2_01[0]` | Line 16 - Tax |
| `w2.federal_withholding` | `topmostSubform[0].Page2[0].f2_09[0]` | Line 25a - Federal withholding |

### Filing Status Checkboxes

| Application Value | Form Field | Checkbox |
|------------------|-----------|----------|
| `Single` | `topmostSubform[0].Page1[0].c1_01[0]` | ✓ Single |
| `Married Filing Jointly` | `topmostSubform[0].Page1[0].c1_01[1]` | ✓ Married filing jointly |
| `Married Filing Separately` | `topmostSubform[0].Page1[0].c1_01[2]` | ✓ Married filing separately |
| `Head of Household` | `topmostSubform[0].Page1[0].c1_01[3]` | ✓ Head of household |
| `Qualifying Surviving Spouse` | `topmostSubform[0].Page1[0].c1_01[4]` | ✓ Qualifying surviving spouse |

## Discovering Form Fields

To find field names in any IRS PDF form:

```bash
# Inspect Form 1040
python utils/pdf_field_inspector.py "IRSTaxReturnDocumentation/Form 1040.pdf"

# Inspect with detailed information
python utils/pdf_field_inspector.py "IRSTaxReturnDocumentation/Form 1040.pdf" --verbose

# Inspect all common forms
python utils/pdf_field_inspector.py
```

Output shows:
- Total number of fields
- Field types (text, checkbox, dropdown)
- Internal field names
- Default values

## Adding Support for New Forms

To add support for a new IRS form:

### 1. Inspect the Form

```bash
python utils/pdf_field_inspector.py "IRSTaxReturnDocumentation/Form 1040 (Schedule A).pdf" > schedule_a_fields.txt
```

### 2. Create a Mapper Class

```python
class ScheduleAMapper:
    """Maps tax data to Schedule A (Itemized Deductions) fields"""
    
    @staticmethod
    def map_medical_expenses(tax_data) -> Dict[str, str]:
        """Map medical expense fields"""
        fields = {}
        
        medical = tax_data.get('itemized.medical_expenses', 0)
        if medical:
            fields['topmostSubform[0].Page1[0].f1_01[0]'] = f"{medical:,.2f}"
        
        return fields
    
    @staticmethod
    def map_taxes_paid(tax_data) -> Dict[str, str]:
        """Map state/local taxes"""
        fields = {}
        
        salt = tax_data.get('itemized.salt', 0)
        if salt:
            # Subject to $10,000 limit (or $40,000 for 2025)
            capped_salt = min(salt, 40000)
            fields['topmostSubform[0].Page1[0].f1_05[0]'] = f"{capped_salt:,.2f}"
        
        return fields
    
    @classmethod
    def get_all_fields(cls, tax_data) -> Dict[str, str]:
        """Get all Schedule A field mappings"""
        fields = {}
        fields.update(cls.map_medical_expenses(tax_data))
        fields.update(cls.map_taxes_paid(tax_data))
        # ... more sections
        return fields
```

### 3. Update TaxReturnPDFExporter

```python
def export_complete_return(self, tax_data, output_path: str) -> bool:
    # ... existing code ...
    
    # Add Schedule A if itemizing
    if data_dict.get('deductions.itemize', False):
        forms_to_include.append({
            'form_name': 'Form 1040 (Schedule A)',
            'field_values': ScheduleAMapper.get_all_fields(data_dict)
        })
```

## Technical Details

### Dependencies

- **pypdf** - Modern PDF manipulation library (replaces PyPDF2)
- Python 3.8+

Install: `pip install pypdf`

### PDF Form Fields

IRS forms use Adobe PDF form technology with AcroForm fields:

- **Text Fields** (`/Tx`) - For names, addresses, dollar amounts
- **Check Boxes** (`/Btn`) - For yes/no options, filing status
- **Choice Fields** (`/Ch`) - For dropdowns (rare in IRS forms)

### Limitations

1. **Field Names May Change** - IRS updates forms annually; field names may change
2. **Calculated Fields** - Some forms have JavaScript calculations; these are preserved but may need manual verification
3. **State Forms** - Only federal forms are included
4. **E-File Codes** - Generated PDFs are for mailing; e-filing requires additional XML generation

## Troubleshooting

### Form Not Found Error

**Problem:** `FileNotFoundError: Form not found: IRSTaxReturnDocumentation/Form 1040.pdf`

**Solution:**
1. Ensure the PDF exists in `IRSTaxReturnDocumentation/`
2. Check exact filename (case-sensitive, include spaces)
3. Re-download from IRS.gov if missing

### Fields Not Filling

**Problem:** PDF is generated but fields are empty

**Solution:**
1. Use PDF field inspector to verify field names
2. Check data mapping in Form1040Mapper
3. Ensure tax data uses correct keys (e.g., `personal.first_name`)
4. Verify data types (numbers should be floats, not strings)

### Incorrect Values

**Problem:** Values appear in wrong locations or are formatted incorrectly

**Solution:**
1. Inspect form to verify field name mapping
2. Check number formatting (should be `"1,234.56"` format)
3. For checkboxes, ensure value is `'1'` (string) not boolean
4. Update mapper to match current year's form layout

## Examples

See `example_pdf_export.py` for complete working examples:

```bash
python example_pdf_export.py
```

This demonstrates:
- Filling Form 1040 with sample data
- Inspecting form fields
- Exporting complete returns with multiple schedules

## Future Enhancements

Planned improvements:

- [ ] Support for all common IRS schedules
- [ ] Automatic field name discovery and mapping
- [ ] Form validation before export
- [ ] PDF/A compliance for archival
- [ ] Batch export for multiple years
- [ ] State tax form support
- [ ] E-file XML generation

## Security Notes

⚠️ **Important Security Considerations:**

1. **Do not store filled PDFs with SSNs in cloud folders**
2. **Encrypt PDF files containing tax data** (use PDF password protection)
3. **Delete generated PDFs after mailing** (or store securely)
4. **Never email unencrypted tax returns**
5. **Verify recipient before transmitting**

### Recommended Workflow

```python
# 1. Export with encryption (future enhancement)
exporter.export_1040_only(tax_data, "my_1040.pdf", password="SecurePassword123!")

# 2. Print immediately
# (manual step - open PDF and print)

# 3. Securely delete digital copy
import os
os.remove("my_1040.pdf")
```

## Related Documentation

- [IRS Form 1040 Instructions](https://www.irs.gov/pub/irs-pdf/i1040gi.pdf)
- [IRS Tax Forms](https://www.irs.gov/forms-instructions)
- [pypdf Documentation](https://pypdf.readthedocs.io/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run `python utils/pdf_field_inspector.py` to verify forms
3. Review `example_pdf_export.py` for correct usage
4. Check IRS.gov for current year form updates
