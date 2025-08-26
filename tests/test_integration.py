#!/usr/bin/env python3
"""
Integration tests for Adobe PDF Extraction System
Tests the complete workflow with mocked Adobe API responses
"""

import pytest
import os
import json
import tempfile
import zipfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from pdf_extractor import PDFExtractor
    from advanced_pdf_extractor import AdvancedPDFExtractor
    from complete_data_extractor import CompleteDataExtractor
    from securities_extractor import SecuritiesExtractor
    from exceptions import (
        CredentialsNotFoundError, APIConnectionError, 
        TableExtractionError, PDFNotFoundError
    )
except ImportError as e:
    pytest.skip(f"Skipping integration tests due to import error: {e}", allow_module_level=True)


class MockAdobeResponse:
    """Mock Adobe API response objects"""
    
    @staticmethod
    def create_mock_extract_result(include_tables=True, include_text=True):
        """Create mock ExtractPDFResult"""
        mock_result = Mock()
        mock_resource = Mock()
        mock_result.get_result.return_value.get_resource.return_value = mock_resource
        
        # Create mock ZIP content
        zip_content = MockAdobeResponse._create_mock_zip_content(include_tables, include_text)
        mock_stream_asset = Mock()
        mock_stream_asset.get_input_stream.return_value = zip_content
        
        return mock_result, mock_stream_asset
    
    @staticmethod
    def _create_mock_zip_content(include_tables=True, include_text=True):
        """Create mock ZIP file content"""
        # Create a temporary ZIP file with mock content
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zf:
            # Add mock structured data JSON
            structured_data = {
                "elements": [
                    {
                        "Text": "MESSOS ENTERPRISES LTD.",
                        "Page": 1,
                        "Bounds": [100, 50, 300, 20],
                        "Font": {"name": "Arial", "size": 12}
                    },
                    {
                        "Text": "Client Number: 366223",
                        "Page": 1,
                        "Bounds": [100, 80, 200, 15],
                        "Font": {"name": "Arial", "size": 10}
                    },
                    {
                        "Text": "Portfolio Valuation",
                        "Page": 1,
                        "Bounds": [100, 120, 250, 18],
                        "Font": {"name": "Arial", "size": 14}
                    }
                ]
            }
            
            if include_tables:
                structured_data["elements"].extend([
                    {
                        "Text": "Swiss Government Bond",
                        "Page": 1,
                        "Bounds": [50, 200, 200, 15],
                        "Font": {"name": "Arial", "size": 10}
                    },
                    {
                        "Text": "CH0123456789",
                        "Page": 1,
                        "Bounds": [250, 200, 120, 15],
                        "Font": {"name": "Arial", "size": 10}
                    },
                    {
                        "Text": "CHF 100,000",
                        "Page": 1,
                        "Bounds": [370, 200, 100, 15],
                        "Font": {"name": "Arial", "size": 10}
                    },
                    {
                        "Text": "98.75",
                        "Page": 1,
                        "Bounds": [470, 200, 60, 15],
                        "Font": {"name": "Arial", "size": 10}
                    }
                ])
            
            zf.writestr("structuredData.json", json.dumps(structured_data, indent=2))
            
            # Add mock table CSV if requested
            if include_tables:
                table_csv = """Security Name,ISIN,Currency,Amount,Price,Market Value
Swiss Government Bond,CH0123456789,CHF,100000,98.75,98750.00
European Equity Fund,LU0987654321,EUR,50000,245.80,122900.00
US Treasury Note,US0123456789,USD,75000,101.25,75937.50"""
                zf.writestr("tables.csv", table_csv)
        
        # Read the ZIP content
        with open(temp_zip.name, 'rb') as f:
            zip_content = f.read()
        
        # Clean up
        os.unlink(temp_zip.name)
        return zip_content


@pytest.fixture
def mock_credentials():
    """Create mock credentials file"""
    credentials = {
        "client_credentials": {
            "client_id": "test_client_id_12345",
            "client_secret": "test_client_secret_67890"
        },
        "service_account_credentials": {
            "organization_id": "test_org_id",
            "account_id": "test_account_id"
        }
    }
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(credentials, temp_file)
    temp_file.flush()
    
    yield temp_file.name
    
    os.unlink(temp_file.name)


