#!/usr/bin/env python3
"""
Unit tests for custom exceptions
"""

import pytest
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from exceptions import (
    PDFExtractionBaseException, CredentialsError, CredentialsNotFoundError,
    InvalidCredentialsFormatError, APIError, APIConnectionError,
    APIAuthenticationError, APIQuotaExceededError, APITimeoutError,
    FileError, PDFNotFoundError, InvalidPDFError, PDFTooLargeError,
    OutputDirectoryError, ExtractionError, TableExtractionError,
    TextExtractionError, NoTablesFoundError, ProcessingError,
    SpatialAnalysisError, ImageAnalysisError, OCRError,
    ValidationError, ConfigurationValidationError, DataValidationError,
    RetryableError, TemporaryAPIError, ExceptionHandler
)


class TestBaseException:
    """Test cases for base exception class"""
    
    def test_base_exception_creation(self):
        """Test basic exception creation"""
        exc = PDFExtractionBaseException(
            message="Test error",
            error_code="TEST_ERROR",
            context={"key": "value"}
        )
        
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.context == {"key": "value"}
    
    def test_base_exception_to_dict(self):
        """Test exception serialization to dictionary"""
        exc = PDFExtractionBaseException(
            message="Test error",
            error_code="TEST_ERROR",
            context={"file": "test.pdf", "page": 1}
        )
        
        result = exc.to_dict()
        expected = {
            'exception_type': 'PDFExtractionBaseException',
            'message': 'Test error',
            'error_code': 'TEST_ERROR',
            'context': {'file': 'test.pdf', 'page': 1}
        }
        
        assert result == expected
    
    def test_base_exception_minimal(self):
        """Test exception creation with minimal parameters"""
        exc = PDFExtractionBaseException("Simple error")
        
        assert str(exc) == "Simple error"
        assert exc.error_code is None
        assert exc.context == {}


class TestCredentialsExceptions:
    """Test cases for credentials-related exceptions"""
    
    def test_credentials_not_found_error(self):
        """Test CredentialsNotFoundError"""
        path = "/path/to/credentials.json"
        exc = CredentialsNotFoundError(path)
        
        assert "not found" in str(exc)
        assert path in str(exc)
        assert exc.error_code == "CREDS_NOT_FOUND"
        assert exc.context["credentials_path"] == path
    
    def test_invalid_credentials_format_error(self):
        """Test InvalidCredentialsFormatError"""
        path = "/path/to/credentials.json"
        missing_fields = ["client_id", "client_secret"]
        
        exc = InvalidCredentialsFormatError(path, missing_fields)
        
        assert "Invalid credentials format" in str(exc)
        assert "client_id" in str(exc)
        assert "client_secret" in str(exc)
        assert exc.error_code == "CREDS_INVALID_FORMAT"
        assert exc.context["missing_fields"] == missing_fields
    
    def test_invalid_credentials_format_error_minimal(self):
        """Test InvalidCredentialsFormatError with minimal parameters"""
        path = "/path/to/credentials.json"
        exc = InvalidCredentialsFormatError(path)
        
        assert "Invalid credentials format" in str(exc)
        assert exc.context["missing_fields"] == []


class TestAPIExceptions:
    """Test cases for API-related exceptions"""
    
    def test_api_connection_error(self):
        """Test APIConnectionError"""
        endpoint = "https://api.adobe.com"
        original_error = ConnectionError("Network timeout")
        
        exc = APIConnectionError(endpoint, original_error)
        
        assert "Failed to connect" in str(exc)
        assert endpoint in str(exc)
        assert exc.error_code == "API_CONNECTION_FAILED"
        assert exc.context["endpoint"] == endpoint
        assert "Network timeout" in exc.context["original_error"]
    
    def test_api_authentication_error(self):
        """Test APIAuthenticationError"""
        client_id_prefix = "abc12345"
        exc = APIAuthenticationError(client_id_prefix)
        
        assert "authentication failed" in str(exc)
        assert client_id_prefix in str(exc)
        assert exc.error_code == "API_AUTH_FAILED"
        assert exc.context["client_id_prefix"] == client_id_prefix
    
    def test_api_quota_exceeded_error(self):
        """Test APIQuotaExceededError"""
        quota_info = {"limit": 1000, "used": 1000, "reset_time": "2025-01-01"}
        exc = APIQuotaExceededError(quota_info)
        
        assert "quota exceeded" in str(exc)
        assert exc.error_code == "API_QUOTA_EXCEEDED"
        assert exc.context == quota_info
    
    def test_api_timeout_error(self):
        """Test APITimeoutError"""
        timeout_duration = 30.0
        operation = "extract_tables"
        
        exc = APITimeoutError(timeout_duration, operation)
        
        assert "timed out" in str(exc)
        assert "30.0s" in str(exc)
        assert operation in str(exc)
        assert exc.error_code == "API_TIMEOUT"
        assert exc.context["timeout_duration"] == timeout_duration
        assert exc.context["operation"] == operation


