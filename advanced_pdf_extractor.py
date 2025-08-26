#!/usr/bin/env python3
"""
Advanced Adobe PDF Extract API - Table Extraction with Renditions
Based on official Adobe samples with enhanced table extraction capabilities
"""

import os
import sys
import json
import argparse
import zipfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.table_structure_type import TableStructureType
    from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
except ImportError:
    print("❌ Adobe PDF Services SDK not installed.")
    print("Run: pip install pdfservices-sdk")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedPDFExtractor:
    """Advanced Adobe PDF Extract API wrapper with renditions support"""
    
    def __init__(self, credentials_path: str = "credentials/pdfservices-api-credentials.json"):
        """
        Initialize the advanced PDF extractor
        
        Args:
            credentials_path: Path to Adobe PDF Services API credentials JSON file
        """
        self.credentials_path = credentials_path
        self.pdf_services = None
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup Adobe PDF Services API credentials"""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}\n"
                "Please download your credentials from Adobe Developer Console"
            )
        
        try:
            # Load credentials from JSON file
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
            
            client_id = creds_data["client_credentials"]["client_id"]
            client_secret = creds_data["client_credentials"]["client_secret"]
            
            # Create credentials object
            credentials = ServicePrincipalCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Initialize PDF Services
            self.pdf_services = PDFServices(credentials=credentials)
            logger.info("✅ Adobe PDF Services API credentials loaded successfully")
            
        except Exception as e:
            raise Exception(f"Failed to load credentials: {str(e)}")
    
    def extract_with_renditions(
        self, 
        input_pdf_path: str, 
        output_dir: str = "output_advanced",
        table_format: str = "csv",
        extract_text: bool = True,
        extract_figures: bool = True,
        extract_tables: bool = True
    ) -> Dict[str, Any]:
        """
        Advanced extraction with table and figure renditions
        
        Args:
            input_pdf_path: Path to input PDF file
            output_dir: Directory to save extracted data
            table_format: Format for table extraction ('csv' or 'xlsx')
            extract_text: Whether to extract text elements
            extract_figures: Whether to extract figure renditions
            extract_tables: Whether to extract table renditions
            
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
        
        # Configure extraction elements
        elements_to_extract = []
        if extract_text:
            elements_to_extract.append(ExtractElementType.TEXT)
        if extract_tables:
            elements_to_extract.append(ExtractElementType.TABLES)
        
        # Configure rendition elements (this is the key!)
        elements_to_extract_renditions = []
        if extract_tables:
            elements_to_extract_renditions.append(ExtractRenditionsElementType.TABLES)
        if extract_figures:
            elements_to_extract_renditions.append(ExtractRenditionsElementType.FIGURES)
        
        # Set table structure format
        if table_format.lower() == "xlsx":
            table_structure_format = TableStructureType.XLSX
        else:
            table_structure_format = TableStructureType.CSV
        
        # Create extraction parameters with renditions
        extract_pdf_params = ExtractPDFParams(
            elements_to_extract=elements_to_extract,
            elements_to_extract_renditions=elements_to_extract_renditions
        )
        extract_pdf_params.table_structure_format = table_structure_format
        extract_pdf_params.add_char_info = True  # Enable character-level info
        
        try:
            logger.info(f"🔄 Advanced extraction from: {input_pdf_path}")
            logger.info(f"📊 Extracting renditions for: {[e.value for e in elements_to_extract_renditions]}")
            
            # Create and submit job
            extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
            location = self.pdf_services.submit(extract_pdf_job)
            pdf_services_response = self.pdf_services.get_job_result(location, ExtractPDFResult)
            
            # Get result asset
            result_asset = pdf_services_response.get_result().get_resource()
            stream_asset = self.pdf_services.get_content(result_asset)
            
            # Generate output filename
            pdf_name = Path(input_pdf_path).stem
            output_zip_path = os.path.join(output_dir, f"{pdf_name}_advanced_extracted.zip")
            
            # Save result
            with open(output_zip_path, "wb") as file:
                file.write(stream_asset.get_input_stream())
            
            logger.info(f"✅ Advanced extraction completed: {output_zip_path}")
            
            # Extract and organize the ZIP contents
            extracted_files = self._process_advanced_extraction_results(output_zip_path, output_dir, pdf_name)
            
            return {
                "success": True,
                "input_file": input_pdf_path,
                "output_zip": output_zip_path,
                "extracted_files": extracted_files,
                "table_format": table_format,
                "renditions_extracted": len(elements_to_extract_renditions) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Advanced extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "input_file": input_pdf_path
            }
    
    def _process_advanced_extraction_results(self, zip_path: str, output_dir: str, pdf_name: str) -> Dict[str, Any]:
        """
        Process and organize advanced extraction results from ZIP file
        
        Args:
            zip_path: Path to the extraction results ZIP file
            output_dir: Output directory
            pdf_name: Name of the original PDF (without extension)
            
        Returns:
            Dictionary mapping file types to their paths and counts
        """
        extracted_files = {
            "json": None,
            "tables": [],
            "figures": [],
            "csv_files": [],
            "xlsx_files": []
        }
        
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
                        logger.info(f"📄 JSON data: {file_path}")
                    
                    elif 'tables/' in file_name:
                        if file_name.endswith('.png'):
                            extracted_files['tables'].append(file_path)
                            logger.info(f"📊 Table image: {file_path}")
                        elif file_name.endswith('.csv'):
                            extracted_files['csv_files'].append(file_path)
                            logger.info(f"📊 Table CSV: {file_path}")
                        elif file_name.endswith('.xlsx'):
                            extracted_files['xlsx_files'].append(file_path)
                            logger.info(f"📊 Table Excel: {file_path}")
                    
                    elif 'figures/' in file_name and file_name.endswith('.png'):
                        extracted_files['figures'].append(file_path)
                        logger.info(f"🖼️  Figure image: {file_path}")
                
                # Summary
                logger.info(f"📊 Extraction summary:")
                logger.info(f"   • Table images: {len(extracted_files['tables'])}")
                logger.info(f"   • Figure images: {len(extracted_files['figures'])}")
                logger.info(f"   • CSV files: {len(extracted_files['csv_files'])}")
                logger.info(f"   • Excel files: {len(extracted_files['xlsx_files'])}")
                
        except Exception as e:
            logger.error(f"❌ Failed to process advanced extraction results: {str(e)}")
        
        return extracted_files


