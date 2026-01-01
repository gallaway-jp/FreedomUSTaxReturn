# Phase 3: Code Quality Automation Setup Guide

**Freedom US Tax Return Application**  
**Phase**: 3 of 5  
**Focus**: Pre-Commit Hooks & Automated Code Quality Gates  
**Estimated Maintainability Impact**: +0.3-0.5 points

---

## Overview

Phase 3 establishes automated code quality gates that run before commits and during CI/CD pipelines. This prevents low-quality code from entering the repository and maintains consistent code standards across the project.

### What You'll Get

✅ **Automatic code formatting** (Black)  
✅ **Import organization** (isort)  
✅ **Lint checking** (Pylint)  
✅ **Type safety** (mypy)  
✅ **Security scanning** (Bandit)  
✅ **Docstring validation** (pydocstyle)  
✅ **Complexity warnings** (radon)  
✅ **CI/CD Pipeline** (GitHub Actions)

---

## Installation

### Step 1: Install Pre-Commit Framework

```bash
# Install pre-commit
pip install pre-commit

# Navigate to project root
cd d:\Development\Python\FreedomUSTaxReturn

# Install git hooks
pre-commit install
```

**What this does**:
- Installs `.git/hooks/pre-commit` script
- Hooks run automatically before each commit
- Prevents commits with quality issues (unless explicitly skipped)

### Step 2: Install Development Dependencies

```bash
# Install all development tools at once
pip install -e ".[dev]"

# Or individually:
pip install black isort pylint mypy bandit pydocstyle radon pytest pytest-cov
```

### Step 3: (Optional) Run Checks on Existing Code

```bash
# Run all pre-commit hooks on entire codebase
pre-commit run --all-files

# This identifies issues to fix before first commit
```

---

## Configured Hooks

### 1. **Black** - Code Formatter
**Purpose**: Enforces consistent code style  
**Configuration**: Line length 100, Python 3.13  
**When it runs**: Before every commit  
**What it does**: Auto-formats code to Black standard

```bash
# Run manually
black .

# Check without formatting
black --check .
```

### 2. **isort** - Import Organizer
**Purpose**: Sorts and organizes imports consistently  
**Configuration**: Black-compatible, groups stdlib/third-party/local  
**When it runs**: Before every commit  
**What it does**: Auto-organizes imports

```bash
# Run manually
isort .

# Check without organizing
isort --check-only .
```

### 3. **Pylint** - Linter
**Purpose**: Checks for code errors, style violations, complexity  
**Configuration**: Custom rules in `pyproject.toml`  
**When it runs**: Before every commit (warnings allowed)  
**What it does**: Reports style/error violations

```bash
# Run manually
pylint services/ models/ utils/ gui/
```

### 4. **mypy** - Type Checker
**Purpose**: Static type checking for Python  
**Configuration**: Strict mode on, ignore missing imports  
**When it runs**: Before every commit (warnings allowed)  
**What it does**: Validates type annotations

```bash
# Run manually
mypy --ignore-missing-imports services/ models/ utils/ gui/
```

### 5. **Bandit** - Security Scanner
**Purpose**: Scans for common security vulnerabilities  
**Configuration**: Checks all Python files  
**When it runs**: Before every commit (warnings allowed)  
**What it does**: Reports potential security issues

```bash
# Run manually
bandit -r services/ models/ utils/ gui/
```

### 6. **pydocstyle** - Docstring Checker
**Purpose**: Ensures docstrings follow Google style  
**Configuration**: Google convention, public functions required  
**When it runs**: Before every commit (warnings allowed)  
**What it does**: Validates docstring presence/format

```bash
# Run manually
pydocstyle --convention=google services/ models/ utils/ gui/
```

### 7. **radon** - Complexity Checker
**Purpose**: Identifies overly complex functions  
**Configuration**: Warns on high complexity, allows commit  
**When it runs**: Before every commit (warnings allowed)  
**What it does**: Reports cyclomatic complexity

```bash
# Run manually
radon cc -a services/ models/ utils/ gui/
```

### 8. **Trailing Whitespace & EOF**
**Purpose**: Removes trailing whitespace, ensures files end with newline  
**When it runs**: Before every commit  
**What it does**: Auto-fixes whitespace issues