@pytest.fixture
def mock_pdf_file():
    """Create mock PDF file"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.write(b'%PDF-1.4\n%Mock PDF content for testing')
    temp_file.flush()
    
    yield temp_file.name
    
    os.unlink(temp_file.name)


class TestPDFExtractorIntegration:
    """Integration tests for PDFExtractor"""
    
    @patch('pdf_extractor.PDFServices')
    @patch('pdf_extractor.ServicePrincipalCredentials')
    def test_successful_table_extraction(self, mock_creds, mock_pdf_services, 
                                       mock_credentials, mock_pdf_file):
        """Test successful table extraction workflow"""
        # Setup mocks
        mock_service_instance = Mock()
        mock_pdf_services.return_value = mock_service_instance
        
        # Mock upload
        mock_asset = Mock()
        mock_service_instance.upload.return_value = mock_asset
        
        # Mock job submission and results
        mock_location = "https://api.adobe.com/job/123"
        mock_service_instance.submit.return_value = mock_location
        
        mock_result, mock_stream_asset = MockAdobeResponse.create_mock_extract_result()
        mock_service_instance.get_job_result.return_value = mock_result
        mock_service_instance.get_content.return_value = mock_stream_asset
        
        # Create extractor and test
        extractor = PDFExtractor(credentials_path=mock_credentials)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = extractor.extract_tables(
                input_pdf_path=mock_pdf_file,
                output_dir=temp_dir,
                table_format="csv"
            )
            
            # Verify results
            assert result["success"] is True
            assert result["input_file"] == mock_pdf_file
            assert "output_zip" in result
            assert "extracted_files" in result
            
            # Verify API calls
            mock_service_instance.upload.assert_called_once()
            mock_service_instance.submit.assert_called_once()
            mock_service_instance.get_job_result.assert_called_once_with(mock_location, pytest.skip)
    
    @patch('pdf_extractor.PDFServices')
    @patch('pdf_extractor.ServicePrincipalCredentials')
    def test_extraction_with_api_error(self, mock_creds, mock_pdf_services,
                                     mock_credentials, mock_pdf_file):
        """Test extraction workflow with API error"""
        # Setup mocks to raise exception
        mock_service_instance = Mock()
        mock_pdf_services.return_value = mock_service_instance
        mock_service_instance.upload.return_value = Mock()
        mock_service_instance.submit.side_effect = Exception("API Error")
        
        # Create extractor and test
        extractor = PDFExtractor(credentials_path=mock_credentials)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = extractor.extract_tables(
                input_pdf_path=mock_pdf_file,
                output_dir=temp_dir
            )
            
            # Verify error handling
            assert result["success"] is False
            assert "error" in result
            assert "API Error" in result["error"]
    
    def test_pdf_not_found_error(self, mock_credentials):
        """Test handling of missing PDF file"""
        extractor = PDFExtractor(credentials_path=mock_credentials)
        
        with pytest.raises(FileNotFoundError):
            extractor.extract_tables("nonexistent.pdf")
    
    def test_credentials_not_found_error(self):
        """Test handling of missing credentials"""
        with pytest.raises(CredentialsNotFoundError):
            PDFExtractor(credentials_path="nonexistent_creds.json")


class TestAdvancedPDFExtractorIntegration:
    """Integration tests for AdvancedPDFExtractor"""
    
    @patch('advanced_pdf_extractor.PDFServices')
    @patch('advanced_pdf_extractor.ServicePrincipalCredentials')
    def test_advanced_extraction_with_renditions(self, mock_creds, mock_pdf_services,
                                                mock_credentials, mock_pdf_file):
        """Test advanced extraction with renditions"""
        # Setup mocks
        mock_service_instance = Mock()
        mock_pdf_services.return_value = mock_service_instance
        mock_service_instance.upload.return_value = Mock()
        mock_service_instance.submit.return_value = "job_location"
        
        # Create more complex mock response with figures
        mock_result, mock_stream_asset = MockAdobeResponse.create_mock_extract_result()
        mock_service_instance.get_job_result.return_value = mock_result
        mock_service_instance.get_content.return_value = mock_stream_asset
        
        # Create extractor
        extractor = AdvancedPDFExtractor(credentials_path=mock_credentials)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = extractor.extract_with_renditions(
                input_pdf_path=mock_pdf_file,
                output_dir=temp_dir,
                extract_figures=True,
                extract_tables=True
            )
            
            # Verify results
            assert result["success"] is True
            assert result["renditions_extracted"] is True
            assert "extracted_files" in result


class TestCompleteDataExtractorIntegration:
    """Integration tests for CompleteDataExtractor"""
    
    def setup_mock_extraction_output(self, temp_dir):
        """Setup mock Adobe extraction output for CompleteDataExtractor"""
        # Create the expected directory structure
        output_dir = os.path.join(temp_dir, "output_advanced", "messos 30.5")
        figures_dir = os.path.join(output_dir, "figures")
        os.makedirs(figures_dir, exist_ok=True)
        
        # Create mock structuredData.json
        structured_data = {
            "elements": [
                {
                    "Text": "MESSOS ENTERPRISES LTD.",
                    "Page": 1,
                    "Bounds": [100, 50, 300, 20],
                    "Font": {"name": "Arial", "size": 14}
                },
                {
                    "Text": "Client Number: 366223",
                    "Page": 1,
                    "Bounds": [100, 80, 200, 15],
                    "Font": {"name": "Arial", "size": 10}
                },
                {
                    "Text": "Portfolio Valuation: USD 1,234,567.89",
                    "Page": 1,
                    "Bounds": [100, 110, 300, 15],
                    "Font": {"name": "Arial", "size": 12}
                },
                {
                    "Text": "Swiss Government Bond",
                    "Page": 1,
                    "Bounds": [50, 200, 200, 15],
                    "Font": {"name": "Arial", "size": 10}
                },
                {
                    "Text": "CH0123456789",
                    "Page": 1,
                    "Bounds": [260, 200, 120, 15],
                    "Font": {"name": "Arial", "size": 10}
                },
                {
                    "Text": "CHF",
                    "Page": 1,
                    "Bounds": [390, 200, 30, 15],
                    "Font": {"name": "Arial", "size": 10}
                },
                {
                    "Text": "100,000",
                    "Page": 1,
                    "Bounds": [430, 200, 70, 15],
                    "Font": {"name": "Arial", "size": 10}
                },
                {
                    "Text": "98.75",
                    "Page": 1,
                    "Bounds": [510, 200, 50, 15],
                    "Font": {"name": "Arial", "size": 10}
                }
            ]
        }
        
        json_file = os.path.join(output_dir, "structuredData.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2)
        
        # Create mock figure files
        figure_files = [
            ("fileoutpart1.png", 1500000),  # Large file - main table
            ("fileoutpart2.png", 800000),   # Medium file - supporting table
            ("fileoutpart3.png", 50000),    # Small file - header
        ]
        
        for filename, size in figure_files:
            figure_path = os.path.join(figures_dir, filename)
            with open(figure_path, 'wb') as f:
                f.write(b'PNG_MOCK_DATA' * (size // 13))  # Approximate file size
        
        return output_dir, figures_dir, json_file
    
    def test_complete_data_extraction_workflow(self):
        """Test complete data extraction and analysis workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup mock data
            output_dir, figures_dir, json_file = self.setup_mock_extraction_output(temp_dir)
            
            # Patch the paths in CompleteDataExtractor
            with patch.object(CompleteDataExtractor, '__init__') as mock_init:
                def init_patch(self):
                    self.json_file = json_file
                    self.figures_dir = figures_dir
                    self.output_dir = os.path.join(temp_dir, "extracted_data")
                    os.makedirs(self.output_dir, exist_ok=True)
                    self.structured_data = None
                    self.extracted_tables = []
                    self.financial_elements = []
                
                mock_init.side_effect = init_patch
                
                # Create and test extractor
                extractor = CompleteDataExtractor()
                report = extractor.create_comprehensive_report()
                
                # Verify report structure
                assert report is not None
                assert "extraction_summary" in report
                assert "client_information" in report
                assert "financial_data" in report
                assert "image_analysis" in report
                assert "extraction_confidence" in report
                
                # Verify extraction summary
                summary = report["extraction_summary"]
                assert summary["total_text_elements"] > 0
                assert summary["financial_elements"] > 0
                assert summary["image_files"] == 3
                assert summary["high_confidence_images"] >= 1  # At least the large file
                
                # Verify client information extraction
                client_info = report["client_information"]
                assert "company_name" in client_info
                assert "MESSOS ENTERPRISES" in client_info.get("company_name", "")
                
                # Verify financial data categorization
                financial_data = report["financial_data"]
                assert "client_info" in financial_data
                assert "securities" in financial_data
                assert "currencies" in financial_data
                
                # Verify image analysis
                image_analysis = report["image_analysis"]
                assert len(image_analysis) == 3
                
                # Find the high confidence image
                high_conf_image = next((img for img in image_analysis if img["confidence"] > 0.8), None)
                assert high_conf_image is not None
                assert high_conf_image["filename"] == "fileoutpart1.png"


