"""
Import Utilities - Import tax data from various sources

This module provides functionality to import tax data from:
- Prior year returns (JSON format)
- W-2 forms (PDF format)
- 1099 forms (PDF format)
- Tax software exports (TXF format)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from pypdf import PdfReader
import re

logger = logging.getLogger(__name__)


class TaxDataImporter:
    """
    Handles importing tax data from various sources.

    Supports importing from:
    - Prior year tax returns (JSON)
    - W-2 forms (PDF)
    - 1099 forms (PDF)
    - Tax software exports (TXF)
    """

    def __init__(self):
        self.supported_formats = {
            'json': self._import_from_json,
            'pdf': self._import_from_pdf,
            'txf': self._import_from_txf
        }

    def import_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Import tax data from a file.

        Args:
            file_path: Path to the file to import

        Returns:
            Dictionary containing imported tax data

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = path.suffix.lower().lstrip('.')

        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")

        importer = self.supported_formats[file_extension]
        return importer(file_path)

    def _import_from_json(self, file_path: str) -> Dict[str, Any]:
        """
        Import tax data from JSON file (prior year return).

        Args:
            file_path: Path to JSON file

        Returns:
            Tax data dictionary
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate that this looks like tax data
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON format: expected dictionary")

        # Basic validation - check for expected top-level keys
        expected_keys = ['personal_info', 'filing_status', 'income', 'deductions']
        if not any(key in data for key in expected_keys):
            logger.warning("JSON file may not contain tax data - missing expected keys")

        logger.info(f"Successfully imported tax data from JSON: {file_path}")
        return data

    def _import_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Import tax data from PDF file (W-2, 1099, etc.).

        Args:
            file_path: Path to PDF file

        Returns:
            Tax data dictionary with extracted form data
        """
        # Read PDF content
        reader = PdfReader(file_path)
        text_content = ""

        # Extract text from all pages
        for page in reader.pages:
            text_content += page.extract_text() + "\n"

        # Determine form type and extract data
        form_type = self._identify_form_type(text_content)

        if form_type == 'w2':
            return self._extract_w2_data(text_content)
        elif form_type.startswith('1099'):
            return self._extract_1099_data(text_content, form_type)
        else:
            raise ValueError(f"Unsupported PDF form type: {form_type}")

    def _identify_form_type(self, text_content: str) -> str:
        """
        Identify the type of tax form from PDF text content.

        Args:
            text_content: Extracted text from PDF

        Returns:
            Form type identifier (e.g., 'w2', '1099-div', '1099-int')
        """
        text_lower = text_content.lower()

        # Check for W-2
        if 'w-2' in text_lower or 'wage and tax statement' in text_lower:
            return 'w2'

        # Check for 1099 forms
        if '1099-div' in text_lower or 'dividends and distributions' in text_lower:
            return '1099-div'
        elif '1099-int' in text_lower or 'interest income' in text_lower:
            return '1099-int'
        elif '1099-b' in text_lower or 'proceeds from broker' in text_lower:
            return '1099-b'
        elif '1099-misc' in text_lower or 'miscellaneous income' in text_lower:
            return '1099-misc'
        elif '1099-r' in text_lower or 'distributions from' in text_lower:
            return '1099-r'

        # Default to unknown
        return 'unknown'

    def _extract_w2_data(self, text_content: str) -> Dict[str, Any]:
        """
        Extract W-2 data from PDF text content.

        Args:
            text_content: Extracted text from W-2 PDF

        Returns:
            Tax data dictionary with W-2 information
        """
        # Initialize W-2 data structure
        w2_data = {
            'income': {
                'w2_forms': [{
                    'employer_ein': '',
                    'employer_name': '',
                    'employer_address': '',
                    'wages': 0.0,
                    'federal_withholding': 0.0,
                    'social_security_wages': 0.0,
                    'social_security_withheld': 0.0,
                    'medicare_wages': 0.0,
                    'medicare_withheld': 0.0,
                    'state_income_tax': 0.0,
                    'state_wages': 0.0,
                    'local_income_tax': 0.0,
                    'local_wages': 0.0
                }]
            }
        }

        # Extract data using regex patterns
        # These patterns are simplified - real implementation would need more robust parsing

        # Employer information
        ein_match = re.search(r'(\d{2}-\d{7})', text_content)
        if ein_match:
            w2_data['income']['w2_forms'][0]['employer_ein'] = ein_match.group(1)

        # Wages (Box 1)
        wages_match = re.search(r'Wages, tips, other compensation[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
        if wages_match:
            w2_data['income']['w2_forms'][0]['wages'] = float(wages_match.group(1).replace(',', ''))

        # Federal withholding (Box 2)
        fed_withholding_match = re.search(r'Federal income tax withheld[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
        if fed_withholding_match:
            w2_data['income']['w2_forms'][0]['federal_withholding'] = float(fed_withholding_match.group(1).replace(',', ''))

        # Social Security wages (Box 3)
        ss_wages_match = re.search(r'Social security wages[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
        if ss_wages_match:
            w2_data['income']['w2_forms'][0]['social_security_wages'] = float(ss_wages_match.group(1).replace(',', ''))

        # Social Security withheld (Box 4)
        ss_withheld_match = re.search(r'Social security tax withheld[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
        if ss_withheld_match:
            w2_data['income']['w2_forms'][0]['social_security_withheld'] = float(ss_withheld_match.group(1).replace(',', ''))

        # Medicare wages (Box 5)
        medicare_wages_match = re.search(r'Medicare wages[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
        if medicare_wages_match:
            w2_data['income']['w2_forms'][0]['medicare_wages'] = float(medicare_wages_match.group(1).replace(',', ''))

        # Medicare withheld (Box 6)
        medicare_withheld_match = re.search(r'Medicare tax withheld[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
        if medicare_withheld_match:
            w2_data['income']['w2_forms'][0]['medicare_withheld'] = float(medicare_withheld_match.group(1).replace(',', ''))

        logger.info("Successfully extracted W-2 data from PDF")
        return w2_data

    def _extract_1099_data(self, text_content: str, form_type: str) -> Dict[str, Any]:
        """
        Extract 1099 data from PDF text content.

        Args:
            text_content: Extracted text from 1099 PDF
            form_type: Type of 1099 form (1099-div, 1099-int, etc.)

        Returns:
            Tax data dictionary with 1099 information
        """
        data = {'income': {}}

        if form_type == '1099-div':
            data['income']['dividend_income'] = [{
                'source': 'Imported from 1099-DIV',
                'ordinary': 0.0,
                'qualified': 0.0,
                'total': 0.0
            }]

            # Extract dividend amounts
            # This is simplified - real implementation would need better parsing
            ordinary_match = re.search(r'ordinary dividends[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
            if ordinary_match:
                data['income']['dividend_income'][0]['ordinary'] = float(ordinary_match.group(1).replace(',', ''))

            qualified_match = re.search(r'qualified dividends[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
            if qualified_match:
                data['income']['dividend_income'][0]['qualified'] = float(qualified_match.group(1).replace(',', ''))

        elif form_type == '1099-int':
            data['income']['interest_income'] = [{
                'source': 'Imported from 1099-INT',
                'amount': 0.0,
                'tax_exempt': False
            }]

            # Extract interest amount
            interest_match = re.search(r'interest income[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
            if interest_match:
                data['income']['interest_income'][0]['amount'] = float(interest_match.group(1).replace(',', ''))

        elif form_type == '1099-b':
            data['income']['capital_gains'] = [{
                'description': 'Imported from 1099-B',
                'date_acquired': '',
                'date_sold': '',
                'sales_price': 0.0,
                'cost_basis': 0.0,
                'gain_loss': 0.0,
                'holding_period': 'Short-term'
            }]

            # Extract capital gains data
            proceeds_match = re.search(r'proceeds[\s\S]*?\$?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
            if proceeds_match:
                data['income']['capital_gains'][0]['sales_price'] = float(proceeds_match.group(1).replace(',', ''))

        logger.info(f"Successfully extracted {form_type} data from PDF")
        return data

    def _import_from_txf(self, file_path: str) -> Dict[str, Any]:
        """
        Import tax data from TXF (Tax Exchange Format) file.

        TXF is a standard format used by tax software for data exchange.

        Args:
            file_path: Path to TXF file

        Returns:
            Tax data dictionary
        """
        # TXF format parsing would be implemented here
        # This is a placeholder for future implementation
        logger.warning("TXF import not yet implemented")
        return {}


def import_w2_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to import W-2 data from PDF.

    Args:
        file_path: Path to W-2 PDF file

    Returns:
        W-2 data dictionary
    """
    importer = TaxDataImporter()
    return importer._import_from_pdf(file_path)


def import_1099_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to import 1099 data from PDF.

    Args:
        file_path: Path to 1099 PDF file

    Returns:
        1099 data dictionary
    """
    importer = TaxDataImporter()
    return importer._import_from_pdf(file_path)


def import_prior_year_return(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to import prior year tax return.

    Args:
        file_path: Path to JSON file containing prior year return

    Returns:
        Tax data dictionary
    """
    importer = TaxDataImporter()
    return importer._import_from_json(file_path)