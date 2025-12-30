"""
PDF Generation - Main interface for generating complete tax returns

This module provides the main generate_pdf function that analyzes tax data
and generates all applicable IRS forms for a complete tax return.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from utils.async_pdf import AsyncPDFGenerator, PDFGenerationTask, PDFGenerationResult
from utils.plugins import PluginRegistry
from utils.pdf.form_filler import PDFFormFiller

logger = logging.getLogger(__name__)


class TaxReturnPDFGenerator:
    """
    Main class for generating complete tax returns with all applicable forms
    """

    def __init__(self):
        self.plugin_registry = PluginRegistry.get_instance()
        self.pdf_generator = AsyncPDFGenerator()

    def determine_required_forms(self, tax_data: Dict[str, Any]) -> List[str]:
        """
        Analyze tax data and determine which IRS forms are required

        Args:
            tax_data: Complete tax data dictionary

        Returns:
            List of form names that need to be generated
        """
        required_forms = ["Form 1040"]  # Form 1040 is always required

        # Check for Schedule C (self-employment income)
        if self._has_schedule_c_data(tax_data):
            required_forms.append("Schedule C")

        # Check for capital gains/losses (Form 8949)
        if self._has_capital_gains_data(tax_data):
            required_forms.append("Form 8949")

        # Check for dependents
        if self._has_dependents_data(tax_data):
            # Dependents are reported on Form 1040, no separate form needed
            pass

        # Check for other income types that might require schedules
        if self._has_dividend_income(tax_data):
            # Schedule B for dividends/interest over certain amounts
            pass

        # Check for itemized deductions
        if self._has_itemized_deductions(tax_data):
            required_forms.append("Schedule A")

        # Check for retirement income
        if self._has_retirement_income(tax_data):
            required_forms.append("Form 1099-R")

        # Check for rental income
        if self._has_rental_income(tax_data):
            required_forms.append("Schedule E")

        return required_forms

    def _has_schedule_c_data(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains Schedule C information"""
        schedule_c = tax_data.get('schedules', {}).get('schedule_c', {})
        return bool(schedule_c and (schedule_c.get('gross_receipts', 0) > 0 or schedule_c.get('expenses')))

    def _has_capital_gains_data(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains capital gains/losses"""
        capital_gains = tax_data.get('income', {}).get('capital_gains', [])
        return bool(capital_gains and len(capital_gains) > 0)

    def _has_dependents_data(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains dependents"""
        dependents = tax_data.get('dependents', [])
        return bool(dependents and len(dependents) > 0)

    def _has_dividend_income(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains dividend income"""
        dividends = tax_data.get('income', {}).get('dividends', 0)
        return dividends > 0

    def _has_itemized_deductions(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains itemized deductions"""
        deductions = tax_data.get('deductions', {})
        itemized = deductions.get('itemized', {})
        return bool(itemized and sum(itemized.values()) > 0)

    def _has_retirement_income(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains retirement income"""
        retirement = tax_data.get('income', {}).get('retirement', 0)
        return retirement > 0

    def _has_rental_income(self, tax_data: Dict[str, Any]) -> bool:
        """Check if tax data contains rental income"""
        rental = tax_data.get('income', {}).get('rental', {})
        return bool(rental and (rental.get('income', 0) > 0 or rental.get('expenses')))

    def generate_complete_return(
        self,
        tax_data: Dict[str, Any],
        output_directory: str,
        progress_callback: Optional[callable] = None
    ) -> List[PDFGenerationResult]:
        """
        Generate a complete tax return with all applicable forms

        Args:
            tax_data: Complete tax data dictionary
            output_directory: Directory to save generated PDFs
            progress_callback: Optional callback for progress updates

        Returns:
            List of PDFGenerationResult objects for each generated form
        """
        # Ensure output directory exists
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine which forms are needed
        required_forms = self.determine_required_forms(tax_data)
        logger.info(f"Generating forms: {required_forms}")

        # Create PDF generation tasks
        tasks = []
        for form_name in required_forms:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{form_name.replace(' ', '_')}_{timestamp}.pdf"
            output_path = output_dir / filename

            task = PDFGenerationTask(
                form_name=form_name,
                tax_data=tax_data,
                output_path=output_path
            )
            tasks.append(task)

        # Generate all PDFs concurrently
        import asyncio
        try:
            results = asyncio.run(
                self.pdf_generator.generate_multiple_pdfs(tasks, progress_callback)
            )
        except Exception as e:
            logger.error(f"Failed to generate PDFs: {e}")
            # Fallback to synchronous generation if async fails
            results = []
            for task in tasks:
                try:
                    self._generate_single_pdf_sync(task)
                    results.append(PDFGenerationResult(
                        task_id=task.task_id,
                        form_name=task.form_name,
                        success=True,
                        output_path=task.output_path,
                        duration=0.0
                    ))
                except Exception as task_error:
                    logger.error(f"Failed to generate {task.form_name}: {task_error}")
                    results.append(PDFGenerationResult(
                        task_id=task.task_id,
                        form_name=task.form_name,
                        success=False,
                        error=str(task_error),
                        duration=0.0
                    ))

        return results

    def _generate_single_pdf_sync(self, task: PDFGenerationTask) -> None:
        """
        Generate a single PDF synchronously (fallback method)
        """
        filler = PDFFormFiller()

        if task.form_name == "Form 1040":
            filler.export_form_1040(task.tax_data, task.output_path)
        elif task.form_name == "Schedule C":
            self._generate_schedule_c(task)
        elif task.form_name == "Form 8949":
            self._generate_form_8949(task)
        else:
            raise ValueError(f"Unsupported form: {task.form_name}")

        logger.info(f"Generated PDF: {task.output_path}")

    def _generate_schedule_c(self, task: PDFGenerationTask) -> None:
        """
        Generate Schedule C PDF using the plugin system
        """
        plugin = self.plugin_registry.get_plugin("Schedule C")
        if not plugin:
            raise ValueError("Schedule C plugin not found")

        # Get field mappings from plugin
        calculated_data = plugin.calculate_schedule_data(task.tax_data)
        field_mappings = plugin.map_to_pdf_fields(task.tax_data, calculated_data)

        # Generate PDF
        filler = PDFFormFiller()
        filler.fill_form("f1040sc.pdf", field_mappings, str(task.output_path))

    def _generate_form_8949(self, task: PDFGenerationTask) -> None:
        """
        Generate Form 8949 PDF for capital gains/losses
        """
        from utils.pdf.form_mappers import Form8949Mapper
        
        # Get field mappings from Form8949Mapper
        field_mappings = Form8949Mapper.get_all_fields(task.tax_data)
        
        # Generate PDF
        filler = PDFFormFiller()
        filler.fill_form("f8949.pdf", field_mappings, str(task.output_path))


def generate_pdf(
    tax_data: Dict[str, Any],
    output_directory: str,
    progress_callback: Optional[callable] = None
) -> List[PDFGenerationResult]:
    """
    Main function to generate a complete tax return PDF package

    Args:
        tax_data: Complete tax data dictionary
        output_directory: Directory to save generated PDFs
        progress_callback: Optional callback for progress updates

    Returns:
        List of PDFGenerationResult objects for each generated form
    """
    generator = TaxReturnPDFGenerator()
    return generator.generate_complete_return(tax_data, output_directory, progress_callback)</content>
<parameter name="filePath">d:\Development\Python\FreedomUSTaxReturn\utils\pdf_generator.py