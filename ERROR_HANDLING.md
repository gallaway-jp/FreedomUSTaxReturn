# Error Handling Framework - Phase 1B Documentation

## Overview

Phase 1B of the maintainability roadmap implements a comprehensive error handling infrastructure across all 24 services in the Freedom US Tax Return application. This document describes the exception hierarchy, error logging system, and best practices for error handling throughout the codebase.

## Exception Hierarchy

### Base Exception Class

All custom exceptions inherit from `TaxReturnException`:

```python
from services.exceptions import TaxReturnException

class TaxReturnException(Exception):
    """
    Base exception for the Tax Return application.
    
    Provides structured error information including error codes,
    detailed context, and cause chaining for better debugging.
    """
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.__cause__ = cause
        super().__init__(message)
```

### Exception Categories

The exception hierarchy is organized by functional category:

#### 1. Authentication Exceptions

```python
InvalidPasswordException(field_name, details={})
MasterPasswordNotSetException(details={})
AuthenticationTimeoutException(context, timeout_seconds, details={})
AuthenticationException(message, details={})
```

**When to use:**
- `InvalidPasswordException`: User entered incorrect password
- `MasterPasswordNotSetException`: Master password required but not configured
- `AuthenticationTimeoutException`: Authentication session expired
- `AuthenticationException`: Other authentication failures

**Example:**
```python
from services.exceptions import InvalidPasswordException
from services.error_logger import get_error_logger

error_logger = get_error_logger()

try:
    if not verify_password(entered_password, stored_hash):
        raise InvalidPasswordException(
            field_name="password",
            details={"attempt_count": 3, "max_attempts": 5}
        )
except InvalidPasswordException as e:
    error_logger.log_exception(
        e,
        context="authentication_service.verify_user",
        extra_details={"user_id": user_id}
    )
    raise
```

#### 2. Encryption Exceptions

```python
EncryptionKeyNotFoundException(details={})
DecryptionFailedException(reason, file_path=None, details={})
InvalidEncryptionKeyException(message, details={})
```

**When to use:**
- `EncryptionKeyNotFoundException`: Encryption key cannot be found/loaded
- `DecryptionFailedException`: Data cannot be decrypted
- `InvalidEncryptionKeyException`: Encryption key format is invalid

**Example:**
```python
from services.exceptions import DecryptionFailedException
from services.error_logger import get_error_logger

error_logger = get_error_logger()

try:
    decrypted_data = cipher.decrypt(encrypted_data)
except InvalidToken as e:
    error_logger.log_exception(
        e,
        context="encryption_service.decrypt"
    )
    raise DecryptionFailedException(
        reason="Invalid or corrupted data",
        details={"data_length": len(encrypted_data)}
    ) from e
```

#### 3. Validation Exceptions

```python
InvalidInputException(field_name, details={})
MissingRequiredFieldException(field_name, details={})
DataValidationException(message, details={})
```

**When to use:**
- `InvalidInputException`: Field value is invalid format
- `MissingRequiredFieldException`: Required field is missing
- `DataValidationException`: Validation logic failure

**Example:**
```python
from services.exceptions import InvalidInputException, MissingRequiredFieldException
from services.error_logger import get_error_logger

error_logger = get_error_logger()

def validate_tax_data(tax_data):
    if not tax_data:
        raise InvalidInputException(
            field_name="tax_data",
            details={"reason": "Tax data cannot be None"}
        )
    
    if not hasattr(tax_data, 'tax_year'):
        raise MissingRequiredFieldException(
            field_name="tax_year",
            details={"available_fields": dir(tax_data)}
        )
```

#### 4. Data Processing Exceptions

```python
FileProcessingException(file_path, operation, details={})
PDFProcessingException(file_path, page_number=None, details={})
DataImportException(source, details={})
DataExportException(destination, details={})
```

**When to use:**
- `FileProcessingException`: General file operation failure
- `PDFProcessingException`: PDF-specific processing error
- `DataImportException`: Data import from external source fails
- `DataExportException`: Data export to external format fails

