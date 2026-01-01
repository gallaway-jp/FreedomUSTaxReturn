"""
Exception Hierarchy for Freedom US Tax Return Application

Defines a comprehensive exception hierarchy for consistent error handling
across all services and components.

Exception Hierarchy:
    TaxReturnException (base)
    ├─ AuthenticationException
    │  ├─ InvalidPasswordException
    │  ├─ MasterPasswordNotSetException
    │  └─ AuthenticationTimeoutException
    ├─ EncryptionException
    │  ├─ EncryptionKeyNotFoundException
    │  ├─ DecryptionFailedException
    │  └─ InvalidEncryptionKeyException
    ├─ ValidationException
    │  ├─ InvalidInputException
    │  ├─ MissingRequiredFieldException
    │  └─ DataValidationException
    ├─ DataProcessingException
    │  ├─ FileProcessingException
    │  ├─ PDFProcessingException
    │  ├─ DataImportException
    │  └─ DataExportException
    ├─ ConfigurationException
    │  ├─ ConfigurationLoadException
    │  ├─ InvalidConfigurationException
    │  └─ MissingConfigurationException
    └─ ServiceException
       ├─ ServiceUnavailableException
       ├─ ServiceInitializationException
       └─ ServiceExecutionException
"""

from typing import Optional, Any


