"""
State Form PDF Generator - Generate state tax return PDFs

This module provides functionality for:
- State-specific tax form generation
- PDF creation for state tax returns
- Form field population for major states
- State form validation and completion
"""

import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from services.state_tax_service import StateTaxService, StateCode, StateTaxCalculation
from constants.pdf_fields import (
    California540Fields, NewYorkIT201Fields, NewJersey1040Fields,
    IllinoisIL1040Fields, PennsylvaniaPA40Fields, Massachusetts1Fields
)
from utils.pdf.pdf_generator import TaxReturnPDFGenerator

logger = logging.getLogger(__name__)


@dataclass
class StateFormData:
    """Data structure for state form generation"""
    state_code: StateCode
    tax_year: int
    taxpayer_info: Dict[str, Any]
    income_data: Dict[str, Any]
    tax_calculation: StateTaxCalculation
    filing_status: str
    dependents: int


class StateFormPDFGenerator:
    """
    Generator for state tax return PDF forms.

    Handles PDF generation for state-specific tax forms with proper field mapping.
    """

    def __init__(self):
        self.state_service = StateTaxService()
        self.templates_dir = Path(__file__).parent.parent / "templates" / "state_forms"

        # Ensure templates directory exists
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def generate_state_form_pdf(self, form_data: StateFormData,
                              output_path: Optional[str] = None) -> str:
        """
        Generate a state tax form PDF.

        Args:
            form_data: State form data including taxpayer info and calculations
            output_path: Optional custom output path

        Returns:
            Path to generated PDF file

        Raises:
            ValueError: If state is not supported or template not found
        """
        if form_data.state_code not in self.get_supported_states():
            raise ValueError(f"State {form_data.state_code.value} is not supported for PDF generation")

        # Generate default output path if not provided
        if output_path is None:
            output_path = self._generate_output_path(form_data)

        # Prepare form field data
        field_data = self._prepare_form_fields(form_data)

        # Generate PDF using reportlab
        try:
            self._generate_pdf_with_reportlab(form_data, output_path)
            logger.info(f"Generated state form PDF: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate state form PDF: {e}")
            raise

    def get_supported_states(self) -> List[StateCode]:
        """Get list of states supported for PDF generation"""
        return [
            StateCode.CA,  # California
            StateCode.NY,  # New York
            StateCode.NJ,  # New Jersey
            StateCode.IL,  # Illinois
            StateCode.PA,  # Pennsylvania
            StateCode.MA,  # Massachusetts
        ]

    def _get_template_path(self, state_code: StateCode) -> Path:
        """Get the template file path for a state"""
        template_map = {
            StateCode.CA: "ca_540.pdf",
            StateCode.NY: "ny_it201.pdf",
            StateCode.NJ: "nj_1040.pdf",
            StateCode.IL: "il_1040.pdf",
            StateCode.PA: "pa_40.pdf",
            StateCode.MA: "ma_1.pdf",
        }

        template_file = template_map.get(state_code)
        if not template_file:
            raise ValueError(f"No template mapping for state {state_code.value}")

        return self.templates_dir / template_file

    def _generate_output_path(self, form_data: StateFormData) -> str:
        """Generate default output path for the PDF"""
        taxpayer_name = form_data.taxpayer_info.get('last_name', 'Unknown')
        state_code = form_data.state_code.value
        tax_year = form_data.tax_year

        filename = f"{taxpayer_name}_{state_code}_{tax_year}_tax_return.pdf"
        return str(Path.cwd() / "output" / filename)

    def _prepare_form_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare form field data based on state and form data"""
        state_code = form_data.state_code

        if state_code == StateCode.CA:
            return self._prepare_california_fields(form_data)
        elif state_code == StateCode.NY:
            return self._prepare_new_york_fields(form_data)
        elif state_code == StateCode.NJ:
            return self._prepare_new_jersey_fields(form_data)
        elif state_code == StateCode.IL:
            return self._prepare_illinois_fields(form_data)
        elif state_code == StateCode.PA:
            return self._prepare_pennsylvania_fields(form_data)
        elif state_code == StateCode.MA:
            return self._prepare_massachusetts_fields(form_data)
        else:
            raise ValueError(f"Unsupported state for field preparation: {state_code.value}")

    def _prepare_california_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare field data for California Form 540"""
        fields = {}
        info = form_data.taxpayer_info
        calc = form_data.tax_calculation

        # Personal Information
        fields[California540Fields.SSN] = info.get('ssn', '')
        fields[California540Fields.FIRST_NAME] = info.get('first_name', '')
        fields[California540Fields.MIDDLE_INITIAL] = info.get('middle_initial', '')
        fields[California540Fields.LAST_NAME] = info.get('last_name', '')

        # Address
        fields[California540Fields.ADDRESS] = info.get('address', '')
        fields[California540Fields.CITY] = info.get('city', '')
        fields[California540Fields.STATE] = info.get('state', '')
        fields[California540Fields.ZIP_CODE] = info.get('zip_code', '')

        # Filing Status
        status_map = {
            'single': California540Fields.SINGLE,
            'married_joint': California540Fields.MARRIED_FILING_JOINTLY,
            'married_separate': California540Fields.MARRIED_FILING_SEPARATELY,
            'head_household': California540Fields.HEAD_OF_HOUSEHOLD,
        }
        if form_data.filing_status in status_map:
            fields[status_map[form_data.filing_status]] = '/1'  # Checked

        # Income and Tax Data
        fields[California540Fields.FEDERAL_ADJUSTED_GROSS_INCOME] = f"{form_data.income_data.get('federal_agi', 0):.2f}"
        fields[California540Fields.CALIFORNIA_ADJUSTED_GROSS_INCOME] = f"{calc.taxable_income:.2f}"
        fields[California540Fields.TAX] = f"{calc.tax_owed:.2f}"
        fields[California540Fields.NET_TAX] = f"{calc.tax_owed:.2f}"

        return fields

    def _prepare_new_york_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare field data for New York Form IT-201"""
        fields = {}
        info = form_data.taxpayer_info
        calc = form_data.tax_calculation

        # Personal Information
        fields[NewYorkIT201Fields.SSN] = info.get('ssn', '')
        fields[NewYorkIT201Fields.FIRST_NAME] = info.get('first_name', '')
        fields[NewYorkIT201Fields.MIDDLE_INITIAL] = info.get('middle_initial', '')
        fields[NewYorkIT201Fields.LAST_NAME] = info.get('last_name', '')

        # Address
        fields[NewYorkIT201Fields.ADDRESS] = info.get('address', '')
        fields[NewYorkIT201Fields.CITY] = info.get('city', '')
        fields[NewYorkIT201Fields.STATE] = info.get('state', '')
        fields[NewYorkIT201Fields.ZIP_CODE] = info.get('zip_code', '')

        # Filing Status
        status_map = {
            'single': NewYorkIT201Fields.SINGLE,
            'married_joint': NewYorkIT201Fields.MARRIED_FILING_JOINTLY,
            'married_separate': NewYorkIT201Fields.MARRIED_FILING_SEPARATELY,
            'head_household': NewYorkIT201Fields.HEAD_OF_HOUSEHOLD,
        }
        if form_data.filing_status in status_map:
            fields[status_map[form_data.filing_status]] = '/1'  # Checked

        # Income and Tax Data
        fields[NewYorkIT201Fields.FEDERAL_AGI] = f"{form_data.income_data.get('federal_agi', 0):.2f}"
        fields[NewYorkIT201Fields.NEW_YORK_AGI] = f"{calc.taxable_income:.2f}"
        fields[NewYorkIT201Fields.TAXABLE_INCOME] = f"{calc.taxable_income:.2f}"
        fields[NewYorkIT201Fields.TAX_BEFORE_CREDITS] = f"{calc.tax_owed:.2f}"
        fields[NewYorkIT201Fields.TAX_AFTER_CREDITS] = f"{calc.tax_owed:.2f}"

        return fields

    def _prepare_new_jersey_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare field data for New Jersey Form NJ-1040"""
        fields = {}
        info = form_data.taxpayer_info
        calc = form_data.tax_calculation

        # Personal Information
        fields[NewJersey1040Fields.SSN] = info.get('ssn', '')
        fields[NewJersey1040Fields.FIRST_NAME] = info.get('first_name', '')
        fields[NewJersey1040Fields.MIDDLE_INITIAL] = info.get('middle_initial', '')
        fields[NewJersey1040Fields.LAST_NAME] = info.get('last_name', '')

        # Address
        fields[NewJersey1040Fields.ADDRESS] = info.get('address', '')
        fields[NewJersey1040Fields.CITY] = info.get('city', '')
        fields[NewJersey1040Fields.STATE] = info.get('state', '')
        fields[NewJersey1040Fields.ZIP_CODE] = info.get('zip_code', '')

        # Filing Status
        status_map = {
            'single': NewJersey1040Fields.SINGLE,
            'married_joint': NewJersey1040Fields.MARRIED_FILING_JOINTLY,
            'married_separate': NewJersey1040Fields.MARRIED_FILING_SEPARATELY,
            'head_household': NewJersey1040Fields.HEAD_OF_HOUSEHOLD,
        }
        if form_data.filing_status in status_map:
            fields[status_map[form_data.filing_status]] = '/1'  # Checked

        # Income and Tax Data
        fields[NewJersey1040Fields.WAGES] = f"{form_data.income_data.get('wages', 0):.2f}"
        fields[NewJersey1040Fields.TAXABLE_INCOME] = f"{calc.taxable_income:.2f}"
        fields[NewJersey1040Fields.TAX_DUE] = f"{calc.tax_owed:.2f}"

        return fields

    def _prepare_illinois_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare field data for Illinois Form IL-1040"""
        fields = {}
        info = form_data.taxpayer_info
        calc = form_data.tax_calculation

        # Personal Information
        fields[IllinoisIL1040Fields.SSN] = info.get('ssn', '')
        fields[IllinoisIL1040Fields.FIRST_NAME] = info.get('first_name', '')
        fields[IllinoisIL1040Fields.MIDDLE_INITIAL] = info.get('middle_initial', '')
        fields[IllinoisIL1040Fields.LAST_NAME] = info.get('last_name', '')

        # Address
        fields[IllinoisIL1040Fields.ADDRESS] = info.get('address', '')
        fields[IllinoisIL1040Fields.CITY] = info.get('city', '')
        fields[IllinoisIL1040Fields.STATE] = info.get('state', '')
        fields[IllinoisIL1040Fields.ZIP_CODE] = info.get('zip_code', '')

        # Filing Status
        status_map = {
            'single': IllinoisIL1040Fields.SINGLE,
            'married_joint': IllinoisIL1040Fields.MARRIED_FILING_JOINTLY,
            'married_separate': IllinoisIL1040Fields.MARRIED_FILING_SEPARATELY,
            'head_household': IllinoisIL1040Fields.HEAD_OF_HOUSEHOLD,
        }
        if form_data.filing_status in status_map:
            fields[status_map[form_data.filing_status]] = '/1'  # Checked

        # Income and Tax Data
        fields[IllinoisIL1040Fields.FEDERAL_AGI] = f"{form_data.income_data.get('federal_agi', 0):.2f}"
        fields[IllinoisIL1040Fields.ILLINOIS_BASE_INCOME] = f"{calc.taxable_income:.2f}"
        fields[IllinoisIL1040Fields.NET_INCOME] = f"{calc.taxable_income:.2f}"
        fields[IllinoisIL1040Fields.TAX_DUE] = f"{calc.tax_owed:.2f}"

        return fields

    def _prepare_pennsylvania_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare field data for Pennsylvania Form PA-40"""
        fields = {}
        info = form_data.taxpayer_info
        calc = form_data.tax_calculation

        # Personal Information
        fields[PennsylvaniaPA40Fields.SSN] = info.get('ssn', '')
        fields[PennsylvaniaPA40Fields.FIRST_NAME] = info.get('first_name', '')
        fields[PennsylvaniaPA40Fields.MIDDLE_INITIAL] = info.get('middle_initial', '')
        fields[PennsylvaniaPA40Fields.LAST_NAME] = info.get('last_name', '')

        # Address
        fields[PennsylvaniaPA40Fields.ADDRESS] = info.get('address', '')
        fields[PennsylvaniaPA40Fields.CITY] = info.get('city', '')
        fields[PennsylvaniaPA40Fields.STATE] = info.get('state', '')
        fields[PennsylvaniaPA40Fields.ZIP_CODE] = info.get('zip_code', '')

        # Filing Status
        status_map = {
            'single': PennsylvaniaPA40Fields.SINGLE,
            'married_joint': PennsylvaniaPA40Fields.MARRIED_FILING_JOINTLY,
            'married_separate': PennsylvaniaPA40Fields.MARRIED_FILING_SEPARATELY,
        }
        if form_data.filing_status in status_map:
            fields[status_map[form_data.filing_status]] = '/1'  # Checked

        # Income and Tax Data
        fields[PennsylvaniaPA40Fields.FEDERAL_GROSS_INCOME] = f"{form_data.income_data.get('federal_gross_income', 0):.2f}"
        fields[PennsylvaniaPA40Fields.TAXABLE_INCOME] = f"{calc.taxable_income:.2f}"
        fields[PennsylvaniaPA40Fields.TAX_DUE] = f"{calc.tax_owed:.2f}"

        return fields

    def _prepare_massachusetts_fields(self, form_data: StateFormData) -> Dict[str, Any]:
        """Prepare field data for Massachusetts Form 1"""
        fields = {}
        info = form_data.taxpayer_info
        calc = form_data.tax_calculation

        # Personal Information
        fields[Massachusetts1Fields.SSN] = info.get('ssn', '')
        fields[Massachusetts1Fields.FIRST_NAME] = info.get('first_name', '')
        fields[Massachusetts1Fields.MIDDLE_INITIAL] = info.get('middle_initial', '')
        fields[Massachusetts1Fields.LAST_NAME] = info.get('last_name', '')

        # Address
        fields[Massachusetts1Fields.ADDRESS] = info.get('address', '')
        fields[Massachusetts1Fields.CITY] = info.get('city', '')
        fields[Massachusetts1Fields.STATE] = info.get('state', '')
        fields[Massachusetts1Fields.ZIP_CODE] = info.get('zip_code', '')

        # Filing Status
        status_map = {
            'single': Massachusetts1Fields.SINGLE,
            'married_joint': Massachusetts1Fields.MARRIED_FILING_JOINTLY,
            'married_separate': Massachusetts1Fields.MARRIED_FILING_SEPARATELY,
            'head_household': Massachusetts1Fields.HEAD_OF_HOUSEHOLD,
        }
        if form_data.filing_status in status_map:
            fields[status_map[form_data.filing_status]] = '/1'  # Checked

        # Income and Tax Data
        fields[Massachusetts1Fields.WAGES] = f"{form_data.income_data.get('wages', 0):.2f}"
        fields[Massachusetts1Fields.MA_ADJUSTED_GROSS_INCOME] = f"{calc.taxable_income:.2f}"
        fields[Massachusetts1Fields.TAXABLE_INCOME] = f"{calc.taxable_income:.2f}"
        fields[Massachusetts1Fields.TAX_DUE] = f"{calc.tax_owed:.2f}"

        return fields

    def _generate_pdf_with_reportlab(self, form_data: StateFormData, output_path: str):
        """Generate PDF using reportlab with form data"""
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        state_info = self.state_service.get_state_info(form_data.state_code)
        state_name = state_info.name if state_info else form_data.state_code.value
        title = f"{state_name} State Income Tax Return - {form_data.tax_year}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

        # Taxpayer Information
        story.append(Paragraph("Taxpayer Information", styles['Heading2']))
        taxpayer_data = [
            ["Field", "Value"],
            ["Name", f"{form_data.taxpayer_info.get('first_name', '')} {form_data.taxpayer_info.get('last_name', '')}"],
            ["SSN", form_data.taxpayer_info.get('ssn', '')],
            ["Address", form_data.taxpayer_info.get('address', '')],
            ["City, State, ZIP", f"{form_data.taxpayer_info.get('city', '')}, {form_data.taxpayer_info.get('state', '')} {form_data.taxpayer_info.get('zip_code', '')}"],
            ["Filing Status", form_data.filing_status.title()],
            ["Dependents", str(form_data.dependents)]
        ]
        taxpayer_table = Table(taxpayer_data)
        taxpayer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(taxpayer_table)
        story.append(Spacer(1, 12))

        # Income Information
        story.append(Paragraph("Income Information", styles['Heading2']))
        income_data = [
            ["Income Type", "Amount"],
            ["Federal Adjusted Gross Income", f"${form_data.income_data.get('federal_agi', 0):,.2f}"],
            ["Wages", f"${form_data.income_data.get('wages', 0):,.2f}"],
            ["Interest", f"${form_data.income_data.get('interest', 0):,.2f}"],
            ["Dividends", f"${form_data.income_data.get('dividends', 0):,.2f}"],
            ["Business Income", f"${form_data.income_data.get('business_income', 0):,.2f}"]
        ]
        income_table = Table(income_data)
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(income_table)
        story.append(Spacer(1, 12))

        # Tax Calculation
        story.append(Paragraph("Tax Calculation", styles['Heading2']))
        calc = form_data.tax_calculation
        tax_data = [
            ["Calculation Item", "Amount"],
            ["Taxable Income", f"${calc.taxable_income:,.2f}"],
            ["Tax Rate", f"{calc.effective_rate:.2%}"],
            ["Tax Owed", f"${calc.tax_owed:,.2f}"],
            ["Credits", f"${calc.credits:,.2f}"],
            ["Net Tax Due", f"${calc.tax_owed - calc.credits:,.2f}"]
        ]
        tax_table = Table(tax_data)
        tax_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(tax_table)
        story.append(Spacer(1, 12))

        # Disclaimer
        disclaimer = """
        <b>Important Notice:</b> This is a computer-generated representation of your state tax return for informational purposes only.
        It is not an official tax form and should not be filed with your state tax authority.
        Please consult with a tax professional and use official state tax forms for actual filing.
        """
        story.append(Paragraph(disclaimer, styles['Normal']))

        # Build the PDF
        doc.build(story)