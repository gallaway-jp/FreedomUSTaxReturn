# Test Suite Documentation

## Overview

This directory contains comprehensive tests for the FreedomUSTaxReturn application.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_tax_data.py   # TaxData model tests
│   └── test_pdf_form_filler.py  # PDF form filler tests
├── integration/            # Integration tests
│   └── test_pdf_export.py # End-to-end PDF export tests
├── fixtures/              # Test data and fixtures
│   └── sample_tax_returns.py  # Sample tax return data
├── conftest.py            # Shared pytest fixtures
└── README.md             # This file
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/unit/test_tax_data.py
```

### Run Specific Test Class
```bash
pytest tests/unit/test_tax_data.py::TestTaxDataInitialization
```

### Run Specific Test
```bash
pytest tests/unit/test_tax_data.py::TestTaxDataInitialization::test_create_empty_tax_data
```

### Run with Coverage
```bash
pytest --cov=models --cov=utils --cov-report=html
```

### Run Only Unit Tests
```bash
pytest tests/unit/
```

### Run Only Integration Tests
```bash
pytest tests/integration/
```

### Verbose Output
```bash
pytest -v
```

### Show Print Statements
```bash
pytest -s
```

## Test Categories

### Unit Tests

**test_tax_data.py** - Tests for the TaxData model
- Initialization and defaults
- Getting and setting data
- W-2 form operations
- Dependent operations
- Data validation
- Serialization (save/load)

**test_pdf_form_filler.py** - Tests for PDF form filling utilities
- DotDict helper class
- Standard deduction calculations
- Form 1040 field mapping
- PDF form inspection

### Integration Tests

**test_pdf_export.py** - End-to-end PDF export tests
- Exporting with TaxData objects
- Exporting with plain dictionaries
- Data verification in exported PDFs
- Multiple W-2 handling
- Spouse information
- Complete return exports

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_personal_info` - Sample personal information
- `sample_spouse_info` - Sample spouse information
- `sample_filing_status` - Sample filing status
- `sample_w2_form` - Sample W-2 form data
- `sample_deductions` - Sample deduction data
- `test_output_dir` - Temporary directory for test outputs

## Writing New Tests

### Unit Test Example

```python
def test_new_feature():
    """Test description"""
    # Arrange
    tax_data = TaxData()
    
    # Act
    tax_data.set('some.field', 'value')
    
    # Assert
    assert tax_data.get('some.field') == 'value'
```

### Integration Test Example

```python
def test_pdf_export_feature(test_output_dir, sample_personal_info):
    """Test description"""
    # Arrange
    tax_data = TaxData()
    for key, value in sample_personal_info.items():
        tax_data.set(f'personal_info.{key}', value)
    
    # Act
    exporter = TaxReturnPDFExporter()
    output_file = test_output_dir / "test.pdf"
    success = exporter.export_1040_only(tax_data, str(output_file))
    
    # Assert
    assert success
    assert output_file.exists()
```

## Code Coverage

After running tests with coverage:

```bash
pytest --cov=models --cov=utils --cov-report=html
```

Open `htmlcov/index.html` in a browser to see detailed coverage reports.

## Continuous Integration

Tests should be run:
- Before committing code
- In pull requests
- Before releases
- On schedule (nightly builds)

## Test Best Practices

1. **Each test should test one thing**
2. **Use descriptive test names** - `test_export_with_multiple_w2s`
3. **Follow AAA pattern** - Arrange, Act, Assert
4. **Use fixtures** for common setup
5. **Keep tests independent** - No test should depend on another
6. **Clean up** - Use tmp_path for temporary files
7. **Test edge cases** - Empty data, invalid data, boundary conditions

## Known Issues

None currently.

## Future Improvements

- Add GUI tests (if possible with tkinter)
- Add performance tests
- Add security tests for sensitive data handling
- Add tests for tax calculation logic
- Increase code coverage to 90%+
