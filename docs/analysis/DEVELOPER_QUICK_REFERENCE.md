# Code Maintainability Quick Reference Guide

**For Developers Working on FreedomUSTaxReturn**

---

## 📋 Quick Checklist Before Committing Code

### Code Quality ✅
- [ ] Code follows existing patterns in the module
- [ ] Type hints present on function signatures
- [ ] Docstrings added to functions/classes
- [ ] No placeholder implementations (remove or implement)
- [ ] No hardcoded values (use config or constants)

### Testing ✅
- [ ] All new code has corresponding tests
- [ ] Tests pass locally: `python -m pytest`
- [ ] Test coverage maintained or improved

### Documentation ✅
- [ ] Function docstrings include examples
- [ ] Complex logic has inline comments
- [ ] CHANGELOG.md updated (if applicable)

### Git ✅
- [ ] Commit message is clear and descriptive
- [ ] Related files grouped in single commit
- [ ] No debug files included (print statements, test data)

---

## 🏗️ Architecture Quick Reference

### Project Layers
```
┌─────────────────────────────────────────┐
│    Presentation Layer (gui/)            │
│  - Modern main window                   │
│  - Pages (income, deductions, etc)      │
│  - UI components                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Application Layer (services/)        │
│  - Business logic                       │
│  - Tax calculations                     │
│  - Data processing                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Domain Layer (models/)               │
│  - TaxData (central model)              │
│  - Data validation                      │
│  - Data persistence                     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Infrastructure (config/, utils/)     │
│  - Configuration management             │
│  - Utility functions                    │
│  - Constants                            │
└─────────────────────────────────────────┘
```

### Key Dependencies
- **Services should NOT import GUI components** ❌
- **GUI should import services but NOT modify them directly** (use callbacks)
- **Models should be framework-agnostic** (no GUI/service dependencies)

---

## 🚨 Common Maintainability Anti-Patterns

### ❌ DON'T DO THIS

**1. God Objects (Too Many Responsibilities)**
```python
# Bad: Single class doing everything
class TaxData:
    def save(self): pass
    def validate(self): pass
    def encrypt(self): pass
    def calculate_taxes(self): pass
    def export_pdf(self): pass
    # ... 10 more methods
```

**2. Placeholder Methods**
```python
# Bad: Unimplemented feature in production code
def _open_audit_trail(self):
    show_info_message("Not implemented")
```

**3. Hardcoded Values**
```python
# Bad: Magic numbers scattered everywhere
if filing_status == "single":
    deduction = 14600  # Where did this come from?
```

**4. Silent Failures**
```python
# Bad: Swallowing exceptions hides problems
try:
    result = self.service.process()
except:
    pass  # Problem hidden! 😱
```

**5. Deep Nesting**
```python
# Bad: Hard to follow logic
if condition1:
    if condition2:
        if condition3:
            if condition4:
                # What are we doing here?
                result = do_something()
```

---

## ✅ GOOD PATTERNS TO FOLLOW

### 1. Single Responsibility
```python
# Good: Each class has one job
class IncomeCalculator:
    """Calculate income totals"""
    def calculate_w2_income(self, w2s: List[W2]) -> float: pass

class IncomeValidator:
    """Validate income data"""
    def validate_w2(self, w2: W2) -> Tuple[bool, List[str]]: pass

class IncomePersistence:
    """Save/load income data"""
    def save_income(self, income_data: Dict) -> None: pass
```

### 2. Dependency Injection
```python
# Good: Dependencies passed in, not created internally
class IncomeProcessor:
    def __init__(self, calculator: IncomeCalculator, validator: IncomeValidator):
        self.calculator = calculator
        self.validator = validator

# Usage
processor = IncomeProcessor(
    calculator=IncomeCalculator(),
    validator=IncomeValidator()
)
```

### 3. Clear Error Handling
```python
# Good: Specific exceptions with context
try:
    result = self.validator.validate(data)
except ValidationError as e:
    logger.error(f"Income validation failed: {e}")
    show_error_message("Validation Error", str(e))
except TaxReturnError as e:
    logger.error(f"Tax operation failed: {e}")
```

### 4. Configuration Over Hardcoding
```python
# Good: Use config for values that change
TAX_TABLES = get_tax_year_config(2025)
standard_deduction = TAX_TABLES['standard_deduction']['single']

# Bad: Hardcoded
standard_deduction = 14600
```

### 5. Meaningful Names
```python
# Good: Clear what the variable represents
user_input_salary = entry.get()
calculated_tax = calculate_income_tax(salary, filing_status)

# Bad: Cryptic names
val = entry.get()
tax = calc(v, fs)
```

---

## 🧪 Testing Guidelines

### Unit Test Pattern
```python
import pytest
from services.tax_calculator import TaxCalculator

class TestTaxCalculator:
    @pytest.fixture
    def calculator(self):
        """Setup calculator for each test"""
        return TaxCalculator()
    
    def test_calculate_single_filer_2025(self, calculator):
        """Test tax calculation for single filer"""
        # Arrange
        salary = 50000
        filing_status = "single"
        
        # Act
        result = calculator.calculate(salary, filing_status)
        
        # Assert
        assert result == expected_value
        assert result > 0
```