### 9. **YAML/JSON/TOML Validators**
**Purpose**: Checks syntax of config files  
**When it runs**: Before every commit  
**What it does**: Prevents syntax errors in config files

### 10. **Private Key Detector**
**Purpose**: Prevents accidental commit of secrets  
**When it runs**: Before every commit  
**What it does**: Blocks files containing keys/tokens

---

## Usage Examples

### Normal Commit (With Quality Checks)

```bash
# Make changes
git add .

# Commit - pre-commit hooks run automatically
git commit -m "Add new feature"

# If issues found, fix them and retry
git commit -m "Add new feature"
```

### Bypass Hooks (Use Cautiously)

```bash
# Skip all hooks
git commit --no-verify -m "Emergency fix"

# Skip specific hook
SKIP=pylint git commit -m "Commit with linting warnings"
```

### Run Checks Manually

```bash
# Check all files
pre-commit run --all-files

# Check specific hook
pre-commit run black --all-files

# Check specific files
pre-commit run --files services/tax_calculation_service.py
```

### Auto-Fix Issues

```bash
# Format code with Black
black .

# Organize imports with isort
isort .

# Fix simple issues
autopep8 --in-place --aggressive services/
```

---

## GitHub Actions CI/CD

### Workflow: `ci.yml`

Runs on:
- Every push to `main` or `develop`
- Every pull request
- Nightly schedule (2 AM UTC)

### Jobs

#### 1. **Quality Checks**
- Black formatter check
- isort import check
- Pylint linting
- mypy type checking
- Bandit security scan
- pydocstyle docstring check
- radon complexity check

**Result**: Reports issues (non-blocking)

#### 2. **Unit & Integration Tests**
- Runs full pytest suite
- Generates coverage report
- Uploads to Codecov
- Requires 70% coverage minimum

**Result**: Blocks PR if tests fail

#### 3. **Syntax & File Checks**
- Runs all pre-commit hooks
- Validates YAML/JSON/TOML
- Checks trailing whitespace

**Result**: Blocks PR if syntax invalid

#### 4. **Security Scanning**
- Bandit vulnerability scan
- Safety dependency check
- Secret detection (TruffleHog)

**Result**: Reports issues (non-blocking)

#### 5. **Summary**
- Collects results from all jobs
- Shows overall status

---

## Configuration Files

### `.pre-commit-config.yaml`
**Purpose**: Defines which hooks run and their settings  
**Location**: Project root  
**Usage**: Loaded automatically by pre-commit framework

**Key settings**:
```yaml
default_language_version:
  python: python3.13  # Python version for hooks

repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1  # Version
    hooks:
      - id: black
        args: [--line-length=100]  # Configuration
```

### `pyproject.toml`
**Purpose**: Centralized configuration for all Python tools  
**Location**: Project root  
**Usage**: Loaded automatically by each tool

**Tool sections**:
```toml
[tool.black]           # Black configuration
[tool.isort]           # isort configuration
[tool.mypy]            # mypy configuration
[tool.pylint.***]      # Pylint configuration
[tool.pytest.***]      # pytest configuration
[tool.coverage.***]    # Coverage configuration
[tool.pydocstyle]      # pydocstyle configuration
[tool.radon]           # radon configuration
[tool.bandit]          # Bandit configuration
```

### `.github/workflows/ci.yml`
**Purpose**: GitHub Actions workflow definition  
**Location**: `.github/workflows/`  
**Usage**: Runs automatically on push/PR

**Jobs**:
- quality (code quality checks)
- tests (pytest with coverage)
- syntax (pre-commit all files)
- security (Bandit + Safety + TruffleHog)
- summary (collects results)

---

## Best Practices

### 1. Keep Hooks Fast

Current hooks run in ~30 seconds. If slower:
- Run only modified files (git hook feature)
- Parallelize checks (future improvement)

### 2. Address Issues Properly

```bash
# Good: Fix issues
git commit -m "Fix: Remove trailing whitespace"

# Bad: Bypass hooks
git commit --no-verify -m "Quick fix"
```

### 3. Update Hook Versions

```bash
# Update all hooks to latest versions
pre-commit autoupdate

# Commit the update
git add .pre-commit-config.yaml
git commit -m "chore: Update pre-commit hooks"
```