class TestFileExceptions:
    """Test cases for file-related exceptions"""
    
    def test_pdf_not_found_error(self):
        """Test PDFNotFoundError"""
        pdf_path = "/path/to/document.pdf"
        exc = PDFNotFoundError(pdf_path)
        
        assert "PDF file not found" in str(exc)
        assert pdf_path in str(exc)
        assert exc.error_code == "PDF_NOT_FOUND"
        assert exc.context["pdf_path"] == pdf_path
    
    def test_invalid_pdf_error(self):
        """Test InvalidPDFError"""
        pdf_path = "/path/to/corrupt.pdf"
        validation_error = "File header invalid"
        
        exc = InvalidPDFError(pdf_path, validation_error)
        
        assert "Invalid or corrupted" in str(exc)
        assert pdf_path in str(exc)
        assert validation_error in str(exc)
        assert exc.error_code == "PDF_INVALID"
        assert exc.context["validation_error"] == validation_error
    
    def test_pdf_too_large_error(self):
        """Test PDFTooLargeError"""
        pdf_path = "/path/to/huge.pdf"
        file_size_mb = 150.5
        max_size_mb = 100.0
        
        exc = PDFTooLargeError(pdf_path, file_size_mb, max_size_mb)
        
        assert "too large" in str(exc)
        assert "150.5MB" in str(exc)
        assert "100MB" in str(exc)
        assert exc.error_code == "PDF_TOO_LARGE"
        assert exc.context["file_size_mb"] == file_size_mb
        assert exc.context["max_size_mb"] == max_size_mb
    
    def test_output_directory_error(self):
        """Test OutputDirectoryError"""
        output_dir = "/read/only/directory"
        original_error = PermissionError("Permission denied")
        
        exc = OutputDirectoryError(output_dir, original_error)
        
        assert "output directory" in str(exc)
        assert output_dir in str(exc)
        assert exc.error_code == "OUTPUT_DIR_ERROR"
        assert exc.context["output_dir"] == output_dir
        assert "Permission denied" in exc.context["original_error"]


class TestExtractionExceptions:
    """Test cases for extraction-related exceptions"""
    
    def test_table_extraction_error(self):
        """Test TableExtractionError"""
        pdf_path = "/path/to/document.pdf"
        page_number = 5
        extraction_details = {"tables_found": 0, "confidence": 0.2}
        
        exc = TableExtractionError(pdf_path, page_number, extraction_details)
        
        assert "Table extraction failed" in str(exc)
        assert pdf_path in str(exc)
        assert "page 5" in str(exc)
        assert exc.error_code == "TABLE_EXTRACTION_FAILED"
        assert exc.context["page_number"] == page_number
        assert exc.context["extraction_details"] == extraction_details
    
    def test_text_extraction_error(self):
        """Test TextExtractionError"""
        pdf_path = "/path/to/document.pdf"
        page_number = 3
        
        exc = TextExtractionError(pdf_path, page_number)
        
        assert "Text extraction failed" in str(exc)
        assert pdf_path in str(exc)
        assert "page 3" in str(exc)
        assert exc.error_code == "TEXT_EXTRACTION_FAILED"
    
    def test_no_tables_found_error(self):
        """Test NoTablesFoundError"""
        pdf_path = "/path/to/document.pdf"
        exc = NoTablesFoundError(pdf_path)
        
        assert "No tables found" in str(exc)
        assert pdf_path in str(exc)
        assert exc.error_code == "NO_TABLES_FOUND"


class TestProcessingExceptions:
    """Test cases for processing-related exceptions"""
    
    def test_spatial_analysis_error(self):
        """Test SpatialAnalysisError"""
        page_number = 2
        analysis_type = "table_reconstruction"
        original_error = ValueError("Invalid coordinates")
        
        exc = SpatialAnalysisError(page_number, analysis_type, original_error)
        
        assert "Spatial analysis failed" in str(exc)
        assert "page 2" in str(exc)
        assert analysis_type in str(exc)
        assert exc.error_code == "SPATIAL_ANALYSIS_FAILED"
        assert exc.context["page_number"] == page_number
        assert exc.context["analysis_type"] == analysis_type
        assert "Invalid coordinates" in exc.context["original_error"]
    
    def test_image_analysis_error(self):
        """Test ImageAnalysisError"""
        image_path = "/path/to/image.png"
        analysis_type = "table_detection"
        original_error = OSError("Cannot read image")
        
        exc = ImageAnalysisError(image_path, analysis_type, original_error)
        
        assert "Image analysis failed" in str(exc)
        assert image_path in str(exc)
        assert analysis_type in str(exc)
        assert exc.error_code == "IMAGE_ANALYSIS_FAILED"
    
    def test_ocr_error(self):
        """Test OCRError"""
        image_path = "/path/to/scan.png"
        ocr_service = "Azure"
        original_error = TimeoutError("OCR timeout")
        
        exc = OCRError(image_path, ocr_service, original_error)
        
        assert "OCR processing failed" in str(exc)
        assert image_path in str(exc)
        assert ocr_service in str(exc)
        assert exc.error_code == "OCR_FAILED"
        assert exc.context["ocr_service"] == ocr_service