**Example:**
```python
from services.exceptions import FileProcessingException
from services.error_logger import get_error_logger
from pathlib import Path

error_logger = get_error_logger()

def process_receipt_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            image = Image.open(f)
            # Process image...
    except IOError as e:
        error_logger.log_exception(
            e,
            context="receipt_scanning_service.process_receipt_file"
        )
        raise FileProcessingException(
            file_path=file_path,
            operation="open_and_process",
            details={"error": str(e)}
        ) from e
```

#### 5. Configuration Exceptions

```python
ConfigurationLoadException(config_file, details={})
InvalidConfigurationException(message, details={})
MissingConfigurationException(config_key, details={})
```

**When to use:**
- `ConfigurationLoadException`: Cannot load configuration file
- `InvalidConfigurationException`: Configuration is malformed
- `MissingConfigurationException`: Required configuration key missing

#### 6. Service Exceptions

```python
ServiceUnavailableException(service_name, details={})
ServiceInitializationException(service_name, details={})
ServiceExecutionException(service_name, operation, details={})
```

**When to use:**
- `ServiceUnavailableException`: External service is unavailable
- `ServiceInitializationException`: Service failed to initialize
- `ServiceExecutionException`: Service method execution failed

**Example:**
```python
from services.exceptions import ServiceUnavailableException, ServiceExecutionException
from services.error_logger import get_error_logger

error_logger = get_error_logger()

def connect_to_bank_api(bank_code):
    try:
        response = requests.get(f"https://api.{bank_code}.com/health", timeout=5)
        if response.status_code != 200:
            raise ServiceUnavailableException(
                service_name=f"Bank API ({bank_code})",
                details={"status_code": response.status_code}
            )
    except requests.Timeout as e:
        error_logger.log_exception(
            e,
            context="bank_account_linking_service.connect_to_bank_api"
        )
        raise ServiceUnavailableException(
            service_name=f"Bank API ({bank_code})",
            details={"reason": "Connection timeout"}
        ) from e
    except ServiceUnavailableException:
        raise
    except Exception as e:
        error_logger.log_exception(
            e,
            context="bank_account_linking_service.connect_to_bank_api"
        )
        raise ServiceExecutionException(
            service_name="BankAccountLinkingService",
            operation="connect_to_bank_api",
            details={"error": str(e)}
        ) from e
```

## Error Logger

### Initialization

The ErrorLogger uses a singleton pattern for global access:

```python
from services.error_logger import get_error_logger

# Get the logger instance (creates if needed, otherwise returns existing)
error_logger = get_error_logger()
```

### Logging Methods

#### log_exception(exception, context, severity, extra_details)

Logs an exception with full context and stack trace:

```python
from services.error_logger import get_error_logger

error_logger = get_error_logger()

try:
    # Some operation
    pass
except InvalidPasswordException as e:
    error_logger.log_exception(
        e,
        context="authentication_service.verify_password",
        severity="warning",
        extra_details={"user_id": "12345", "attempt": 2}
    )
    raise
```

#### log_error(message, component, details, severity)

Logs a general error without an exception:

```python
error_logger.log_error(
    message="Tax calculation resulted in invalid value",
    component="tax_calculation_service",
    details={"calculated_value": -1000, "filing_status": "MFJ"},
    severity="error"
)
```

#### log_validation_error(field_name, validation_error, value, context)

Logs validation errors with field-specific context:

```python
error_logger.log_validation_error(
    field_name="income_amount",
    validation_error="Value cannot be negative",
    value="-5000.00",
    context="tax_interview_service.validate_income_section"
)
```

#### log_security_event(event_type, details, severity)

Logs security-related events:

```python
error_logger.log_security_event(
    event_type="password_reset_attempt",
    details={
        "user_id": "12345",
        "ip_address": "192.168.1.1",
        "success": True
    },
    severity="info"
)
```

### Error History and Filtering

Access logged errors:

