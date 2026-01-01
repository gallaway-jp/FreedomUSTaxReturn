"""
Centralized Error Logger for Freedom US Tax Return Application

Provides comprehensive error logging, tracking, and reporting capabilities
for all services and components.
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
from threading import Lock

from services.exceptions import TaxReturnException


class ErrorLogger:
    """
    Centralized error logging system for the application.
    
    Features:
    - Logs errors with full context and stack traces
    - Maintains error history
    - Categorizes errors by type and severity
    - Thread-safe logging
    - File and console output
    """
    
    # Severity levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    # Singleton instance
    _instance = None
    _lock = Lock()
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the error logger.
        
        Args:
            log_dir: Directory for log files (default: logs/)
        """
        self.log_dir = Path(log_dir or "logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure Python's logging module
        self.logger = logging.getLogger("TaxReturn")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler
        log_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Error history
        self.error_history: list = []
        self.max_history = 100
    
    @classmethod
    def get_instance(cls, log_dir: Optional[Path] = None) -> 'ErrorLogger':
        """
        Get or create the singleton ErrorLogger instance.
        
        Args:
            log_dir: Directory for log files (only used on first creation)
        
        Returns:
            ErrorLogger instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(log_dir)
        return cls._instance
    
    def log_exception(
        self,
        exception: Exception,
        context: Optional[str] = None,
        severity: str = ERROR,
        extra_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log an exception with full context.
        
        Args:
            exception: The exception to log
            context: Optional context about what was happening
            severity: Log severity level
            extra_details: Additional context information
        
        Returns:
            Dictionary with logged error details
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "exception_type": exception.__class__.__name__,
            "message": str(exception),
            "context": context,
            "stacktrace": traceback.format_exc(),
            "extra_details": extra_details or {}
        }
        
        # Add TaxReturnException-specific details
        if isinstance(exception, TaxReturnException):
            error_entry["error_code"] = exception.error_code
            error_entry["details"] = exception.details
            error_entry["cause"] = str(exception.cause) if exception.cause else None
        
        # Log to file and console
        log_method = getattr(self.logger, severity.lower(), self.logger.error)
        
        log_message = f"{context}: {exception}" if context else str(exception)
        log_method(log_message, exc_info=True)
        
        # Add to history
        self._add_to_history(error_entry)
        
        return error_entry
    
    def log_error(
        self,
        message: str,
        component: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = ERROR
    ) -> Dict[str, Any]:
        """
        Log a general error message.
        
        Args:
            message: Error message
            component: Component or service name
            details: Additional error details
            severity: Log severity level
        
        Returns:
            Dictionary with logged error details
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "component": component,
            "message": message,
            "details": details or {}
        }
        
        log_method = getattr(self.logger, severity.lower(), self.logger.error)
        log_method(f"[{component}] {message}")
        
        self._add_to_history(error_entry)
        
        return error_entry
    
    def log_validation_error(
        self,
        field_name: str,
        validation_error: str,
        value: Any = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a validation error.
        
        Args:
            field_name: Name of the field that failed validation
            validation_error: Description of validation failure
            value: The invalid value (will be sanitized)
            context: Additional context
        
        Returns:
            Dictionary with logged error details
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "severity": self.WARNING,
            "type": "VALIDATION_ERROR",
            "field": field_name,
            "error": validation_error,
            "value": self._sanitize_value(value),
            "context": context
        }
        
        self.logger.warning(
            f"Validation error in '{field_name}': {validation_error}",
            extra={"details": error_entry}
        )
        
        self._add_to_history(error_entry)
        
        return error_entry
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = INFO
    ) -> Dict[str, Any]:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Log severity level
        
        Returns:
            Dictionary with logged event details
        """
        event_entry = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "event_type": f"SECURITY_{event_type}",
            "details": self._sanitize_dict(details)
        }
        
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(f"Security Event - {event_type}", extra={"details": event_entry})
        
        self._add_to_history(event_entry)
        
        return event_entry
    
    def get_error_history(self, limit: Optional[int] = None) -> list:
        """
        Get error history.
        
        Args:
            limit: Maximum number of errors to return (default: all)
        
        Returns:
            List of logged errors
        """
        if limit:
            return self.error_history[-limit:]
        return self.error_history.copy()
    
    def get_errors_by_type(self, exception_type: str) -> list:
        """
        Get errors of a specific type.
        
        Args:
            exception_type: Type of exception to filter
        
        Returns:
            List of matching errors
        """
        return [
            error for error in self.error_history
            if error.get("exception_type") == exception_type
        ]
    
    def get_errors_by_severity(self, severity: str) -> list:
        """
        Get errors of a specific severity.
        
        Args:
            severity: Severity level to filter
        
        Returns:
            List of matching errors
        """
        return [
            error for error in self.error_history
            if error.get("severity") == severity
        ]
    
    def clear_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
    
    def _add_to_history(self, error_entry: Dict[str, Any]) -> None:
        """
        Add entry to error history, maintaining max size.
        
        Args:
            error_entry: Error entry to add
        """
        self.error_history.append(error_entry)
        
        # Keep only recent errors
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    @staticmethod
    def _sanitize_value(value: Any) -> Any:
        """
        Sanitize a value to remove sensitive information.
        
        Args:
            value: Value to sanitize
        
        Returns:
            Sanitized value
        """
        if value is None:
            return None
        
        value_str = str(value).lower()
        
        # Check if value contains sensitive keywords
        sensitive_keywords = ['password', 'token', 'key', 'secret', 'credential', 'pin', 'ssn']
        if any(keyword in value_str for keyword in sensitive_keywords):
            return "[REDACTED]"
        
        return value
    
    @staticmethod
    def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize dictionary to remove sensitive information.
        
        Args:
            data: Dictionary to sanitize
        
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Redact sensitive keys
            if any(sensitive in key_lower for sensitive in ['password', 'token', 'key', 'secret', 'credential']):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = ErrorLogger._sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [ErrorLogger._sanitize_value(v) for v in value]
            else:
                sanitized[key] = ErrorLogger._sanitize_value(value)
        
        return sanitized


# Convenience function for easy access
def get_error_logger(log_dir: Optional[Path] = None) -> ErrorLogger:
    """
    Get the global ErrorLogger instance.
    
    Args:
        log_dir: Directory for log files (only used on first call)
    
    Returns:
        ErrorLogger instance
    """
    return ErrorLogger.get_instance(log_dir)
