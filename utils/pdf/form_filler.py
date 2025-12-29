"""
PDF Form Filler - Core functionality for filling IRS PDF forms

This module handles the low-level PDF operations including
reading form fields, writing data to PDFs, and managing form files.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache
from pypdf import PdfReader, PdfWriter
from utils.pdf.form_mappers import Form1040Mapper
from utils.pdf.field_mapper import DotDict

logger = logging.getLogger(__name__)


class PDFFormFiller:
    """
    Handles filling PDF forms with taxpayer data.
    
    This class manages PDF file operations including:
    - Loading IRS form PDFs
    - Inspecting form fields
    - Filling forms with data
    - Exporting completed PDFs
    """
    
    def __init__(self, forms_directory: str = None):
        """
        Initialize PDF form filler.
        
        Args:
            forms_directory: Path to directory containing IRS PDF forms
        """
        if forms_directory is None:
            # Default to IRSTaxReturnDocumentation folder
            base_dir = Path(__file__).parent.parent.parent
            self.forms_directory = base_dir / "IRSTaxReturnDocumentation"
        else:
            self.forms_directory = Path(forms_directory)
            
        if not self.forms_directory.exists():
            raise FileNotFoundError(f"Forms directory not found: {self.forms_directory}")
    
    def get_form_path(self, form_name: str) -> Path:
        """
        Get path to a specific form PDF.
        
        Args:
            form_name: Name of the form (e.g., "Form 1040", "Form 1040 (Schedule 1)")
            
        Returns:
            Path to the PDF file
        """
        pdf_path = self.forms_directory / f"{form_name}.pdf"
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"Form not found: {pdf_path}")
        
        return pdf_path
    
    def get_form_fields(self, form_name: str) -> Dict[str, Any]:
        """
        Get all fillable fields from a PDF form.
        
        Args:
            form_name: Name of the form
            
        Returns:
            Dictionary of field names and their properties
        """
        form_path = self.get_form_path(form_name)
        
        reader = PdfReader(str(form_path))
        
        fields = {}
        if reader.get_fields():
            for field_name, field_info in reader.get_fields().items():
                fields[field_name] = {
                    'type': field_info.get('/FT', 'unknown'),
                    'value': field_info.get('/V', ''),
                    'flags': field_info.get('/Ff', 0)
                }
        
        return fields
    
    def inspect_form_fields(self, form_name: str) -> None:
        """
        Print all fields in a form for debugging.
        
        Args:
            form_name: Name of the form to inspect
        """
        fields = self.get_form_fields(form_name)
        
        logger.info(f"\n=== Fields in {form_name} ===")
        for field_name, field_info in sorted(fields.items()):
            logger.info(f"{field_name}")
            logger.info(f"  Type: {field_info['type']}")
            logger.info(f"  Value: {field_info['value']}")
            logger.info(f"  Flags: {field_info['flags']}")
        logger.info(f"\nTotal fields: {len(fields)}")
    
    def fill_form(
        self,
        form_name: str,
        field_values: Dict[str, str],
        output_path: str,
        flatten: bool = False
    ) -> None:
        """
        Fill a PDF form with provided values.
        
        Args:
            form_name: Name of the form to fill
            field_values: Dictionary mapping field names to values
            output_path: Path where filled PDF should be saved
            flatten: If True, flatten form (make fields non-editable)
        """
        form_path = self.get_form_path(form_name)
        
        # Read the form
        reader = PdfReader(str(form_path))
        writer = PdfWriter()
        
        # Clone all pages first
        writer.append(reader)
        
        # Update form fields if they exist
        if field_values and reader.get_fields():
            # Update fields on each page (fields can be on any page)
            for page in writer.pages:
                try:
                    writer.update_page_form_field_values(
                        page,
                        field_values
                    )
                except Exception:
                    # Skip if page doesn't have form fields
                    pass
        
        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'wb') as f:
            writer.write(f)
        
        logger.info(f"Created PDF: {output_file}")
    
    def export_form_1040(
        self,
        tax_data,
        output_path: str,
        flatten: bool = False
    ) -> None:
        """
        Export Form 1040 with tax data.
        
        Args:
            tax_data: Tax data object or dictionary
            output_path: Path where filled PDF should be saved
            flatten: If True, flatten form (make fields non-editable)
        """
        # Wrap dict in DotDict if needed
        if isinstance(tax_data, dict) and not hasattr(tax_data, 'get'):
            tax_data = DotDict(tax_data)
        
        # Get all field mappings
        fields = Form1040Mapper.get_all_fields(tax_data)
        
        # Fill the form
        self.fill_form('Form 1040', fields, output_path, flatten)
        
        logger.info(f"Exported Form 1040 to {output_path}")