```python
# Get last 10 errors
recent_errors = error_logger.get_error_history(limit=10)

# Get errors of specific type
validation_errors = error_logger.get_errors_by_type(InvalidInputException)

# Get errors by severity
critical_errors = error_logger.get_errors_by_severity("error")
```

### Sensitive Data Protection

The error logger automatically redacts sensitive information:

- Passwords: `[REDACTED]`
- Authentication tokens: `[REDACTED]`
- Credit card numbers: `[REDACTED]`
- Social Security Numbers (SSNs): `[REDACTED]`

## Error Handling Best Practices

### 1. Always Catch Specific Exceptions First

```python
# Good - specific exceptions first
try:
    authenticate_user(credentials)
except InvalidPasswordException as e:
    # Handle authentication error specifically
    error_logger.log_exception(e, context="...")
    raise
except AuthenticationTimeoutException as e:
    # Handle timeout differently
    error_logger.log_exception(e, context="...")
    raise
except Exception as e:
    # Catch-all for unexpected errors
    error_logger.log_exception(e, context="...")
    raise ServiceExecutionException(...) from e

# Bad - generic exception first
try:
    authenticate_user(credentials)
except Exception as e:
    # This catches everything, losing error specificity
    handle_error(e)
```

### 2. Use Exception Chaining with 'from'

```python
# Good - preserves exception chain for debugging
try:
    decrypt_data(encrypted_data)
except InvalidToken as e:
    error_logger.log_exception(e, context="...")
    raise DecryptionFailedException(
        reason="Invalid or corrupted data",
        details={}
    ) from e

# Bad - loses original exception context
try:
    decrypt_data(encrypted_data)
except InvalidToken:
    raise DecryptionFailedException(reason="Failed to decrypt")
```

### 3. Provide Contextual Details

```python
# Good - includes relevant debugging information
try:
    calculate_tax(tax_data)
except DataValidationException as e:
    error_logger.log_exception(
        e,
        context="tax_calculation_service.calculate_complete_return",
        extra_details={
            "tax_year": tax_data.tax_year,
            "filing_status": tax_data.filing_status,
            "total_income": total_income
        }
    )
    raise

# Bad - minimal context
try:
    calculate_tax(tax_data)
except DataValidationException:
    raise
```

### 4. Log Before Re-raising

```python
# Good - error is logged for troubleshooting
try:
    operation()
except CustomException as e:
    error_logger.log_exception(e, context="...")
    raise  # Re-raise after logging

# Bad - error is lost if not caught upstream
try:
    operation()
except CustomException as e:
    raise
```

### 5. Use Appropriate Exception Types

```python
# Good - specific exception for specific problem
def load_config(config_file):
    try:
        with open(config_file) as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise ConfigurationLoadException(
            config_file=config_file,
            details={"reason": "File not found"}
        ) from e
    except json.JSONDecodeError as e:
        raise InvalidConfigurationException(
            message=f"Invalid JSON in {config_file}",
            details={"error": str(e)}
        ) from e

# Bad - generic exception for all problems
def load_config(config_file):
    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Config error: {str(e)}")
```

## Common Error Handling Patterns

### Pattern 1: Validation Error Handling

```python
from services.exceptions import InvalidInputException, MissingRequiredFieldException

def validate_and_process(data):
    # Validate required fields
    if not data:
        raise InvalidInputException("data", {"reason": "Data is None"})
    
    if not hasattr(data, 'required_field'):
        raise MissingRequiredFieldException("required_field")
    
    # Validate field values
    if not isinstance(data.required_field, str):
        raise InvalidInputException(
            "required_field",
            {"reason": "Expected string", "actual_type": type(data.required_field).__name__}
        )
    
    # Process if validation passes
    return process(data)
```

### Pattern 2: Service Call Error Handling

