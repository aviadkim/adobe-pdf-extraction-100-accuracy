#!/usr/bin/env python3
"""
Adobe PDF Extract API - Table Extraction Tool
Extracts tables and structured data from PDF files using Adobe PDF Services API
"""

import os
import sys
import json
import argparse
import zipfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import time

# Import custom exceptions and logging
try:
    from exceptions import (
        CredentialsNotFoundError, InvalidCredentialsFormatError, 
        APIConnectionError, APIAuthenticationError, APITimeoutError,
        PDFNotFoundError, InvalidPDFError, PDFTooLargeError,
        TableExtractionError, NoTablesFoundError, OutputDirectoryError,
        TemporaryAPIError, ExceptionHandler
    )
    from logging_config import setup_logging, log_performance
except ImportError:
    # Fallback if modules not available
    logging.warning("Custom exception and logging modules not available, using defaults")
    class ExceptionHandler:
        @staticmethod
        def is_retryable(e): return False
        @staticmethod
        def get_retry_delay(e): return 1.0
        @staticmethod
        def get_max_retries(e): return 3
    def log_performance(func): return func

try:
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset
    from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.table_structure_type import TableStructureType
    from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
except ImportError:
    print("Adobe PDF Services SDK not installed.")
    print("Run: pip install pdfservices-sdk")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFExtractor:
    """Adobe PDF Extract API wrapper for table extraction"""
    
    def __init__(self, credentials_path: str = "credentials/pdfservices-api-credentials.json"):
        """
        Initialize the PDF extractor

        Args:
            credentials_path: Path to Adobe PDF Services API credentials JSON file
        """
        self.credentials_path = credentials_path
        self.pdf_services = None
        self._setup_credentials()

    def _setup_credentials(self):
        """Setup Adobe PDF Services API credentials with specific error handling"""
        # Check if credentials file exists
        if not os.path.exists(self.credentials_path):
            raise CredentialsNotFoundError(self.credentials_path)

        try:
            # Load credentials from JSON file
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)

        except json.JSONDecodeError as e:
            raise InvalidCredentialsFormatError(
                self.credentials_path, 
                ["Invalid JSON format"]
            )
        except PermissionError:
            raise InvalidCredentialsFormatError(
                self.credentials_path,
                ["Permission denied accessing credentials file"]
            )

        # Validate required fields
        missing_fields = []
        try:
            client_credentials = creds_data["client_credentials"]
            client_id = client_credentials["client_id"]
            client_secret = client_credentials["client_secret"]
            
            if not client_id:
                missing_fields.append("client_id")
            if not client_secret:
                missing_fields.append("client_secret")
                
        except KeyError as e:
            missing_fields.append(str(e).strip("'\""))

        if missing_fields:
            raise InvalidCredentialsFormatError(self.credentials_path, missing_fields)

        try:
            # Create credentials object
            credentials = ServicePrincipalCredentials(
                client_id=client_id,
                client_secret=client_secret
            )

            # Initialize PDF Services
            self.pdf_services = PDFServices(credentials=credentials)
            client_id_display = client_id[:8] + "..." if len(client_id) > 8 else client_id
            logger.info(f"Adobe PDF Services API credentials loaded successfully (Client: {client_id_display})")

        except Exception as e:
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                raise APIAuthenticationError(client_id[:8] + "..." if len(client_id) > 8 else None)
            elif "connection" in str(e).lower() or "network" in str(e).lower():
                raise APIConnectionError(original_error=e)
            else:
                raise InvalidCredentialsFormatError(self.credentials_path, [f"SDK initialization failed: {str(e)}"])
    
    def extract_tables(
        self,
        input_pdf_path: str,
        output_dir: str = "output",
        table_format: str = "csv",
        extract_text: bool = True,
        enable_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Extract tables and text from a PDF file

        Args:
            input_pdf_path: Path to input PDF file
            output_dir: Directory to save extracted data
            table_format: Format for table extraction ('csv' or 'xlsx')
            extract_text: Whether to extract text elements
            enable_ocr: Whether to enable OCR for scanned/image content

        Returns:
            Dictionary with extraction results and file paths
        """
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input PDF not found: {input_pdf_path}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create stream asset from file
        with open(input_pdf_path, 'rb') as file:
            input_stream = file.read()

        input_asset = self.pdf_services.upload(input_stream, PDFServicesMediaType.PDF)

        # Configure extraction parameters
        elements_to_extract = [ExtractElementType.TABLES]
        if extract_text:
            elements_to_extract.append(ExtractElementType.TEXT)

        # Set table structure format
        if table_format.lower() == "xlsx":
            table_structure_format = TableStructureType.XLSX
        else:
            table_structure_format = TableStructureType.CSV

        # Create extraction parameters
        extract_pdf_params = ExtractPDFParams(
            elements_to_extract=elements_to_extract
        )
        extract_pdf_params.table_structure_format = table_structure_format

        # Enable OCR for scanned/image content
        if enable_ocr:
            extract_pdf_params.add_char_info = True
            logger.info("OCR enabled for image-based content")

        try:
            logger.info(f"Extracting data from: {input_pdf_path}")

            # Create and submit job
            extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
            location = self.pdf_services.submit(extract_pdf_job)
            pdf_services_response = self.pdf_services.get_job_result(location, ExtractPDFResult)

            # Get result asset
            result_asset = pdf_services_response.get_result().get_resource()
            stream_asset = self.pdf_services.get_content(result_asset)

            # Generate output filename
            pdf_name = Path(input_pdf_path).stem
            output_zip_path = os.path.join(output_dir, f"{pdf_name}_extracted.zip")

            # Save result
            with open(output_zip_path, "wb") as file:
                file.write(stream_asset.get_input_stream())
            
            logger.info(f"Extraction completed: {output_zip_path}")
            
            # Extract and organize the ZIP contents
            extracted_files = self._process_extraction_results(output_zip_path, output_dir, pdf_name)
            
            return {
                "success": True,
                "input_file": input_pdf_path,
                "output_zip": output_zip_path,
                "extracted_files": extracted_files,
                "table_format": table_format
            }
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "input_file": input_pdf_path
            }
    
    def _process_extraction_results(self, zip_path: str, output_dir: str, pdf_name: str) -> Dict[str, str]:
        """
        Process and organize extraction results from ZIP file
        
        Args:
            zip_path: Path to the extraction results ZIP file
            output_dir: Output directory
            pdf_name: Name of the original PDF (without extension)
            
        Returns:
            Dictionary mapping file types to their paths
        """
        extracted_files = {}
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Create subdirectory for this PDF's results
                pdf_output_dir = os.path.join(output_dir, pdf_name)
                os.makedirs(pdf_output_dir, exist_ok=True)
                
                # Extract all files
                zip_ref.extractall(pdf_output_dir)
                
                # Organize extracted files
                for file_name in zip_ref.namelist():
                    file_path = os.path.join(pdf_output_dir, file_name)
                    
                    if file_name.endswith('.json'):
                        extracted_files['json'] = file_path
                        logger.info(f"JSON data: {file_path}")
                    elif file_name.endswith('.csv'):
                        extracted_files['csv'] = file_path
                        logger.info(f"CSV tables: {file_path}")
                    elif file_name.endswith('.xlsx'):
                        extracted_files['xlsx'] = file_path
                        logger.info(f"Excel tables: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to process extraction results: {str(e)}")
        
        return extracted_files


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Extract tables from PDF files using Adobe PDF Extract API"
    )
    parser.add_argument(
        "input_pdf", 
        help="Path to input PDF file"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Output directory for extracted data (default: output)"
    )
    parser.add_argument(
        "--table-format", "-f",
        choices=["csv", "xlsx"],
        default="csv",
        help="Table output format (default: csv)"
    )
    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Skip text extraction, only extract tables"
    )
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        default=True,
        help="Enable OCR for scanned/image content (default: enabled)"
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR processing"
    )
    parser.add_argument(
        "--credentials", "-c",
        default="credentials/pdfservices-api-credentials.json",
        help="Path to Adobe PDF Services API credentials"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize extractor
        extractor = PDFExtractor(credentials_path=args.credentials)
        
        # Extract data
        enable_ocr = args.enable_ocr and not args.no_ocr
        result = extractor.extract_tables(
            input_pdf_path=args.input_pdf,
            output_dir=args.output_dir,
            table_format=args.table_format,
            extract_text=not args.no_text,
            enable_ocr=enable_ocr
        )
        
        # Print results
        if result["success"]:
            print(f"\nExtraction successful!")
            print(f"📁 Output directory: {args.output_dir}")
            
            if "extracted_files" in result:
                print("\n📋 Extracted files:")
                for file_type, file_path in result["extracted_files"].items():
                    print(f"  {file_type.upper()}: {file_path}")
        else:
            print(f"\nExtraction failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