### 4. Manage False Positives

If a tool reports false positives:

```bash
# Add to tool configuration in pyproject.toml
[tool.pylint.messages_control]
disable = [
    "C0330",  # Specific rule to disable
]
```

### 5. Handle Formatting Conflicts

If Black and isort conflict:

```yaml
# In isort config
profile = "black"  # Makes isort compatible with Black
```

---

## Troubleshooting

### Hook Runs Too Long

**Problem**: Hooks take >60 seconds to run

**Solution**:
```bash
# Check which hook is slow
time pre-commit run --all-files

# Run only modified files instead
pre-commit run
```

### Hook Prevents Legitimate Code

**Problem**: Hook blocks valid code

**Solution**:
```bash
# 1. Check if configuration is correct
# 2. Update configuration in pyproject.toml
# 3. Test updated config
# 4. Commit configuration change
```

### Different Results Locally vs CI

**Problem**: Code passes locally but fails in CI

**Possible causes**:
- Different Python versions (use 3.13 in both)
- Different hook versions (update locally)
- Different environment variables

**Solution**:
```bash
# Update hooks to match CI
pre-commit autoupdate

# Run full check like CI does
pre-commit run --all-files
```

### Accidentally Committed Bad Code

**Problem**: Code already committed without hooks running

**Solution**:
```bash
# Option 1: Amend last commit (local only)
git commit --amend --no-edit

# Option 2: Fix in new commit
git add .
git commit -m "fix: Address code quality issues"
```

---

## Maintenance

### Weekly Tasks

```bash
# Check for hook updates
pre-commit autoupdate

# Review CI/CD logs in GitHub
# -> Actions tab -> See any failed jobs
```

### Monthly Tasks

```bash
# Update dependencies
pip install --upgrade -e ".[dev]"

# Review and update tool versions in .pre-commit-config.yaml
```

### Quarterly Tasks

```bash
# Review and update quality thresholds
# - Update minimum coverage % in pytest config
# - Review complexity limits in radon config
# - Review docstring requirements in pydocstyle config
```

---

## Success Metrics

### Phase 3 Targets

| Metric | Target | Status |
|--------|--------|--------|
| **Code formatted consistently** | 100% | Automated by Black |
| **Imports organized** | 100% | Automated by isort |
| **Type hints checked** | 100% | mypy validates |
| **Security issues identified** | 100% | Bandit scans |
| **Test coverage** | 70%+ | pytest enforces |
| **CI/CD pipeline** | Operational | GitHub Actions |
| **Zero bypassed hooks** | Goal | Monitored |

### Maintainability Score Impact

**Before Phase 3**: 8.5-8.7/10  
**After Phase 3**: 8.8-9.0/10 (estimated)

**Why**:
- ✅ Code quality consistent and enforced
- ✅ Type safety verified automatically
- ✅ Security vulnerabilities caught early
- ✅ Test coverage maintained
- ✅ Onboarding faster (clear standards)

---

## Next Steps

### Phase 3 Complete When:

✅ Pre-commit hooks installed and working  
✅ GitHub Actions CI/CD running successfully  
✅ All code passes quality checks  
✅ Team trained on hook usage

### Phase 4: Test Coverage Improvements

After Phase 3 stabilizes, Phase 4 will:
- Expand test suite coverage to 80%+
- Add specific error handling tests
- Add integration tests
- Add performance benchmarks

---

## Quick Reference

```bash
# Install
pip install pre-commit && pre-commit install

# Check
pre-commit run --all-files

# Auto-fix
black . && isort .

# Bypass (emergency only)
git commit --no-verify

# Update
pre-commit autoupdate

# CI Status
# Open: https://github.com/yourorg/freedom-us-tax-return/actions
```

---

## Support

For issues with:
- **Pre-commit**: `pre-commit --version && pre-commit run --help`
- **Black**: `black --help`
- **isort**: `isort --help`
- **Pylint**: `pylint --help-all`
- **mypy**: `mypy --help`
- **Bandit**: `bandit --help`

---

**Document Status**: COMPLETE ✅  
**Configuration Status**: READY ✅  
**Automation Status**: CONFIGURED ✅