### Integration Test Pattern
```python
class TestTaxCalculationIntegration:
    def test_complete_tax_return_workflow(self, config):
        """Test complete workflow from data entry to calculation"""
        # Create services
        tax_data = TaxData(config)
        validator = TaxValidator(config)
        calculator = TaxCalculator(config)
        
        # Process workflow
        tax_data.add_income(W2(...))
        assert validator.validate(tax_data)
        result = calculator.calculate(tax_data)
        assert result.total_tax > 0
```

---

## 📝 Documentation Standards

### Function Documentation
```python
def calculate_standard_deduction(filing_status: str, tax_year: int = 2025) -> float:
    """
    Calculate IRS standard deduction for given tax year and filing status.
    
    This function returns the standard deduction amount based on current
    IRS tax tables. Used when taxpayer does not itemize deductions.
    
    Args:
        filing_status: One of 'single', 'married_filing_jointly',
                      'married_filing_separately', 'head_of_household',
                      'qualifying_widow'
        tax_year: Tax year for calculation (default 2025)
    
    Returns:
        Standard deduction amount in dollars
    
    Raises:
        ValueError: If filing_status is invalid
        KeyError: If tax_year not found in tax tables
    
    Examples:
        >>> calculate_standard_deduction('single', 2025)
        14600.0
        
        >>> calculate_standard_deduction('married_filing_jointly', 2025)
        29200.0
    
    Note:
        Standard deductions are indexed for inflation annually.
        See: https://www.irs.gov/filingstatus
    """
```

### Class Documentation
```python
class TaxCalculator:
    """
    Service for calculating federal income tax.
    
    Performs all tax calculations including:
    - Income tax based on progressive brackets
    - Tax credits (child tax credit, earned income credit, etc)
    - Alternative minimum tax (AMT)
    - Net investment income tax
    
    Attributes:
        config: Application configuration
        tax_tables: Tax bracket tables for current year
        
    Example:
        calculator = TaxCalculator(config)
        tax_data = TaxData()
        # ... populate tax_data ...
        result = calculator.calculate(tax_data)
        print(f"Total tax: ${result.total_tax:,.2f}")
    """
```

---

## 🔧 Common Development Tasks

### Adding a New Feature

1. **Create the service**:
   ```python
   # services/new_feature_service.py
   class NewFeatureService:
       def __init__(self, config: AppConfig):
           self.config = config
       
       def process(self) -> Result:
           pass
   ```

2. **Create tests**:
   ```python
   # tests/unit/test_new_feature_service.py
   class TestNewFeatureService:
       def test_process(self):
           pass
   ```

3. **Add to GUI** (if UI needed):
   ```python
   # gui/pages/new_feature_page.py
   class NewFeaturePage(ModernScrollableFrame):
       def __init__(self, service: NewFeatureService):
           self.service = service
   ```

4. **Update main window**:
   ```python
   # gui/modern_main_window.py
   self.new_feature_service = NewFeatureService(config)
   ```

### Running Tests Locally
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_calculator.py

# Run with coverage
python -m pytest --cov=services --cov=models

# Run specific test
python -m pytest tests/unit/test_calculator.py::TestTaxCalculator::test_single_filer
```

### Code Formatting
```bash
# Check code format
black --check .

# Auto-format code
black .

# Sort imports
isort .

# Check style
flake8 .
```

---

## 📊 Current Maintainability Status

| Aspect | Rating | Target | Priority |
|--------|--------|--------|----------|
| Code Organization | 9/10 | 9/10 | ✅ Good |
| Error Handling | 6/10 | 8/10 | 🟡 Medium |
| Documentation | 7.5/10 | 8.5/10 | 🟡 Medium |
| Test Coverage | 8.5/10 | 9/10 | ✅ Good |
| Code Duplication | 7/10 | 9/10 | 🟡 Medium |
| Dependency Management | 9/10 | 9/10 | ✅ Good |

---

## 🎯 Your Responsibility as a Developer

**When Writing Code:**
1. Follow existing patterns in the codebase
2. Add tests for new functionality
3. Document complex logic
4. Don't leave placeholder methods
5. Use configuration, not hardcoding

**Before Committing:**
1. Run tests: `pytest`
2. Format code: `black . && isort .`
3. Write clear commit messages
4. Review your own code first

**Code Review Mindset:**
- Is this code maintainable?
- Can someone understand it in 6 months?
- Is it testable?
- Does it follow project patterns?
- Are there security concerns?

---

## 📚 Further Reading

- See [MAINTAINABILITY_AUDIT_2026.md](./MAINTAINABILITY_AUDIT_2026.md) for detailed analysis
- See [CODE_REVIEW_CLEAN_CODE_SOLID.md](./CODE_REVIEW_CLEAN_CODE_SOLID.md) for design patterns
- See [docs/guides/](../guides/) for user documentation
- See [docs/roadmap/](../roadmap/) for development plans

---

**Last Updated**: January 2026  
**Questions?** Check the full maintainability audit document for detailed guidance.
