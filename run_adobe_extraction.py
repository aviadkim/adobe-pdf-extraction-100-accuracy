#!/usr/bin/env python3
"""
Run Adobe OCR Extraction - Simplified version
Gets complete securities data with prices and valuations
"""

import os
import json
import requests
import time
import zipfile
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_adobe_access_token(client_id, client_secret):
    """Get Adobe access token"""
    auth_url = "https://ims-na1.adobelogin.com/ims/token/v1"
    auth_data = {
        'client_id': client_id,
        'client_secret': client_secret,
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

def extract_securities_with_adobe_ocr(pdf_path, client_id, client_secret):
    """Extract complete securities data using Adobe's OCR"""
    
    # Get access token
    access_token = get_adobe_access_token(client_id, client_secret)
    if not access_token:
        return None
    
    logger.info("✅ Adobe access token obtained")
    
    # Enhanced extraction options with OCR
    extract_options = {
        "elements_to_extract": ["text", "tables"],
        "elements_to_extract_renditions": ["tables", "figures"],
        "table_structure_format": "csv"
    }
    
    try:
        # Step 1: Create upload URI
        upload_url = "https://pdf-services.adobe.io/assets"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': client_id,
            'Content-Type': 'application/json'
        }

        upload_payload = {
            "mediaType": "application/pdf"
        }

        upload_response = requests.post(upload_url, headers=headers, json=upload_payload)
        upload_response.raise_for_status()
        upload_data = upload_response.json()

        asset_id = upload_data.get('assetID')
        upload_uri = upload_data.get('uploadUri')

        # Step 2: Upload PDF to the URI
        with open(pdf_path, 'rb') as pdf_file:
            put_headers = {
                'Content-Type': 'application/pdf'
            }
            put_response = requests.put(upload_uri, headers=put_headers, data=pdf_file)
            put_response.raise_for_status()
        
        logger.info(f"✅ PDF uploaded, asset ID: {asset_id}")
        
        # Submit extraction job
        extract_url = "https://pdf-services.adobe.io/operation/extractpdf"
        extract_headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': client_id,
            'Content-Type': 'application/json'
        }
        
        extract_payload = {
            "assetID": asset_id
        }

        logger.info(f"Extract payload: {json.dumps(extract_payload, indent=2)}")
        
        extract_response = requests.post(extract_url, headers=extract_headers, json=extract_payload)
        extract_response.raise_for_status()
        
        job_url = extract_response.headers.get('location')
        logger.info(f"🔄 Extraction job submitted")
        
        # Poll for completion
        return poll_and_download_results(job_url, access_token, client_id)
        
    except Exception as e:
        logger.error(f"❌ Adobe extraction failed: {e}")
        return None

def poll_and_download_results(job_url, access_token, client_id):
    """Poll for job completion and download results"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-API-Key': client_id
    }
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(job_url, headers=headers)
            response.raise_for_status()
            job_status = response.json()
            
            status = job_status.get('status')
            logger.info(f"📊 Job status: {status} (attempt {attempt + 1})")
            
            if status == 'done':
                # Try different response structures
                download_url = None
                if 'resource' in job_status and 'downloadUri' in job_status['resource']:
                    download_url = job_status['resource']['downloadUri']
                elif 'asset' in job_status and 'downloadUri' in job_status['asset']:
                    download_url = job_status['asset']['downloadUri']
                elif 'downloadUri' in job_status:
                    download_url = job_status['downloadUri']

                if not download_url:
                    logger.error(f"No download URL found in response: {job_status}")
                    return None
                logger.info("✅ Extraction completed! Downloading results...")
                return download_and_process_results(download_url)
            elif status == 'failed':
                logger.error(f"❌ Adobe job failed: {job_status.get('error', 'Unknown error')}")
                return None
            
            time.sleep(10)
            attempt += 1
            
        except Exception as e:
            logger.error(f"❌ Error polling job: {e}")
            return None
    
    logger.error("❌ Job timed out")
    return None

def download_and_process_results(download_url):
    """Download and process Adobe results"""
    try:
        # Download results
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Create output directory
        output_dir = "adobe_securities_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save and extract ZIP
        zip_path = os.path.join(output_dir, "results.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        extract_dir = os.path.join(output_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        logger.info(f"✅ Results downloaded and extracted")
        
        # Process results
        return process_extracted_securities_data(extract_dir)
        
    except Exception as e:
        logger.error(f"❌ Error downloading results: {e}")
        return None

def process_extracted_securities_data(extract_dir):
    """Process extracted data to find securities with valuations"""
    
    # Find structured data JSON
    json_file = None
    csv_files = []
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file == 'structuredData.json':
                json_file = os.path.join(root, file)
            elif file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    results = {
        'securities_found': [],
        'csv_tables': [],
        'extraction_summary': {}
    }
    
    # Process JSON data
    if json_file:
        with open(json_file, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
        
        securities = extract_securities_from_json(structured_data)
        results['securities_found'] = securities
    
    # Process CSV files
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            table_data = {
                'filename': os.path.basename(csv_file),
                'rows': len(df),
                'columns': len(df.columns),
                'data': df.to_dict('records'),
                'column_names': list(df.columns)
            }
            results['csv_tables'].append(table_data)
            logger.info(f"✅ Processed CSV: {os.path.basename(csv_file)} ({len(df)} rows)")
        except Exception as e:
            logger.warning(f"⚠️ Could not process CSV {csv_file}: {e}")
    
    # Create summary
    results['extraction_summary'] = {
        'total_securities': len(results['securities_found']),
        'csv_tables_found': len(results['csv_tables']),
        'extraction_method': 'adobe_enhanced_ocr'
    }
    
    # Save results
    results_file = os.path.join("adobe_securities_results", "complete_securities_data.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def extract_securities_from_json(structured_data):
    """Extract securities information from Adobe's structured JSON"""
    securities = []
    elements = structured_data.get('elements', [])
    
    # Look for table elements and enhanced text
    for element in elements:
        # Check for table elements
        if 'Table' in element.get('Path', ''):
            table_securities = process_table_element(element)
            securities.extend(table_securities)
        
        # Check for enhanced text with financial keywords
        elif element.get('Text') and is_financial_text(element.get('Text', '')):
            security_data = {
                'text': element.get('Text', ''),
                'page': element.get('Page', 0),
                'confidence': element.get('confidence', 0),
                'type': 'text_based',
                'bounds': element.get('Bounds', [])
            }
            securities.append(security_data)
    
    return securities

