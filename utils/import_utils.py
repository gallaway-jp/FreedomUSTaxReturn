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
        Format example:
        V042
        ADavid Jones
        ^John Smith
        T1040
        L1^10000.00
        L2^5000.00

        Args:
            file_path: Path to TXF file

        Returns:
            Tax data dictionary
        """
        tax_data = {
            'personal_info': {},
            'income': {},
            'deductions': {},
            'credits': {},
            'payments': {}
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_form = None
            account_name = ""
            current_line = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Handle line continuation (^)
                if line.startswith('^'):
                    current_line += line[1:]
                    continue
                else:
                    # Process previous complete line
                    if current_line:
                        current_form = self._process_txf_line(current_line, tax_data, current_form)
                    current_line = line

            # Process the last line
            if current_line:
                current_form = self._process_txf_line(current_line, tax_data, current_form)

            logger.info(f"Successfully imported tax data from TXF: {file_path}")
            return tax_data

        except Exception as e:
            logger.error(f"Error importing TXF file {file_path}: {e}")
            raise ValueError(f"Invalid TXF file format: {str(e)}")

    def _process_txf_line(self, line: str, tax_data: Dict[str, Any], current_form: Optional[str]) -> Optional[str]:
        """
        Process a single TXF line and update tax data accordingly.

        Args:
            line: TXF line to process
            tax_data: Tax data dictionary to update
            current_form: Current form being processed

        Returns:
            Updated current_form value
        """
        if not line:
            return current_form

        code = line[0]
        value = line[1:] if len(line) > 1 else ""

        if code == 'V':
            # Version - we can validate this
            if not value.startswith('04'):
                logger.warning(f"TXF version {value} may not be fully compatible")
        elif code == 'A':
            # Account name (taxpayer name)
            tax_data['personal_info']['full_name'] = value
        elif code == 'T':
            # Form type
            current_form = value
        elif code == 'L':
            # Line item
            self._process_txf_line_item(value, tax_data, current_form)
        elif code == 'D':
            # Date field
            self._process_txf_date(value, tax_data, current_form)
        elif code == 'N':
            # Description field
            self._process_txf_description(value, tax_data, current_form)

        return current_form

    def _process_txf_line_item(self, value: str, tax_data: Dict[str, Any], form_type: Optional[str]):
        """
        Process TXF line item (L code).

        Args:
            value: Line value in format "line_number^amount"
            tax_data: Tax data to update
            form_type: Current form type
        """
        if '^' not in value:
            return

        line_num, amount_str = value.split('^', 1)
        try:
            line_number = int(line_num)
            amount = float(amount_str)
        except ValueError:
            return

        # Map TXF line numbers to our data structure based on form type
        if form_type == '1040':
            self._map_1040_line(line_number, amount, tax_data)
        elif form_type == 'W2':
            self._map_w2_line(line_number, amount, tax_data)
        elif form_type.startswith('1099'):
            self._map_1099_line(line_number, amount, tax_data, form_type)

    def _map_1040_line(self, line_number: int, amount: float, tax_data: Dict[str, Any]):
        """
        Map Form 1040 line numbers to tax data structure.

        Args:
            line_number: TXF line number
            amount: Amount value
            tax_data: Tax data to update
        """
        # Common 1040 line mappings
        line_mappings = {
            1: ('income', 'wages', 'total_wages'),
            2: ('income', 'interest', 'taxable_interest'),
            3: ('income', 'dividends', 'ordinary_dividends'),
            4: ('income', 'dividends', 'qualified_dividends'),
            5: ('income', 'rental', 'rental_income'),
            6: ('income', 'capital_gains', 'net_capital_gains'),
            7: ('income', 'other_income', 'other_income'),
            8: ('income', 'total_income', 'adjusted_gross_income'),
            9: ('deductions', 'standard_deduction', 'amount'),
            10: ('deductions', 'itemized', 'total_itemized'),
            11: ('deductions', 'total_deductions', 'total'),
            12: ('credits', 'child_tax_credit', 'amount'),
            13: ('credits', 'earned_income_credit', 'amount'),
            14: ('credits', 'total_credits', 'total'),
            15: ('payments', 'federal_withholding', 'total'),
            16: ('payments', 'estimated_payments', 'total'),
            17: ('payments', 'total_payments', 'total')
        }

        if line_number in line_mappings:
            section, field, subfield = line_mappings[line_number]
            if section not in tax_data:
                tax_data[section] = {}
            if field not in tax_data[section]:
                tax_data[section][field] = {}
            tax_data[section][field][subfield] = amount

    def _map_w2_line(self, line_number: int, amount: float, tax_data: Dict[str, Any]):
        """
        Map W-2 line numbers to tax data structure.

        Args:
            line_number: TXF line number
            amount: Amount value
            tax_data: Tax data to update
        """
        if 'income' not in tax_data:
            tax_data['income'] = {}
        if 'w2_forms' not in tax_data['income']:
            tax_data['income']['w2_forms'] = [{}]

        w2_form = tax_data['income']['w2_forms'][0]

        # W-2 box mappings
        w2_mappings = {
            1: 'wages',  # Box 1
            2: 'federal_withholding',  # Box 2
            3: 'social_security_wages',  # Box 3
            4: 'social_security_withheld',  # Box 4
            5: 'medicare_wages',  # Box 5
            6: 'medicare_withheld',  # Box 6
            17: 'state_income_tax',  # Box 17
            18: 'local_income_tax'  # Box 18
        }

        if line_number in w2_mappings:
            w2_form[w2_mappings[line_number]] = amount

    def _map_1099_line(self, line_number: int, amount: float, tax_data: Dict[str, Any], form_type: str):
        """
        Map 1099 line numbers to tax data structure.

        Args:
            line_number: TXF line number
            amount: Amount value
            tax_data: Tax data to update
            form_type: 1099 form type
        """
        if 'income' not in tax_data:
            tax_data['income'] = {}

        if form_type == '1099-DIV':
            if 'dividend_income' not in tax_data['income']:
                tax_data['income']['dividend_income'] = [{}]
            dividend = tax_data['income']['dividend_income'][0]

            if line_number == 1:
                dividend['ordinary'] = amount
            elif line_number == 2:
                dividend['qualified'] = amount

        elif form_type == '1099-INT':
            if 'interest_income' not in tax_data['income']:
                tax_data['income']['interest_income'] = [{}]
            interest = tax_data['income']['interest_income'][0]

            if line_number == 1:
                interest['amount'] = amount

        elif form_type == '1099-B':
            if 'capital_gains' not in tax_data['income']:
                tax_data['income']['capital_gains'] = [{}]
            gain = tax_data['income']['capital_gains'][0]

            if line_number == 1:
                gain['sales_price'] = amount
            elif line_number == 2:
                gain['cost_basis'] = amount

    def _process_txf_date(self, value: str, tax_data: Dict[str, Any], form_type: Optional[str]):
        """
        Process TXF date field (D code).

        Args:
            value: Date value
            tax_data: Tax data to update
            form_type: Current form type
        """
        # Date processing - simplified implementation
        # In a full implementation, you'd parse and validate dates
        pass

    def _process_txf_description(self, value: str, tax_data: Dict[str, Any], form_type: Optional[str]):
        """
        Process TXF description field (N code).

        Args:
            value: Description value
            tax_data: Tax data to update
            form_type: Current form type
        """
        # Description processing - could be used for additional context
        pass


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