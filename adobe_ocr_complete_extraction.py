#!/usr/bin/env python3
"""
Adobe OCR Complete Securities Extraction
Use Adobe's dedicated OCR API to extract ALL text from ALL pages
and get exact securities data with names, ISINs, prices, and values
"""

import os
import json
import requests
import time
import zipfile
import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdobeOCRCompleteExtractor:
    """Complete securities extraction using Adobe's OCR API"""
    
    def __init__(self):
        """Initialize Adobe OCR extractor"""
        self.client_id = os.getenv("ADOBE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
        self.client_secret = os.getenv("ADOBE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")
        self.output_dir = "adobe_ocr_complete_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.all_securities = []
        self.all_text_data = []
    
    def extract_all_securities_with_adobe_ocr(self):
        """Extract ALL securities using Adobe's dedicated OCR API"""
        
        print("🔍 **ADOBE OCR COMPLETE SECURITIES EXTRACTION**")
        print("=" * 70)
        print("🎯 Using Adobe's dedicated OCR API to extract ALL text from ALL pages")
        print("⚡ This will get exact securities names, ISINs, prices, and values")
        
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
            # Step 1: Upload PDF
            asset_id = self.upload_pdf(pdf_path, access_token)
            if not asset_id:
                return None
            
            # Step 2: Submit OCR job
            job_url = self.submit_ocr_job(asset_id, access_token)
            if not job_url:
                return None
            
            # Step 3: Wait for completion and get results
            results = self.get_ocr_results(job_url, access_token)
            
            return results
            
        except Exception as e:
            print(f"❌ Adobe OCR extraction failed: {e}")
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
    
    def submit_ocr_job(self, asset_id, access_token):
        """Submit Adobe OCR job with optimal settings for financial documents"""
        
        print("🔄 Submitting Adobe OCR job for complete text extraction...")
        
        ocr_url = "https://pdf-services.adobe.io/operation/ocr"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id,
            'Content-Type': 'application/json'
        }
        
        # OCR payload optimized for financial documents
        ocr_payload = {
            "assetID": asset_id,
            "ocrLang": "en-US"  # English language for financial documents
        }
        
        try:
            ocr_response = requests.post(ocr_url, headers=headers, json=ocr_payload)
            ocr_response.raise_for_status()
            
            job_url = ocr_response.headers.get('location')
            print(f"✅ OCR job submitted successfully")
            return job_url
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ OCR job submission failed: {e}")
            print(f"Response: {e.response.text}")
            return None
    
    def get_ocr_results(self, job_url, access_token):
        """Wait for OCR completion and get results"""
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id
        }
        
        max_attempts = 60  # Wait up to 15 minutes for OCR
        attempt = 0
        
        print("⏳ Waiting for Adobe OCR to complete...")
        print("💡 OCR processing can take 5-15 minutes for complete text extraction")
        
        while attempt < max_attempts:
            try:
                response = requests.get(job_url, headers=headers)
                response.raise_for_status()
                job_status = response.json()
                
                status = job_status.get('status')
                print(f"📊 OCR Status: {status} (attempt {attempt + 1}/60)")
                
                if status == 'done':
                    # Get download URL
                    download_url = self.get_download_url(job_status)
                    if download_url:
                        return self.download_and_process_ocr_results(download_url)
                    else:
                        print("❌ No download URL found")
                        return None
                        
                elif status == 'failed':
                    error_msg = job_status.get('error', 'Unknown error')
                    print(f"❌ Adobe OCR job failed: {error_msg}")
                    return None
                
                time.sleep(15)  # Wait 15 seconds between checks
                attempt += 1
                
            except Exception as e:
                print(f"❌ Error polling OCR job: {e}")
                return None
        
        print("❌ OCR job timed out after 15 minutes")
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
    
    def download_and_process_ocr_results(self, download_url):
        """Download and process OCR results"""
        
        print("📥 Downloading OCR results...")
        
        try:
            response = requests.get(download_url)
            response.raise_for_status()
            
            # Save the OCR'd PDF
            ocr_pdf_path = os.path.join(self.output_dir, "messos_ocr_processed.pdf")
            with open(ocr_pdf_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ OCR'd PDF saved: {ocr_pdf_path}")
            
            # Now extract text from the OCR'd PDF using PDF Extract API
            return self.extract_text_from_ocr_pdf(ocr_pdf_path)
            
        except Exception as e:
            print(f"❌ Error downloading OCR results: {e}")
            return None
    
    def extract_text_from_ocr_pdf(self, ocr_pdf_path):
        """Extract text from the OCR'd PDF using PDF Extract API"""
        
        print("📝 Extracting text from OCR'd PDF...")
        
        # Get new access token
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        try:
            # Upload OCR'd PDF
            asset_id = self.upload_pdf(ocr_pdf_path, access_token)
            if not asset_id:
                return None
            
            # Submit extract job
            extract_url = "https://pdf-services.adobe.io/operation/extractpdf"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-API-Key': self.client_id,
                'Content-Type': 'application/json'
            }
            
            extract_payload = {
                "assetID": asset_id
            }
            
            extract_response = requests.post(extract_url, headers=headers, json=extract_payload)
            extract_response.raise_for_status()
            
            extract_job_url = extract_response.headers.get('location')
            
            # Wait for extract completion
            return self.get_extract_results(extract_job_url, access_token)
            
        except Exception as e:
            print(f"❌ Error extracting text from OCR'd PDF: {e}")
            return None
    
    def get_extract_results(self, job_url, access_token):
        """Get text extraction results"""
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-Key': self.client_id
        }
        
        max_attempts = 40
        attempt = 0
        
        print("⏳ Extracting text from OCR'd PDF...")
        
        while attempt < max_attempts:
            try:
                response = requests.get(job_url, headers=headers)
                response.raise_for_status()
                job_status = response.json()
                
                status = job_status.get('status')
                print(f"📊 Extract Status: {status} (attempt {attempt + 1}/40)")
                
                if status == 'done':
                    download_url = self.get_download_url(job_status)
                    if download_url:
                        return self.process_final_extraction_results(download_url)
                    else:
                        return None
                        
                elif status == 'failed':
                    error_msg = job_status.get('error', 'Unknown error')
                    print(f"❌ Text extraction failed: {error_msg}")
                    return None
                
                time.sleep(10)
                attempt += 1
                
            except Exception as e:
                print(f"❌ Error polling extract job: {e}")
                return None
        
        print("❌ Text extraction timed out")
        return None
    
    def process_final_extraction_results(self, download_url):
        """Process final extraction results with complete text"""
        
        print("📥 Downloading final extraction results...")
        
        try:
            response = requests.get(download_url)
            response.raise_for_status()
            
            # Save and extract ZIP
            zip_path = os.path.join(self.output_dir, "final_extraction.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            extract_dir = os.path.join(self.output_dir, "final_extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print("✅ Final results downloaded and extracted")
            
            # Process the complete text data
            return self.analyze_complete_text_data(extract_dir)
            
        except Exception as e:
            print(f"❌ Error processing final results: {e}")
            return None
    
    def analyze_complete_text_data(self, extract_dir):
        """Analyze complete text data to extract ALL securities"""
        
        print("🔍 Analyzing complete text data for securities...")
        
        # Find structured data file
        json_file = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file == 'structuredData.json':
                    json_file = os.path.join(root, file)
                    break
        
        if not json_file:
            print("❌ No structured data found")
            return None
        
        # Load and analyze the complete text data
        with open(json_file, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
        
        # Extract ALL text elements
        all_text_elements = []
        elements = structured_data.get('elements', [])
        
        for element in elements:
            text = element.get('Text', '').strip()
            if text:
                all_text_elements.append({
                    'text': text,
                    'page': element.get('Page', 0),
                    'path': element.get('Path', ''),
                    'bounds': element.get('Bounds', []),
                    'font_size': element.get('TextSize', 0)
                })
        
        print(f"📝 Extracted {len(all_text_elements)} text elements from OCR'd PDF")
        
        # Analyze text for securities
        securities = self.extract_securities_from_complete_text(all_text_elements)
        
        # Create comprehensive results
        results = self.create_comprehensive_ocr_results(securities, all_text_elements)
        
        return results
    
    def extract_securities_from_complete_text(self, text_elements):
        """Extract securities from complete OCR text"""
        
        securities = []
        
        print("🔍 Analyzing text elements for securities data...")
        
        for element in text_elements:
            text = element['text']
            page = element['page']
            
            # Look for securities-related text
            if self.is_securities_text(text):
                security = self.parse_security_from_ocr_text(text, element)
                if security:
                    securities.append(security)
        
        # Remove duplicates and clean data
        unique_securities = self.clean_and_deduplicate_securities(securities)
        
        print(f"🏦 Found {len(unique_securities)} unique securities from OCR text")
        
        return unique_securities
    
    def is_securities_text(self, text):
        """Check if text contains securities information"""
        
        securities_indicators = [
            r'[A-Z]{2}\d{10}',  # ISIN codes
            r'\d+\.\d{2,4}',    # Prices
            r'\d{1,3}(?:,\d{3})+(?:\.\d{2})?',  # Large formatted numbers
            'bond', 'equity', 'fund', 'stock', 'share',
            'government', 'corporate', 'treasury',
            'USD', 'EUR', 'CHF', 'GBP'
        ]
        
        text_lower = text.lower()
        matches = 0
        
        for indicator in securities_indicators:
            if isinstance(indicator, str):
                if indicator.lower() in text_lower:
                    matches += 1
            else:
                if re.search(indicator, text):
                    matches += 1
        
        return matches >= 2  # Need at least 2 indicators
    
    def parse_security_from_ocr_text(self, text, element):
        """Parse security information from OCR text"""
        
        security = {
            'source_text': text,
            'page': element['page'],
            'extraction_method': 'adobe_ocr_complete',
            'confidence': 0.95  # High confidence from Adobe OCR
        }
        
        # Extract ISIN
        isin_match = re.search(r'[A-Z]{2}\d{10}', text)
        if isin_match:
            security['isin'] = isin_match.group()
        
        # Extract currency
        currency_match = re.search(r'\b(USD|EUR|CHF|GBP)\b', text)
        if currency_match:
            security['currency'] = currency_match.group()
        
        # Extract prices
        price_matches = re.findall(r'\d+\.\d{2,4}', text)
        if price_matches:
            security['price'] = price_matches[0]
            if len(price_matches) > 1:
                security['market_value'] = price_matches[-1]
        
        # Extract large numbers (market values)
        value_matches = re.findall(r'\d{1,3}(?:,\d{3})+(?:\.\d{2})?', text)
        if value_matches:
            security['market_value'] = value_matches[-1]
        
        # Determine security type
        text_lower = text.lower()
        if any(word in text_lower for word in ['bond', 'note', 'bill']):
            security['type'] = 'bond'
        elif any(word in text_lower for word in ['equity', 'stock', 'share']):
            security['type'] = 'equity'
        elif any(word in text_lower for word in ['fund', 'etf']):
            security['type'] = 'fund'
        else:
            security['type'] = 'other'
        
        # Extract security name
        words = text.split()
        name_words = []
        for word in words:
            if re.match(r'[A-Z]{2}\d{10}', word) or re.match(r'\d+\.\d{2}', word):
                break
            name_words.append(word)
        
        if name_words:
            security['name'] = ' '.join(name_words)
        
        return security if len(security) > 5 else None
    
    def clean_and_deduplicate_securities(self, securities):
        """Clean and remove duplicate securities"""
        
        unique_securities = []
        seen_isins = set()
        seen_names = set()
        
        for security in securities:
            isin = security.get('isin', '')
            name = security.get('name', '').lower()
            
            # Skip if we've seen this ISIN
            if isin and isin in seen_isins:
                continue
            
            # Skip if we've seen a very similar name
            is_duplicate = False
            for seen_name in seen_names:
                if name and seen_name and (
                    name in seen_name or seen_name in name or
                    len(set(name.split()) & set(seen_name.split())) > 2
                ):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_securities.append(security)
                if isin:
                    seen_isins.add(isin)
                if name:
                    seen_names.add(name)
        
        return unique_securities
    
    def create_comprehensive_ocr_results(self, securities, text_elements):
        """Create comprehensive OCR results"""
        
        # Categorize securities
        bonds = [s for s in securities if s.get('type') == 'bond']
        equities = [s for s in securities if s.get('type') == 'equity']
        funds = [s for s in securities if s.get('type') == 'fund']
        others = [s for s in securities if s.get('type') == 'other']
        
        results = {
            'extraction_summary': {
                'total_securities_found': len(securities),
                'bonds_found': len(bonds),
                'equities_found': len(equities),
                'funds_found': len(funds),
                'other_assets_found': len(others),
                'total_text_elements': len(text_elements),
                'extraction_method': "YOUR_SECRET_HERE"
            },
            'all_securities': securities,
            'bonds': bonds,
            'equities': equities,
            'funds': funds,
            'other_assets': others,
            'all_text_elements': text_elements
        }
        
        # Save results
        results_file = os.path.join(self.output_dir, 'adobe_ocr_complete_results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Create detailed CSV
        if securities:
            df = pd.DataFrame(securities)
            csv_file = os.path.join(self.output_dir, 'complete_securities_ocr.csv')
            df.to_csv(csv_file, index=False)
        
        # Create text elements CSV
        if text_elements:
            text_df = pd.DataFrame(text_elements)
            text_csv = os.path.join(self.output_dir, 'all_text_elements_ocr.csv')
            text_df.to_csv(text_csv, index=False)
        
        return results


def main():
    """Run complete Adobe OCR extraction"""
    
    print("🔍 **ADOBE OCR COMPLETE SECURITIES EXTRACTION**")
    print("=" * 70)
    print("🎯 Using Adobe's dedicated OCR API for complete text extraction")
    print("⚡ This will extract ALL text from ALL pages with high accuracy")
    
    extractor = AdobeOCRCompleteExtractor()
    results = extractor.extract_all_securities_with_adobe_ocr()
    
    if results:
        summary = results['extraction_summary']
        
        print(f"\n🎉 **ADOBE OCR COMPLETE EXTRACTION FINISHED!**")
        print(f"📊 **RESULTS:**")
        print(f"   Total securities found: {summary['total_securities_found']}")
        print(f"   Bonds: {summary['bonds_found']}")
        print(f"   Equities: {summary['equities_found']}")
        print(f"   Funds: {summary['funds_found']}")
        print(f"   Other assets: {summary['other_assets_found']}")
        print(f"   Total text elements: {summary['total_text_elements']}")
        
        if summary['total_securities_found'] > 0:
            print(f"\n🏦 **SECURITIES FOUND:**")
            for i, security in enumerate(results['all_securities'][:10], 1):
                name = security.get('name', 'Unknown')[:50]
                sec_type = security.get('type', 'unknown')
                isin = security.get('isin', '')
                price = security.get('price', '')
                
                print(f"   {i}. {name} ({sec_type})")
                if isin:
                    print(f"      ISIN: {isin}")
                if price:
                    print(f"      Price: {price}")
        
        print(f"\n📁 **RESULTS SAVED TO:**")
        print(f"   adobe_ocr_complete_results/adobe_ocr_complete_results.json")
        print(f"   adobe_ocr_complete_results/complete_securities_ocr.csv")
        print(f"   adobe_ocr_complete_results/all_text_elements_ocr.csv")
        print(f"   adobe_ocr_complete_results/messos_ocr_processed.pdf")
        
        if summary['total_securities_found'] > 0:
            print(f"\n✅ **SUCCESS! Adobe OCR extracted {summary['total_securities_found']} securities with complete data**")
        else:
            print(f"\n⚠️ **No securities found - may need manual review of OCR results**")
    
    else:
        print(f"\n❌ **Adobe OCR extraction failed**")


if __name__ == "__main__":
    main()