class TaxReturnException(Exception):
    """
    Base exception for all tax return application errors.
    
    All custom exceptions should inherit from this class to enable
    centralized exception handling and logging.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize a TaxReturnException.
        
        Args:
            message: Human-readable error message
            error_code: Optional application-specific error code
            details: Optional dictionary with additional error context
            cause: Optional original exception (for chaining)
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return formatted error message with code."""
        return f"[{self.error_code}] {self.message}"
    
    def get_details(self) -> dict:
        """Get complete error details including cause."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
            "exception_type": self.__class__.__name__
        }


# ============================================================================
# AUTHENTICATION EXCEPTIONS
# ============================================================================

class AuthenticationException(TaxReturnException):
    """Base exception for authentication-related errors."""
    pass


class InvalidPasswordException(AuthenticationException):
    """Raised when password validation fails."""
    
    def __init__(self, message: str = "Invalid password provided", details: Optional[dict] = None):
        super().__init__(message, error_code="AUTH_INVALID_PASSWORD", details=details)


class MasterPasswordNotSetException(AuthenticationException):
    """Raised when master password is required but not configured."""
    
    def __init__(self, message: str = "Master password has not been set", details: Optional[dict] = None):
        super().__init__(message, error_code="AUTH_NO_MASTER_PASSWORD", details=details)


class AuthenticationTimeoutException(AuthenticationException):
    """Raised when authentication session times out."""
    
    def __init__(self, message: str = "Authentication session has expired", details: Optional[dict] = None):
        super().__init__(message, error_code="AUTH_TIMEOUT", details=details)


# ============================================================================
# ENCRYPTION EXCEPTIONS
# ============================================================================

class EncryptionException(TaxReturnException):
    """Base exception for encryption-related errors."""
    pass


class EncryptionKeyNotFoundException(EncryptionException):
    """Raised when encryption key file is not found."""
    
    def __init__(self, key_path: str, details: Optional[dict] = None):
        msg = f"Encryption key not found at: {key_path}"
        details = details or {}
        details['key_path'] = key_path
        super().__init__(msg, error_code="ENC_KEY_NOT_FOUND", details=details)


class DecryptionFailedException(EncryptionException):
    """Raised when decryption of data fails."""
    
    def __init__(self, message: str = "Failed to decrypt data", details: Optional[dict] = None):
        super().__init__(message, error_code="ENC_DECRYPTION_FAILED", details=details)


class InvalidEncryptionKeyException(EncryptionException):
    """Raised when encryption key is invalid or corrupted."""
    
    def __init__(self, message: str = "Encryption key is invalid or corrupted", details: Optional[dict] = None):
        super().__init__(message, error_code="ENC_INVALID_KEY", details=details)


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================

class ValidationException(TaxReturnException):
    """Base exception for data validation errors."""
    pass


class InvalidInputException(ValidationException):
    """Raised when user input is invalid."""
    
    def __init__(self, field_name: str, message: str = "Invalid input", details: Optional[dict] = None):
        details = details or {}
        details['field_name'] = field_name
        full_msg = f"Invalid input for field '{field_name}': {message}"
        super().__init__(full_msg, error_code="VAL_INVALID_INPUT", details=details)


class MissingRequiredFieldException(ValidationException):
    """Raised when a required field is missing."""
    
    def __init__(self, field_name: str, details: Optional[dict] = None):
        details = details or {}
        details['field_name'] = field_name
        msg = f"Required field is missing: {field_name}"
        super().__init__(msg, error_code="VAL_MISSING_FIELD", details=details)


class DataValidationException(ValidationException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str = "Data validation failed", details: Optional[dict] = None):
        super().__init__(message, error_code="VAL_DATA_VALIDATION", details=details)


# ============================================================================
# DATA PROCESSING EXCEPTIONS
# ============================================================================

class DataProcessingException(TaxReturnException):
    """Base exception for data processing errors."""
    pass


class FileProcessingException(DataProcessingException):
    """Raised when file processing fails."""
    
    def __init__(self, file_path: str, operation: str = "process", details: Optional[dict] = None):
        details = details or {}
        details['file_path'] = file_path
        details['operation'] = operation
        msg = f"Failed to {operation} file: {file_path}"
        super().__init__(msg, error_code="FILE_PROCESSING_ERROR", details=details)


class PDFProcessingException(DataProcessingException):
    """Raised when PDF processing fails."""
    
    def __init__(self, message: str = "PDF processing failed", details: Optional[dict] = None):
        super().__init__(message, error_code="PDF_PROCESSING_ERROR", details=details)


class DataImportException(DataProcessingException):
    """Raised when data import fails."""
    
    def __init__(self, source: str, message: str = "Failed to import data", details: Optional[dict] = None):
        details = details or {}
        details['source'] = source
        full_msg = f"Import from {source} failed: {message}"
        super().__init__(full_msg, error_code="IMPORT_ERROR", details=details)


class DataExportException(DataProcessingException):
    """Raised when data export fails."""
    
    def __init__(self, destination: str, message: str = "Failed to export data", details: Optional[dict] = None):
        details = details or {}
        details['destination'] = destination
        full_msg = f"Export to {destination} failed: {message}"
        super().__init__(full_msg, error_code="EXPORT_ERROR", details=details)


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================

class ConfigurationException(TaxReturnException):
    """Base exception for configuration errors."""
    pass


class ConfigurationLoadException(ConfigurationException):
    """Raised when configuration loading fails."""
    
    def __init__(self, config_file: str, message: str = "Failed to load configuration", details: Optional[dict] = None):
        details = details or {}
        details['config_file'] = config_file
        full_msg = f"Failed to load configuration from {config_file}: {message}"
        super().__init__(full_msg, error_code="CONFIG_LOAD_ERROR", details=details)


class InvalidConfigurationException(ConfigurationException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration is invalid", details: Optional[dict] = None):
        super().__init__(message, error_code="CONFIG_INVALID", details=details)


class MissingConfigurationException(ConfigurationException):
    """Raised when required configuration is missing."""
    
    def __init__(self, config_key: str, details: Optional[dict] = None):
        details = details or {}
        details['config_key'] = config_key
        msg = f"Required configuration is missing: {config_key}"
        super().__init__(msg, error_code="CONFIG_MISSING", details=details)


# ============================================================================
# SERVICE EXCEPTIONS
# ============================================================================

class ServiceException(TaxReturnException):
    """Base exception for service-related errors."""
    pass


class ServiceUnavailableException(ServiceException):
    """Raised when a required service is unavailable."""
    
    def __init__(self, service_name: str, details: Optional[dict] = None):
        details = details or {}
        details['service_name'] = service_name
        msg = f"Service is unavailable: {service_name}"
        super().__init__(msg, error_code="SERVICE_UNAVAILABLE", details=details)


class ServiceInitializationException(ServiceException):
    """Raised when service initialization fails."""
    
    def __init__(self, service_name: str, message: str = "Service initialization failed", details: Optional[dict] = None):
        details = details or {}
        details['service_name'] = service_name
        full_msg = f"Failed to initialize service {service_name}: {message}"
        super().__init__(full_msg, error_code="SERVICE_INIT_ERROR", details=details)


class ServiceExecutionException(ServiceException):
    """Raised when service execution fails."""
    
    def __init__(self, service_name: str, operation: str, message: str = "Operation failed", details: Optional[dict] = None):
        details = details or {}
        details['service_name'] = service_name
        details['operation'] = operation
        full_msg = f"Service {service_name} failed during {operation}: {message}"
        super().__init__(full_msg, error_code="SERVICE_EXECUTION_ERROR", details=details)
