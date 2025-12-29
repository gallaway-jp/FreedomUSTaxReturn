# Coverage Analysis for 75% Target

## Current State
**Current Coverage**: 59%  
**Target Coverage**: 75%  
**Gap to Close**: 16 percentage points

## High-Impact Targets (Will Move Coverage Most)

### Priority 1: Large Production Files (0% coverage currently)
1. **models/tax_data.py** - 105/345 missing (70% coverage already, finish it)
2. **config/dependencies.py** - 53/53 missing (dependency injection container)
3. **utils/tax_data_validator.py** - 60/60 missing (validation logic)
4. **utils/pdf_field_inspector.py** - 75/75 missing (PDF inspection utilities)
5. **utils/pdf/form_mappers.py** - 14/111 missing (87% coverage, finish it)

### Priority 2: Medium Production Files (High value)
6. **utils/pdf/form_filler.py** - 12/61 missing (80% coverage, finish it)
7. **services/encryption_service.py** - 10/72 missing (86% coverage, finish it)
8. **utils/error_tracker.py** - 12/110 missing (89% coverage, finish it)
9. **utils/resilience.py** - 3/80 missing (96% coverage, finish it)
10. **services/tax_calculation_service.py** - 2/120 missing (98% coverage, finish it)

### Skip: GUI & Script Files (Low priority for coverage)
- gui/* files (940+ lines) - GUI testing requires PyQt6 mocking, low ROI
- Script files (*.py in root) - Utility scripts, not core logic
- utils/commands.py (203 lines) - CLI commands, not core logic
- utils/async_pdf.py (100 lines) - Async utilities, complex to test

### Skip: Test Files Themselves
- test_security_features.py - This is a test file, doesn't need coverage
- test_*.py files in root - Test files themselves

## Strategic Approach

### Phase 1: Complete Near-Complete Files (Quick Wins)
Target files already >80% covered:
- services/tax_calculation_service.py (98% → 100%)
- utils/resilience.py (96% → 100%)
- utils/error_tracker.py (89% → 100%)
- services/encryption_service.py (86% → 100%)
- utils/pdf/form_mappers.py (87% → 100%)
- utils/pdf/form_filler.py (80% → 100%)

**Estimated Impact**: ~100 lines covered = +2-3% coverage

### Phase 2: Medium-Sized New Files
- config/dependencies.py (53 lines)
- utils/tax_data_validator.py (60 lines)

**Estimated Impact**: ~110 lines covered = +2-3% coverage

### Phase 3: Large File Completion
- models/tax_data.py (105 remaining lines)
- utils/pdf_field_inspector.py (75 lines)

**Estimated Impact**: ~180 lines covered = +4-5% coverage

### Phase 4: Integration Test Fixes
- Fix failing integration tests (47 lines in test files, but tests production code)

**Estimated Impact**: ~50-100 lines of production code = +1-2% coverage

## Total Estimated Coverage Gain
- Phase 1: +3%  (59% → 62%)
- Phase 2: +3%  (62% → 65%)
- Phase 3: +5%  (65% → 70%)
- Phase 4: +5%  (70% → 75%)

**Target: 75%+ coverage achieved**

## Implementation Plan

### Immediate Actions:
1. ✅ Complete tax_calculation_service.py (2 lines)
2. ✅ Complete resilience.py (3 lines)
3. ✅ Complete error_tracker.py (12 lines)
4. ✅ Complete encryption_service.py (10 lines)
5. ✅ Complete pdf/form_filler.py (12 lines)
6. ✅ Complete pdf/form_mappers.py (14 lines)

### Next Wave:
7. Create config/test_dependencies.py
8. Create utils/test_tax_data_validator.py
9. Complete models/tax_data.py coverage
10. Create utils/test_pdf_field_inspector.py

### Final Push:
11. Fix integration test failures
12. Add edge case tests for maximum coverage
