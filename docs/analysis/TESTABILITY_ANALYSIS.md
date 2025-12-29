# Testability Analysis

**Analysis Date**: 2025-01-XX  
**Current Test Coverage**: 31%  
**Test Count**: 68 tests (all passing)

---

## Executive Summary

The FreedomUSTaxReturn application has a solid foundation of 68 passing tests covering core functionality, but significant gaps exist in critical areas. While integration and unit tests provide good coverage for PDF operations and error handling, **tax calculation logic (18% coverage)** and **GUI components (0% coverage)** remain largely untested. The codebase demonstrates good testability in many areas but requires focused effort to improve test coverage of business-critical calculations.

### Quality Grade: **C+ (63/100)**

**Breakdown**:
- ✅ Test Infrastructure: **A** (Well-organized, good fixtures)
- ⚠️ Coverage Breadth: **D** (31% overall, critical gaps)
- ✅ Test Quality: **B+** (Tests are well-written, comprehensive where they exist)
- ⚠️ Testability: **B** (Some complex functions, but mostly testable)

---

## Current Test Coverage Summary

### Overall Metrics

| Metric | Value |
|--------|-------|
| **Total Coverage** | **31%** |
| **Total Statements** | 4,191 |
| **Covered Statements** | 1,280 |
| **Uncovered Statements** | 2,911 |
| **Test Files** | 4 |
| **Total Tests** | 68 |
| **Pass Rate** | 100% |

### Coverage by Module

