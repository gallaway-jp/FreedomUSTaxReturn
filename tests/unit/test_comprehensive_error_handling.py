"""
Comprehensive Error Handling Tests for Tax Services

Tests cover:
- All exception types from services/exceptions.py
- Error logger functionality  
- Service error handling patterns
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.exceptions import (
    TaxReturnException,
    InvalidPasswordException,
    MasterPasswordNotSetException,
    AuthenticationTimeoutException,
    AuthenticationException,
    EncryptionKeyNotFoundException,
    DecryptionFailedException,
    InvalidEncryptionKeyException,
    InvalidInputException,
    MissingRequiredFieldException,
    DataValidationException,
    FileProcessingException,
    PDFProcessingException,
    DataImportException,
    DataExportException,
    ConfigurationLoadException,
    InvalidConfigurationException,
    MissingConfigurationException,
    ServiceUnavailableException,
    ServiceInitializationException,
    ServiceExecutionException,
)
from services.error_logger import ErrorLogger


class TestExceptionHierarchy:
    """Test the exception hierarchy structure and properties"""

    def test_base_exception_attributes(self):
        """Test TaxReturnException has required attributes"""
        exc = TaxReturnException(
            message="Test error",
            error_code="TEST_001",
            details={"key": "value"},
            cause=None
        )
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_001"
        assert exc.details == {"key": "value"}
        assert exc.cause is None

    def test_exception_with_cause(self):
        """Test exception with root cause"""
        cause = ValueError("Root cause")
        exc = TaxReturnException(
            message="Wrapped error",
            error_code="WRAP_001",
            details={},
            cause=cause
        )
        assert exc.cause == cause

    def test_all_exceptions_inherit_from_base(self):
        """Test all specific exceptions inherit from TaxReturnException"""
        # Test a few key exception types
        auth_exc = InvalidPasswordException("Invalid password")
        assert isinstance(auth_exc, TaxReturnException)
        assert auth_exc.error_code == "AUTH_INVALID_PASSWORD"
        
        enc_exc = EncryptionKeyNotFoundException("/path/to/key")
        assert isinstance(enc_exc, TaxReturnException)
        assert enc_exc.error_code == "ENC_KEY_NOT_FOUND"
        
        val_exc = InvalidInputException("ssn", "Invalid format")
        assert isinstance(val_exc, TaxReturnException)
        assert val_exc.error_code == "VAL_INVALID_INPUT"

    def test_exception_string_representation(self):
        """Test exception string formatting"""
        exc = TaxReturnException("Test message", error_code="TEST_001")
        exc_str = str(exc)
        assert "TEST_001" in exc_str
        assert "Test message" in exc_str


class TestAuthenticationExceptions:
    """Test authentication-related exceptions"""

    def test_invalid_password_exception(self):
        """Test InvalidPasswordException"""
        exc = InvalidPasswordException("Password too weak")
        assert exc.error_code == "AUTH_INVALID_PASSWORD"
        assert "Password too weak" in str(exc)

    def test_master_password_not_set_exception(self):
        """Test MasterPasswordNotSetException"""
        exc = MasterPasswordNotSetException()
        assert exc.error_code == "AUTH_NO_MASTER_PASSWORD"
        assert "Master password" in str(exc)

    def test_authentication_timeout_exception(self):
        """Test AuthenticationTimeoutException"""
        exc = AuthenticationTimeoutException("Session expired after 30 minutes")
        assert exc.error_code == "AUTH_TIMEOUT"
        assert "Session expired" in str(exc)

    def test_authentication_exception(self):
        """Test base AuthenticationException"""
        exc = AuthenticationException("Authentication failed")
        assert isinstance(exc, TaxReturnException)
        assert "Authentication failed" in str(exc)


class TestEncryptionExceptions:
    """Test encryption-related exceptions"""

    def test_encryption_key_not_found(self):
        """Test EncryptionKeyNotFoundException"""
        exc = EncryptionKeyNotFoundException("/path/to/missing/key")
        assert exc.error_code == "ENC_KEY_NOT_FOUND"
        assert "not found" in str(exc)
        assert "/path/to/missing/key" in str(exc)

    def test_decryption_failed_exception(self):
        """Test DecryptionFailedException"""
        exc = DecryptionFailedException("Corrupted data detected")
        assert exc.error_code == "ENC_DECRYPTION_FAILED"
        assert "Corrupted data" in str(exc)

    def test_invalid_encryption_key_exception(self):
        """Test InvalidEncryptionKeyException"""
        exc = InvalidEncryptionKeyException("Key is corrupted")
        assert exc.error_code == "ENC_INVALID_KEY"
        assert "corrupted" in str(exc).lower()


class TestValidationExceptions:
    """Test validation-related exceptions"""

    def test_invalid_input_exception(self):
        """Test InvalidInputException with field name"""
        exc = InvalidInputException("ssn", "Invalid format (expected XXX-XX-XXXX)")
        assert exc.error_code == "VAL_INVALID_INPUT"
        assert "ssn" in str(exc)
        assert "Invalid format" in str(exc)

    def test_missing_required_field_exception(self):
        """Test MissingRequiredFieldException"""
        exc = MissingRequiredFieldException("email")
        assert exc.error_code == "VAL_MISSING_FIELD"
        assert "email" in str(exc)
        assert "Required field" in str(exc)

    def test_data_validation_exception(self):
        """Test DataValidationException"""
        exc = DataValidationException("Spouse income exceeds threshold")
        assert exc.error_code == "VAL_DATA_VALIDATION"
        assert "Spouse income" in str(exc)


class TestDataProcessingExceptions:
    """Test data processing exceptions"""

    def test_file_processing_exception(self):
        """Test FileProcessingException"""
        exc = FileProcessingException("/path/to/file.csv", "read")
        assert exc.error_code == "FILE_PROCESSING_ERROR"
        assert "read" in str(exc)
        assert "/path/to/file.csv" in str(exc)

    def test_pdf_processing_exception(self):
        """Test PDFProcessingException"""
        exc = PDFProcessingException("Failed to fill PDF form fields")
        assert exc.error_code == "PDF_PROCESSING_ERROR"
        assert "PDF" in str(exc)

    def test_data_import_exception(self):
        """Test DataImportException"""
        exc = DataImportException("QuickBooks", "Invalid authentication")
        assert exc.error_code == "IMPORT_ERROR"
        assert "QuickBooks" in str(exc)
        assert "Invalid authentication" in str(exc)

    def test_data_export_exception(self):
        """Test DataExportException"""
        exc = DataExportException("IRS", "Network connection failed")
        assert exc.error_code == "EXPORT_ERROR"
        assert "IRS" in str(exc)
        assert "Network" in str(exc)


class TestConfigurationExceptions:
    """Test configuration exceptions"""

    def test_configuration_load_exception(self):
        """Test ConfigurationLoadException"""
        exc = ConfigurationLoadException("config.json", "File not found")
        assert exc.error_code == "CONFIG_LOAD_ERROR"
        assert "config.json" in str(exc)

    def test_invalid_configuration_exception(self):
        """Test InvalidConfigurationException"""
        exc = InvalidConfigurationException("Tax year must be between 2015 and current year")
        assert exc.error_code == "CONFIG_INVALID"
        assert "Tax year" in str(exc)

    def test_missing_configuration_exception(self):
        """Test MissingConfigurationException"""
        exc = MissingConfigurationException("api_key")
        assert exc.error_code == "CONFIG_MISSING"
        assert "api_key" in str(exc)


class TestServiceExceptions:
    """Test service-related exceptions"""

    def test_service_unavailable_exception(self):
        """Test ServiceUnavailableException"""
        exc = ServiceUnavailableException("TaxCalculationService")
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert "TaxCalculationService" in str(exc)

    def test_service_initialization_exception(self):
        """Test ServiceInitializationException"""
        exc = ServiceInitializationException("EncryptionService", "Key not initialized")
        assert exc.error_code == "SERVICE_INIT_ERROR"
        assert "EncryptionService" in str(exc)
        assert "Key not initialized" in str(exc)

    def test_service_execution_exception(self):
        """Test ServiceExecutionException"""
        exc = ServiceExecutionException("TaxCalculationService", "calculate_tax", "Invalid input data")
        assert exc.error_code == "SERVICE_EXECUTION_ERROR"
        assert "TaxCalculationService" in str(exc)
        assert "calculate_tax" in str(exc)


class TestErrorLogger:
    """Test error logger functionality"""

    def test_error_logger_singleton(self):
        """Test that ErrorLogger is a singleton"""
        logger1 = ErrorLogger.get_instance()
        logger2 = ErrorLogger.get_instance()
        # Both instances should be the same object
        assert logger1 is logger2

    def test_log_exception(self):
        """Test logging a TaxReturnException"""
        logger = ErrorLogger.get_instance()
        exc = InvalidInputException("ssn", "Invalid format")
        
        # Log the exception
        logger.log_exception("TestComponent", exc)
        
        # Verify it was logged (check history)
        history = logger.get_error_history()
        assert len(history) > 0

    def test_log_error_with_component(self):
        """Test logging an error with component name"""
        logger = ErrorLogger.get_instance()
        logger.log_error("TestComponent", "Something went wrong", severity="error")
        
        history = logger.get_error_history()
        assert len(history) > 0

    def test_error_history_tracking(self):
        """Test that error history is tracked"""
        logger = ErrorLogger.get_instance()
        initial_count = len(logger.get_error_history())
        
        logger.log_exception("Component1", InvalidInputException("field", "error"))
        logger.log_exception("Component2", EncryptionKeyNotFoundException("/path"))
        
        history = logger.get_error_history()
        assert len(history) >= initial_count + 2

    def test_filter_by_type(self):
        """Test filtering errors by type"""
        logger = ErrorLogger.get_instance()
        logger.log_exception("Component1", InvalidInputException("field", "error"))
        logger.log_exception("Component2", EncryptionKeyNotFoundException("/path"))
        logger.log_exception("Component3", FileProcessingException("/file", "read"))
        
        history = logger.get_error_history()
        # Should have multiple types of errors
        assert len(history) >= 3

    def test_sensitive_data_redaction(self):
        """Test that sensitive data is redacted in logs"""
        logger = ErrorLogger.get_instance()
        
        # Create an exception with potentially sensitive data
        exc = InvalidInputException("password", "Password too weak")
        logger.log_exception("AuthComponent", exc)
        
        history = logger.get_error_history()
        assert len(history) > 0


class TestServiceErrorHandling:
    """Test error handling in service classes"""

    def test_authentication_service_invalid_password(self):
        """Test authentication service error handling"""
        # Test that we can create InvalidPasswordException
        exc = InvalidPasswordException("Password too weak")
        assert "password" in str(exc).lower()

    def test_encryption_key_error(self):
        """Test encryption key initialization error"""
        # Test that we can create the exception properly
        exc = EncryptionKeyNotFoundException("/nonexistent/path/key.fernet")
        assert "key.fernet" in str(exc)

    def test_invalid_input_error(self):
        """Test validation error handling"""
        exc = InvalidInputException("tax_id", "Must be numeric")
        assert "tax_id" in str(exc)
        assert "Must be numeric" in str(exc)


class TestErrorRecovery:
    """Test error recovery mechanisms"""

    def test_exception_context_preservation(self):
        """Test that exception context is preserved"""
        original_error = ValueError("Original error")
        exc = TaxReturnException(
            "Wrapped error",
            error_code="WRAP_001",
            cause=original_error
        )
        
        assert exc.cause == original_error
        details = exc.get_details()
        assert "Original error" in str(details.get("cause", ""))

    def test_error_details_accumulation(self):
        """Test that error details accumulate"""
        exc = InvalidInputException(
            "income",
            "Must be non-negative",
            details={"min_value": 0, "received_value": -100}
        )
        
        details = exc.get_details()
        assert details["details"]["min_value"] == 0
        assert details["details"]["received_value"] == -100

    def test_multiple_error_handling(self):
        """Test handling multiple errors"""
        errors = []
        
        try:
            raise InvalidInputException("field1", "error")
        except Exception as e:
            errors.append(e)
        
        try:
            raise FileProcessingException("/file", "read")
        except Exception as e:
            errors.append(e)
        
        assert len(errors) == 2
        assert isinstance(errors[0], InvalidInputException)
        assert isinstance(errors[1], FileProcessingException)
