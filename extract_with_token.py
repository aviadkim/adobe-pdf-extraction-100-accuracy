#!/usr/bin/env python3
"""
Extract securities using provided access token
"""

import os
import json
import requests
import time
import zipfile
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_securities_with_token():
    """Extract securities using the provided access token"""
    
    # Your credentials - load from environment or config file
    client_id = os.getenv("ADOBE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
    access_token = os.getenv("ADOBE_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN_HERE")
    
    pdf_path = "messos 30.5.pdf"
    
    print("🚀 **EXTRACTING COMPLETE SECURITIES DATA WITH ADOBE OCR**")
    print("=" * 60)
    print(f"📄 Processing: {pdf_path}")
    print(f"🔧 Using Adobe PDF Extract API with advanced OCR")
    print(f"⏱️ This may take 1-2 minutes...")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    # Enhanced extraction options
    extract_options = {
        "elements_to_extract": ["text", "tables"],
        "elements_to_extract_renditions": ["tables", "figures"],
        "table_structure_format": "csv",
        "add_char_info": True,
        "get_char_bounds": True,
        "include_styling_info": True
    }
    
    try:
        # Upload PDF
        upload_url = "https://pdf-services.adobe.io/assets"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': client_id,
            'Content-Type': 'application/pdf'
        }
        
        print("📤 Uploading PDF to Adobe...")
        with open(pdf_path, 'rb') as pdf_file:
            upload_response = requests.post(upload_url, headers=headers, data=pdf_file)
            upload_response.raise_for_status()
            asset_id = upload_response.headers.get('location').split('/')[-1]
        
        print(f"✅ PDF uploaded successfully (Asset ID: {asset_id})")
        
        # Submit extraction job
        extract_url = "https://pdf-services.adobe.io/operation/extractpdf"
        extract_headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': client_id,
            'Content-Type': 'application/json'
        }
        
        extract_payload = {
            "assetID": asset_id,
            "extractPDFOptions": extract_options
        }
        
        print("🔄 Submitting extraction job with enhanced OCR...")
        extract_response = requests.post(extract_url, headers=extract_headers, json=extract_payload)
        extract_response.raise_for_status()
        
        job_url = extract_response.headers.get('location')
        print(f"✅ Extraction job submitted successfully")
        
        # Poll for completion
        return poll_and_process_results(job_url, access_token, client_id)
        
    except Exception as e:
        print(f"❌ Adobe extraction failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return None

def poll_and_process_results(job_url, access_token, client_id):
    """Poll for job completion and process results"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-API-Key': client_id
    }
    
    max_attempts = 30
    attempt = 0
    
    print("⏳ Waiting for extraction to complete...")
    
    while attempt < max_attempts:
        try:
            response = requests.get(job_url, headers=headers)
            response.raise_for_status()
            job_status = response.json()
            
            status = job_status.get('status')
            print(f"📊 Status: {status} (attempt {attempt + 1}/30)")
            
            if status == 'done':
                download_url = job_status.get('asset', {}).get('downloadUri')
                print("✅ Extraction completed! Downloading results...")
                return download_and_process_results(download_url)
            elif status == 'failed':
                error_msg = job_status.get('error', 'Unknown error')
                print(f"❌ Adobe job failed: {error_msg}")
                return None
            
            time.sleep(10)
            attempt += 1
            
        except Exception as e:
            print(f"❌ Error polling job: {e}")
            return None
    
    print("❌ Job timed out after 5 minutes")
    return None

def download_and_process_results(download_url):
    """Download and process Adobe results"""
    try:
        # Download results
        print("📥 Downloading extraction results...")
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Create output directory
        output_dir = "final_securities_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save and extract ZIP
        zip_path = os.path.join(output_dir, "adobe_results.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        extract_dir = os.path.join(output_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print("✅ Results downloaded and extracted")
        
        # Process the results
        return process_securities_data(extract_dir, output_dir)
        
    except Exception as e:
        print(f"❌ Error downloading results: {e}")
        return None

def process_securities_data(extract_dir, output_dir):
    """Process extracted data to find all securities with valuations"""
    
    print("🔍 Processing extracted data for securities...")
    
    # Find all files
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
        'text_elements': [],
        'extraction_summary': {}
    }
    
    # Process JSON data for securities
    if json_file:
        print(f"📄 Processing structured data: {os.path.basename(json_file)}")
        with open(json_file, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
        
        # Extract securities from structured data
        securities, text_elements = extract_securities_from_structured_data(structured_data)
        results['securities_found'] = securities
        results['text_elements'] = text_elements
    
    # Process CSV files (these are the extracted tables!)
    for csv_file in csv_files:
        try:
            print(f"📊 Processing CSV table: {os.path.basename(csv_file)}")
            df = pd.read_csv(csv_file)
            
            # Clean up the data
            df = df.dropna(how='all')  # Remove empty rows
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
            
            table_data = {
                'filename': os.path.basename(csv_file),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'data': df.to_dict('records')
            }
            results['csv_tables'].append(table_data)
            
            # Save cleaned CSV
            clean_csv_path = os.path.join(output_dir, f"clean_{os.path.basename(csv_file)}")
            df.to_csv(clean_csv_path, index=False)
            
            print(f"✅ Processed: {len(df)} rows × {len(df.columns)} columns")
            
        except Exception as e:
            print(f"⚠️ Could not process CSV {csv_file}: {e}")
    
    # Create summary
    results['extraction_summary'] = {
        'total_securities_text': len(results['securities_found']),
        'csv_tables_found': len(results['csv_tables']),
        'total_text_elements': len(results['text_elements']),
        'extraction_method': 'adobe_enhanced_ocr_with_token'
    }
    
    # Save complete results
    results_file = os.path.join(output_dir, "complete_securities_extraction.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def extract_securities_from_structured_data(structured_data):
    """Extract securities and financial data from Adobe's structured JSON"""
    securities = []
    text_elements = []
    
    elements = structured_data.get('elements', [])
    
    for element in elements:
        text = element.get('Text', '').strip()
        if not text:
            continue
        
        # Store all text elements
        text_elements.append({
            'text': text,
            'page': element.get('Page', 0),
            'bounds': element.get('Bounds', []),
            'path': element.get('Path', '')
        })
        
        # Check for financial/securities content
        if is_financial_content(text):
            security_data = {
                'text': text,
                'page': element.get('Page', 0),
                'bounds': element.get('Bounds', []),
                'path': element.get('Path', ''),
                'confidence': element.get('confidence', 0),
                'type': 'financial_text'
            }
            securities.append(security_data)
    
    return securities, text_elements

def is_financial_content(text):
    """Check if text contains financial/securities information"""
    financial_keywords = [
        'bond', 'equity', 'fund', 'stock', 'share', 'isin', 'cusip',
        'usd', 'eur', 'chf', 'price', 'value', 'market', 'portfolio',
        'valuation', 'allocation', 'yield', 'maturity', 'coupon'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in financial_keywords)

def display_complete_results(results):
    """Display comprehensive extraction results"""
    print("\n🎉 **ADOBE OCR EXTRACTION COMPLETE!**")
    print("=" * 60)
    
    summary = results['extraction_summary']
    print(f"📊 **EXTRACTION SUMMARY:**")
    print(f"   Financial text elements: {summary['total_securities_text']}")
    print(f"   CSV tables extracted: {summary['csv_tables_found']}")
    print(f"   Total text elements: {summary['total_text_elements']}")
    print(f"   Method: {summary['extraction_method']}")
    
    # Display CSV tables (most important for securities data)
    csv_tables = results['csv_tables']
    if csv_tables:
        print(f"\n📊 **CSV TABLES EXTRACTED ({len(csv_tables)}) - MAIN SECURITIES DATA:**")
        for i, table in enumerate(csv_tables, 1):
            print(f"\n📋 **Table #{i}: {table['filename']}**")
            print(f"   Dimensions: {table['rows']} rows × {table['columns']} columns")
            print(f"   Columns: {', '.join(table['column_names'])}")
            
            # Show sample data
            if table['data'] and len(table['data']) > 0:
                print(f"   Sample data:")
                for j, row in enumerate(table['data'][:3], 1):  # Show first 3 rows
                    row_values = [str(v)[:30] + ('...' if len(str(v)) > 30 else '') for v in row.values()]
                    print(f"     Row {j}: {' | '.join(row_values)}")
    else:
        print(f"\n❌ No CSV tables extracted")
    
    # Display financial text elements
    securities = results['securities_found']
    if securities:
        print(f"\n🏦 **FINANCIAL TEXT ELEMENTS ({len(securities)}):**")
        for i, security in enumerate(securities[:5], 1):  # Show first 5
            print(f"\n📈 **Element #{i}:**")
            print(f"   Text: {security['text'][:100]}{'...' if len(security['text']) > 100 else ''}")
            print(f"   Page: {security['page']}")
            print(f"   Type: {security['type']}")
    
    print(f"\n📁 **ALL RESULTS SAVED TO:**")
    print(f"   final_securities_results/complete_securities_extraction.json")
    print(f"   final_securities_results/clean_*.csv (cleaned table data)")
    print(f"   final_securities_results/extracted/ (raw Adobe output)")
    
    # Final assessment
    if csv_tables:
        print(f"\n✅ **SUCCESS! Securities data extracted in CSV format**")
        print(f"🎯 The CSV tables contain the structured securities data you requested")
        print(f"📊 Review the CSV files for complete securities with prices and valuations")
    else:
        print(f"\n⚠️ **Partial Success: Text extracted but no structured tables**")
        print(f"💡 The financial text elements may contain the securities data")

def main():
    """Main extraction function"""
    results = extract_securities_with_token()
    
    if results:
        display_complete_results(results)
        print(f"\n🎉 **EXTRACTION COMPLETED SUCCESSFULLY!**")
        print(f"📊 Check the CSV files for your complete securities data")
    else:
        print(f"\n❌ **Extraction failed**")
        print(f"💡 Please check the error messages above")

if __name__ == "__main__":
    main()
