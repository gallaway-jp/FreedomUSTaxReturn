# Quick Reference: New Test Files Guide

## Overview
This guide provides quick access to the 4 new comprehensive test suites created for advanced tax services.

---

## 1. Cryptocurrency Tax Service Tests

**File**: `tests/unit/test_cryptocurrency_tax_service.py`
**Status**: ✅ ALL 23 TESTS PASSING
**Service**: `services/cryptocurrency_tax_service.py`

### Key Test Coverage:
- Transaction management (ADD, SELL, TRADE, MINING, STAKING, AIRDROP)
- Capital gains/losses calculation (FIFO method)
- Short-term vs. long-term holding periods
- Income reporting (mining, staking, airdrops)
- Multiple cryptocurrency support
- Portfolio value tracking

### Running Tests:
```bash
# Run all crypto tests
pytest tests/unit/test_cryptocurrency_tax_service.py -v

# Run specific test
pytest tests/unit/test_cryptocurrency_tax_service.py::TestCryptocurrencyTaxService::test_calculate_cost_basis_fifo -v

# Run with coverage
pytest tests/unit/test_cryptocurrency_tax_service.py --cov=services.cryptocurrency_tax_service
```

### Test Classes:
- `TestCryptocurrencyTaxService` (23 tests)

### Important Methods Tested:
- `add_transaction()` - Add crypto transaction to tax data
- `get_transactions()` - Retrieve all transactions
- `calculate_capital_gains_losses()` - Calculate gains/losses (FIFO)
- `get_tax_liability_estimate()` - Estimate tax owed on crypto gains

---

## 2. Estate & Trust Tax Service Tests

**File**: `tests/unit/test_estate_trust_service.py`
**Status**: Tests created (service implementation in progress)
**Service**: `services/estate_trust_service.py`

### Key Test Coverage:
- Trust and estate types (Simple, Complex, Grantor, CRT, etc.)
- Beneficiary management and distributions
- Trust income calculations
- Trust deductions (fiduciary, attorney, charitable, etc.)
- Form 1041 (Estate/Trust Income Tax Return)
- K-1 generation for beneficiaries
- Capital account tracking

### Running Tests:
```bash
# Run all estate/trust tests
pytest tests/unit/test_estate_trust_service.py -v

# Run specific test class
pytest tests/unit/test_estate_trust_service.py::TestEstateTrustService -v

# Run with specific keyword
pytest tests/unit/test_estate_trust_service.py -k "beneficiary" -v
```

### Test Classes:
- `TestEstateTrustService` (46 tests)

### Data Classes Tested:
- `TrustBeneficiary` - Represents a trust beneficiary
- `TrustIncome` - Income sources for trusts
- `TrustDeductions` - Deductions available to trusts

### Important Methods (to be implemented):
- `add_beneficiary()` - Add beneficiary to trust
- `get_beneficiaries()` - Retrieve all beneficiaries
- `validate_beneficiary_data()` - Validate beneficiary information
- `calculate_beneficiary_distribution()` - Calculate income allocation

---

## 3. Receipt Scanning & OCR Service Tests

**File**: `tests/unit/test_receipt_scanning_service.py`
**Status**: Tests created (OCR library integration needed)
**Service**: `services/receipt_scanning_service.py`

### Key Test Coverage:
- Receipt image scanning and OCR
- Vendor name extraction and pattern matching
- Amount and tax extraction
- Date parsing (multiple formats)
- Line item extraction
- Category detection (medical, charitable, business, education, vehicle, home office, retirement, energy, state/local)
- Confidence scoring
- Batch processing
- Expense aggregation and summarization

### Running Tests:
```bash
# Run all receipt scanning tests
pytest tests/unit/test_receipt_scanning_service.py -v

# Run category detection tests
pytest tests/unit/test_receipt_scanning_service.py -k "category" -v

# Run validation tests
pytest tests/unit/test_receipt_scanning_service.py -k "validate" -v
```

### Test Classes:
- `TestReceiptScanningService` (46+ tests)

### Data Classes Tested:
- `ReceiptData` - Extracted receipt information
- `ScanResult` - Result of scanning operation

### Important Methods Tested:
- `scan_receipt()` - Scan receipt image and extract data
- `_detect_category()` - Categorize receipt by type
- `_extract_total_amount()` - Extract total amount
- `_extract_vendor_name()` - Identify vendor
- `_extract_date()` - Parse receipt date
- `_extract_line_items()` - Extract individual items

### Dependencies:
```bash
pip install pytesseract opencv-python pillow
# Also requires system Tesseract-OCR installation
```

---

## 4. Partnership & S-Corp Service Tests

**File**: `tests/unit/test_partnership_s_corp_service.py`
**Status**: Tests created (service implementation in progress)
**Service**: `services/partnership_s_corp_service.py`

### Key Test Coverage:
- Partnership and S-Corp entity types
- Partner/shareholder management
- Business income and deductions
- K-1 form generation
- Form 1065 (Partnership return)
- Form 1120-S (S-Corp return)
- Partner share calculations
- Capital account tracking
- Guaranteed payments

