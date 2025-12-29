# Third-Party Library License Review

## Summary
This document reviews the licenses of all third-party libraries used in the FreedomUSTaxReturn project. All libraries are open-source and their licenses are compatible with typical open-source projects. However, note that pylint uses GPL-2.0, which has copyleft implications.

## Production Dependencies

### pypdf (v4.0.0+)
- **License**: BSD-3-Clause
- **Permissive**: Yes
- **Usage**: PDF manipulation and form filling
- **Compliance**: No issues

### cryptography (v42.0.0+)
- **License**: Apache-2.0 OR BSD-3-Clause (dual license)
- **Permissive**: Yes
- **Usage**: Encryption for sensitive tax data (AES-256)
- **Compliance**: No issues

## Development Dependencies

### pytest (v7.4.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Testing framework
- **Compliance**: No issues

### pytest-cov (v4.1.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Coverage reporting for pytest
- **Compliance**: No issues

### pytest-mock (v3.11.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Mocking utilities for pytest
- **Compliance**: No issues

### black (v23.7.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Code formatting
- **Compliance**: No issues

### flake8 (v6.1.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Code linting
- **Compliance**: No issues

### pylint (v2.17.0+)
- **License**: GPL-2.0
- **Permissive**: No (copyleft)
- **Usage**: Advanced code linting
- **Compliance Notes**: 
  - GPL-2.0 requires that any derivative works also be licensed under GPL-2.0
  - If this project is distributed commercially or as proprietary software, consider replacing pylint with MIT-licensed alternatives like flake8 + plugins
  - For open-source projects, GPL-2.0 is acceptable

### mypy (v1.5.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Type checking
- **Compliance**: No issues

### sphinx (v7.1.0+)
- **License**: BSD-2-Clause
- **Permissive**: Yes
- **Usage**: Documentation generation
- **Compliance**: No issues

### sphinx-rtd-theme (v1.3.0+)
- **License**: MIT
- **Permissive**: Yes
- **Usage**: Read the Docs theme for Sphinx
- **Compliance**: No issues

## Recommendations

1. **Monitor License Changes**: Regularly check for license updates in dependencies
2. **Consider Alternatives for GPL**: If commercial distribution is planned, replace pylint with:
   - flake8 + additional plugins (all MIT)
   - ruff (MIT) - a fast Python linter
3. **License Attribution**: Ensure proper attribution in documentation or notices
4. **Dependency Scanning**: Use tools like `pip-licenses` or `licensecheck` to automate license checking

## Compliance Status
- **Overall**: ✅ Compliant
- **Permissive Licenses**: 10/11 libraries
- **Copyleft Licenses**: 1/11 libraries (pylint)
- **Action Required**: None, unless commercial distribution is planned