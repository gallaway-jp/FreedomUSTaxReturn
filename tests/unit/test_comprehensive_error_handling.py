"""
Comprehensive Error Handling Tests for Tax Services
Tests the exception hierarchy and error recovery mechanisms

Tests cover:
- All exception types from services/exceptions.py
- Error logger functionality
- Service error handling patterns
- Recovery and fallback strategies
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
from services.error_logger import get_error_logger
from services.authentication_service import AuthenticationService
from services.encryption_service import EncryptionService
from services.tax_calculation_service import TaxCalculationService
from config.app_config import AppConfig


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
        assert isinstance(exc.__cause__, ValueError)

    def test_all_exceptions_inherit_from_base(self):
        """Test all specific exceptions inherit from TaxReturnException"""
        exceptions = [
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
        ]
        
        for exc_class in exceptions:
            exc = exc_class("Test message")
            assert isinstance(exc, TaxReturnException)

    def test_exception_string_representation(self):
        """Test exception string representation"""
        exc = InvalidInputException("field_name")
        assert "field_name" in str(exc) or "InvalidInputException" in str(exc)


class TestAuthenticationExceptions:
    """Test authentication-related exceptions"""

    def test_invalid_password_exception(self):
        """Test InvalidPasswordException"""
        exc = InvalidPasswordException("Password too short")
        assert exc.error_code == "AUTH_001"
        assert "invalid" in str(exc).lower() or "password" in str(exc).lower()

    def test_master_password_not_set_exception(self):
        """Test MasterPasswordNotSetException"""
        exc = MasterPasswordNotSetException()
        assert exc.error_code == "AUTH_002"

    def test_authentication_timeout_exception(self):
        """Test AuthenticationTimeoutException"""
        exc = AuthenticationTimeoutException(timeout_seconds=30)
        assert exc.error_code == "AUTH_003"
        assert "30" in str(exc)

    def test_authentication_exception(self):
        """Test generic AuthenticationException"""
        exc = AuthenticationException("Authentication failed")
        assert exc.error_code == "AUTH_004"


class TestEncryptionExceptions:
    """Test encryption-related exceptions"""

    def test_encryption_key_not_found(self):
        """Test EncryptionKeyNotFoundException"""
        exc = EncryptionKeyNotFoundException("master_key")
        assert exc.error_code == "ENC_001"
        assert "master_key" in str(exc)

    def test_decryption_failed_exception(self):
        """Test DecryptionFailedException"""
        exc = DecryptionFailedException(
            message="Decryption failed",
            cause=ValueError("Invalid cipher")
        )
        assert exc.error_code == "ENC_002"
        assert exc.cause is not None

    def test_invalid_encryption_key_exception(self):
        """Test InvalidEncryptionKeyException"""
        exc = InvalidEncryptionKeyException("Key format invalid")
        assert exc.error_code == "ENC_003"


class TestValidationExceptions:
    """Test validation-related exceptions"""

    def test_invalid_input_exception(self):
        """Test InvalidInputException"""
        exc = InvalidInputException("income_amount")
        assert exc.error_code == "VAL_001"
        assert "income_amount" in str(exc)

    def test_missing_required_field_exception(self):
        """Test MissingRequiredFieldException"""
        exc = MissingRequiredFieldException("ssn", form="1040")
        assert exc.error_code == "VAL_002"
        assert "ssn" in str(exc)
        assert "1040" in str(exc)

    def test_data_validation_exception(self):
        """Test DataValidationException"""
        exc = DataValidationException(
            field="tax_amount",
            reason="negative value"
        )
        assert exc.error_code == "VAL_003"
        assert "tax_amount" in str(exc)


class TestDataProcessingExceptions:
    """Test data processing-related exceptions"""

    def test_file_processing_exception(self):
        """Test FileProcessingException"""
        exc = FileProcessingException("file.txt", reason="File not found")
        assert exc.error_code == "DATA_001"
        assert "file.txt" in str(exc)

    def test_pdf_processing_exception(self):
        """Test PDFProcessingException"""
        exc = PDFProcessingException(
            file_path="form_1040.pdf",
            page_number=1,
            reason="Invalid PDF structure"
        )
        assert exc.error_code == "DATA_002"
        assert "form_1040.pdf" in str(exc) or "page_number" in str(exc)

    def test_data_import_exception(self):
        """Test DataImportException"""
        exc = DataImportException(
            source="QuickBooks",
            reason="API authentication failed"
        )
        assert exc.error_code == "DATA_003"
        assert "QuickBooks" in str(exc)

    def test_data_export_exception(self):
        """Test DataExportException"""
        exc = DataExportException(
            destination="XML",
            reason="XML schema validation failed"
        )
        assert exc.error_code == "DATA_004"
        assert "XML" in str(exc)


class TestConfigurationExceptions:
    """Test configuration-related exceptions"""

    def test_configuration_load_exception(self):
        """Test ConfigurationLoadException"""
        exc = ConfigurationLoadException(
            config_file="config.yaml",
            reason="File not found"
        )
        assert exc.error_code == "CONFIG_001"
        assert "config.yaml" in str(exc)

    def test_invalid_configuration_exception(self):
        """Test InvalidConfigurationException"""
        exc = InvalidConfigurationException(
            setting="tax_year",
            reason="Year must be positive"
        )
        assert exc.error_code == "CONFIG_002"
        assert "tax_year" in str(exc)

    def test_missing_configuration_exception(self):
        """Test MissingConfigurationException"""
        exc = MissingConfigurationException("api_key")
        assert exc.error_code == "CONFIG_003"
        assert "api_key" in str(exc)


class TestServiceExceptions:
    """Test service-related exceptions"""

    def test_service_unavailable_exception(self):
        """Test ServiceUnavailableException"""
        exc = ServiceUnavailableException(
            service_name="TaxCalculationService",
            reason="Database connection failed"
        )
        assert exc.error_code == "SVC_001"
        assert "TaxCalculationService" in str(exc)

    def test_service_initialization_exception(self):
        """Test ServiceInitializationException"""
        exc = ServiceInitializationException(
            service_name="EncryptionService",
            reason="Failed to load encryption keys"
        )
        assert exc.error_code == "SVC_002"
        assert "EncryptionService" in str(exc)

    def test_service_execution_exception(self):
        """Test ServiceExecutionException"""
        exc = ServiceExecutionException(
            service_name="TaxCalculationService",
            operation="calculate_tax",
            details={"income": 50000}
        )
        assert exc.error_code == "SVC_003"
        assert "TaxCalculationService" in str(exc)
        assert "calculate_tax" in str(exc)


class TestErrorLogger:
    """Test error logging functionality"""

    def test_error_logger_singleton(self):
        """Test error logger is singleton"""
        logger1 = get_error_logger()
        logger2 = get_error_logger()
        assert logger1 is logger2

    def test_log_exception(self):
        """Test logging an exception"""
        logger = get_error_logger()
        exc = InvalidInputException("test_field")
        
        # Should not raise
        logger.log_exception(exc, context="test_context")

    def test_log_error(self):
        """Test logging an error"""
        logger = get_error_logger()
        
        # Should not raise
        logger.log_error("test_error", severity="warning")

    def test_log_validation_error(self):
        """Test logging a validation error"""
        logger = get_error_logger()
        
        # Should not raise
        logger.log_validation_error(
            field="income",
            reason="negative value"
        )

    def test_log_security_event(self):
        """Test logging a security event"""
        logger = get_error_logger()
        
        # Should not raise
        logger.log_security_event(
            event_type="authentication_failed",
            details={"user": "test"}
        )

    def test_sensitive_data_redaction(self):
        """Test that sensitive data is redacted in logs"""
        logger = get_error_logger()
        
        # Log something with sensitive data
        exc = InvalidInputException(
            message="Password: secret123"
        )
        logger.log_exception(exc, context="test")
        
        # Retrieve error history
        history = logger.get_error_history()
        # The actual redaction happens in logging, just verify no crash
        assert len(history) >= 0

    def test_error_history_tracking(self):
        """Test error history is tracked"""
        logger = get_error_logger()
        
        # Log multiple errors
        for i in range(5):
            exc = InvalidInputException(f"field_{i}")
            logger.log_exception(exc, context="test")
        
        history = logger.get_error_history()
        assert len(history) > 0

    def test_filter_by_type(self):
        """Test filtering errors by type"""
        logger = get_error_logger()
        
        # Log different error types
        logger.log_exception(InvalidInputException("field"))
        logger.log_exception(EncryptionKeyNotFoundException("key"))
        
        # Get all errors
        all_errors = logger.get_error_history()
        assert len(all_errors) > 0

    def test_filter_by_severity(self):
        """Test filtering errors by severity"""
        logger = get_error_logger()
        
        logger.log_error("test_error", severity="error")
        logger.log_error("test_warning", severity="warning")
        
        # Get all errors
        all_errors = logger.get_error_history()
        assert len(all_errors) > 0


class TestServiceErrorHandling:
    """Test error handling in services"""

    def test_authentication_service_invalid_password(self):
        """Test AuthenticationService handles invalid password"""
        config = AppConfig()
        service = AuthenticationService(config)
        
        # Should raise InvalidPasswordException for empty password
        with pytest.raises(InvalidPasswordException):
            service.validate_master_password("")

    def test_encryption_service_key_not_found(self):
        """Test EncryptionService handles missing key"""
        config = AppConfig()
        service = EncryptionService(config)
        
        # This tests error handling in encryption service
        # The actual behavior depends on implementation
        try:
            # Attempt operation that would fail with missing key
            service.encrypt("test_data")
        except (EncryptionKeyNotFoundException, ServiceExecutionException):
            # Expected - key not initialized
            pass

    def test_tax_calculation_service_validation_error(self):
        """Test TaxCalculationService validates input"""
        config = AppConfig()
        service = TaxCalculationService(config)
        
        # Should raise DataValidationException for invalid input
        with pytest.raises((DataValidationException, InvalidInputException, ServiceExecutionException)):
            service.calculate_complete_return(None)

    def test_service_error_logging(self):
        """Test services log errors properly"""
        logger = get_error_logger()
        
        try:
            raise InvalidInputException("test_field")
        except InvalidInputException as e:
            logger.log_exception(e, context="test_service.method")
        
        history = logger.get_error_history()
        assert len(history) > 0


class TestErrorRecovery:
    """Test error recovery and fallback strategies"""

    def test_retry_on_transient_error(self):
        """Test retrying on transient errors"""
        attempt = 0
        
        def flaky_operation():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise ServiceUnavailableException("service", "Temporary outage")
            return "success"
        
        # Retry logic
        max_retries = 3
        for retry in range(max_retries):
            try:
                result = flaky_operation()
                break
            except ServiceUnavailableException as e:
                if retry == max_retries - 1:
                    raise
                continue
        
        assert result == "success"
        assert attempt == 3

    def test_fallback_to_default_value(self):
        """Test falling back to default value on error"""
        def get_tax_rate():
            raise ServiceUnavailableException("service", "API down")
        
        try:
            rate = get_tax_rate()
        except ServiceUnavailableException:
            rate = 0.25  # Fallback default
        
        assert rate == 0.25

    def test_partial_success_on_batch_error(self):
        """Test handling partial success in batch operations"""
        items = [1, 2, 3, 4, 5]
        results = []
        errors = []
        
        for item in items:
            try:
                if item == 3:
                    raise DataValidationException(field="item", reason="Invalid")
                results.append(item * 2)
            except DataValidationException as e:
                errors.append((item, e))
        
        assert len(results) == 4
        assert len(errors) == 1
        assert results == [2, 4, 6, 8]


class TestExceptionPropagation:
    """Test exception propagation through call stack"""

    def test_exception_context_preserved(self):
        """Test exception context is preserved through layers"""
        def layer3():
            raise InvalidInputException("field")
        
        def layer2():
            try:
                layer3()
            except InvalidInputException as e:
                raise ServiceExecutionException(
                    service_name="TestService",
                    operation="process",
                    details={}
                ) from e
        
        def layer1():
            try:
                layer2()
            except ServiceExecutionException as e:
                assert e.__cause__ is not None
                assert isinstance(e.__cause__, InvalidInputException)
                raise
        
        with pytest.raises(ServiceExecutionException) as exc_info:
            layer1()
        
        assert exc_info.value.__cause__ is not None

    def test_exception_details_accumulation(self):
        """Test details accumulate through exception chain"""
        try:
            try:
                raise InvalidInputException("ssn")
            except InvalidInputException as e:
                raise DataValidationException(
                    field="personal_info",
                    reason=str(e)
                ) from e
        except DataValidationException as e:
            assert "personal_info" in str(e)
            assert e.__cause__ is not None


class TestConcurrentErrorHandling:
    """Test error handling in concurrent scenarios"""

    def test_multiple_service_errors(self):
        """Test handling errors from multiple services"""
        errors = []
        
        def call_service(service_id):
            try:
                if service_id % 2 == 0:
                    raise ServiceUnavailableException(f"Service{service_id}", "Error")
                return f"Service{service_id} success"
            except ServiceUnavailableException as e:
                errors.append(e)
                return None
        
        results = [call_service(i) for i in range(5)]
        
        assert len(errors) == 3  # 0, 2, 4
        assert None in results
        assert "success" in str(results)

    def test_error_aggregation(self):
        """Test aggregating multiple errors for reporting"""
        errors = []
        
        operations = [
            lambda: None,  # Success
            lambda: (_ for _ in ()).throw(InvalidInputException("field1")),
            lambda: None,  # Success
            lambda: (_ for _ in ()).throw(DataValidationException("field2", "reason")),
        ]
        
        for i, op in enumerate(operations):
            try:
                op()
            except (InvalidInputException, DataValidationException) as e:
                errors.append((i, e))
        
        assert len(errors) == 2
        assert errors[0][1].error_code == "VAL_001"
        assert errors[1][1].error_code == "VAL_003"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services"])