| Module | Coverage | Priority | Status |
|--------|----------|----------|--------|
| **models/tax_data.py** | 50% | ⚠️ HIGH | Partially tested - missing calculate_totals, calculate_credits |
| **services/tax_calculation_service.py** | 37% | 🔴 CRITICAL | Major gaps in calculation orchestration |
| **utils/tax_calculations.py** | 18% | 🔴 CRITICAL | Core tax logic largely untested |
| **utils/validation.py** | 53% | ⚠️ HIGH | Some validators missing tests |
| **utils/w2_calculator.py** | 60% | ⚠️ MEDIUM | Decent coverage but edge cases needed |
| **utils/event_bus.py** | 87% | ✅ GOOD | Well tested |
| **utils/resilience.py** | 88% | ✅ GOOD | Comprehensive coverage |
| **utils/pdf/form_mappers.py** | 87% | ✅ GOOD | Well tested |
| **utils/pdf/form_filler.py** | 79% | ✅ GOOD | Solid coverage |
| **gui/** (all pages) | 0% | ⚠️ LOW | GUI testing challenging but needed |

### Test Distribution

```
Unit Tests (61):
├── test_tax_data.py          → 14 tests (TaxData model CRUD, serialization)
├── test_pdf_form_filler.py   → 25 tests (PDF mapping, field filling)
└── test_error_handling.py    → 22 tests (Resilience, error tracking, retries)

Integration Tests (7):
└── test_pdf_export.py        → 7 tests (End-to-end PDF generation workflows)
```

---

## Critical Coverage Gaps

### 🔴 **1. Tax Calculation Logic (18% coverage) - CRITICAL**

**File**: [utils/tax_calculations.py](utils/tax_calculations.py)

**Uncovered Functions**:
- `calculate_income_tax()` - Federal income tax calculation
- `calculate_self_employment_tax()` - SE tax calculation
- `calculate_child_tax_credit()` - Child tax credit
- `calculate_earned_income_credit()` - EITC calculation

**Risk**: Tax calculation errors could result in incorrect returns, IRS penalties, or legal issues.

**Example Missing Test**:
```python
def test_calculate_income_tax_single_low_income():
    """Test income tax for single filer with low income"""
    # Taxable income: $30,000 (should be in 12% bracket)
    tax = calculate_income_tax(30000, 'Single', 2025)
    
    # Expected: (11600 * 0.10) + (30000 - 11600) * 0.12 = 1160 + 2208 = 3368
    assert tax == 3368.0

def test_calculate_income_tax_multiple_brackets():
    """Test income tax calculation across multiple tax brackets"""
    tax = calculate_income_tax(100000, 'MFJ', 2025)
    # Validate against expected calculation
    assert tax > 0
    assert tax < 100000  # Sanity check
```

**Recommendation**: Add comprehensive tax calculation test suite with:
- All filing statuses (Single, MFJ, MFS, HOH, QW)
- Multiple income levels (low, medium, high)
- Boundary cases (exactly on bracket threshold)
- Edge cases (zero income, negative income)

---

### 🔴 **2. TaxCalculationService (37% coverage) - CRITICAL**

**File**: [services/tax_calculation_service.py](services/tax_calculation_service.py)

**Uncovered Functions**:
- `calculate_complete_return()` - Main orchestration method
- `_calculate_income_components()` - Income aggregation
- `_calculate_deductions()` - Deduction calculations
- `_calculate_tax_and_payments()` - Tax and payment totals

**Risk**: This service orchestrates all tax calculations. Bugs here affect entire return accuracy.

**Example Missing Test**:
```python
def test_calculate_complete_return_simple_w2():
    """Test complete return calculation with single W-2"""
    service = TaxCalculationService(tax_year=2025)
    
    tax_data = TaxData()
    tax_data.set('personal_info.first_name', 'John')
    tax_data.set('filing_status.status', 'Single')
    tax_data.add_w2_form({
        'employer_name': 'ABC Corp',
        'wages': 50000,
        'federal_withholding': 5000
    })
    
    result = service.calculate_complete_return(tax_data)
    
    assert result.total_wages == 50000
    assert result.adjusted_gross_income == 50000
    assert result.taxable_income > 0  # After standard deduction
    assert result.income_tax > 0
    assert result.federal_withholding == 5000
    # Should get refund (withholding exceeds tax)
    assert result.refund_amount > 0 or result.amount_owed >= 0
```

**Recommendation**: Add TaxCalculationService test suite covering:
- Simple W-2 returns
- Multiple income sources
- Self-employment income
- Itemized vs. standard deduction
- Credits and payments
- Refund vs. owed scenarios

---

### ⚠️ **3. TaxData Model (50% coverage) - HIGH PRIORITY**

**File**: [models/tax_data.py](models/tax_data.py)

**Uncovered Methods**:
- `calculate_totals()` - ✅ **REFACTORED** (now uses helper methods)
  - `_calculate_total_income()` - Not tested individually
  - `_calculate_agi()` - Not tested individually
  - `_calculate_taxable_income()` - Not tested individually
  - `_calculate_total_payments()` - Not tested individually
- `calculate_credits()` - Not tested
- `load_from_file()` - ✅ **REFACTORED** (now uses helper methods)
  - Helper methods not tested individually

**Risk**: These are recently refactored methods. New bugs could be introduced without tests.

**Example Missing Test**:
```python
def test_calculate_total_income_multiple_sources():
    """Test total income calculation with multiple income sources"""
    tax_data = TaxData()
    
    # Add W-2 income
    tax_data.add_w2_form({'employer_name': 'ABC', 'wages': 50000})
    tax_data.add_w2_form({'employer_name': 'XYZ', 'wages': 25000})
    
    # Add interest income
    tax_data.set('income.interest_income', [{'amount': 500}])
    
    # Add dividend income
    tax_data.set('income.dividend_income', [{'amount': 1000}])
    
    totals = tax_data.calculate_totals()
    
    # Verify total income = 50000 + 25000 + 500 + 1000 = 76500
    assert totals['total_income'] == 76500

def test_calculate_credits_with_children():
    """Test credit calculation with child tax credit"""
    tax_data = TaxData()
    tax_data.set('filing_status.status', 'MFJ')
    
    # Add 2 qualifying children
    tax_data.add_dependent({
        'name': 'Child 1',
        'ssn': '123-45-6789',
        'relationship': 'Son',
        'birth_date': '01/15/2020',
        'qualifies_child_tax_credit': True
    })
    tax_data.add_dependent({
        'name': 'Child 2',
        'ssn': '987-65-4321',
        'relationship': 'Daughter',
        'birth_date': '06/22/2022',
        'qualifies_child_tax_credit': True
    })
    
    credits = tax_data.calculate_credits(agi=75000)
    
    # Expected: 2 * $2000 = $4000 child tax credit
    assert credits['child_tax_credit'] == 4000
    assert credits['total_credits'] >= 4000
```

**Recommendation**: Add tests for newly refactored helper methods:
- Test each `_calculate_*` helper individually
- Test `calculate_totals()` integration
- Test `calculate_credits()` for all credit types
- Test edge cases (no income, no deductions, etc.)

---

### ⚠️ **4. Validation Functions (53% coverage) - HIGH PRIORITY**

**File**: [utils/validation.py](utils/validation.py)

**Missing Tests**:
- `validate_ssn()` edge cases
- `validate_ein()` 
- `validate_email()`
- `validate_phone()` edge cases
- Invalid format handling

**Risk**: Invalid data could be accepted or valid data rejected.

**Example Missing Test**:
```python
def test_validate_ssn_valid_formats():
    """Test SSN validation with various valid formats"""
    # With hyphens
    valid, cleaned = validate_ssn('123-45-6789')
    assert valid == True
    assert cleaned == '123456789'
    
    # Without hyphens
    valid, cleaned = validate_ssn('123456789')
    assert valid == True
    assert cleaned == '123456789'
    
    # With spaces
    valid, cleaned = validate_ssn('123 45 6789')
    assert valid == True
    assert cleaned == '123456789'

def test_validate_ssn_invalid_patterns():
    """Test SSN validation rejects invalid patterns"""
    # All zeros in area number
    valid, msg = validate_ssn('000-12-3456')
    assert valid == False
    assert 'Invalid' in msg
    
    # 666 prefix (reserved)
    valid, msg = validate_ssn('666-12-3456')
    assert valid == False
    
    # 9XX prefix (ITIN range)
    valid, msg = validate_ssn('900-12-3456')
    assert valid == False
    
    # Too short
    valid, msg = validate_ssn('12-34-567')
    assert valid == False
    assert '9 digits' in msg
```

**Recommendation**: Add comprehensive validation test suite covering:
- All valid input formats
- All invalid patterns
- Edge cases and boundary values
- Error message validation

---

### ⚠️ **5. GUI Components (0% coverage) - MEDIUM PRIORITY**

**Files**: All files in [gui/](gui/) directory

**Challenges**:
- Tkinter GUI testing is complex
- Requires mocking window events
- Visual validation difficult to automate

**Recommendation**: Multi-tiered approach:

1. **Unit test business logic extracted from GUI** (HIGH PRIORITY):
   ```python
   def test_password_validation_logic():
       """Test password validation without GUI"""
       # Extract validation logic to separate function
       result = validate_pdf_password('test123', 'test123')
       assert result['valid'] == True
       
       result = validate_pdf_password('test123', 'different')
       assert result['valid'] == False
       assert 'match' in result['error']
   ```

2. **Manual test scripts** (MEDIUM PRIORITY):
   - Document manual test procedures
   - Create automated setup scripts
   - Screenshot comparison for regressions

3. **Integration tests for GUI workflows** (LOWER PRIORITY):
   - Test navigation flow
   - Test data persistence
   - Test form submission

---

## Testability Issues

### 🟡 **Issue 1: Large Methods Recently Refactored**

**Status**: IMPROVED but needs test coverage

**File**: [models/tax_data.py](models/tax_data.py)  
**Methods**: `calculate_totals()`, `load_from_file()`

**Previous State**:
- `calculate_totals()`: 80+ lines, cyclomatic complexity 15
- `load_from_file()`: Multiple nested try-except blocks

**Current State** (After Refactoring):
- ✅ Extracted into focused helper methods
- ✅ Reduced complexity by 67%
- ⚠️ **NEW ISSUE**: Helper methods not individually tested

**Recommendation**: Add tests for each new helper method:
```python
def test_calculate_total_income_w2_only():
    """Test _calculate_total_income with only W-2 wages"""
    tax_data = TaxData()
    tax_data.add_w2_form({'wages': 50000})
    
    income = tax_data.get_section('income')
    total = tax_data._calculate_total_income(income)
    
    assert total == 50000

def test_calculate_agi_no_adjustments():
    """Test _calculate_agi with no adjustments to income"""
    tax_data = TaxData()
    
    agi = tax_data._calculate_agi(total_income=75000)
    
    # With no adjustments, AGI should equal total income
    assert agi == 75000
```

---

### 🟡 **Issue 2: Tight Coupling to Configuration**

**File**: [services/tax_calculation_service.py](services/tax_calculation_service.py)

**Problem**: Service depends on global tax year configuration.

**Impact**: Hard to test different tax years in parallel.

**Current Code**:
```python
class TaxCalculationService:
    def __init__(self, tax_year: int = 2025):
        self.tax_year = tax_year
        self.config = get_tax_year_config(tax_year)  # Global lookup
```

**Recommendation**: Inject configuration for better testability:
```python
class TaxCalculationService:
    def __init__(self, tax_year: int = 2025, config: Optional[TaxYearConfig] = None):
        self.tax_year = tax_year
        self.config = config or get_tax_year_config(tax_year)

# In tests:
def test_with_custom_config():
    custom_config = TaxYearConfig(
        tax_year=2025,
        standard_deductions={'Single': 15000},  # Custom values
        tax_brackets={'Single': [(11600, 0.10), (47150, 0.12)]}
    )
    service = TaxCalculationService(2025, config=custom_config)
    # Test with controlled configuration
```

---

### 🟡 **Issue 3: GUI Password Validation (Nested Logic)**

**File**: [gui/pages/form_viewer.py](gui/pages/form_viewer.py)

**Status**: IMPROVED (5 nesting levels → 2 levels)

**Current State** (After Refactoring):
- ✅ Extracted 9 helper methods
- ✅ Flattened nesting structure
- ⚠️ **Still tightly coupled to GUI**

**Recommendation**: Extract pure validation logic for testing:
```python
# In utils/password_validator.py
def validate_password_requirements(password: str) -> Dict[str, Any]:
    """Validate password meets requirements (pure function)"""
    return {
        'valid': len(password) >= 8,
        'length': len(password),
        'errors': [] if len(password) >= 8 else ['Password too short']
    }

def validate_password_match(password: str, confirm: str) -> bool:
    """Check if passwords match (pure function)"""
    return password == confirm

# In tests:
def test_validate_password_requirements():
    result = validate_password_requirements('test123')
    assert result['valid'] == False
    assert 'too short' in result['errors'][0]
    
    result = validate_password_requirements('test12345')
    assert result['valid'] == True
```

---

## Test Quality Assessment

### ✅ **Strengths**

1. **Well-Organized Structure**:
   - Clear separation: `tests/unit/` vs. `tests/integration/`
   - Logical test file naming
   - Good use of pytest features

2. **Comprehensive Fixtures** ([tests/conftest.py](tests/conftest.py)):
   ```python
   @pytest.fixture
   def sample_personal_info()  # Personal information
   def sample_spouse_info()    # Spouse data
   def sample_w2_form()        # W-2 form data
   def sample_deductions()     # Deduction data
   def test_output_dir()       # Temporary directory
   ```

3. **Good Test Patterns**:
   - Arrange-Act-Assert structure
   - Descriptive test names
   - Clear assertions
   - Good edge case coverage (where tests exist)

4. **Integration Tests Validate End-to-End**:
   - PDF export workflows tested
   - Data actually verified in generated PDFs
   - Error scenarios covered

### ⚠️ **Weaknesses**

1. **Coverage Gaps**: Only 31% overall coverage

2. **Missing Critical Tests**:
   - Tax calculation logic (core business value)
   - TaxCalculationService (orchestration layer)
   - Validation functions (data integrity)

3. **No Performance Tests**:
   - Large W-2 counts not tested
   - PDF generation speed not measured
   - Memory usage not validated

4. **Limited Parametrization**:
   ```python
   # Current: Separate test per filing status
   def test_standard_deduction_single(): ...
   def test_standard_deduction_married(): ...
   
   # Better: Parametrized test
   @pytest.mark.parametrize("filing_status,expected", [
       ('Single', 15750),
       ('MFJ', 31500),
       ('MFS', 15750),
       ('HOH', 23650),
       ('QW', 31500)
   ])
   def test_standard_deduction(filing_status, expected):
       assert calculate_standard_deduction(filing_status, 2025) == expected
   ```

---

## Recommendations

### 🔴 **Critical Priority (Implement Immediately)**

1. **Add Tax Calculation Test Suite**
   - File: `tests/unit/test_tax_calculations.py`
   - Coverage target: 90%+
   - Tests needed: ~30 tests
   - Estimated effort: 8 hours
   
   **Tests to add**:
   - `calculate_income_tax()`: 12 tests (all filing statuses, multiple brackets)
   - `calculate_self_employment_tax()`: 6 tests (various income levels)
   - `calculate_child_tax_credit()`: 6 tests (0-4 children, income phaseouts)
   - `calculate_earned_income_credit()`: 6 tests (qualifying scenarios)

2. **Add TaxCalculationService Test Suite**
   - File: `tests/unit/test_tax_calculation_service.py`
   - Coverage target: 85%+
   - Tests needed: ~20 tests
   - Estimated effort: 6 hours
   
   **Tests to add**:
   - `calculate_complete_return()`: 10 tests (various scenarios)
   - Income component calculation: 4 tests
   - Deduction calculation: 3 tests
   - Tax and payment calculation: 3 tests

3. **Add Tests for Refactored TaxData Methods**
   - File: `tests/unit/test_tax_data.py` (extend existing)
   - Coverage target: 80%+
   - Tests needed: ~15 tests
   - Estimated effort: 4 hours
   
   **Tests to add**:
   - `_calculate_total_income()`: 4 tests
   - `_calculate_agi()`: 3 tests
   - `_calculate_taxable_income()`: 3 tests
   - `calculate_credits()`: 5 tests

### ⚠️ **High Priority (Next Sprint)**

4. **Add Validation Test Suite**
   - File: `tests/unit/test_validation.py`
   - Coverage target: 90%+
   - Tests needed: ~20 tests
   - Estimated effort: 3 hours

5. **Add W2Calculator Tests**
   - File: `tests/unit/test_w2_calculator.py`
   - Coverage target: 90%+
   - Tests needed: ~10 tests
   - Estimated effort: 2 hours

6. **Increase TaxData Coverage**
   - Extend existing tests
   - Add edge cases
   - Tests needed: ~10 tests
   - Estimated effort: 3 hours

### 🟡 **Medium Priority (Future Iteration)**

7. **Add Performance Tests**
   - File: `tests/performance/test_performance.py`
   - Test PDF generation with 10+ W-2s
   - Test calculation speed with complex returns
   - Estimated effort: 4 hours

8. **Add Property-Based Tests**
   - Use `hypothesis` library
   - Generate random valid tax data
   - Verify invariants (e.g., refund + owed = 0)
   - Estimated effort: 6 hours

9. **Document Manual GUI Test Procedures**
   - Create test scripts
   - Screenshot comparison tools
   - Estimated effort: 4 hours

---

## Testability Improvement Roadmap

### Phase 1: Critical Gaps (Week 1-2)
- [ ] Create `tests/unit/test_tax_calculations.py` with 30 tests
- [ ] Create `tests/unit/test_tax_calculation_service.py` with 20 tests
- [ ] Add 15 tests to existing `test_tax_data.py`
- **Target**: Increase coverage from 31% → 50%

### Phase 2: High Priority (Week 3-4)
- [ ] Create `tests/unit/test_validation.py` with 20 tests
- [ ] Create `tests/unit/test_w2_calculator.py` with 10 tests
- [ ] Add parametrized tests for existing coverage
- **Target**: Increase coverage from 50% → 65%

### Phase 3: Medium Priority (Week 5-6)
- [ ] Add performance tests
- [ ] Implement property-based tests
- [ ] Document GUI manual testing
- [ ] Add integration tests for complex workflows
- **Target**: Increase coverage from 65% → 75%

### Phase 4: Continuous Improvement
- [ ] Maintain 75%+ coverage on all new code
- [ ] Add tests for bug fixes
- [ ] Regular coverage audits
- [ ] Refactor for testability when needed

---

## Testing Best Practices for This Project

### 1. **Parametrize Similar Tests**
```python
@pytest.mark.parametrize("income,filing_status,expected_tax", [
    (30000, 'Single', 3368.0),
    (50000, 'Single', 6328.0),
    (100000, 'MFJ', 11000.0),
])
def test_income_tax_calculation(income, filing_status, expected_tax):
    tax = calculate_income_tax(income, filing_status, 2025)
    assert tax == expected_tax
```

### 2. **Test Edge Cases**
```python
def test_calculate_income_tax_zero_income():
    """Zero income should result in zero tax"""
    assert calculate_income_tax(0, 'Single', 2025) == 0

def test_calculate_income_tax_exact_bracket_threshold():
    """Test income exactly at bracket threshold"""
    # Test at 11,600 (top of 10% bracket for Single)
    tax = calculate_income_tax(11600, 'Single', 2025)
    assert tax == 1160.0  # 11,600 * 0.10
```

### 3. **Use Fixtures for Complex Test Data**
```python
@pytest.fixture
def complete_tax_return():
    """Fixture for a complete, realistic tax return"""
    tax_data = TaxData()
    tax_data.set('personal_info.first_name', 'John')
    tax_data.set('personal_info.last_name', 'Doe')
    tax_data.set('filing_status.status', 'MFJ')
    tax_data.add_w2_form({
        'employer_name': 'ABC Corp',
        'wages': 75000,
        'federal_withholding': 8000
    })
    # Add spouse W-2
    tax_data.add_w2_form({
        'employer_name': 'XYZ Inc',
        'wages': 60000,
        'federal_withholding': 6500
    })
    return tax_data

def test_complete_return_calculation(complete_tax_return):
    service = TaxCalculationService(2025)
    result = service.calculate_complete_return(complete_tax_return)
    assert result.total_wages == 135000
```

### 4. **Test Error Conditions**
```python
def test_calculate_income_tax_negative_income():
    """Negative income should raise ValueError"""
    with pytest.raises(ValueError, match="negative"):
        calculate_income_tax(-1000, 'Single', 2025)

def test_invalid_filing_status():
    """Invalid filing status should raise ValueError"""
    with pytest.raises(ValueError, match="filing status"):
        calculate_income_tax(50000, 'INVALID', 2025)
```

### 5. **Verify Calculation Accuracy**
```python
def test_income_tax_calculation_accuracy():
    """Test income tax calculation matches IRS tables"""
    # For Single filer with $50,000 taxable income in 2025:
    # $0 - $11,600: $11,600 × 10% = $1,160
    # $11,600 - $47,150: $35,550 × 12% = $4,266
    # $47,150 - $50,000: $2,850 × 22% = $627
    # Total: $1,160 + $4,266 + $627 = $6,053
    
    tax = calculate_income_tax(50000, 'Single', 2025)
    assert tax == 6053.0
```

---

## Continuous Integration Checklist

### Pre-Commit Requirements
- [ ] All tests pass (`pytest`)
- [ ] Coverage ≥ current baseline (31% → 50% → 75%)
- [ ] New code has tests (80%+ coverage)
- [ ] No decrease in existing coverage

### Pull Request Requirements
- [ ] Tests added for new features
- [ ] Tests added for bug fixes
- [ ] Integration tests pass
- [ ] Coverage report included
- [ ] Test documentation updated

---

## Conclusion

The FreedomUSTaxReturn application has a solid test foundation with well-organized infrastructure and good test quality. However, **critical gaps in tax calculation coverage (18%)** pose significant risks. The recent complexity refactoring improved code maintainability but introduced new helper methods that require dedicated tests.

**Immediate Action Items**:
1. ✅ Add tax calculation tests (30 tests, 8 hours) - **CRITICAL**
2. ✅ Add TaxCalculationService tests (20 tests, 6 hours) - **CRITICAL**
3. ✅ Add tests for refactored TaxData methods (15 tests, 4 hours) - **HIGH**

**Expected Outcome**: Implementing Phase 1 recommendations will increase coverage from **31% → 50%** and provide confidence in core tax calculation accuracy.

**Long-term Goal**: Achieve and maintain **75%+ code coverage** with focus on business-critical calculation logic.

---

## Appendix: Test Coverage Details

### Full Module Coverage Report

| Module | Stmts | Miss | Cover | Status |
|--------|-------|------|-------|--------|
| **Tests (100%)** | | | | |
| tests/integration/test_pdf_export.py | 97 | 0 | 100% | ✅ |
| tests/unit/test_error_handling.py | 185 | 0 | 100% | ✅ |
| tests/unit/test_pdf_form_filler.py | 91 | 0 | 100% | ✅ |
| tests/unit/test_tax_data.py | 124 | 0 | 100% | ✅ |
| **Config (100%)** | | | | |
| config/__init__.py | 3 | 0 | 100% | ✅ |
| config/app_config.py | 27 | 0 | 100% | ✅ |
| constants/__init__.py | 2 | 0 | 100% | ✅ |
| constants/pdf_fields.py | 34 | 0 | 100% | ✅ |
| **Good Coverage (75%+)** | | | | |
| config/tax_year_config.py | 24 | 1 | 96% | ✅ |
| tests/conftest.py | 25 | 1 | 96% | ✅ |
| utils/pdf/field_mapper.py | 16 | 1 | 94% | ✅ |
| utils/resilience.py | 80 | 10 | 88% | ✅ |
| utils/event_bus.py | 83 | 11 | 87% | ✅ |
| utils/pdf/form_mappers.py | 111 | 14 | 87% | ✅ |
| utils/pdf/form_filler.py | 61 | 13 | 79% | ✅ |
| **Moderate Coverage (50-74%)** | | | | |
| utils/error_tracker.py | 110 | 36 | 67% | ⚠️ |
| utils/w2_calculator.py | 25 | 10 | 60% | ⚠️ |
| utils/validation.py | 51 | 24 | 53% | ⚠️ |
| models/tax_data.py | 325 | 162 | 50% | ⚠️ |
| **Poor Coverage (<50%)** | | | | |
| services/tax_calculation_service.py | 111 | 70 | 37% | 🔴 |
| services/encryption_service.py | 72 | 57 | 21% | 🔴 |
| utils/tax_calculations.py | 77 | 63 | 18% | 🔴 |
| **No Coverage (0%)** | | | | |
| gui/main_window.py | 107 | 107 | 0% | 🔴 |
| gui/pages/*.py (all) | ~840 | ~840 | 0% | 🔴 |
| utils/async_pdf.py | 100 | 100 | 0% | 🔴 |
| utils/commands.py | 203 | 203 | 0% | 🔴 |
| All utility scripts (*.py in root) | ~500 | ~500 | 0% | ⚠️ |

---

**Report Generated**: 2025-01-XX  
**Test Framework**: pytest 9.0.2  
**Coverage Tool**: pytest-cov 7.0.0  
**Python Version**: 3.13.9
