"""
Custom exceptions for PDF form operations
Following Clean Code principles for error handling
"""


class PDFFormError(Exception):
    """Base exception for all PDF form operations"""
    pass


class FormNotFoundError(PDFFormError):
    """Raised when a form file cannot be found"""
    pass


class FormFieldError(PDFFormError):
    """Raised when there's an issue with form fields"""
    pass


class PDFEncryptionError(PDFFormError):
    """Raised when PDF encryption fails"""
    pass


class PDFWriteError(PDFFormError):
    """Raised when PDF writing fails"""
    pass
