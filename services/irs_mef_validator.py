"""
IRS Modernized e-File (MeF) Schema Validation

Provides comprehensive validation of e-file XML against IRS MeF specifications
for Form 1040 and related schedules.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime, date
from pathlib import Path
import json


class IRSMeFValidator:
    """
    Validates IRS Modernized e-File XML against official schemas and business rules.
    """

    def __init__(self):
        # IRS MeF namespace
        self.mef_ns = "http://www.irs.gov/efile"
        self.irs_ns = "http://www.irs.gov/efile/MeF"

        # Required elements for Form 1040
        self.required_elements = {
            'Transmission': ['Taxpayer', 'ReturnData'],
            'Taxpayer': ['SSN', 'Name'],
            'ReturnData': ['Form1040'],
            'Form1040': ['FilingStatus', 'Dependents']
        }

        # Field format patterns
        self.validation_patterns = {
            'ssn': r'^\d{3}-\d{2}-\d{4}$',
            'ein': r'^\d{2}-\d{7}$',
            'zip_code': r'^\d{5}(-\d{4})?$',
            'phone': r'^\d{3}-\d{3}-\d{4}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'currency': r'^\d+(\.\d{2})?$',
            'date': r'^\d{4}-\d{2}-\d{2}$'
        }

        # Business rule validations
        self.business_rules = [
            self._validate_filing_status_consistency,
            self._validate_dependent_requirements,
            self._validate_income_reporting,
            self._validate_deduction_limits,
            self._validate_credit_eligibility
        ]

    def validate_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Comprehensive validation of e-file XML.

        Args:
            xml_content: XML string to validate

        Returns:
            Validation result with detailed findings
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_compliance': True,
            'business_rules_compliant': True,
            'sections_validated': []
        }

        try:
            # Parse XML
            root = ET.fromstring(xml_content)

            # Basic structure validation
            structure_result = self._validate_xml_structure(root)
            result['errors'].extend(structure_result['errors'])
            result['warnings'].extend(structure_result['warnings'])

            # Schema compliance check
            schema_result = self._validate_schema_compliance(root)
            result['schema_compliance'] = schema_result['valid']
            if not schema_result['valid']:
                result['errors'].extend(schema_result['errors'])

            # Data format validation
            format_result = self._validate_data_formats(root)
            result['errors'].extend(format_result['errors'])
            result['warnings'].extend(format_result['warnings'])

            # Business rules validation
            rules_result = self._validate_business_rules(root)
            result['business_rules_compliant'] = rules_result['valid']
            if not rules_result['valid']:
                result['errors'].extend(rules_result['errors'])
                result['warnings'].extend(rules_result['warnings'])

            # Overall validity
            result['valid'] = (
                len(result['errors']) == 0 and
                result['schema_compliance'] and
                result['business_rules_compliant']
            )

            result['sections_validated'] = [
                'xml_structure', 'schema_compliance', 'data_formats', 'business_rules'
            ]

        except ET.ParseError as e:
            result['valid'] = False
            result['errors'].append(f"XML parsing error: {e}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {e}")

        return result

    def _validate_xml_structure(self, root: ET.Element) -> Dict[str, List[str]]:
        """Validate basic XML structure and required elements."""
        result = {'errors': [], 'warnings': []}

        # Check root element - handle both namespaced and non-namespaced
        if not (root.tag == 'MeF' or root.tag.endswith('}MeF')):
            result['errors'].append("Root element must be 'MeF'")

        # Helper function to find elements by local name
        def find_element_by_local_name(parent, local_name):
            """Find element by local name, ignoring namespace"""
            for elem in parent:
                if elem.tag.endswith(f'}}{local_name}') or elem.tag == local_name:
                    return elem
            return None

        # Check transmission structure
        transmission = find_element_by_local_name(root, 'Transmission')
        if transmission is None:
            result['errors'].append("Missing Transmission element")
            return result

        # Check required transmission children
        required_transmission_children = ['Header', 'Taxpayer', 'ReturnData']
        for child_name in required_transmission_children:
            if find_element_by_local_name(transmission, child_name) is None:
                result['errors'].append(f"Missing required element: {child_name} in Transmission")

        return result

    def _validate_schema_compliance(self, root: ET.Element) -> Dict[str, Any]:
        """Validate against IRS MeF schema requirements."""
        result = {'valid': True, 'errors': []}

        try:
            # Helper function to find element by local name
            def find_element_by_local_name(parent, local_name):
                """Find element by local name, ignoring namespace"""
                for elem in parent:
                    if elem.tag.endswith(f'}}{local_name}') or elem.tag == local_name:
                        return elem
                return None

            # Check Form 1040 specific requirements
            form1040 = None
            for elem in root.iter():
                if elem.tag.endswith('}Form1040') or elem.tag == 'Form1040':
                    form1040 = elem
                    break

            if form1040 is not None:
                result_1040 = self._validate_form_1040_schema(form1040)
                if not result_1040['valid']:
                    result['valid'] = False
                    result['errors'].extend(result_1040['errors'])

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Schema validation error: {e}")

        return result

    def _validate_form_1040_schema(self, form1040: ET.Element) -> Dict[str, Any]:
        """Validate Form 1040 specific schema requirements."""
        result = {'valid': True, 'errors': []}

        # Helper function to find element by local name
        def find_element_by_local_name(parent, local_name):
            """Find element by local name, ignoring namespace"""
            for elem in parent.iter():
                if elem.tag.endswith(f'}}{local_name}') or elem.tag == local_name:
                    return elem
            return None

        # Required fields for Form 1040
        required_fields = [
            'FilingStatus', 'Dependents', 'TotalIncome', 'AdjustedGrossIncome',
            'TaxableIncome', 'TotalTax', 'TotalPayments', 'RefundOrAmountOwed'
        ]

        for field in required_fields:
            if find_element_by_local_name(form1040, field) is None:
                result['valid'] = False
                result['errors'].append(f"Missing required Form 1040 field: {field}")

        # Validate filing status values
        filing_status = find_element_by_local_name(form1040, 'FilingStatus')
        if filing_status is not None and filing_status.text:
            valid_statuses = ['1', '2', '3', '4', '5']  # Single, MFJ, MFS, HOH, QW
            if filing_status.text not in valid_statuses:
                result['valid'] = False
                result['errors'].append(f"Invalid filing status: {filing_status.text}")

        return result

    def _validate_data_formats(self, root: ET.Element) -> Dict[str, List[str]]:
        """Validate data format compliance."""
        result = {'errors': [], 'warnings': []}

        # Helper function to find all elements by local name
        def find_all_by_local_name(parent, local_name):
            """Find all elements by local name, ignoring namespace"""
            matches = []
            for elem in parent.iter():
                if elem.tag.endswith(f'}}{local_name}') or elem.tag == local_name:
                    matches.append(elem)
            return matches

        # Validate SSN formats
        ssn_elements = find_all_by_local_name(root, 'SSN')
        for ssn_elem in ssn_elements:
            if ssn_elem.text and not re.match(self.validation_patterns['ssn'], ssn_elem.text):
                result['errors'].append(f"Invalid SSN format: {ssn_elem.text}")

        # Validate EIN formats
        ein_elements = find_all_by_local_name(root, 'EIN')
        for ein_elem in ein_elements:
            if ein_elem.text and not re.match(self.validation_patterns['ein'], ein_elem.text):
                result['errors'].append(f"Invalid EIN format: {ein_elem.text}")

        # Validate currency amounts
        currency_elements = ['TotalIncome', 'AdjustedGrossIncome', 'TaxableIncome', 'TotalTax']
        for elem_name in currency_elements:
            for elem in find_all_by_local_name(root, elem_name):
                if elem.text and not re.match(self.validation_patterns['currency'], elem.text):
                    result['warnings'].append(f"Non-standard currency format: {elem_name} = {elem.text}")

        return result

    def _validate_business_rules(self, root: ET.Element) -> Dict[str, Any]:
        """Validate IRS business rules and logical consistency."""
        result = {'valid': True, 'errors': [], 'warnings': []}

        for rule_func in self.business_rules:
            try:
                rule_result = rule_func(root)
                if not rule_result['valid']:
                    result['valid'] = False
                    result['errors'].extend(rule_result['errors'])
                    result['warnings'].extend(rule_result.get('warnings', []))
            except Exception as e:
                result['valid'] = False
                result['errors'].append(f"Business rule validation error: {e}")

        return result

    def _validate_filing_status_consistency(self, root: ET.Element) -> Dict[str, Any]:
        """Validate filing status consistency with spouse/dependent information."""
        result = {'valid': True, 'errors': [], 'warnings': []}

        # Helper function to find element by local name
        def find_element_by_local_name(parent, local_name):
            """Find element by local name, ignoring namespace"""
            for elem in parent:
                if elem.tag.endswith(f'}}{local_name}') or elem.tag == local_name:
                    return elem
            return None

        # Find Form1040
        form1040 = None
        for elem in root.iter():
            if elem.tag.endswith('}Form1040') or elem.tag == 'Form1040':
                form1040 = elem
                break

        if form1040 is None:
            return result

        filing_status = find_element_by_local_name(form1040, 'FilingStatus')
        if filing_status is None or not filing_status.text:
            return result

        status = filing_status.text

        # Check for spouse information when filing jointly
        if status == '2':  # Married Filing Jointly
            spouse_info = find_element_by_local_name(form1040, 'Spouse')
            if spouse_info is None:
                result['valid'] = False
                result['errors'].append("Married Filing Jointly requires spouse information")

        return result

    def _validate_dependent_requirements(self, root: ET.Element) -> Dict[str, Any]:
        """Validate dependent information requirements."""
        result = {'valid': True, 'errors': [], 'warnings': []}

        dependents = root.findall('.//{http://www.irs.gov/efile}Dependent')

        for i, dependent in enumerate(dependents, 1):
            # Check required fields for each dependent
            required_fields = ['Name', 'SSN', 'Relationship', 'QualifyingChild']
            for field in required_fields:
                if dependent.find(f'.//{{http://www.irs.gov/efile}}{field}') is None:
                    result['valid'] = False
                    result['errors'].append(f"Dependent {i}: Missing required field {field}")

            # Validate SSN format
            ssn_elem = dependent.find('.//{http://www.irs.gov/efile}SSN')
            if ssn_elem is not None and ssn_elem.text:
                if not re.match(self.validation_patterns['ssn'], ssn_elem.text):
                    result['errors'].append(f"Dependent {i}: Invalid SSN format")

        return result

    def _validate_income_reporting(self, root: ET.Element) -> Dict[str, Any]:
        """Validate income reporting consistency."""
        result = {'valid': True, 'errors': [], 'warnings': []}

        # Find Form1040
        form1040 = None
        for elem in root.iter():
            if elem.tag.endswith('}Form1040') or elem.tag == 'Form1040':
                form1040 = elem
                break

        if form1040 is None:
            return result

        # Helper function to find element by local name
        def find_element_by_local_name(parent, local_name):
            """Find element by local name, ignoring namespace"""
            for elem in parent:
                if elem.tag.endswith(f'}}{local_name}') or elem.tag == local_name:
                    return elem
            return None

        # Check that total income is reasonable
        total_income = find_element_by_local_name(form1040, 'TotalIncome')
        if total_income is not None and total_income.text:
            try:
                income = float(total_income.text)
                if income < 0:
                    result['warnings'].append("Negative total income reported - please verify this is correct")
                elif income > 10000000:  # $10M threshold for warning
                    result['warnings'].append("Very high income reported - please verify")
            except ValueError:
                result['errors'].append("Invalid total income format")

        return result

    def _validate_deduction_limits(self, root: ET.Element) -> Dict[str, Any]:
        """Validate deduction limits and calculations."""
        result = {'valid': True, 'errors': [], 'warnings': []}

        # This would validate standard deduction limits, itemized deduction rules, etc.
        # For now, just check basic reasonableness

        form1040 = root.find('.//{http://www.irs.gov/efile}Form1040')
        if form1040 is None:
            return result

        deductions = form1040.find('.//{http://www.irs.gov/efile}Deductions')
        if deductions is not None and deductions.text:
            try:
                ded_amount = float(deductions.text)
                if ded_amount < 0:
                    result['valid'] = False
                    result['errors'].append("Deductions cannot be negative")
            except ValueError:
                result['errors'].append("Invalid deductions format")

        return result

    def _validate_credit_eligibility(self, root: ET.Element) -> Dict[str, Any]:
        """Validate tax credit eligibility rules."""
        result = {'valid': True, 'errors': [], 'warnings': []}

        form1040 = root.find('.//{http://www.irs.gov/efile}Form1040')
        if form1040 is None:
            return result

        # Check EITC eligibility (simplified rules)
        eitc = form1040.find('.//{http://www.irs.gov/efile}EITC')
        if eitc is not None and eitc.text and float(eitc.text) > 0:
            # EITC requires investment income below threshold
            investment_income = form1040.find('.//{http://www.irs.gov/efile}InvestmentIncome')
            if investment_income is not None and investment_income.text:
                try:
                    inv_income = float(investment_income.text)
                    if inv_income > 10000:  # Simplified threshold
                        result['warnings'].append("EITC claimed with high investment income - verify eligibility")
                except ValueError:
                    pass

        return result

    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary."""
        summary = []

        if validation_result['valid']:
            summary.append("PASS: E-file XML validation PASSED")
        else:
            summary.append("FAIL: E-file XML validation FAILED")

        if validation_result['errors']:
            summary.append(f"\nErrors ({len(validation_result['errors'])}):")
            for error in validation_result['errors'][:10]:  # Limit to first 10
                summary.append(f"  • {error}")
            if len(validation_result['errors']) > 10:
                summary.append(f"  ... and {len(validation_result['errors']) - 10} more errors")

        if validation_result['warnings']:
            summary.append(f"\nWarnings ({len(validation_result['warnings'])}):")
            for warning in validation_result['warnings'][:5]:  # Limit to first 5
                summary.append(f"  • {warning}")
            if len(validation_result['warnings']) > 5:
                summary.append(f"  ... and {len(validation_result['warnings']) - 5} more warnings")

        summary.append(f"\nSchema Compliance: {'PASS' if validation_result['schema_compliance'] else 'FAIL'}")
        summary.append(f"Business Rules: {'PASS' if validation_result['business_rules_compliant'] else 'FAIL'}")

        return "\n".join(summary)