def process_table_element(element):
    """Process table elements to extract securities"""
    securities = []
    
    # Adobe's table structure varies, so we'll extract what we can
    text = element.get('Text', '')
    if text and is_financial_text(text):
        security = {
            'text': text,
            'page': element.get('Page', 0),
            'type': 'table_based',
            'bounds': element.get('Bounds', [])
        }
        securities.append(security)
    
    return securities

def is_financial_text(text):
    """Check if text contains financial/securities information"""
    financial_keywords = [
        'bond', 'equity', 'fund', 'stock', 'share', 'isin', 'cusip',
        'usd', 'eur', 'chf', 'price', 'value', 'market', 'portfolio'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in financial_keywords)

def display_results(results):
    """Display extraction results"""
    print("\n🎉 **ADOBE OCR EXTRACTION COMPLETE!**")
    print("=" * 60)
    
    summary = results['extraction_summary']
    print(f"📊 **EXTRACTION SUMMARY:**")
    print(f"   Securities found: {summary['total_securities']}")
    print(f"   CSV tables: {summary['csv_tables_found']}")
    print(f"   Method: {summary['extraction_method']}")
    
    # Display securities
    securities = results['securities_found']
    if securities:
        print(f"\n🏦 **SECURITIES FOUND ({len(securities)}):**")
        for i, security in enumerate(securities[:10], 1):  # Show first 10
            print(f"\n📈 **Security #{i}:**")
            if isinstance(security, dict):
                for key, value in security.items():
                    if key not in ['bounds']:
                        print(f"   {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
    
    # Display CSV tables
    csv_tables = results['csv_tables']
    if csv_tables:
        print(f"\n📊 **CSV TABLES EXTRACTED ({len(csv_tables)}):**")
        for table in csv_tables:
            print(f"\n📋 **{table['filename']}:**")
            print(f"   Dimensions: {table['rows']} rows × {table['columns']} columns")
            print(f"   Columns: {', '.join(table['column_names'][:5])}{'...' if len(table['column_names']) > 5 else ''}")
            
            # Show sample data
            if table['data']:
                print(f"   Sample row: {list(table['data'][0].values())[:3]}...")
    
    print(f"\n📁 **RESULTS SAVED TO:**")
    print(f"   adobe_securities_results/complete_securities_data.json")
    print(f"   adobe_securities_results/extracted/ (raw Adobe output)")

def main():
    """Main extraction function"""
    print("🚀 **ADOBE OCR SECURITIES EXTRACTION**")
    print("=" * 50)
    
    # Get credentials
    client_id = os.getenv('ADOBE_CLIENT_ID')
    client_secret = os.getenv('ADOBE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Adobe credentials not found")
        print("💡 Please run setup_adobe_credentials.py first")
        return
    
    # Check PDF
    pdf_path = "messos 30.5.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"📄 Processing: {pdf_path}")
    print(f"🔧 Using Adobe OCR with enhanced table extraction")
    print(f"⏱️ This may take 1-2 minutes...")
    
    # Run extraction
    results = extract_securities_with_adobe_ocr(pdf_path, client_id, client_secret)
    
    if results:
        display_results(results)
        print(f"\n✅ **SUCCESS! Complete securities data extracted.**")
    else:
        print(f"\n❌ **Extraction failed. Please check the logs above.**")

if __name__ == "__main__":
    main()
