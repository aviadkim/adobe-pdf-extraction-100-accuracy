#!/usr/bin/env python3
"""
Custom Exception Classes for Adobe PDF Extraction System
Provides specific exception types for better error handling and debugging
"""

from typing import Optional, Dict, Any, List


class PDFExtractionBaseException(Exception):
    """Base exception class for PDF extraction system"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            context: Optional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            'exception_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context
        }


class CredentialsError(PDFExtractionBaseException):
    """Raised when Adobe API credentials are invalid or missing"""
    pass


class CredentialsNotFoundError(CredentialsError):
    """Raised when credentials file is not found"""
    
    def __init__(self, credentials_path: str):
        message = f"Adobe API credentials file not found: {credentials_path}"
        super().__init__(
            message=message,
            error_code="CREDS_NOT_FOUND",
            context={"credentials_path": credentials_path}
        )


class InvalidCredentialsFormatError(CredentialsError):
    """Raised when credentials file has invalid format"""
    
    def __init__(self, credentials_path: str, missing_fields: Optional[List[str]] = None):
        message = f"Invalid credentials format in: {credentials_path}"
        if missing_fields:
            message += f". Missing fields: {', '.join(missing_fields)}"
        
        super().__init__(
            message=message,
            error_code="CREDS_INVALID_FORMAT",
            context={
                "credentials_path": credentials_path,
                "missing_fields": missing_fields or []
            }
        )


class APIError(PDFExtractionBaseException):
    """Base class for Adobe API related errors"""
    pass


class APIConnectionError(APIError):
    """Raised when unable to connect to Adobe API"""
    
    def __init__(self, endpoint: Optional[str] = None, original_error: Optional[Exception] = None):
        message = "Failed to connect to Adobe PDF Services API"
        if endpoint:
            message += f" at {endpoint}"
        
        super().__init__(
            message=message,
            error_code="API_CONNECTION_FAILED",
            context={
                "endpoint": endpoint,
                "original_error": str(original_error) if original_error else None
            }
        )


class APIAuthenticationError(APIError):
    """Raised when API authentication fails"""
    
    def __init__(self, client_id_prefix: Optional[str] = None):
        message = "Adobe API authentication failed"
        if client_id_prefix:
            message += f" for client ID: {client_id_prefix}..."
        
        super().__init__(
            message=message,
            error_code="API_AUTH_FAILED",
            context={"client_id_prefix": client_id_prefix}
        )


class APIQuotaExceededError(APIError):
    """Raised when API quota is exceeded"""
    
    def __init__(self, quota_info: Optional[Dict[str, Any]] = None):
        message = "Adobe API quota exceeded"
        super().__init__(
            message=message,
            error_code="API_QUOTA_EXCEEDED",
            context=quota_info or {}
        )


class APITimeoutError(APIError):
    """Raised when API request times out"""
    
    def __init__(self, timeout_duration: Optional[float] = None, operation: Optional[str] = None):
        message = f"Adobe API request timed out"
        if timeout_duration:
            message += f" after {timeout_duration}s"
        if operation:
            message += f" during {operation}"
        
        super().__init__(
            message=message,
            error_code="API_TIMEOUT",
            context={
                "timeout_duration": timeout_duration,
                "operation": operation
            }
        )


class FileError(PDFExtractionBaseException):
    """Base class for file-related errors"""
    pass


class PDFNotFoundError(FileError):
    """Raised when input PDF file is not found"""
    
    def __init__(self, pdf_path: str):
        message = f"PDF file not found: {pdf_path}"
        super().__init__(
            message=message,
            error_code="PDF_NOT_FOUND",
            context={"pdf_path": pdf_path}
        )


class InvalidPDFError(FileError):
    """Raised when PDF file is corrupted or invalid"""
    
    def __init__(self, pdf_path: str, validation_error: Optional[str] = None):
        message = f"Invalid or corrupted PDF file: {pdf_path}"
        if validation_error:
            message += f". Error: {validation_error}"
        
        super().__init__(
            message=message,
            error_code="PDF_INVALID",
            context={
                "pdf_path": pdf_path,
                "validation_error": validation_error
            }
        )


class PDFTooLargeError(FileError):
    """Raised when PDF file exceeds size limits"""
    
    def __init__(self, pdf_path: str, file_size_mb: float, max_size_mb: float):
        message = f"PDF file too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)"
        super().__init__(
            message=message,
            error_code="PDF_TOO_LARGE",
            context={
                "pdf_path": pdf_path,
                "file_size_mb": file_size_mb,
                "max_size_mb": max_size_mb
            }
        )


class OutputDirectoryError(FileError):
    """Raised when output directory cannot be created or accessed"""
    
    def __init__(self, output_dir: str, original_error: Optional[Exception] = None):
        message = f"Cannot access or create output directory: {output_dir}"
        super().__init__(
            message=message,
            error_code="OUTPUT_DIR_ERROR",
            context={
                "output_dir": output_dir,
                "original_error": str(original_error) if original_error else None
            }
        )


class ExtractionError(PDFExtractionBaseException):
    """Base class for extraction-related errors"""
    pass


class TableExtractionError(ExtractionError):
    """Raised when table extraction fails"""
    
    def __init__(self, pdf_path: str, page_number: Optional[int] = None, 
                 extraction_details: Optional[Dict[str, Any]] = None):
        message = f"Table extraction failed for: {pdf_path}"
        if page_number:
            message += f" on page {page_number}"
        
        super().__init__(
            message=message,
            error_code="TABLE_EXTRACTION_FAILED",
            context={
                "pdf_path": pdf_path,
                "page_number": page_number,
                "extraction_details": extraction_details or {}
            }
        )


class TextExtractionError(ExtractionError):
    """Raised when text extraction fails"""
    
    def __init__(self, pdf_path: str, page_number: Optional[int] = None):
        message = f"Text extraction failed for: {pdf_path}"
        if page_number:
            message += f" on page {page_number}"
        
        super().__init__(
            message=message,
            error_code="TEXT_EXTRACTION_FAILED",
            context={
                "pdf_path": pdf_path,
                "page_number": page_number
            }
        )


class NoTablesFoundError(ExtractionError):
    """Raised when no tables are found in the PDF"""
    
    def __init__(self, pdf_path: str):
        message = f"No tables found in PDF: {pdf_path}"
        super().__init__(
            message=message,
            error_code="NO_TABLES_FOUND",
            context={"pdf_path": pdf_path}
        )


class ProcessingError(PDFExtractionBaseException):
    """Base class for processing-related errors"""
    pass


class SpatialAnalysisError(ProcessingError):
    """Raised when spatial analysis fails"""
    
    def __init__(self, page_number: int, analysis_type: str, 
                 original_error: Optional[Exception] = None):
        message = f"Spatial analysis failed on page {page_number} during {analysis_type}"
        super().__init__(
            message=message,
            error_code="SPATIAL_ANALYSIS_FAILED",
            context={
                "page_number": page_number,
                "analysis_type": analysis_type,
                "original_error": str(original_error) if original_error else None
            }
        )


class ImageAnalysisError(ProcessingError):
    """Raised when image analysis fails"""
    
    def __init__(self, image_path: str, analysis_type: str, 
                 original_error: Optional[Exception] = None):
        message = f"Image analysis failed for {image_path} during {analysis_type}"
        super().__init__(
            message=message,
            error_code="IMAGE_ANALYSIS_FAILED",
            context={
                "image_path": image_path,
                "analysis_type": analysis_type,
                "original_error": str(original_error) if original_error else None
            }
        )


class OCRError(ProcessingError):
    """Raised when OCR processing fails"""
    
    def __init__(self, image_path: str, ocr_service: str = "Azure", 
                 original_error: Optional[Exception] = None):
        message = f"OCR processing failed for {image_path} using {ocr_service}"
        super().__init__(
            message=message,
            error_code="OCR_FAILED",
            context={
                "image_path": image_path,
                "ocr_service": ocr_service,
                "original_error": str(original_error) if original_error else None
            }
        )


class ValidationError(PDFExtractionBaseException):
    """Base class for validation-related errors"""
    pass


class ConfigurationValidationError(ValidationError):
    """Raised when configuration validation fails"""
    
    def __init__(self, config_errors: List[str], config_file: Optional[str] = None):
        message = f"Configuration validation failed: {'; '.join(config_errors)}"
        super().__init__(
            message=message,
            error_code="CONFIG_VALIDATION_FAILED",
            context={
                "config_errors": config_errors,
                "config_file": config_file
            }
        )


class DataValidationError(ValidationError):
    """Raised when extracted data validation fails"""
    
    def __init__(self, validation_errors: List[str], data_type: str):
        message = f"{data_type} validation failed: {'; '.join(validation_errors)}"
        super().__init__(
            message=message,
            error_code="DATA_VALIDATION_FAILED",
            context={
                "validation_errors": validation_errors,
                "data_type": data_type
            }
        )


class RetryableError(PDFExtractionBaseException):
    """Base class for errors that can be retried"""
    
    def __init__(self, message: str, retry_after: Optional[float] = None, 
                 max_retries: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.max_retries = max_retries


class TemporaryAPIError(RetryableError, APIError):
    """Raised for temporary API errors that can be retried"""
    
    def __init__(self, message: str, retry_after: Optional[float] = 30, 
                 max_retries: Optional[int] = 3):
        super().__init__(
            message=message,
            retry_after=retry_after,
            max_retries=max_retries,
            error_code="TEMPORARY_API_ERROR"
        )


class ExceptionHandler:
    """Centralized exception handling utilities"""
    
    @staticmethod
    def is_retryable(exception: Exception) -> bool:
        """Check if an exception is retryable"""
        return isinstance(exception, RetryableError)
    
    @staticmethod
    def get_retry_delay(exception: Exception) -> float:
        """Get retry delay for retryable exceptions"""
        if isinstance(exception, RetryableError) and exception.retry_after:
            return exception.retry_after
        return 1.0  # Default delay
    
    @staticmethod
    def get_max_retries(exception: Exception) -> int:
        """Get max retries for retryable exceptions"""
        if isinstance(exception, RetryableError) and exception.max_retries:
            return exception.max_retries
        return 3  # Default max retries
    
    @staticmethod
    def categorize_exception(exception: Exception) -> str:
        """Categorize exception for logging and monitoring"""
        if isinstance(exception, CredentialsError):
            return "CREDENTIALS"
        elif isinstance(exception, APIError):
            return "API"
        elif isinstance(exception, FileError):
            return "FILE"
        elif isinstance(exception, ExtractionError):
            return "EXTRACTION"
        elif isinstance(exception, ProcessingError):
            return "PROCESSING"
        elif isinstance(exception, ValidationError):
            return "VALIDATION"
        else:
            return "UNKNOWN"