def main():
    """Main CLI function for advanced extraction"""
    parser = argparse.ArgumentParser(
        description="Advanced PDF table extraction with Adobe PDF Extract API"
    )
    parser.add_argument(
        "input_pdf", 
        help="Path to input PDF file"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="output_advanced",
        help="Output directory for extracted data (default: output_advanced)"
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
        help="Skip text extraction"
    )
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Skip figure rendition extraction"
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Skip table rendition extraction"
    )
    parser.add_argument(
        "--credentials", "-c",
        default="credentials/pdfservices-api-credentials.json",
        help="Path to Adobe PDF Services API credentials"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize advanced extractor
        extractor = AdvancedPDFExtractor(credentials_path=args.credentials)
        
        # Extract data with renditions
        result = extractor.extract_with_renditions(
            input_pdf_path=args.input_pdf,
            output_dir=args.output_dir,
            table_format=args.table_format,
            extract_text=not args.no_text,
            extract_figures=not args.no_figures,
            extract_tables=not args.no_tables
        )
        
        # Print results
        if result["success"]:
            print(f"\n🎉 Advanced extraction successful!")
            print(f"📁 Output directory: {args.output_dir}")
            print(f"🔧 Renditions extracted: {result['renditions_extracted']}")
            
            if "extracted_files" in result:
                files = result["extracted_files"]
                print(f"\n📋 Extracted content:")
                if files["json"]:
                    print(f"  📄 Structured data: {files['json']}")
                if files["tables"]:
                    print(f"  📊 Table images: {len(files['tables'])} files")
                if files["figures"]:
                    print(f"  🖼️  Figure images: {len(files['figures'])} files")
                if files["csv_files"]:
                    print(f"  📊 CSV tables: {len(files['csv_files'])} files")
                if files["xlsx_files"]:
                    print(f"  📊 Excel tables: {len(files['xlsx_files'])} files")
        else:
            print(f"\n❌ Advanced extraction failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