class TestSecuritiesExtractorIntegration:
    """Integration tests for SecuritiesExtractor"""
    
    def test_securities_extraction_workflow(self):
        """Test securities-specific extraction workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock structured data with securities information
            output_dir = os.path.join(temp_dir, "output_advanced", "messos 30.5")
            figures_dir = os.path.join(output_dir, "figures")
            os.makedirs(figures_dir, exist_ok=True)
            
            # Enhanced structured data with more securities
            structured_data = {
                "elements": [
                    {"Text": "MESSOS ENTERPRISES LTD.", "Page": 1, "Bounds": [100, 50, 300, 20]},
                    {"Text": "Swiss Government Bond 2.5%", "Page": 1, "Bounds": [50, 200, 200, 15]},
                    {"Text": "CH0123456789", "Page": 1, "Bounds": [260, 200, 120, 15]},
                    {"Text": "CHF 100,000", "Page": 1, "Bounds": [390, 200, 90, 15]},
                    {"Text": "98.75", "Page": 1, "Bounds": [490, 200, 50, 15]},
                    {"Text": "European Equity Fund", "Page": 1, "Bounds": [50, 230, 200, 15]},
                    {"Text": "LU0987654321", "Page": 1, "Bounds": [260, 230, 120, 15]},
                    {"Text": "EUR 50,000", "Page": 1, "Bounds": [390, 230, 90, 15]},
                    {"Text": "245.80", "Page": 1, "Bounds": [490, 230, 50, 15]},
                    {"Text": "US Treasury Note 3.0%", "Page": 1, "Bounds": [50, 260, 200, 15]},
                    {"Text": "US0123456789", "Page": 1, "Bounds": [260, 260, 120, 15]},
                    {"Text": "USD 75,000", "Page": 1, "Bounds": [390, 260, 90, 15]},
                    {"Text": "101.25", "Page": 1, "Bounds": [490, 260, 50, 15]},
                ]
            }
            
            json_file = os.path.join(output_dir, "structuredData.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2)
            
            # Create large figure file (main table)
            figure_path = os.path.join(figures_dir, "fileoutpart1.png")
            with open(figure_path, 'wb') as f:
                f.write(b'LARGE_TABLE_IMAGE' * 50000)  # ~750KB file
            
            # Patch the paths in SecuritiesExtractor
            with patch.object(SecuritiesExtractor, '__init__') as mock_init:
                def init_patch(self):
                    self.json_file = json_file
                    self.figures_dir = figures_dir
                    self.output_dir = os.path.join(temp_dir, "securities_data")
                    os.makedirs(self.output_dir, exist_ok=True)
                    self.structured_data = None
                    self.all_securities = []
                
                mock_init.side_effect = init_patch
                
                # Create and test extractor
                extractor = SecuritiesExtractor()
                report = extractor.create_comprehensive_securities_report()
                
                # Verify report structure
                assert report is not None
                assert "extraction_summary" in report
                assert "all_securities_found" in report
                assert "financial_elements" in report
                assert "high_confidence_images" in report
                
                # Verify securities were found
                summary = report["extraction_summary"]
                assert summary["total_securities_identified"] >= 3  # Should find the 3 securities
                assert summary["potential_securities_found"] >= 3
                assert summary["currencies_found"] >= 3  # CHF, EUR, USD
                
                # Verify securities details
                securities = report["all_securities_found"]
                assert len(securities) >= 3
                
                # Check for specific securities
                security_names = [s["name"] for s in securities]
                assert any("Swiss Government Bond" in name for name in security_names)
                assert any("European Equity Fund" in name for name in security_names)
                assert any("US Treasury Note" in name for name in security_names)
                
                # Verify financial elements
                financial_elements = report["financial_elements"]
                assert len(financial_elements["currencies"]) >= 3
                assert "CHF" in str(financial_elements["currencies"])
                assert "EUR" in str(financial_elements["currencies"])
                assert "USD" in str(financial_elements["currencies"])


class TestEndToEndWorkflow:
    """End-to-end integration tests"""
    
    @patch('pdf_extractor.PDFServices')
    @patch('pdf_extractor.ServicePrincipalCredentials')
    def test_full_extraction_pipeline(self, mock_creds, mock_pdf_services,
                                    mock_credentials, mock_pdf_file):
        """Test complete extraction pipeline from PDF to final report"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup Adobe API mocks
            mock_service_instance = Mock()
            mock_pdf_services.return_value = mock_service_instance
            mock_service_instance.upload.return_value = Mock()
            mock_service_instance.submit.return_value = "job_location"
            
            mock_result, mock_stream_asset = MockAdobeResponse.create_mock_extract_result()
            mock_service_instance.get_job_result.return_value = mock_result
            mock_service_instance.get_content.return_value = mock_stream_asset
            
            # Step 1: Basic extraction
            extractor = PDFExtractor(credentials_path=mock_credentials)
            basic_result = extractor.extract_tables(
                input_pdf_path=mock_pdf_file,
                output_dir=temp_dir
            )
            
            assert basic_result["success"] is True
            
            # Step 2: Advanced extraction (if available)
            try:
                advanced_extractor = AdvancedPDFExtractor(credentials_path=mock_credentials)
                advanced_result = advanced_extractor.extract_with_renditions(
                    input_pdf_path=mock_pdf_file,
                    output_dir=temp_dir + "_advanced"
                )
                assert advanced_result["success"] is True
            except ImportError:
                pytest.skip("Advanced extractor not available")
            
            # Verify files were created
            assert os.path.exists(basic_result["output_zip"])
            
            # Step 3: Verify extraction results exist
            pdf_name = Path(mock_pdf_file).stem
            output_subdir = os.path.join(temp_dir, pdf_name)
            assert os.path.exists(output_subdir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])