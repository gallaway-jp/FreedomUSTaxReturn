"""
PDF Form Filler - Fills IRS PDF forms with taxpayer data

DEPRECATED: This module is kept for backward compatibility.
New code should use:
  - utils.pdf.form_filler.PDFFormFiller
  - utils.pdf.form_mappers.Form1040Mapper
  - utils.pdf.field_mapper.DotDict
"""

# Re-export from new modules for backward compatibility
from utils.pdf.form_filler import PDFFormFiller
from utils.pdf.form_mappers import Form1040Mapper
from utils.pdf.field_mapper import DotDict
from utils.tax_calculations import calculate_standard_deduction


class TaxReturnPDFExporter:
    """High-level interface for exporting complete tax returns to PDF"""
    
    def __init__(self, forms_directory: str = None):
        self.form_filler = PDFFormFiller(forms_directory)
    
    def export_1040_only(self, tax_data, output_path: str, password: str = None) -> bool:
        """Export only Form 1040 with optional password protection"""
        self.form_filler.export_form_1040(tax_data, output_path, password)
        return True
    
    def export_complete_return(self, tax_data, output_path: str, password: str = None) -> bool:
        """Export complete tax return - currently just exports 1040"""
        return self.export_1040_only(tax_data, output_path, password)


__all__ = ['PDFFormFiller', 'Form1040Mapper', 'DotDict', 'TaxReturnPDFExporter', 'calculate_standard_deduction']
