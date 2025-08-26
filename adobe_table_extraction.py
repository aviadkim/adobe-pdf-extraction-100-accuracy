#!/usr/bin/env python3
"""
Adobe Advanced Table Extraction
Use Adobe's Document Intelligence to extract structured table data
"""

import os
import json
import requests
import time
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdobeTableExtractor:
    """Extract structured table data using Adobe's advanced capabilities"""
    
    def __init__(self):
        """Initialize Adobe table extractor"""
        self.client_id = os.getenv("ADOBE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
        self.client_secret = os.getenv("ADOBE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")
        self.output_dir = "adobe_table_extraction"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def extract_tables_from_pdf(self):
        """Extract all tables from PDF using Adobe's table recognition"""
        
        print("📊 **ADOBE ADVANCED TABLE EXTRACTION**")
        print("=" * 60)
        print("🎯 Using Adobe's Document Intelligence for table extraction")
        print("⚡ This should extract structured table data automatically")
        
        pdf_path = "messos 30.5.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            return None
        
        # Get access token
        access_token = self.get_access_token()
        if not access_token:
            print("❌ Failed to get Adobe access token")
            return None
        
        print("✅ Adobe authentication successful")
        
        try:
            # Upload PDF
            asset_id = self.upload_pdf(pdf_path, access_token)
            if not asset_id:
                return None
            
            # Submit table extraction job
            job_url = self.submit_table_extraction_job(asset_id, access_token)
            if not job_url:
                return None
            
            # Wait for completion and get results
            results = self.get_extraction_results(job_url, access_token)
            
            return results
            
        except Exception as e:
            print(f"❌ Adobe table extraction failed: {e}")
            return None
    
    def get_access_token(self):
        """Get Adobe access token"""
        auth_url = "https://ims-na1.adobelogin.com/ims/token/v1"
        auth_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'openid,AdobeID,read_organizations,additional_info.projectedProductContext'
        }
        
        try:
            response = requests.post(auth_url, data=auth_data, timeout=30)
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            return None
    
    def upload_pdf(self, pdf_path, access_token):
        """Upload PDF to Adobe"""
        
        print("📤 Uploading PDF to Adobe...")
        
        # Step 1: Create upload URI
        upload_url = "https://pdf-services.adobe.io/assets"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id,
            'Content-Type': 'application/json'
        }
        
        upload_payload = {"mediaType": "application/pdf"}
        upload_response = requests.post(upload_url, headers=headers, json=upload_payload)
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        
        asset_id = upload_data.get('assetID')
        upload_uri = upload_data.get('uploadUri')
        
        # Step 2: Upload PDF
        with open(pdf_path, 'rb') as pdf_file:
            put_headers = {'Content-Type': 'application/pdf'}
            put_response = requests.put(upload_uri, headers=put_headers, data=pdf_file)
            put_response.raise_for_status()
        
        print(f"✅ PDF uploaded (Asset ID: {asset_id})")
        return asset_id
    
    def submit_table_extraction_job(self, asset_id, access_token):
        """Submit advanced table extraction job"""
        
        print("🔄 Submitting advanced table extraction job...")
        
        extract_url = "https://pdf-services.adobe.io/operation/extractpdf"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id,
            'Content-Type': 'application/json'
        }
        
        # Advanced extraction payload focused on tables
        extract_payload = {
            "assetID": asset_id,
            "extractPDFOptions": {
                "elementsToExtract": ["text", "tables"],
                "elementsToExtractRenditions": ["tables"],
                "tableStructureFormat": "csv",
                "includeStylingInfo": True
            }
        }
        
        try:
            extract_response = requests.post(extract_url, headers=headers, json=extract_payload)
            extract_response.raise_for_status()
            
            job_url = extract_response.headers.get('location')
            print(f"✅ Table extraction job submitted")
            return job_url
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            
            # Try with simpler payload
            print("🔄 Trying with simplified extraction options...")
            
            simple_payload = {
                "assetID": asset_id,
                "extractPDFOptions": {
                    "elementsToExtract": ["text", "tables"]
                }
            }
            
            try:
                extract_response = requests.post(extract_url, headers=headers, json=simple_payload)
                extract_response.raise_for_status()
                job_url = extract_response.headers.get('location')
                print(f"✅ Simplified extraction job submitted")
                return job_url
            except Exception as e2:
                print(f"❌ Simplified extraction also failed: {e2}")
                return None
    
    def get_extraction_results(self, job_url, access_token):
        """Wait for job completion and get results"""
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id
        }
        
        max_attempts = 40
        attempt = 0
        
        print("⏳ Waiting for table extraction to complete...")
        
        while attempt < max_attempts:
            try:
                response = requests.get(job_url, headers=headers)
                response.raise_for_status()
                job_status = response.json()
                
                status = job_status.get('status')
                print(f"📊 Status: {status} (attempt {attempt + 1}/40)")
                
                if status == 'done':
                    # Get download URL
                    download_url = self.get_download_url(job_status)
                    if download_url:
                        return self.download_and_process_tables(download_url)
                    else:
                        print("❌ No download URL found")
                        return None
                        
                elif status == 'failed':
                    error_msg = job_status.get('error', 'Unknown error')
                    print(f"❌ Adobe job failed: {error_msg}")
                    return None
                
                time.sleep(15)
                attempt += 1
                
            except Exception as e:
                print(f"❌ Error polling job: {e}")
                return None
        
        print("❌ Job timed out")
        return None
    
    def get_download_url(self, job_status):
        """Extract download URL from job status"""
        
        # Try different response structures
        if 'resource' in job_status and 'downloadUri' in job_status['resource']:
            return job_status['resource']['downloadUri']
        elif 'asset' in job_status and 'downloadUri' in job_status['asset']:
            return job_status['asset']['downloadUri']
        elif 'downloadUri' in job_status:
            return job_status['downloadUri']
        else:
            print(f"❌ No download URL found in response: {list(job_status.keys())}")
            return None
    
    def download_and_process_tables(self, download_url):
        """Download and process table extraction results"""
        
        print("📥 Downloading table extraction results...")
        
        try:
            response = requests.get(download_url)
            response.raise_for_status()
            
            # Save ZIP file
            import zipfile
            zip_path = os.path.join(self.output_dir, "adobe_tables.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract ZIP
            extract_dir = os.path.join(self.output_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print("✅ Results downloaded and extracted")
            
            # Process the extracted data
            return self.process_table_data(extract_dir)
            
        except Exception as e:
            print(f"❌ Error downloading results: {e}")
            return None
    
    def process_table_data(self, extract_dir):
        """Process extracted table data to find securities"""
        
        print("🔍 Processing extracted table data...")
        
        # Find all files
        json_file = None
        csv_files = []
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file == 'structuredData.json':
                    json_file = os.path.join(root, file)
                elif file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        
        print(f"📄 Found structured data: {json_file is not None}")
        print(f"📊 Found CSV tables: {len(csv_files)}")
        
        results = {
            'securities_found': [],
            'csv_tables': [],
            'table_structures': [],
            'extraction_summary': {}
        }
        
        # Process JSON for table structures
        if json_file:
            with open(json_file, 'r', encoding='utf-8') as f:
                structured_data = json.load(f)
            
            # Extract table structures
            table_structures = self.extract_table_structures(structured_data)
            results['table_structures'] = table_structures
            
            # Extract securities from table elements
            securities = self.extract_securities_from_tables(structured_data)
            results['securities_found'] = securities
        
        # Process CSV files
        for csv_file in csv_files:
            try:
                print(f"📊 Processing CSV: {os.path.basename(csv_file)}")
                df = pd.read_csv(csv_file)
                
                # Clean data
                df = df.dropna(how='all')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # Analyze for securities data
                securities_in_csv = self.analyze_csv_for_securities(df, os.path.basename(csv_file))
                
                table_info = {
                    'filename': os.path.basename(csv_file),
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': list(df.columns),
                    'securities_found': len(securities_in_csv),
                    'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                }
                
                results['csv_tables'].append(table_info)
                results['securities_found'].extend(securities_in_csv)
                
                print(f"✅ CSV processed: {len(df)} rows, {len(securities_in_csv)} securities found")
                
            except Exception as e:
                print(f"⚠️ Error processing CSV {csv_file}: {e}")
        
        # Create summary
        results['extraction_summary'] = {
            'total_securities': len(results['securities_found']),
            'csv_tables_processed': len(results['csv_tables']),
            'table_structures_found': len(results['table_structures']),
            'extraction_method': 'adobe_document_intelligence'
        }
        
        # Save results
        results_file = os.path.join(self.output_dir, 'table_extraction_results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def extract_table_structures(self, structured_data):
        """Extract table structures from Adobe data"""
        
        tables = []
        elements = structured_data.get('elements', [])
        
        for element in elements:
            if 'Table' in element.get('Path', ''):
                table_info = {
                    'page': element.get('Page', 0),
                    'bounds': element.get('Bounds', []),
                    'text': element.get('Text', ''),
                    'path': element.get('Path', ''),
                    'table_data': element.get('Table', {})
                }
                tables.append(table_info)
        
        return tables
    
    def extract_securities_from_tables(self, structured_data):
        """Extract securities from table elements"""
        
        securities = []
        elements = structured_data.get('elements', [])
        
        for element in elements:
            if 'Table' in element.get('Path', ''):
                text = element.get('Text', '')
                if self.is_securities_related(text):
                    security = {
                        'source': 'adobe_table_element',
                        'page': element.get('Page', 0),
                        'text': text,
                        'table_path': element.get('Path', ''),
                        'extraction_method': 'adobe_table_structure'
                    }
                    securities.append(security)
        
        return securities
    
    def analyze_csv_for_securities(self, df, filename):
        """Analyze CSV data for securities information"""
        
        securities = []
        
        # Look for securities-related content in each row
        for index, row in df.iterrows():
            row_text = ' '.join([str(val) for val in row.values if pd.notna(val)])
            
            if self.is_securities_related(row_text):
                security = {
                    'source': f'csv_table_{filename}',
                    'row_index': index,
                    'raw_data': row.to_dict(),
                    'text': row_text,
                    'extraction_method': 'csv_table_analysis'
                }
                securities.append(security)
        
        return securities
    
    def is_securities_related(self, text):
        """Check if text is related to securities"""
        
        securities_keywords = [
            'bond', 'equity', 'fund', 'stock', 'share', 'note', 'bill',
            'government', 'corporate', 'treasury', 'municipal',
            'isin', 'cusip', 'yield', 'maturity', 'coupon',
            'USD', 'EUR', 'CHF', 'price', 'value', 'market'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in securities_keywords)


def main():
    """Run Adobe table extraction"""
    
    extractor = AdobeTableExtractor()
    results = extractor.extract_tables_from_pdf()
    
    if results:
        summary = results['extraction_summary']
        
        print(f"\n🎉 **ADOBE TABLE EXTRACTION COMPLETE!**")
        print(f"📊 **RESULTS:**")
        print(f"   Total securities found: {summary['total_securities']}")
        print(f"   CSV tables processed: {summary['csv_tables_processed']}")
        print(f"   Table structures found: {summary['table_structures_found']}")
        
        # Show CSV tables
        if results['csv_tables']:
            print(f"\n📊 **CSV TABLES EXTRACTED:**")
            for table in results['csv_tables']:
                print(f"   📋 {table['filename']}: {table['rows']} rows × {table['columns']} columns")
                print(f"      Securities found: {table['securities_found']}")
                if table['column_names']:
                    print(f"      Columns: {', '.join(table['column_names'][:5])}{'...' if len(table['column_names']) > 5 else ''}")
        
        # Show securities
        if results['securities_found']:
            print(f"\n🏦 **SECURITIES FOUND ({len(results['securities_found'])}):**")
            for i, security in enumerate(results['securities_found'][:5], 1):
                print(f"   {i}. {security.get('text', 'No text')[:80]}...")
        
        print(f"\n📁 **RESULTS SAVED TO:**")
        print(f"   adobe_table_extraction/table_extraction_results.json")
        
        if summary['total_securities'] > 0:
            print(f"\n✅ **SUCCESS! Found {summary['total_securities']} securities using Adobe table extraction**")
        else:
            print(f"\n⚠️ **No securities found in structured tables**")
            print(f"💡 Securities data may be in image format requiring OCR")
    
    else:
        print(f"\n❌ **Adobe table extraction failed**")


if __name__ == "__main__":
    main()
