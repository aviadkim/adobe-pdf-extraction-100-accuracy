#!/usr/bin/env python3
"""
Real Adobe PDF Services API Extractor
This script shows how to actually extract data from PDFs using Adobe's API
"""

import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class RealAdobeExtractor:
    """Real Adobe PDF Services API integration"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Initialize with Adobe credentials
        
        Args:
            client_id: Adobe Client ID (or set ADOBE_CLIENT_ID env var)
            client_secret: Adobe Client Secret (or set ADOBE_CLIENT_SECRET env var)
        """
        self.client_id = client_id or os.getenv('ADOBE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('ADOBE_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Adobe credentials are required. Set ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET environment variables or pass them to constructor.")
        
        self.access_token = None
        self.token_expires = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_access_token(self) -> str:
        """Get Adobe API access token"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        self.logger.info("Getting Adobe API access token...")
        
        auth_url = "https://ims-na1.adobelogin.com/ims/token/v3"
        auth_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'openid,AdobeID,read_organizations'
        }
        
        response = requests.post(auth_url, data=auth_data, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Adobe authentication failed: {response.status_code} - {response.text}")
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        
        # Token expires in seconds, we'll refresh 5 minutes early
        expires_in = token_data.get('expires_in', 3600)
        self.token_expires = datetime.now() + datetime.timedelta(seconds=expires_in - 300)
        
        self.logger.info("Successfully obtained access token")
        return self.access_token
    
    def extract_pdf_data(self, pdf_path: str, output_dir: str = "real_extraction_output") -> Dict[str, Any]:
        """
        Extract data from PDF using Adobe PDF Services API
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save results
            
        Returns:
            Dictionary with extraction results
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.logger.info(f"Starting PDF extraction for: {pdf_path}")
        
        # Get access token
        access_token = self.get_access_token()
        
        # Step 1: Upload PDF
        upload_result = self._upload_pdf(pdf_path, access_token)
        asset_id = upload_result['assetID']
        
        # Step 2: Create extraction job
        job_result = self._create_extraction_job(asset_id, access_token)
        location_header = job_result['location']
        
        # Step 3: Poll for completion
        extraction_result = self._poll_extraction_job(location_header, access_token)
        
        # Step 4: Download and process results
        final_results = self._download_and_process_results(extraction_result, output_dir, access_token)
        
        self.logger.info("PDF extraction completed successfully")
        return final_results
    
    def _upload_pdf(self, pdf_path: str, access_token: str) -> Dict[str, Any]:
        """Upload PDF to Adobe"""
        self.logger.info("Uploading PDF to Adobe...")
        
        upload_url = "https://pdf-services.adobe.io/assets"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id
        }
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {
                'file': (os.path.basename(pdf_path), pdf_file, 'application/pdf')
            }
            
            response = requests.post(upload_url, headers=headers, files=files, timeout=120)
        
        if response.status_code != 201:
            raise Exception(f"PDF upload failed: {response.status_code} - {response.text}")
        
        result = response.json()
        self.logger.info(f"PDF uploaded successfully, Asset ID: {result['assetID']}")
        return result
    
    def _create_extraction_job(self, asset_id: str, access_token: str) -> Dict[str, Any]:
        """Create PDF extraction job"""
        self.logger.info("Creating extraction job...")
        
        job_url = "https://pdf-services.adobe.io/operation/extractpdf"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id,
            'Content-Type': 'application/json'
        }
        
        job_data = {
            "assetID": asset_id,
            "elementsToExtract": [
                "text",
                "tables"
            ],
            "elementsToExtractRenditions": [
                "tables",
                "figures"
            ],
            "tableOutputFormat": "csv"
        }
        
        response = requests.post(job_url, headers=headers, json=job_data, timeout=60)
        
        if response.status_code != 202:
            raise Exception(f"Job creation failed: {response.status_code} - {response.text}")
        
        location_header = response.headers.get('location')
        if not location_header:
            raise Exception("No location header received from job creation")
        
        self.logger.info("Extraction job created successfully")
        return {'location': location_header}
    
    def _poll_extraction_job(self, location_url: str, access_token: str, max_attempts: int = 30) -> Dict[str, Any]:
        """Poll extraction job until completion"""
        self.logger.info("Polling for job completion...")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id
        }
        
        for attempt in range(max_attempts):
            response = requests.get(location_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Job polling failed: {response.status_code} - {response.text}")
            
            result = response.json()
            status = result.get('status')
            
            if status == 'done':
                self.logger.info("Extraction job completed successfully")
                return result
            elif status == 'failed':
                error = result.get('error', 'Unknown error')
                raise Exception(f"Extraction job failed: {error}")
            elif status in ['in_progress', 'running']:
                self.logger.info(f"Job in progress... (attempt {attempt + 1}/{max_attempts})")
                import time
                time.sleep(10)  # Wait 10 seconds before next poll
            else:
                self.logger.warning(f"Unknown job status: {status}")
                import time
                time.sleep(5)
        
        raise Exception("Job did not complete within maximum attempts")
    
    def _download_and_process_results(self, extraction_result: Dict[str, Any], output_dir: str, access_token: str) -> Dict[str, Any]:
        """Download and process extraction results"""
        self.logger.info("Downloading and processing results...")
        
        # Get the download URL from extraction result
        content_url = extraction_result.get('asset', {}).get('downloadUri')
        if not content_url:
            raise Exception("No download URL found in extraction result")
        
        # Download the results ZIP file
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id
        }
        
        response = requests.get(content_url, headers=headers, timeout=120)
        
        if response.status_code != 200:
            raise Exception(f"Results download failed: {response.status_code}")
        
        # Save ZIP file
        zip_path = os.path.join(output_dir, "extraction_results.zip")
        with open(zip_path, 'wb') as zip_file:
            zip_file.write(response.content)
        
        # Extract ZIP file
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        # Process extracted files
        results = self._process_extracted_files(output_dir)
        
        # Save summary
        summary_path = os.path.join(output_dir, "extraction_summary.json")
        with open(summary_path, 'w') as summary_file:
            json.dump(results, summary_file, indent=2)
        
        self.logger.info(f"Results saved to: {output_dir}")
        return results
    
    def _process_extracted_files(self, output_dir: str) -> Dict[str, Any]:
        """Process extracted files and create summary"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "extraction_method": "Adobe PDF Services API",
            "summary": {},
            "files": [],
            "tables": [],
            "securities": [],
            "financial_data": []
        }
        
        # Look for structuredData.json
        json_file = os.path.join(output_dir, "structuredData.json")
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                structured_data = json.load(f)
            
            # Process elements
            elements = structured_data.get('elements', [])
            tables = [elem for elem in elements if elem.get('Path', '').endswith('/Table')]
            text_elements = [elem for elem in elements if 'Text' in elem]
            
            results["summary"] = {
                "total_elements": len(elements),
                "tables_found": len(tables),
                "text_elements": len(text_elements),
                "pages": len(set(elem.get('Page', 1) for elem in elements))
            }
            
            # Process tables
            for i, table in enumerate(tables):
                table_info = {
                    "table_number": i + 1,
                    "page": table.get('Page', 1),
                    "bounds": table.get('Bounds', []),
                    "rows": len(table.get('Table', [])),
                    "columns": len(table.get('Table', [{}])[0].keys()) if table.get('Table') else 0
                }
                results["tables"].append(table_info)
            
            # Look for financial keywords in text
            financial_keywords = ['USD', 'EUR', 'CHF', 'ISIN', 'price', 'value', 'quantity', 'shares']
            for elem in text_elements:
                text = elem.get('Text', '').lower()
                if any(keyword.lower() in text for keyword in financial_keywords):
                    results["financial_data"].append({
                        "text": elem.get('Text', ''),
                        "page": elem.get('Page', 1),
                        "bounds": elem.get('Bounds', [])
                    })
        
        # Look for CSV files
        import glob
        csv_files = glob.glob(os.path.join(output_dir, "*.csv"))
        for csv_file in csv_files:
            results["files"].append({
                "filename": os.path.basename(csv_file),
                "type": "csv",
                "path": csv_file
            })
            
            # Try to extract securities data from CSV
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                
                # Look for securities-like data
                for _, row in df.iterrows():
                    row_text = ' '.join(str(val) for val in row.values).upper()
                    if any(keyword in row_text for keyword in ['ISIN', 'US0', 'GB0', 'CH0']):
                        security_data = {
                            "source_file": os.path.basename(csv_file),
                            "data": row.to_dict()
                        }
                        results["securities"].append(security_data)
                        
            except Exception as e:
                self.logger.warning(f"Could not process CSV file {csv_file}: {e}")
        
        return results

def main():
    """Example usage of the real Adobe extractor"""
    
    # Check for credentials
    client_id = os.getenv('ADOBE_CLIENT_ID')
    client_secret = os.getenv('ADOBE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Adobe credentials not found!")
        print("Please set environment variables:")
        print("  ADOBE_CLIENT_ID=your_client_id")
        print("  ADOBE_CLIENT_SECRET=your_client_secret")
        print("\nOr get them from: https://developer.adobe.com/console")
        return
    
    # Look for PDF files
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if not pdf_files:
        print("❌ No PDF files found in current directory")
        print("Please add a PDF file to extract data from")
        return
    
    # Use first PDF file found
    pdf_file = pdf_files[0]
    print(f"📄 Processing PDF: {pdf_file}")
    
    try:
        # Create extractor and process PDF
        extractor = RealAdobeExtractor(client_id, client_secret)
        results = extractor.extract_pdf_data(pdf_file)
        
        print("✅ Extraction completed successfully!")
        print(f"📊 Results summary:")
        print(f"  - Pages processed: {results['summary'].get('pages', 'N/A')}")
        print(f"  - Tables found: {results['summary'].get('tables_found', 0)}")
        print(f"  - Text elements: {results['summary'].get('text_elements', 0)}")
        print(f"  - Securities identified: {len(results['securities'])}")
        print(f"  - Financial data points: {len(results['financial_data'])}")
        
        if results['securities']:
            print("\n🏦 Sample securities found:")
            for i, security in enumerate(results['securities'][:3]):
                print(f"  {i+1}. {security['data']}")
        
        print(f"\n📁 Results saved to: real_extraction_output/")
        print(f"📄 Summary file: real_extraction_output/extraction_summary.json")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return

if __name__ == "__main__":
    main()