class TestValidationExceptions:
    """Test cases for validation-related exceptions"""
    
    def test_configuration_validation_error(self):
        """Test ConfigurationValidationError"""
        config_errors = ["Missing API key", "Invalid timeout value"]
        config_file = "/path/to/config.json"
        
        exc = ConfigurationValidationError(config_errors, config_file)
        
        assert "Configuration validation failed" in str(exc)
        assert "Missing API key" in str(exc)
        assert "Invalid timeout" in str(exc)
        assert exc.error_code == "CONFIG_VALIDATION_FAILED"
        assert exc.context["config_errors"] == config_errors
        assert exc.context["config_file"] == config_file
    
    def test_data_validation_error(self):
        """Test DataValidationError"""
        validation_errors = ["Invalid ISIN format", "Missing price data"]
        data_type = "securities"
        
        exc = DataValidationError(validation_errors, data_type)
        
        assert "securities validation failed" in str(exc)
        assert "Invalid ISIN format" in str(exc)
        assert "Missing price data" in str(exc)
        assert exc.error_code == "DATA_VALIDATION_FAILED"
        assert exc.context["data_type"] == data_type


class TestRetryableExceptions:
    """Test cases for retryable exceptions"""
    
    def test_retryable_error(self):
        """Test RetryableError base class"""
        exc = RetryableError(
            message="Temporary failure",
            retry_after=30.0,
            max_retries=5,
            error_code="TEMP_ERROR"
        )
        
        assert str(exc) == "Temporary failure"
        assert exc.retry_after == 30.0
        assert exc.max_retries == 5
        assert exc.error_code == "TEMP_ERROR"
    
    def test_temporary_api_error(self):
        """Test TemporaryAPIError"""
        exc = TemporaryAPIError("Service temporarily unavailable")
        
        assert "temporarily unavailable" in str(exc)
        assert exc.error_code == "TEMPORARY_API_ERROR"
        assert exc.retry_after == 30  # default
        assert exc.max_retries == 3   # default
    
    def test_temporary_api_error_custom_params(self):
        """Test TemporaryAPIError with custom parameters"""
        exc = TemporaryAPIError(
            "Rate limited",
            retry_after=60.0,
            max_retries=5
        )
        
        assert exc.retry_after == 60.0
        assert exc.max_retries == 5


class TestExceptionHandler:
    """Test cases for ExceptionHandler utility class"""
    
    def test_is_retryable(self):
        """Test retryable exception detection"""
        retryable_exc = TemporaryAPIError("Temp failure")
        non_retryable_exc = ValueError("Invalid value")
        
        assert ExceptionHandler.is_retryable(retryable_exc) is True
        assert ExceptionHandler.is_retryable(non_retryable_exc) is False
    
    def test_get_retry_delay(self):
        """Test retry delay extraction"""
        exc_with_delay = RetryableError("Error", retry_after=45.0)
        exc_without_delay = ValueError("Error")
        
        assert ExceptionHandler.get_retry_delay(exc_with_delay) == 45.0
        assert ExceptionHandler.get_retry_delay(exc_without_delay) == 1.0  # default
    
    def test_get_max_retries(self):
        """Test max retries extraction"""
        exc_with_retries = RetryableError("Error", max_retries=10)
        exc_without_retries = ValueError("Error")
        
        assert ExceptionHandler.get_max_retries(exc_with_retries) == 10
        assert ExceptionHandler.get_max_retries(exc_without_retries) == 3  # default
    
    def test_categorize_exception(self):
        """Test exception categorization"""
        test_cases = [
            (CredentialsNotFoundError("path"), "CREDENTIALS"),
            (APIConnectionError(), "API"),
            (PDFNotFoundError("path"), "FILE"),
            (TableExtractionError("path"), "EXTRACTION"),
            (SpatialAnalysisError(1, "type"), "PROCESSING"),
            (DataValidationError([], "type"), "VALIDATION"),
            (ValueError("error"), "UNKNOWN")
        ]
        
        for exception, expected_category in test_cases:
            result = ExceptionHandler.categorize_exception(exception)
            assert result == expected_category


if __name__ == "__main__":
    pytest.main([__file__, "-v"])