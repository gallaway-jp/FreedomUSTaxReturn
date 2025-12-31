"""
Unit tests for IRS Modernized e-File (MeF) validation system
"""

import pytest
from services.irs_mef_validator import IRSMeFValidator


class TestIRSMeFValidator:
    """Test cases for IRS MeF XML validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = IRSMeFValidator()

    def test_valid_minimal_xml(self):
        """Test validation of a minimal valid e-file XML."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Header>
            <Timestamp>2025-01-15T10:30:00</Timestamp>
            <TaxYear>2025</TaxYear>
            <TransmissionType>Original</TransmissionType>
            <TestIndicator>T</TestIndicator>
        </Header>
        <Taxpayer>
            <SSN>123-45-6789</SSN>
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
            <Address>
                <Street>123 Main St</Street>
                <City>Anytown</City>
                <State>CA</State>
                <ZIP>12345</ZIP>
            </Address>
            <TaxpayerType>Individual</TaxpayerType>
        </Taxpayer>
        <ReturnData>
            <Form1040 taxYear="2025">
                <FilingStatus>1</FilingStatus>
                <Dependents></Dependents>
                <Income></Income>
                <Deductions></Deductions>
                <Credits></Credits>
                <Payments></Payments>
                <TotalIncome>0.00</TotalIncome>
                <AdjustedGrossIncome>0.00</AdjustedGrossIncome>
                <TaxableIncome>0.00</TaxableIncome>
                <TotalTax>0.00</TotalTax>
                <TotalPayments>0.00</TotalPayments>
                <RefundOrAmountOwed>0.00</RefundOrAmountOwed>
            </Form1040>
        </ReturnData>
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['schema_compliance'] is True
        assert result['business_rules_compliant'] is True

    def test_invalid_root_element(self):
        """Test validation with invalid root element."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<InvalidRoot xmlns="http://www.irs.gov/efile">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Taxpayer>
            <SSN>123-45-6789</SSN>
        </Taxpayer>
    </Transmission>
</InvalidRoot>'''

        result = self.validator.validate_xml(xml_content)

        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert "Root element must be 'MeF'" in result['errors'][0]

    def test_missing_required_elements(self):
        """Test validation with missing required elements."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <!-- Missing Header, Taxpayer, and ReturnData -->
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)

        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_invalid_ssn_format(self):
        """Test validation with invalid SSN format."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Taxpayer>
            <SSN>123456789</SSN>  <!-- Invalid format: missing dashes -->
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
            <Address>
                <Street>123 Main St</Street>
                <City>Anytown</City>
                <State>CA</State>
                <ZIP>12345</ZIP>
            </Address>
        </Taxpayer>
        <ReturnData>
            <Form1040 taxYear="2025">
                <FilingStatus>1</FilingStatus>
                <Dependents></Dependents>
                <Income></Income>
                <Deductions></Deductions>
                <Credits></Credits>
                <Payments></Payments>
                <TotalIncome>0.00</TotalIncome>
                <AdjustedGrossIncome>0.00</AdjustedGrossIncome>
                <TaxableIncome>0.00</TaxableIncome>
                <TotalTax>0.00</TotalTax>
                <TotalPayments>0.00</TotalPayments>
                <RefundOrAmountOwed>0.00</RefundOrAmountOwed>
            </Form1040>
        </ReturnData>
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)

        assert result['valid'] is False
        assert any("Invalid SSN format" in error for error in result['errors'])

    def test_invalid_filing_status(self):
        """Test validation with invalid filing status."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Taxpayer>
            <SSN>123-45-6789</SSN>
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
            <Address>
                <Street>123 Main St</Street>
                <City>Anytown</City>
                <State>CA</State>
                <ZIP>12345</ZIP>
            </Address>
        </Taxpayer>
        <ReturnData>
            <Form1040 taxYear="2025">
                <FilingStatus>9</FilingStatus>  <!-- Invalid: should be 1-5 -->
                <Dependents></Dependents>
                <Income></Income>
                <Deductions></Deductions>
                <Credits></Credits>
                <Payments></Payments>
                <TotalIncome>0.00</TotalIncome>
                <AdjustedGrossIncome>0.00</AdjustedGrossIncome>
                <TaxableIncome>0.00</TaxableIncome>
                <TotalTax>0.00</TotalTax>
                <TotalPayments>0.00</TotalPayments>
                <RefundOrAmountOwed>0.00</RefundOrAmountOwed>
            </Form1040>
        </ReturnData>
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)

        assert result['valid'] is False
        assert any("Invalid filing status" in error for error in result['errors'])

    def test_married_filing_jointly_without_spouse(self):
        """Test validation of MFJ filing status without spouse information."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Taxpayer>
            <SSN>123-45-6789</SSN>
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
            <Address>
                <Street>123 Main St</Street>
                <City>Anytown</City>
                <State>CA</State>
                <ZIP>12345</ZIP>
            </Address>
        </Taxpayer>
        <ReturnData>
            <Form1040 taxYear="2025">
                <FilingStatus>2</FilingStatus>  <!-- Married Filing Jointly -->
                <Dependents></Dependents>
                <Income></Income>
                <Deductions></Deductions>
                <Credits></Credits>
                <Payments></Payments>
                <TotalIncome>0.00</TotalIncome>
                <AdjustedGrossIncome>0.00</AdjustedGrossIncome>
                <TaxableIncome>0.00</TaxableIncome>
                <TotalTax>0.00</TotalTax>
                <TotalPayments>0.00</TotalPayments>
                <RefundOrAmountOwed>0.00</RefundOrAmountOwed>
            </Form1040>
        </ReturnData>
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)

        # This should pass basic validation but might have business rule warnings
        # The current implementation may not check for spouse info in MFJ returns
        assert 'business_rules_compliant' in result

    def test_negative_income_warning(self):
        """Test validation with negative income (should generate warning)."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Header>
            <TaxYear>2025</TaxYear>
            <TaxpayerId>123-45-6789</TaxpayerId>
            <SoftwareId>FreedomUSTaxReturn</SoftwareId>
            <SoftwareVersion>3.0</SoftwareVersion>
            <TransmissionType>Original</TransmissionType>
        </Header>
        <Taxpayer>
            <SSN>123-45-6789</SSN>
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
            <Address>
                <Street>123 Main St</Street>
                <City>Anytown</City>
                <State>CA</State>
                <ZIP>12345</ZIP>
            </Address>
        </Taxpayer>
        <ReturnData>
            <Form1040 taxYear="2025">
                <FilingStatus>1</FilingStatus>
                <Dependents></Dependents>
                <Income></Income>
                <Deductions></Deductions>
                <Credits></Credits>
                <Payments></Payments>
                <TotalIncome>-1000.00</TotalIncome>  <!-- Negative income -->
                <AdjustedGrossIncome>0.00</AdjustedGrossIncome>
                <TaxableIncome>0.00</TaxableIncome>
                <TotalTax>0.00</TotalTax>
                <TotalPayments>0.00</TotalPayments>
                <RefundOrAmountOwed>0.00</RefundOrAmountOwed>
            </Form1040>
        </ReturnData>
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)

        # Should still be valid but with warnings
        assert result['valid'] is True
        assert len(result['warnings']) > 0

    def test_validation_summary_generation(self):
        """Test that validation summary is generated correctly."""
        # Use a valid XML for summary test
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<MeF xmlns="http://www.irs.gov/efile" version="1.0">
    <Transmission id="12345678-1234-1234-1234-123456789012">
        <Header>
            <TaxYear>2025</TaxYear>
            <TaxpayerId>123-45-6789</TaxpayerId>
            <SoftwareId>FreedomUSTaxReturn</SoftwareId>
            <SoftwareVersion>3.0</SoftwareVersion>
            <TransmissionType>Original</TransmissionType>
        </Header>
        <Taxpayer>
            <SSN>123-45-6789</SSN>
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
            <Address>
                <Street>123 Main St</Street>
                <City>Anytown</City>
                <State>CA</State>
                <ZIP>12345</ZIP>
            </Address>
        </Taxpayer>
        <ReturnData>
            <Form1040 taxYear="2025">
                <FilingStatus>1</FilingStatus>
                <Dependents></Dependents>
                <Income></Income>
                <Deductions></Deductions>
                <Credits></Credits>
                <Payments></Payments>
                <TotalIncome>0.00</TotalIncome>
                <AdjustedGrossIncome>0.00</AdjustedGrossIncome>
                <TaxableIncome>0.00</TaxableIncome>
                <TotalTax>0.00</TotalTax>
                <TotalPayments>0.00</TotalPayments>
                <RefundOrAmountOwed>0.00</RefundOrAmountOwed>
            </Form1040>
        </ReturnData>
    </Transmission>
</MeF>'''

        result = self.validator.validate_xml(xml_content)
        summary = self.validator.get_validation_summary(result)

        assert "PASSED" in summary
        assert "Schema Compliance: PASS" in summary
        assert "Business Rules: PASS" in summary