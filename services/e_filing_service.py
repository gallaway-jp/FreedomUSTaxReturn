"""
E-Filing Service - IRS Electronic Filing Integration
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
import hashlib
import hmac
import base64
import json
from urllib.parse import urljoin
import requests

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.audit_trail_service import AuditTrailService
from services.ptin_ero_service import PTINEROService
from services.irs_mef_validator import IRSMeFValidator

logger = logging.getLogger(__name__)

class EFilingService:
    """
    Service for handling IRS e-filing operations including XML generation,
    authentication, submission, and status tracking.
    """

    def __init__(self, config: AppConfig, audit_service: Optional[AuditTrailService] = None, ptin_ero_service: Optional[PTINEROService] = None):
        """
        Initialize e-filing service.

        Args:
            config: Application configuration
            audit_service: Optional audit trail service for logging
            ptin_ero_service: Optional PTIN/ERO service for professional authentication
        """
        self.config = config
        self.audit_service = audit_service
        self.ptin_ero_service = ptin_ero_service
        self.acknowledgment_tracker = EFileAcknowledgmentTracker(config)
        self.validator = IRSMeFValidator()

        # IRS e-file endpoints (these would be real URLs in production)
        self.irs_endpoints = {
            'test': 'https://test.irs.gov/efile',
            'production': 'https://irs.gov/efile'
        }

        # State e-file endpoints for major states (these would be real URLs in production)
        self.state_endpoints = {
            'CA': {'test': 'https://test.ftb.ca.gov/efile', 'production': 'https://ftb.ca.gov/efile'},
            'NY': {'test': 'https://test.tax.ny.gov/efile', 'production': 'https://tax.ny.gov/efile'},
            'NJ': {'test': 'https://test.state.nj.us/efile', 'production': 'https://state.nj.us/efile'},
            'IL': {'test': 'https://test.revenue.state.il.us/efile', 'production': 'https://revenue.state.il.us/efile'},
            'PA': {'test': 'https://test.revenue.pa.gov/efile', 'production': 'https://revenue.pa.gov/efile'},
            'MA': {'test': 'https://test.mass.gov/efile', 'production': 'https://mass.gov/efile'},
            'TX': {'test': 'https://test.comptroller.texas.gov/efile', 'production': 'https://comptroller.texas.gov/efile'},
            'FL': {'test': 'https://test.myflorida.com/efile', 'production': 'https://myflorida.com/efile'},
            'WA': {'test': 'https://test.dor.wa.gov/efile', 'production': 'https://dor.wa.gov/efile'},
            'CO': {'test': 'https://test.revenue.colorado.gov/efile', 'production': 'https://revenue.colorado.gov/efile'}
        }

        # XML namespace for IRS Modernized e-File
        self.mef_namespace = 'http://www.irs.gov/efile'

        # State filing status code mappings (may vary by state)
        self.state_filing_status_codes = {
            'CA': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'NY': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'NJ': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'IL': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4', 'widow_er': '5'},
            'PA': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'MA': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'TX': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'FL': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'WA': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'},
            'CO': {'single': '1', 'married_filing_jointly': '2', 'married_filing_separately': '3', 'head_of_household': '4'}
        }

        # IRS filing status code mapping
        self.filing_status_codes = {
            'single': '1',
            'married_filing_jointly': '2',
            'married_filing_separately': '3',
            'head_of_household': '4',
            'qualifying_survivor': '5'
        }

        logger.info("Initialized EFilingService")

    def generate_efile_xml(self, tax_data: TaxData, tax_year: int = 2025) -> str:
        """
        Generate IRS Modernized e-File XML for Form 1040.

        Args:
            tax_data: Tax return data
            tax_year: Tax year for the return

        Returns:
            XML string in IRS MeF format
        """
        try:
            # Create root element with proper IRS MeF namespace
            root = ET.Element("MeF", xmlns=self.mef_namespace)
            root.set("version", "1.0")
            root.set("id", f"MEF-{tax_year}-{uuid.uuid4().hex[:8].upper()}")

            # Add transmission header with required metadata
            transmission = ET.SubElement(root, "Transmission")
            transmission.set("id", str(uuid.uuid4()))

            # Transmission metadata
            header = ET.SubElement(transmission, "Header")
            ET.SubElement(header, "Timestamp").text = datetime.now().isoformat()
            ET.SubElement(header, "TaxYear").text = str(tax_year)
            ET.SubElement(header, "TransmissionType").text = "Original"
            ET.SubElement(header, "TestIndicator").text = "T"  # Test transmission

            # Add taxpayer information
            taxpayer = ET.SubElement(transmission, "Taxpayer")
            self._add_taxpayer_info(taxpayer, tax_data)

            # Add return data
            return_data = ET.SubElement(transmission, "ReturnData")
            self._add_return_data(return_data, tax_data, tax_year)

            # Convert to string with proper formatting
            rough_string = ET.tostring(root, encoding='unicode', method='xml')
            
            # Add XML declaration
            xml_str = f'<?xml version="1.0" encoding="UTF-8"?>\n{rough_string}'

            # Log the e-file generation
            if self.audit_service:
                self.audit_service.log_event(
                    "e_file_generated",
                    f"Generated e-file XML for tax year {tax_year}",
                    {"tax_year": tax_year, "xml_length": len(xml_str)}
                )

            logger.info(f"Generated e-file XML for tax year {tax_year}")
            return xml_str

        except Exception as e:
            logger.error(f"Failed to generate e-file XML: {e}", exc_info=True)
            raise

    def _add_taxpayer_info(self, taxpayer_element: ET.Element, tax_data: TaxData):
        """Add taxpayer information to XML."""
        personal_info = tax_data.data['years'][tax_data.data['metadata']['current_year']]['personal_info']

        # Basic taxpayer info (required)
        ET.SubElement(taxpayer_element, "SSN").text = personal_info.get('ssn', '')
        ET.SubElement(taxpayer_element, "FirstName").text = personal_info.get('first_name', '')
        ET.SubElement(taxpayer_element, "LastName").text = personal_info.get('last_name', '')

        # Middle initial and suffix (optional)
        if personal_info.get('middle_initial'):
            ET.SubElement(taxpayer_element, "MiddleInitial").text = personal_info['middle_initial']
        if personal_info.get('suffix'):
            ET.SubElement(taxpayer_element, "Suffix").text = personal_info['suffix']

        # Address (required)
        address = ET.SubElement(taxpayer_element, "Address")
        ET.SubElement(address, "Street").text = personal_info.get('address', '')
        ET.SubElement(address, "City").text = personal_info.get('city', '')
        ET.SubElement(address, "State").text = personal_info.get('state', '')
        ET.SubElement(address, "ZIP").text = personal_info.get('zip_code', '')

        # Contact information (optional but recommended)
        if personal_info.get('phone'):
            ET.SubElement(taxpayer_element, "Phone").text = personal_info['phone']
        if personal_info.get('email'):
            ET.SubElement(taxpayer_element, "Email").text = personal_info['email']

        # Taxpayer type
        ET.SubElement(taxpayer_element, "TaxpayerType").text = "Individual"

    def _add_return_data(self, return_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add tax return data to XML."""
        # Form 1040 data
        form1040 = ET.SubElement(return_element, "Form1040")
        form1040.set("taxYear", str(tax_year))

        year_data = tax_data.data['years'][tax_year]

        # Filing status (required)
        filing_status = year_data['filing_status']['status']
        filing_status_code = self.filing_status_codes.get(filing_status, '1')  # Default to single if unknown
        ET.SubElement(form1040, "FilingStatus").text = filing_status_code

        # Dependents (required, even if empty)
        dependents = ET.SubElement(form1040, "Dependents")
        self._add_dependent_data(dependents, tax_data, tax_year)

        # Income section
        income = ET.SubElement(form1040, "Income")
        self._add_income_data(income, tax_data, tax_year)

        # Deductions
        deductions = ET.SubElement(form1040, "Deductions")
        self._add_deduction_data(deductions, tax_data, tax_year)

        # Credits
        credits = ET.SubElement(form1040, "Credits")
        self._add_credit_data(credits, tax_data, tax_year)

        # Payments
        payments = ET.SubElement(form1040, "Payments")
        self._add_payment_data(payments, tax_data, tax_year)

        # Calculate and add totals
        self._add_calculated_totals(form1040, tax_data, tax_year)

    def _add_dependent_data(self, dependents_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add dependent information to XML."""
        year_data = tax_data.data['years'][tax_year]
        dependents_list = year_data.get('dependents', [])

        for dependent in dependents_list:
            dep_elem = ET.SubElement(dependents_element, "Dependent")

            # Required dependent information
            ET.SubElement(dep_elem, "Name").text = dependent.get('name', '')
            ET.SubElement(dep_elem, "SSN").text = dependent.get('ssn', '')
            ET.SubElement(dep_elem, "Relationship").text = dependent.get('relationship', '')

            # Qualifying child status
            qualifying_child = dependent.get('qualifying_child', False)
            ET.SubElement(dep_elem, "QualifyingChild").text = '1' if qualifying_child else '0'

            # Child tax credit eligible
            ctc_eligible = dependent.get('child_tax_credit', False)
            ET.SubElement(dep_elem, "ChildTaxCreditEligible").text = '1' if ctc_eligible else '0'

    def _add_calculated_totals(self, form1040_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add calculated totals to Form 1040."""
        # This would normally use the tax calculation service
        # For now, add placeholder calculated fields

        # Total income (sum of all income sources)
        ET.SubElement(form1040_element, "TotalIncome").text = "0.00"

        # Adjusted gross income
        ET.SubElement(form1040_element, "AdjustedGrossIncome").text = "0.00"

        # Taxable income
        ET.SubElement(form1040_element, "TaxableIncome").text = "0.00"

        # Total tax
        ET.SubElement(form1040_element, "TotalTax").text = "0.00"

        # Total payments and credits
        ET.SubElement(form1040_element, "TotalPayments").text = "0.00"

        # Refund or amount owed
        ET.SubElement(form1040_element, "RefundOrAmountOwed").text = "0.00"

    def _add_income_data(self, income_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add income data to XML."""
        income_data = tax_data.data['years'][tax_year]['income']

        # W-2 wages
        w2_forms = income_data.get('w2_forms', [])
        total_wages = sum(w2.get('wages', 0) for w2 in w2_forms)
        ET.SubElement(income_element, "Wages").text = str(total_wages)

        # Interest income
        interest_income = income_data.get('interest_income', 0)
        ET.SubElement(income_element, "Interest").text = str(interest_income)

        # Dividend income
        dividend_income = income_data.get('dividend_income', 0)
        ET.SubElement(income_element, "Dividends").text = str(dividend_income)

    def _add_deduction_data(self, deductions_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add deduction data to XML."""
        deductions_data = tax_data.data['years'][tax_year].get('deductions', {})

        # Standard deduction (simplified for now)
        standard_deduction = deductions_data.get('standard_deduction', 0)
        ET.SubElement(deductions_element, "StandardDeduction").text = str(standard_deduction)

        # Itemized deductions
        itemized = deductions_data.get('itemized_deductions', {})
        total_itemized = sum(itemized.values())
        ET.SubElement(deductions_element, "ItemizedDeductions").text = str(total_itemized)

    def _add_credit_data(self, credits_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add tax credit data to XML."""
        credits_data = tax_data.data['years'][tax_year].get('credits', {})

        # Child tax credit
        child_credit = credits_data.get('child_tax_credit', 0)
        ET.SubElement(credits_element, "ChildTaxCredit").text = str(child_credit)

        # Education credits
        education_credits = credits_data.get('education_credits', 0)
        ET.SubElement(credits_element, "EducationCredits").text = str(education_credits)

    def _add_payment_data(self, payments_element: ET.Element, tax_data: TaxData, tax_year: int):
        """Add payment/withholding data to XML."""
        payments_data = tax_data.data['years'][tax_year].get('payments', {})

        # Federal withholding
        federal_withholding = payments_data.get('federal_withholding', 0)
        ET.SubElement(payments_element, "FederalWithholding").text = str(federal_withholding)

        # Estimated payments
        estimated_payments = payments_data.get('estimated_tax_payments', 0)
        ET.SubElement(payments_element, "EstimatedPayments").text = str(estimated_payments)

        # Direct deposit information (if enabled)
        direct_deposit = payments_data.get('direct_deposit', {})
        if direct_deposit.get('enabled', False):
            dd_element = ET.SubElement(payments_element, "DirectDeposit")
            ET.SubElement(dd_element, "RoutingNumber").text = direct_deposit.get('routing_number', '')
            ET.SubElement(dd_element, "AccountNumber").text = direct_deposit.get('account_number', '')
            ET.SubElement(dd_element, "AccountType").text = direct_deposit.get('account_type', 'checking')
            ET.SubElement(dd_element, "BankName").text = direct_deposit.get('bank_name', '')
            ET.SubElement(dd_element, "AccountHolderName").text = direct_deposit.get('account_holder_name', '')

    def validate_efile_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Validate e-file XML against IRS schemas and business rules.

        Args:
            xml_content: XML string to validate

        Returns:
            Comprehensive validation result
        """
        try:
            # Use comprehensive IRS MeF validator
            validation_result = self.validator.validate_xml(xml_content)

            # Log validation results
            if self.audit_service:
                self.audit_service.log_event(
                    "e_file_validation",
                    f"E-file XML validation completed: {'PASSED' if validation_result['valid'] else 'FAILED'}",
                    {
                        "errors_count": len(validation_result['errors']),
                        "warnings_count": len(validation_result['warnings']),
                        "schema_compliant": validation_result['schema_compliance'],
                        "business_rules_compliant": validation_result['business_rules_compliant']
                    }
                )

            logger.info(f"E-file validation completed: {'PASSED' if validation_result['valid'] else 'FAILED'}")
            return validation_result

        except Exception as e:
            logger.error(f"E-file validation error: {e}")
            return {
                'valid': False,
                'errors': [f"Validation system error: {e}"],
                'warnings': [],
                'schema_compliance': False,
                'business_rules_compliant': False,
                'sections_validated': []
            }

    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """
        Get a human-readable summary of validation results.

        Args:
            validation_result: Result from validate_efile_xml

        Returns:
            Formatted summary string
        """
        return self.validator.get_validation_summary(validation_result)

    def submit_efile(self, xml_content: str, test_mode: bool = True) -> Dict[str, Any]:
        """
        Submit e-file to IRS (placeholder for actual implementation).

        Args:
            xml_content: Validated XML content
            test_mode: Whether to use test environment

        Returns:
            Submission result
        """
        # This is a placeholder - actual implementation would:
        # 1. Authenticate with IRS
        # 2. Sign the XML
        # 3. Submit via HTTPS
        # 4. Handle response

        logger.info(f"E-file submission initiated (test_mode={test_mode})")

        # Mock successful submission for now
        return {
            'success': True,
            'confirmation_number': f'EF{uuid.uuid4().hex[:8].upper()}',
            'timestamp': datetime.now().isoformat(),
            'status': 'accepted'
        }

    def check_submission_status(self, confirmation_number: str) -> Dict[str, Any]:
        """
        Check status of submitted e-file.

        Args:
            confirmation_number: IRS confirmation number

        Returns:
            Status information
        """
        # Placeholder for status checking
        return {
            'confirmation_number': confirmation_number,
            'status': 'processing',
            'last_updated': datetime.now().isoformat()
        }

    def sign_efile_xml(self, xml_content: str, signature_data: Dict[str, Any]) -> str:
        """
        Add digital signature to e-file XML.

        Args:
            xml_content: XML content to sign
            signature_data: Signature information (PIN, EFIN, PTIN, etc.)

        Returns:
            Signed XML content
        """
        try:
            # Validate PTIN if provided
            ptin = signature_data.get('ptin')
            if ptin and self.ptin_ero_service:
                ptin_record = self.ptin_ero_service.get_ptin_record(ptin)
                if not ptin_record:
                    raise ValueError(f"Invalid PTIN: {ptin}")
                if ptin_record.status != 'active':
                    raise ValueError(f"PTIN is not active: {ptin}")
                
                # Log PTIN authentication
                if self.audit_service:
                    self.audit_service.log_event(
                        "ptin_authentication",
                        f"PTIN authenticated for e-filing: {ptin}",
                        {"ptin": ptin, "name": f"{ptin_record.first_name} {ptin_record.last_name}"}
                    )

            # Parse XML
            root = ET.fromstring(xml_content)

            # Create signature element
            signature = ET.SubElement(root, "DigitalSignature")
            signature.set("xmlns", "http://www.w3.org/2000/09/xmldsig#")

            # SignedInfo
            signed_info = ET.SubElement(signature, "SignedInfo")
            canonicalization_method = ET.SubElement(signed_info, "CanonicalizationMethod")
            canonicalization_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

            signature_method = ET.SubElement(signed_info, "SignatureMethod")
            signature_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha256")

            # Reference to the return data
            reference = ET.SubElement(signed_info, "Reference")
            reference.set("URI", "#ReturnData")

            transforms = ET.SubElement(reference, "Transforms")
            transform = ET.SubElement(transforms, "Transform")
            transform.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")

            digest_method = ET.SubElement(reference, "DigestMethod")
            digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha256")

            # Calculate digest of the return data (simplified)
            return_data = root.find('.//ReturnData')
            if return_data is not None:
                data_str = ET.tostring(return_data, encoding='unicode', method='xml')
                digest_value = hashlib.sha256(data_str.encode('utf-8')).digest()
                digest_element = ET.SubElement(reference, "DigestValue")
                digest_element.text = base64.b64encode(digest_value).decode('utf-8')

            # Signature value (mock for now - would use actual private key)
            signature_value = ET.SubElement(signature, "SignatureValue")
            mock_signature = self._generate_mock_signature(xml_content, signature_data)
            signature_value.text = mock_signature

            # Key info
            key_info = ET.SubElement(signature, "KeyInfo")
            key_name = ET.SubElement(key_info, "KeyName")
            
            # Use PTIN as key identifier if available, otherwise EFIN
            ptin = signature_data.get('ptin')
            efin = signature_data.get('efin', 'MOCK_EFIN')
            key_name.text = ptin if ptin else efin
            
            # Add PTIN info if available
            if ptin and self.ptin_ero_service:
                ptin_record = self.ptin_ero_service.get_ptin_record(ptin)
                if ptin_record:
                    ptin_info = ET.SubElement(key_info, "PTINInfo")
                    ptin_info.set("xmlns", "http://www.irs.gov/efile")
                    name_elem = ET.SubElement(ptin_info, "Name")
                    name_elem.text = f"{ptin_record.first_name} {ptin_record.last_name}"
                    issued_elem = ET.SubElement(ptin_info, "IssuedDate")
                    issued_elem.text = ptin_record.validation_date.isoformat() if ptin_record.validation_date else ""

            # Convert back to string
            signed_xml = ET.tostring(root, encoding='unicode', method='xml')
            signed_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n{signed_xml}'

            logger.info("Digital signature added to e-file XML")
            return signed_xml

        except Exception as e:
            logger.error(f"Failed to sign e-file XML: {e}", exc_info=True)
            raise

    def _generate_mock_signature(self, xml_content: str, signature_data: Dict[str, Any]) -> str:
        """Generate mock digital signature for testing."""
        # In production, this would use actual cryptographic signing
        content_hash = hashlib.sha256(xml_content.encode('utf-8')).hexdigest()
        pin = signature_data.get('pin', '0000')
        combined = f"{content_hash}:{pin}:{datetime.now().isoformat()}"
        signature = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
        return signature

    def submit_efile_to_irs(self, signed_xml: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit signed e-file to IRS.

        Args:
            signed_xml: Signed XML content
            submission_data: Submission metadata (EFIN, PIN, etc.)

        Returns:
            Submission result
        """
        try:
            # Validate PTIN if provided
            ptin = submission_data.get('ptin')
            if ptin and self.ptin_ero_service:
                ptin_record = self.ptin_ero_service.get_ptin_record(ptin)
                if not ptin_record:
                    raise ValueError(f"Invalid PTIN for submission: {ptin}")
                if ptin_record.status != 'active':
                    raise ValueError(f"PTIN is not active for submission: {ptin}")

            # Create IRS submission client
            client = IRSSubmissionClient(
                efin=submission_data.get('efin'),
                ptin=ptin,
                ptin_ero_service=self.ptin_ero_service,
                test_mode=submission_data.get('test_mode', True)
            )

            # Submit the return
            result = client.submit_return(signed_xml, submission_data)

            # Record the submission in acknowledgment tracker
            if result.get('success'):
                self.acknowledgment_tracker.record_submission(
                    result['confirmation_number'],
                    submission_data
                )

            # Log the submission
            if self.audit_service:
                self.audit_service.log_event(
                    "e_file_submitted",
                    f"E-file submitted to IRS (confirmation: {result.get('confirmation_number', 'N/A')})",
                    {
                        "confirmation_number": result.get('confirmation_number'),
                        "status": result.get('status'),
                        "test_mode": submission_data.get('test_mode', True)
                    }
                )

            logger.info(f"E-file submitted successfully: {result.get('confirmation_number')}")
            return result

        except Exception as e:
            logger.error(f"E-file submission failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }

    def check_efile_status(self, confirmation_number: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check e-file status with IRS.

        Args:
            confirmation_number: IRS confirmation number
            submission_data: Submission metadata

        Returns:
            Status information
        """
        try:
            client = IRSSubmissionClient(
                efin=submission_data.get('efin'),
                test_mode=submission_data.get('test_mode', True)
            )

            status = client.check_status(confirmation_number)

            # Update acknowledgment tracker
            self.acknowledgment_tracker.update_status(
                confirmation_number,
                status.get('status', 'unknown'),
                status.get('details', '')
            )

            # Update audit trail
            if self.audit_service:
                self.audit_service.log_event(
                    "e_file_status_check",
                    f"E-file status checked: {status.get('status')}",
                    {
                        "confirmation_number": confirmation_number,
                        "status": status.get('status'),
                        "last_updated": status.get('last_updated')
                    }
                )

            return status

        except Exception as e:
            logger.error(f"Status check failed: {e}", exc_info=True)
            return {
                'confirmation_number': confirmation_number,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

    def get_all_acknowledgments(self) -> Dict[str, Any]:
        """
        Get all e-file acknowledgments.

        Returns:
            All acknowledgment records
        """
        return self.acknowledgment_tracker.get_all_acknowledgments()

    def get_acknowledgment_status(self, confirmation_number: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific e-file submission.

        Args:
            confirmation_number: IRS confirmation number

        Returns:
            Status information or None if not found
        """
        return self.acknowledgment_tracker.get_status(confirmation_number)

    # ==================== STATE E-FILING METHODS ====================

    def get_supported_state_efile_states(self) -> List[str]:
        """
        Get list of states that support e-filing.

        Returns:
            List of two-letter state codes
        """
        return list(self.state_endpoints.keys())

    def generate_state_efile_xml(self, tax_data: TaxData, state_code: str, tax_year: int = 2025) -> str:
        """
        Generate state-specific e-file XML for state tax returns.

        Args:
            tax_data: Tax return data
            state_code: Two-letter state code (e.g., 'CA', 'NY')
            tax_year: Tax year for the return

        Returns:
            XML string in state-specific format

        Raises:
            ValueError: If state is not supported for e-filing
        """
        if state_code not in self.state_endpoints:
            raise ValueError(f"State {state_code} is not supported for e-filing")

        try:
            # Create root element for state filing
            root = ET.Element("StateTaxReturn")
            root.set("state", state_code)
            root.set("taxYear", str(tax_year))
            root.set("version", "1.0")
            root.set("id", f"STATE-{state_code}-{tax_year}-{uuid.uuid4().hex[:8].upper()}")

            # Add XML declaration
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'

            # Add taxpayer information
            taxpayer = ET.SubElement(root, "Taxpayer")
            self._add_state_taxpayer_info(taxpayer, tax_data, state_code)

            # Add return data
            return_data = ET.SubElement(root, "ReturnData")
            self._add_state_return_data(return_data, tax_data, state_code, tax_year)

            # Convert to string
            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            return xml_content + xml_str

        except Exception as e:
            logger.error(f"Failed to generate state e-file XML for {state_code}: {e}")
            raise

    def _add_state_taxpayer_info(self, taxpayer_element: ET.Element, tax_data: TaxData, state_code: str):
        """Add taxpayer information to state XML"""
        personal_info = tax_data.data.get('personal_info', {})

        ET.SubElement(taxpayer_element, "FirstName").text = personal_info.get('first_name', '')
        ET.SubElement(taxpayer_element, "LastName").text = personal_info.get('last_name', '')
        ET.SubElement(taxpayer_element, "SSN").text = personal_info.get('ssn', '')

        # Address information
        address = personal_info.get('address', {})
        ET.SubElement(taxpayer_element, "StreetAddress").text = address.get('street', '')
        ET.SubElement(taxpayer_element, "City").text = address.get('city', '')
        ET.SubElement(taxpayer_element, "State").text = address.get('state', '')
        ET.SubElement(taxpayer_element, "ZIPCode").text = address.get('zip_code', '')

        # State-specific information
        ET.SubElement(taxpayer_element, "StateCode").text = state_code

    def _add_state_return_data(self, return_element: ET.Element, tax_data: TaxData, state_code: str, tax_year: int):
        """Add return data to state XML"""
        # Filing status
        filing_status = tax_data.data.get('filing_status', {}).get('status', 'single')
        state_codes = self.state_filing_status_codes.get(state_code, {})
        filing_code = state_codes.get(filing_status, '1')
        ET.SubElement(return_element, "FilingStatus").text = filing_code

        # Federal AGI (used by most states as starting point)
        federal_agi = self._calculate_federal_agi(tax_data)
        ET.SubElement(return_element, "FederalAGI").text = f"{federal_agi:.2f}"

        # State-specific income adjustments
        income_data = tax_data.data.get('income', {})
        ET.SubElement(return_element, "Wages").text = f"{income_data.get('wages', 0):.2f}"
        ET.SubElement(return_element, "Interest").text = f"{income_data.get('interest', 0):.2f}"
        ET.SubElement(return_element, "Dividends").text = f"{income_data.get('dividends', 0):.2f}"

        # State tax withheld
        payments = tax_data.data.get('payments', {})
        ET.SubElement(return_element, "StateTaxWithheld").text = f"{payments.get('state_withholding', 0):.2f}"
        ET.SubElement(return_element, "StateEstimatedPayments").text = f"{payments.get('state_estimated_payments', 0):.2f}"

    def _calculate_federal_agi(self, tax_data: TaxData) -> float:
        """Calculate federal AGI for state filing purposes"""
        income = tax_data.data.get('income', {})
        adjustments = tax_data.data.get('adjustments', {})

        # Gross income
        gross_income = (
            income.get('wages', 0) +
            income.get('interest', 0) +
            income.get('dividends', 0) +
            income.get('business_income', 0) +
            income.get('rental_income', 0)
        )

        # Subtract adjustments
        agi = gross_income - (
            adjustments.get('traditional_ira', 0) +
            adjustments.get('student_loan_interest', 0) +
            adjustments.get('self_employment_tax', 0)
        )

        return max(0, agi)  # AGI cannot be negative

    def submit_state_efile(self, tax_data: TaxData, state_code: str, tax_year: int = 2025) -> Dict[str, Any]:
        """
        Submit state e-file to state tax authority.

        Args:
            tax_data: Tax return data
            state_code: Two-letter state code
            tax_year: Tax year

        Returns:
            Submission result
        """
        if state_code not in self.state_endpoints:
            raise ValueError(f"State {state_code} is not supported for e-filing")

        # Validate readiness first
        validation_result = self.validate_state_efile_readiness(tax_data, state_code)
        if not validation_result['ready']:
            issues = ', '.join(validation_result['issues'])
            raise ValueError(f"State e-file not ready for {state_code}: {issues}")

        # Generate XML
        xml_content = self.generate_state_efile_xml(tax_data, state_code, tax_year)

        # Submit to state authority
        try:
            submission_result = self.submit_state_efile_to_authority(xml_content, {
                'state_code': state_code,
                'confirmation_number': f"STATE-{state_code}-{uuid.uuid4().hex[:12].upper()}",
                'timestamp': datetime.now().isoformat()
            })
            confirmation_number = submission_result.get('confirmation_number', f"STATE-{state_code}-{uuid.uuid4().hex[:12].upper()}")

            # Record submission in audit trail
            if self.audit_service:
                self.audit_service.record_event(
                    event_type="state_e_file_submitted",
                    description=f"State e-file submitted for {state_code} tax year {tax_year}",
                    details={
                        'state_code': state_code,
                        'tax_year': tax_year,
                        'confirmation_number': confirmation_number,
                        'endpoint': self.state_endpoints[state_code]['test' if self.test_mode else 'production']
                    }
                )

            logger.info(f"Successfully submitted state e-file for {state_code}, confirmation: {confirmation_number}")
            return {
                'success': True,
                'confirmation_number': confirmation_number,
                'status': 'submitted',
                'timestamp': datetime.now().isoformat(),
                'state': state_code
            }

        except Exception as e:
            logger.error(f"Failed to submit state e-file for {state_code}: {e}")
            raise ValueError(f"State e-file submission failed: {str(e)}")

    def submit_state_efile_to_authority(self, xml_content: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit XML to state tax authority (mock implementation).

        In production, this would make actual HTTP requests to state endpoints.
        """
        state_code = submission_data['state_code']
        test_mode = submission_data.get('test_mode', True)

        # Generate mock confirmation number
        confirmation_number = f"STATE-{state_code}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Simulate submission delay and success
        logger.info(f"Mock state e-file submission to {state_code} {'(test mode)' if test_mode else '(production)'}")

        return {
            'success': True,
            'confirmation_number': confirmation_number,
            'status': 'submitted',
            'message': f'Successfully submitted to {state_code} tax authority',
            'estimated_processing_time': '2-4 weeks'
        }

    def check_state_submission_status(self, confirmation_number: str, state_code: str) -> Dict[str, Any]:
        """
        Check status of state e-file submission.

        Args:
            confirmation_number: State confirmation number
            state_code: Two-letter state code

        Returns:
            Status information
        """
        # Load state acknowledgments
        acknowledgments = self._load_state_acknowledgments()

        if confirmation_number in acknowledgments:
            return acknowledgments[confirmation_number]
        else:
            return {
                'status': 'not_found',
                'message': f'Confirmation number {confirmation_number} not found for state {state_code}'
            }

    def record_state_submission(self, confirmation_number: str, submission_data: Dict[str, Any]):
        """
        Record a state e-file submission.

        Args:
            confirmation_number: State confirmation number
            submission_data: Submission details
        """
        acknowledgments = self._load_state_acknowledgments()

        acknowledgments[confirmation_number] = {
            'confirmation_number': confirmation_number,
            'state_code': submission_data.get('state_code'),
            'timestamp': submission_data.get('timestamp', datetime.now().isoformat()),
            'status': 'submitted',
            'test_mode': submission_data.get('test_mode', True),
            'xml_content_length': len(submission_data.get('xml_content', ''))
        }

        self._save_state_acknowledgments(acknowledgments)

    def _load_state_acknowledgments(self) -> Dict[str, Any]:
        """Load state e-file acknowledgments from file"""
        ack_file = self.config.safe_dir / "state_efile_acknowledgments.json"

        if ack_file.exists():
            try:
                with open(ack_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state acknowledgments: {e}")

        return {}

    def _save_state_acknowledgments(self, acknowledgments: Dict[str, Any]):
        """Save state e-file acknowledgments to file"""
        ack_file = self.config.safe_dir / "state_efile_acknowledgments.json"

        try:
            ack_file.parent.mkdir(parents=True, exist_ok=True)
            with open(ack_file, 'w') as f:
                json.dump(acknowledgments, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state acknowledgments: {e}")

    def validate_state_efile_readiness(self, tax_data: TaxData, state_code: str) -> Dict[str, Any]:
        """
        Validate if tax data is ready for state e-filing.

        Args:
            tax_data: Tax return data
            state_code: Two-letter state code

        Returns:
            Validation result with readiness status and issues
        """
        issues = []

        # Check if state is supported
        if state_code not in self.state_endpoints:
            return {
                'ready': False,
                'state_supported': False,
                'issues': [f'State {state_code} does not support e-filing']
            }

        # Check required personal information
        personal_info = tax_data.data.get('personal_info', {})
        required_fields = ['first_name', 'last_name', 'ssn', 'address']

        for field in required_fields:
            if not personal_info.get(field):
                issues.append(f'Missing required field: {field.replace("_", " ").title()}')

        # Check address completeness
        address = personal_info.get('address', {})
        address_fields = ['street', 'city', 'state', 'zip_code']
        for field in address_fields:
            if not address.get(field):
                issues.append(f'Missing address field: {field.replace("_", " ").title()}')

        # Check filing status
        filing_status = tax_data.data.get('filing_status', {}).get('status')
        if not filing_status:
            issues.append('Filing status not specified')

        # Check for income data
        income = tax_data.data.get('income', {})
        if not any(income.values()):  # Check if any income fields have values
            issues.append('No income information provided')

        return {
            'ready': len(issues) == 0,
            'state_supported': True,
            'issues': issues
        }


class IRSSubmissionClient:
    """
    Client for communicating with IRS e-file systems.
    """

    def __init__(self, efin: str, ptin: Optional[str] = None, ptin_ero_service: Optional[PTINEROService] = None, test_mode: bool = True):
        """
        Initialize IRS submission client.

        Args:
            efin: Electronic Filing Identification Number
            ptin: Preparer Tax Identification Number (optional)
            ptin_ero_service: PTIN/ERO service for validation (optional)
            test_mode: Whether to use test environment
        """
        self.efin = efin
        self.ptin = ptin
        self.ptin_ero_service = ptin_ero_service
        self.test_mode = test_mode

        # IRS endpoints (mock URLs for now)
        self.endpoints = {
            'submit': 'https://test.irs.gov/efile/submit' if test_mode else 'https://irs.gov/efile/submit',
            'status': 'https://test.irs.gov/efile/status' if test_mode else 'https://irs.gov/efile/status'
        }

        auth_info = f"EFIN: {efin}"
        if ptin:
            auth_info += f", PTIN: {ptin}"
        auth_info += f", Test Mode: {test_mode}"
        
        logger.info(f"Initialized IRS Submission Client ({auth_info})")

    def submit_return(self, signed_xml: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit tax return to IRS.

        Args:
            signed_xml: Signed XML content
            submission_data: Submission metadata

        Returns:
            Submission result
        """
        try:
            # Prepare submission payload
            payload = {
                'xml_content': signed_xml,
                'efin': self.efin,
                'pin': submission_data.get('pin'),
                'tax_year': submission_data.get('tax_year', 2025),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add PTIN information if available
            if self.ptin:
                payload['ptin'] = self.ptin
                # Include PTIN record details if service is available
                if self.ptin_ero_service:
                    ptin_record = self.ptin_ero_service.get_ptin_record(self.ptin)
                    if ptin_record:
                        payload['ptin_info'] = {
                            'name': ptin_record.name,
                            'issued_date': ptin_record.issued_date.isoformat() if ptin_record.issued_date else None,
                            'status': ptin_record.status
                        }

            # In production, this would make an actual HTTPS request
            # For now, simulate the submission
            confirmation_number = f'EF{uuid.uuid4().hex[:10].upper()}'

            logger.info(f"Tax return submitted to IRS: {confirmation_number}")

            return {
                'success': True,
                'confirmation_number': confirmation_number,
                'status': 'accepted',
                'timestamp': datetime.now().isoformat(),
                'estimated_processing_days': 7 if not self.test_mode else 1
            }

        except Exception as e:
            logger.error(f"IRS submission failed: {e}")
            raise

    def check_status(self, confirmation_number: str) -> Dict[str, Any]:
        """
        Check submission status.

        Args:
            confirmation_number: IRS confirmation number

        Returns:
            Status information
        """
        try:
            # In production, this would query IRS status API
            # For now, simulate status checking
            import random

            statuses = ['processing', 'accepted', 'rejected']
            status = random.choice(statuses)

            return {
                'confirmation_number': confirmation_number,
                'status': status,
                'last_updated': datetime.now().isoformat(),
                'details': f'Return is currently {status}'
            }

        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise


class EFileAcknowledgmentTracker:
    """
    Tracks IRS acknowledgments and status updates for submitted e-files.
    """

    def __init__(self, config: AppConfig):
        """
        Initialize acknowledgment tracker.

        Args:
            config: Application configuration
        """
        self.config = config
        self.acknowledgments_file = Path(config.safe_dir) / 'efile_acknowledgments.json'
        self.acknowledgments_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Initialized E-File Acknowledgment Tracker")

    def record_submission(self, confirmation_number: str, submission_data: Dict[str, Any]) -> None:
        """
        Record a new e-file submission.

        Args:
            confirmation_number: IRS confirmation number
            submission_data: Submission details
        """
        acknowledgments = self._load_acknowledgments()

        acknowledgments[confirmation_number] = {
            'confirmation_number': confirmation_number,
            'submission_date': datetime.now().isoformat(),
            'status': 'submitted',
            'tax_year': submission_data.get('tax_year', 2025),
            'efin': submission_data.get('efin'),
            'test_mode': submission_data.get('test_mode', True),
            'status_history': [{
                'status': 'submitted',
                'timestamp': datetime.now().isoformat(),
                'details': 'Return submitted to IRS'
            }]
        }

        self._save_acknowledgments(acknowledgments)
        logger.info(f"Recorded e-file submission: {confirmation_number}")

    def update_status(self, confirmation_number: str, new_status: str, details: str = "") -> None:
        """
        Update the status of a submitted e-file.

        Args:
            confirmation_number: IRS confirmation number
            new_status: New status
            details: Additional details
        """
        acknowledgments = self._load_acknowledgments()

        if confirmation_number in acknowledgments:
            acknowledgments[confirmation_number]['status'] = new_status
            acknowledgments[confirmation_number]['last_updated'] = datetime.now().isoformat()

            # Add to status history
            status_entry = {
                'status': new_status,
                'timestamp': datetime.now().isoformat(),
                'details': details or f'Status updated to {new_status}'
            }
            acknowledgments[confirmation_number]['status_history'].append(status_entry)

            self._save_acknowledgments(acknowledgments)
            logger.info(f"Updated e-file status: {confirmation_number} -> {new_status}")

    def get_status(self, confirmation_number: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a submitted e-file.

        Args:
            confirmation_number: IRS confirmation number

        Returns:
            Status information or None if not found
        """
        acknowledgments = self._load_acknowledgments()
        return acknowledgments.get(confirmation_number)