### Running Tests:
```bash
# Run all partnership/S-Corp tests
pytest tests/unit/test_partnership_s_corp_service.py -v

# Run partner management tests
pytest tests/unit/test_partnership_s_corp_service.py -k "partner" -v

# Run K-1 generation tests
pytest tests/unit/test_partnership_s_corp_service.py -k "k1" -v
```

### Test Classes:
- `TestPartnershipSCorpService` (53 tests)

### Data Classes Tested:
- `PartnerShareholder` - Partner/shareholder information
- `BusinessIncome` - Entity income sources
- `BusinessDeductions` - Entity deductions

### Important Methods (to be implemented):
- `add_partner_shareholder()` - Add partner/shareholder
- `get_partners_shareholders()` - Retrieve all partners
- `calculate_taxable_income()` - Calculate entity taxable income
- `calculate_partner_share_of_income()` - Calculate partner's share

### Entity Types Supported:
- Partnership (General, Limited)
- S-Corporation
- LLC (taxed as partnership or S-Corp)

---

## Running All New Tests Together

```bash
# Run all 4 new test files
pytest tests/unit/test_cryptocurrency_tax_service.py \
        tests/unit/test_estate_trust_service.py \
        tests/unit/test_receipt_scanning_service.py \
        tests/unit/test_partnership_s_corp_service.py -v

# Run with coverage report
pytest tests/unit/test_cryptocurrency_tax_service.py \
        tests/unit/test_estate_trust_service.py \
        tests/unit/test_receipt_scanning_service.py \
        tests/unit/test_partnership_s_corp_service.py \
        --cov=services --cov-report=html

# Run with minimal output
pytest tests/unit/test_cryptocurrency_tax_service.py \
        tests/unit/test_estate_trust_service.py \
        tests/unit/test_receipt_scanning_service.py \
        tests/unit/test_partnership_s_corp_service.py -q
```

---

## Test Statistics

| Service | Test File | Tests | Status | Lines of Code |
|---------|-----------|-------|--------|---|
| Cryptocurrency | `test_cryptocurrency_tax_service.py` | 23 | ✅ PASSING | 450+ |
| Estate/Trust | `test_estate_trust_service.py` | 46 | Created | 630+ |
| Receipt Scanning | `test_receipt_scanning_service.py` | 46+ | Created | 560+ |
| Partnership/S-Corp | `test_partnership_s_corp_service.py` | 53 | Created | 660+ |
| **TOTALS** | **4 files** | **168+** | **1 passing** | **2,300+** |

---

## Common Test Patterns

### Testing Service Initialization:
```python
def test_service_initialization(self, service, mock_config):
    """Test service initialization"""
    assert service.config == mock_config
    assert service.error_tracker is not None
```

### Testing Data Serialization:
```python
def test_serialization(self, data_object):
    """Test serialization to dictionary"""
    data_dict = data_object.to_dict()
    assert data_dict['field_name'] == expected_value
```

### Testing Error Handling:
```python
def test_error_handling(self, service, mock_data):
    """Test error handling"""
    mock_data.get.side_effect = Exception("Database error")
    result = service.method(mock_data)
    assert result == []  # Should return empty on error
```

---

## Debugging Failed Tests

### Run with Full Traceback:
```bash
pytest tests/unit/test_cryptocurrency_tax_service.py -v --tb=long
```

### Run Specific Test with Debug Output:
```bash
pytest tests/unit/test_cryptocurrency_tax_service.py::TestCryptocurrencyTaxService::test_calculate_capital_gains -vv -s
```

### Drop into Python Debugger on Failure:
```bash
pytest tests/unit/test_cryptocurrency_tax_service.py --pdb
```

---

## Next Steps for Implementation

### Priority 1 (Immediate):
- [ ] Implement missing Estate/Trust service methods
- [ ] Implement missing Partnership/S-Corp service methods
- [ ] Install OCR dependencies for Receipt Scanning

### Priority 2 (Next Sprint):
- [ ] Create GUI components for Cryptocurrency transactions
- [ ] Create GUI components for Estate/Trust management
- [ ] Complete Receipt Scanning OCR integration

### Priority 3 (Future):
- [ ] Performance optimization tests
- [ ] Multi-user scenario tests
- [ ] Large-scale data handling tests

---

## Links to Service Implementations

- Cryptocurrency: `services/cryptocurrency_tax_service.py`
- Estate/Trust: `services/estate_trust_service.py`
- Receipt Scanning: `services/receipt_scanning_service.py`
- Partnership/S-Corp: `services/partnership_s_corp_service.py`

---

## Support & Resources

- **Test Framework**: pytest (https://pytest.org/)
- **Mocking**: unittest.mock (built-in Python)
- **OCR**: pytesseract + Tesseract-OCR
- **Financial Calculations**: decimal.Decimal (built-in Python)

---

**Last Updated**: January 1, 2026
**Test Framework Version**: pytest 9.0.2+
**Python Version**: 3.7+
