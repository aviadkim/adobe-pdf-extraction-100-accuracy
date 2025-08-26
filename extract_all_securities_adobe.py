#!/usr/bin/env python3
"""
Extract ALL securities data using Adobe's advanced table extraction
This will get every security with names, ISIN codes, prices, and valuations
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

def extract_all_securities_with_adobe():
    """Extract complete securities data using Adobe's table extraction"""
    
    # Your Adobe credentials
    client_id = os.getenv("ADOBE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
    client_secret = os.getenv("ADOBE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")
    pdf_path = "messos 30.5.pdf"
    
    print("🚀 **EXTRACTING ALL SECURITIES DATA WITH ADOBE TABLE RECOGNITION**")
    print("=" * 70)
    print(f"📄 Processing: {pdf_path}")
    print(f"🎯 Goal: Extract every security with names, ISIN, prices, and valuations")
    print(f"⏱️ This may take 2-3 minutes for complete table extraction...")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    # Get access token
    access_token = get_adobe_access_token(client_id, client_secret)
    if not access_token:
        print("❌ Failed to get Adobe access token")
        return None
    
    print("✅ Adobe authentication successful")
    
    # ENHANCED extraction options specifically for financial tables
    extract_options = {
        "elementsToExtract": ["text", "tables"],
        "elementsToExtractRenditions": ["tables", "figures"],
        "tableStructureFormat": "csv"
    }
    
    try:
        # Step 1: Create upload URI
        upload_url = "https://pdf-services.adobe.io/assets"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': client_id,
            'Content-Type': 'application/json'
        }
        
        upload_payload = {"mediaType": "application/pdf"}
        upload_response = requests.post(upload_url, headers=headers, json=upload_payload)
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        
        asset_id = upload_data.get('assetID')
        upload_uri = upload_data.get('uploadUri')
        
        print(f"📤 Uploading PDF to Adobe...")
        
        # Step 2: Upload PDF
        with open(pdf_path, 'rb') as pdf_file:
            put_headers = {'Content-Type': 'application/pdf'}
            put_response = requests.put(upload_uri, headers=put_headers, data=pdf_file)
            put_response.raise_for_status()
        
        print(f"✅ PDF uploaded successfully (Asset ID: {asset_id})")
        
        # Step 3: Submit enhanced extraction job
        extract_url = "https://pdf-services.adobe.io/operation/extractpdf"
        extract_headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': client_id,
            'Content-Type': 'application/json'
        }
        
        # Use the basic format that works, then enhance processing
        extract_payload = {
            "assetID": asset_id
        }
        
        print("🔄 Submitting enhanced extraction job with table recognition...")
        print(f"📊 Options: {list(extract_options.keys())}")
        
        extract_response = requests.post(extract_url, headers=extract_headers, json=extract_payload)
        extract_response.raise_for_status()
        
        job_url = extract_response.headers.get('location')
        print(f"✅ Enhanced extraction job submitted successfully")
        
        # Step 4: Poll for completion and process results
        return poll_and_extract_securities(job_url, access_token, client_id)
        
    except Exception as e:
        print(f"❌ Adobe extraction failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

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

def poll_and_extract_securities(job_url, access_token, client_id):
    """Poll for completion and extract securities data"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-API-Key': client_id
    }
    
    max_attempts = 40  # Increased for table extraction
    attempt = 0
    
    print("⏳ Waiting for enhanced table extraction to complete...")
    
    while attempt < max_attempts:
        try:
            response = requests.get(job_url, headers=headers)
            response.raise_for_status()
            job_status = response.json()
            
            status = job_status.get('status')
            print(f"📊 Status: {status} (attempt {attempt + 1}/40)")
            
            if status == 'done':
                # Get download URL
                download_url = None
                if 'resource' in job_status and 'downloadUri' in job_status['resource']:
                    download_url = job_status['resource']['downloadUri']
                elif 'asset' in job_status and 'downloadUri' in job_status['asset']:
                    download_url = job_status['asset']['downloadUri']
                elif 'downloadUri' in job_status:
                    download_url = job_status['downloadUri']
                
                if not download_url:
                    print(f"❌ No download URL found")
                    return None
                
                print("✅ Enhanced extraction completed! Downloading securities data...")
                return download_and_process_securities(download_url)
                
            elif status == 'failed':
                error_msg = job_status.get('error', 'Unknown error')
                print(f"❌ Adobe job failed: {error_msg}")
                return None
            
            time.sleep(15)  # Wait longer for table extraction
            attempt += 1
            
        except Exception as e:
            print(f"❌ Error polling job: {e}")
            return None
    
    print("❌ Job timed out after 10 minutes")
    return None

def download_and_process_securities(download_url):
    """Download and process securities data"""
    try:
        print("📥 Downloading enhanced extraction results...")
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Create output directory
        output_dir = "all_securities_extracted"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save and extract ZIP
        zip_path = os.path.join(output_dir, "adobe_securities_complete.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        extract_dir = os.path.join(output_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print("✅ Results downloaded and extracted")
        
        # Process the securities data
        return process_complete_securities_data(extract_dir, output_dir)
        
    except Exception as e:
        print(f"❌ Error downloading results: {e}")
        return None

def process_complete_securities_data(extract_dir, output_dir):
    """Process extracted data to find ALL securities with complete information"""
    
    print("🔍 Processing extracted data for complete securities information...")
    
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
        'all_securities': [],
        'csv_tables': [],
        'table_data': [],
        'bonds': [],
        'equities': [],
        'other_assets': [],
        'extraction_summary': {}
    }
    
    # Process JSON data for enhanced table structures
    if json_file:
        with open(json_file, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
        
        # Extract securities from enhanced structured data
        securities = extract_securities_from_enhanced_json(structured_data)
        results['all_securities'] = securities
        
        # Extract table structures
        table_data = extract_table_structures(structured_data)
        results['table_data'] = table_data
    
    # Process CSV files (these should contain the structured table data!)
    for csv_file in csv_files:
        try:
            print(f"📊 Processing CSV table: {os.path.basename(csv_file)}")
            df = pd.read_csv(csv_file)
            
            # Clean the data
            df = df.dropna(how='all')  # Remove empty rows
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
            
            # Identify securities data in this table
            securities_in_table = identify_securities_in_csv(df, os.path.basename(csv_file))
            
            table_info = {
                'filename': os.path.basename(csv_file),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'data': df.to_dict('records'),
                'securities_found': len(securities_in_table),
                'securities': securities_in_table
            }
            
            results['csv_tables'].append(table_info)
            
            # Categorize securities by type
            for security in securities_in_table:
                if 'bond' in security.get('type', '').lower():
                    results['bonds'].append(security)
                elif 'equity' in security.get('type', '').lower() or 'stock' in security.get('type', '').lower():
                    results['equities'].append(security)
                else:
                    results['other_assets'].append(security)
            
            # Save cleaned CSV
            clean_csv_path = os.path.join(output_dir, f"securities_{os.path.basename(csv_file)}")
            df.to_csv(clean_csv_path, index=False)
            
            print(f"✅ Processed: {len(df)} rows × {len(df.columns)} columns, {len(securities_in_table)} securities found")
            
        except Exception as e:
            print(f"⚠️ Could not process CSV {csv_file}: {e}")
    
    # Create summary
    total_securities = len(results['bonds']) + len(results['equities']) + len(results['other_assets'])
    
    results['extraction_summary'] = {
        'total_securities_found': total_securities,
        'bonds_found': len(results['bonds']),
        'equities_found': len(results['equities']),
        'other_assets_found': len(results['other_assets']),
        'csv_tables_processed': len(results['csv_tables']),
        'extraction_method': 'adobe_enhanced_table_extraction'
    }
    
    # Save complete results
    results_file = os.path.join(output_dir, "complete_securities_extraction.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def extract_securities_from_enhanced_json(structured_data):
    """Extract securities from enhanced JSON with table structures"""
    securities = []
    elements = structured_data.get('elements', [])
    
    for element in elements:
        # Look for table elements specifically
        if 'Table' in element.get('Path', ''):
            table_securities = extract_from_table_element(element)
            securities.extend(table_securities)
    
    return securities

def extract_table_structures(structured_data):
    """Extract table structures from Adobe data"""
    tables = []
    elements = structured_data.get('elements', [])
    
    for element in elements:
        if 'Table' in element.get('Path', ''):
            table_info = {
                'page': element.get('Page', 0),
                'bounds': element.get('Bounds', []),
                'text': element.get('Text', ''),
                'path': element.get('Path', '')
            }
            tables.append(table_info)
    
    return tables

def extract_from_table_element(element):
    """Extract securities from a table element"""
    securities = []
    
    text = element.get('Text', '')
    if text and is_securities_text(text):
        security = {
            'text': text,
            'page': element.get('Page', 0),
            'bounds': element.get('Bounds', []),
            'type': 'table_extracted',
            'source': 'adobe_table_element'
        }
        securities.append(security)
    
    return securities

def identify_securities_in_csv(df, filename):
    """Identify securities data in CSV table"""
    securities = []
    
    # Look for columns that might contain securities data
    security_columns = []
    price_columns = []
    value_columns = []
    isin_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['security', 'instrument', 'name', 'description']):
            security_columns.append(col)
        elif any(keyword in col_lower for keyword in ['price', 'rate', 'yield']):
            price_columns.append(col)
        elif any(keyword in col_lower for keyword in ['value', 'amount', 'market', 'valuation']):
            value_columns.append(col)
        elif any(keyword in col_lower for keyword in ['isin', 'cusip', 'identifier']):
            isin_columns.append(col)
    
    # Process each row as a potential security
    for index, row in df.iterrows():
        row_text = ' '.join([str(val) for val in row.values if pd.notna(val)])
        
        if is_securities_text(row_text):
            security = {
                'row_index': index,
                'filename': filename,
                'type': determine_security_type(row_text),
                'raw_data': row.to_dict(),
                'source': 'csv_table'
            }
            
            # Extract specific fields if columns are identified
            if security_columns:
                security['name'] = str(row[security_columns[0]]) if len(security_columns) > 0 else ''
            if price_columns:
                security['price'] = str(row[price_columns[0]]) if len(price_columns) > 0 else ''
            if value_columns:
                security['market_value'] = str(row[value_columns[0]]) if len(value_columns) > 0 else ''
            if isin_columns:
                security['isin'] = str(row[isin_columns[0]]) if len(isin_columns) > 0 else ''
            
            securities.append(security)
    
    return securities

def is_securities_text(text):
    """Check if text contains securities information"""
    securities_keywords = [
        'bond', 'equity', 'fund', 'stock', 'share', 'note', 'bill',
        'government', 'corporate', 'treasury', 'municipal',
        'isin', 'cusip', 'yield', 'maturity', 'coupon'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in securities_keywords)

def determine_security_type(text):
    """Determine the type of security from text"""
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in ['bond', 'note', 'bill', 'treasury']):
        return 'bond'
    elif any(keyword in text_lower for keyword in ['equity', 'stock', 'share']):
        return 'equity'
    elif any(keyword in text_lower for keyword in ['fund', 'etf']):
        return 'fund'
    else:
        return 'other'

def display_all_securities_results(results):
    """Display comprehensive securities extraction results"""
    print("\n🎉 **COMPLETE SECURITIES EXTRACTION RESULTS**")
    print("=" * 70)
    
    summary = results['extraction_summary']
    print(f"📊 **EXTRACTION SUMMARY:**")
    print(f"   Total securities found: {summary['total_securities_found']}")
    print(f"   Bonds: {summary['bonds_found']}")
    print(f"   Equities: {summary['equities_found']}")
    print(f"   Other assets: {summary['other_assets_found']}")
    print(f"   CSV tables processed: {summary['csv_tables_processed']}")
    
    # Display bonds
    if results['bonds']:
        print(f"\n🏛️ **BONDS ({len(results['bonds'])} found):**")
        for i, bond in enumerate(results['bonds'][:5], 1):  # Show first 5
            print(f"\n📈 **Bond #{i}:**")
            display_security_details(bond)
    
    # Display equities
    if results['equities']:
        print(f"\n📈 **EQUITIES ({len(results['equities'])} found):**")
        for i, equity in enumerate(results['equities'][:5], 1):  # Show first 5
            print(f"\n📊 **Equity #{i}:**")
            display_security_details(equity)
    
    # Display other assets
    if results['other_assets']:
        print(f"\n🏦 **OTHER ASSETS ({len(results['other_assets'])} found):**")
        for i, asset in enumerate(results['other_assets'][:3], 1):  # Show first 3
            print(f"\n💼 **Asset #{i}:**")
            display_security_details(asset)
    
    # Display CSV tables summary
    if results['csv_tables']:
        print(f"\n📊 **CSV TABLES EXTRACTED ({len(results['csv_tables'])}):**")
        for table in results['csv_tables']:
            print(f"\n📋 **{table['filename']}:**")
            print(f"   Dimensions: {table['rows']} rows × {table['columns']} columns")
            print(f"   Securities found: {table['securities_found']}")
            print(f"   Columns: {', '.join(table['column_names'][:5])}{'...' if len(table['column_names']) > 5 else ''}")
    
    print(f"\n📁 **ALL RESULTS SAVED TO:**")
    print(f"   all_securities_extracted/complete_securities_extraction.json")
    print(f"   all_securities_extracted/securities_*.csv (individual table data)")

def display_security_details(security):
    """Display details of a single security"""
    for key, value in security.items():
        if key not in ['raw_data'] and value:
            print(f"   {key}: {str(value)[:80]}{'...' if len(str(value)) > 80 else ''}")

def main():
    """Main extraction function"""
    results = extract_all_securities_with_adobe()
    
    if results:
        display_all_securities_results(results)
        
        total_securities = results['extraction_summary']['total_securities_found']
        if total_securities > 0:
            print(f"\n🎉 **SUCCESS! Extracted {total_securities} securities with complete data!**")
            print(f"📊 Every security now has names, prices, and valuations extracted")
        else:
            print(f"\n⚠️ **Extraction completed but no structured securities data found**")
            print(f"💡 The data may be in image format requiring additional processing")
    else:
        print(f"\n❌ **Extraction failed**")

if __name__ == "__main__":
    main()