```python
from services.exceptions import ServiceUnavailableException, ServiceExecutionException

def call_external_service(service_name, endpoint, data):
    error_logger = get_error_logger()
    
    try:
        response = requests.post(
            f"{endpoint}/api/endpoint",
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.ConnectionError as e:
        error_logger.log_exception(e, context=f"{service_name}.call_external_service")
        raise ServiceUnavailableException(
            service_name=service_name,
            details={"reason": "Connection failed"}
        ) from e
    except requests.Timeout as e:
        error_logger.log_exception(e, context=f"{service_name}.call_external_service")
        raise ServiceUnavailableException(
            service_name=service_name,
            details={"reason": "Request timeout"}
        ) from e
    except requests.HTTPError as e:
        error_logger.log_exception(e, context=f"{service_name}.call_external_service")
        raise ServiceExecutionException(
            service_name=service_name,
            operation="call_external_service",
            details={"status_code": e.response.status_code}
        ) from e
    except Exception as e:
        error_logger.log_exception(e, context=f"{service_name}.call_external_service")
        raise ServiceExecutionException(
            service_name=service_name,
            operation="call_external_service",
            details={"error": str(e)}
        ) from e
```

### Pattern 3: Resource Management Error Handling

```python
from services.exceptions import FileProcessingException

def process_file_safely(file_path):
    error_logger = get_error_logger()
    
    try:
        with open(file_path, 'rb') as f:
            # Process file
            data = f.read()
            result = process_data(data)
            return result
    except IOError as e:
        error_logger.log_exception(
            e,
            context="process_file_safely",
            extra_details={"file_path": str(file_path)}
        )
        raise FileProcessingException(
            file_path=file_path,
            operation="read_and_process",
            details={"error": str(e)}
        ) from e
    except Exception as e:
        error_logger.log_exception(
            e,
            context="process_file_safely",
            extra_details={"file_path": str(file_path)}
        )
        raise FileProcessingException(
            file_path=file_path,
            operation="process",
            details={"error": str(e)}
        ) from e
```

## Error Logging Output

### Log Files

Errors are logged to:
- **Debug log**: `logs/debug.log` (all severity levels)
- **Console**: WARNING and above (real-time visibility)

### Error History

The error logger maintains a history of the 100 most recent errors accessible via:

```python
error_logger = get_error_logger()
history = error_logger.get_error_history(limit=50)

for error_entry in history:
    print(f"{error_entry['timestamp']}: {error_entry['message']}")
    print(f"  Type: {error_entry['exception_type']}")
    print(f"  Severity: {error_entry['severity']}")
```

## Integration with Services

All 24 services have been updated to support the new error handling framework:

1. **Exception imports**: All services import the exception hierarchy
2. **Error logger imports**: All services have access to the centralized logger
3. **Reference implementations**: Three services (authentication, encryption, form_recommendation, tax_calculation) have enhanced error handling in key methods
4. **Systematic update path**: Remaining services can follow the reference implementations

## Migration Checklist

When adding error handling to a service method:

- [ ] Import required exceptions at top of service file
- [ ] Import error_logger via `get_error_logger()`
- [ ] Wrap main logic in try-except blocks
- [ ] Catch specific exception types before generic ones
- [ ] Log exceptions with `error_logger.log_exception()`
- [ ] Raise appropriate custom exceptions with context
- [ ] Use exception chaining with `from e`
- [ ] Document Raises section in method docstring

Example docstring:

```python
def process_tax_data(self, tax_data: 'TaxData') -> Dict[str, Any]:
    """
    Process tax data and return results.
    
    Args:
        tax_data: Tax return data to process
        
    Returns:
        Dictionary with processing results
        
    Raises:
        InvalidInputException: If tax_data is None or missing required fields
        DataValidationException: If calculated values are invalid
        ServiceExecutionException: If processing fails unexpectedly
    """
```

## Performance Considerations

- Error logging is optimized for minimal overhead
- Sensitive data redaction happens at log time
- Error history is limited to 100 most recent entries
- File logging is asynchronous when possible

## Future Improvements

- Error metrics and dashboards
- Error notification system
- Automated error recovery for transient failures
- Integration with external error tracking (Sentry, etc.)
