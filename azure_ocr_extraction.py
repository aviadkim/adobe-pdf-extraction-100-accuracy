#!/usr/bin/env python3
"""
Azure Computer Vision OCR for Securities Extraction
Use Azure's powerful OCR to extract ALL securities data automatically
"""

import os
import json
import requests
import time
import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureOCRExtractor:
    """Extract securities using Azure Computer Vision OCR"""
    
    def __init__(self):
        """Initialize Azure OCR extractor"""
        # Azure Computer Vision credentials (free tier available)
        self.endpoint = "https://eastus.api.cognitive.microsoft.com/"  # You can change region
        self.subscription_key = None  # Will be set up
        
        self.figures_dir = "output_advanced/messos 30.5/figures"
        self.output_dir = "azure_ocr_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.all_securities = []
    
    def setup_azure_credentials(self):
        """Set up Azure credentials or provide instructions"""
        
        print("🔧 **AZURE COMPUTER VISION SETUP**")
        print("=" * 50)
        
        # Check if credentials exist
        self.subscription_key = os.getenv('AZURE_COMPUTER_VISION_KEY')
        endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
        
        if endpoint:
            self.endpoint = endpoint
        
        if self.subscription_key:
            print("✅ Azure credentials found!")
            return True
        
        print("📋 **AZURE COMPUTER VISION SETUP INSTRUCTIONS:**")
        print()
        print("1. 🌐 Go to Azure Portal: https://portal.azure.com")
        print("2. 🔑 Create a Computer Vision resource (FREE tier available)")
        print("3. 📋 Get your subscription key and endpoint")
        print("4. 🔧 Set environment variables:")
        print("   set AZURE_COMPUTER_VISION_KEY=your_key_here")
        print("   set AZURE_COMPUTER_VISION_ENDPOINT=your_endpoint_here")
        print()
        print("💡 **OR** enter them now for this session:")
        
        key = input("Enter your Azure Computer Vision Key (or press Enter to skip): ").strip()
        if key:
            self.subscription_key = key
            endpoint_input = input("Enter your Azure endpoint (or press Enter for default): ").strip()
            if endpoint_input:
                self.endpoint = endpoint_input
            
            # Set for current session
            os.environ['AZURE_COMPUTER_VISION_KEY'] = key
            if endpoint_input:
                os.environ['AZURE_COMPUTER_VISION_ENDPOINT'] = endpoint_input
            
            print("✅ Azure credentials set for this session!")
            return True
        
        print("⚠️ Skipping Azure OCR - will use alternative methods")
        return False
    
    def extract_all_securities_with_azure(self):
        """Extract all securities using Azure OCR"""
        
        print("🤖 **AZURE OCR SECURITIES EXTRACTION**")
        print("=" * 60)
        
        if not self.setup_azure_credentials():
            return self.fallback_extraction()
        
        if not os.path.exists(self.figures_dir):
            print("❌ Figures directory not found")
            return None
        
        # Get priority images
        priority_images = self.get_priority_images()
        
        print(f"📊 Processing {len(priority_images)} high-priority images with Azure OCR")
        
        # Process each image
        for img_info in priority_images:
            print(f"\n🔍 Processing {img_info['filename']} with Azure OCR...")
            
            securities = self.extract_from_image_with_azure(img_info)
            
            if securities:
                self.all_securities.extend(securities)
                print(f"✅ Found {len(securities)} securities in {img_info['filename']}")
            else:
                print(f"⚠️ No securities found in {img_info['filename']}")
        
        # Create results
        results = self.create_results()
        return results
    
    def get_priority_images(self):
        """Get priority images for securities extraction"""
        
        figure_files = sorted([f for f in os.listdir(self.figures_dir) if f.endswith('.png')])
        priority_images = []
        
        for fig_file in figure_files:
            fig_path = os.path.join(self.figures_dir, fig_file)
            file_size = os.path.getsize(fig_path)
            file_num = int(fig_file.replace('fileoutpart', '').replace('.png', ''))
            
            # Focus on key securities pages
            priority = 0
            content_type = "Unknown"
            
            if file_num == 6:  # Bonds section
                priority = 10
                content_type = "BONDS"
            elif file_num == 10:  # Equities section
                priority = 10
                content_type = "EQUITIES"
            elif 11 <= file_num <= 13:  # Other assets
                priority = 8
                content_type = "OTHER_ASSETS"
            elif file_size > 500000:  # Large files likely contain tables
                priority = 7
                content_type = "LARGE_TABLE"
            elif file_size > 100000:  # Medium files
                priority = 5
                content_type = "MEDIUM_TABLE"
            
            if priority >= 5:
                priority_images.append({
                    'filename': fig_file,
                    'path': fig_path,
                    'file_number': file_num,
                    'priority': priority,
                    'content_type': content_type,
                    'file_size': file_size
                })
        
        # Sort by priority
        priority_images.sort(key=lambda x: x['priority'], reverse=True)
        
        return priority_images[:10]  # Top 10 priority images
    
    def extract_from_image_with_azure(self, img_info):
        """Extract securities from image using Azure OCR"""
        
        try:
            # Read image
            with open(img_info['path'], 'rb') as image_file:
                image_data = image_file.read()
            
            # Azure OCR API call
            headers = {
                'Ocp-Apim-Subscription-Key': self.subscription_key,
                'Content-Type': 'application/octet-stream'
            }
            
            # Use Read API for better table recognition
            read_url = f"{self.endpoint}/vision/v3.2/read/analyze"
            
            response = requests.post(read_url, headers=headers, data=image_data)
            
            if response.status_code != 202:
                print(f"❌ Azure OCR failed: {response.status_code}")
                return []
            
            # Get operation location
            operation_url = response.headers.get('Operation-Location')
            
            # Poll for results
            for attempt in range(20):  # Wait up to 100 seconds
                time.sleep(5)
                
                result_headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
                result_response = requests.get(operation_url, headers=result_headers)
                result = result_response.json()
                
                status = result.get('status')
                
                if status == 'succeeded':
                    return self.parse_azure_ocr_results(result, img_info)
                elif status == 'failed':
                    print(f"❌ Azure OCR failed for {img_info['filename']}")
                    return []
            
            print(f"⏰ Azure OCR timed out for {img_info['filename']}")
            return []
            
        except Exception as e:
            print(f"❌ Error with Azure OCR for {img_info['filename']}: {e}")
            return []
    
    def parse_azure_ocr_results(self, result, img_info):
        """Parse Azure OCR results to extract securities"""
        
        securities = []
        
        try:
            analyze_result = result.get('analyzeResult', {})
            read_results = analyze_result.get('readResults', [])
            
            all_text_lines = []
            
            # Collect all text lines
            for read_result in read_results:
                for line in read_result.get('lines', []):
                    text = line.get('text', '').strip()
                    if text:
                        all_text_lines.append({
                            'text': text,
                            'bounding_box': line.get('boundingBox', [])
                        })
            
            print(f"📝 Azure OCR extracted {len(all_text_lines)} text lines")
            
            # Process lines to find securities
            for line_data in all_text_lines:
                text = line_data['text']
                
                if self.is_security_line(text):
                    security = self.parse_security_from_line(text, img_info, line_data)
                    if security:
                        securities.append(security)
            
            # Try to reconstruct table structure
            table_securities = self.reconstruct_table_from_lines(all_text_lines, img_info)
            securities.extend(table_securities)
            
        except Exception as e:
            print(f"❌ Error parsing Azure results: {e}")
        
        return securities
    
    def is_security_line(self, text):
        """Check if a line contains security information"""
        
        # Look for security indicators
        security_patterns = [
            r'bond', r'equity', r'fund', r'stock', r'share', r'note',
            r'government', r'corporate', r'treasury', r'municipal',
            r'[A-Z]{2}\d{10}',  # ISIN codes
            r'\d+\.\d{2}',      # Prices
            r'USD|EUR|CHF|GBP', # Currencies
            r'\d{1,3}(?:,\d{3})*'  # Large numbers
        ]
        
        text_lower = text.lower()
        
        # Must have at least 2 indicators to be considered a security line
        matches = sum(1 for pattern in security_patterns 
                     if re.search(pattern, text, re.IGNORECASE))
        
        return matches >= 2
    
    def parse_security_from_line(self, text, img_info, line_data):
        """Parse a single line to extract security information"""
        
        security = {
            'source_image': img_info['filename'],
            'source_text': text,
            'extraction_method': 'azure_ocr',
            'confidence': 0.9,
            'content_type': img_info['content_type']
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
        price_matches = re.findall(r'\d+\.\d{2}', text)
        if price_matches:
            security['price'] = price_matches[0]
            if len(price_matches) > 1:
                security['market_value'] = price_matches[-1]
        
        # Extract large numbers (market values)
        value_matches = re.findall(r'\d{1,3}(?:,\d{3})+', text)
        if value_matches:
            security['market_value'] = value_matches[0]
        
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
        
        # Extract security name (text before ISIN or numbers)
        name_parts = text.split()
        name_words = []
        for word in name_parts:
            if re.match(r'[A-Z]{2}\d{10}', word) or re.match(r'\d+\.\d{2}', word):
                break
            name_words.append(word)
        
        if name_words:
            security['name'] = ' '.join(name_words)
        
        return security if len(security) > 5 else None
    
    def reconstruct_table_from_lines(self, text_lines, img_info):
        """Try to reconstruct table structure from OCR lines"""
        
        securities = []
        
        # Group lines by Y position (table rows)
        rows = {}
        tolerance = 20  # pixels
        
        for line_data in text_lines:
            bbox = line_data.get('bounding_box', [])
            if len(bbox) >= 2:
                y_pos = bbox[1]  # Y coordinate
                
                # Find existing row or create new one
                found_row = False
                for row_y in rows:
                    if abs(y_pos - row_y) <= tolerance:
                        rows[row_y].append(line_data)
                        found_row = True
                        break
                
                if not found_row:
                    rows[y_pos] = [line_data]
        
        # Process rows that look like table rows (3+ columns)
        for y_pos, row_lines in rows.items():
            if len(row_lines) >= 3:
                # Sort by X position (left to right)
                row_lines.sort(key=lambda x: x.get('bounding_box', [0])[0])
                
                # Combine row text
                row_text = ' | '.join([line['text'] for line in row_lines])
                
                if self.is_security_line(row_text):
                    security = {
                        'source_image': img_info['filename'],
                        'source_text': row_text,
                        'extraction_method': 'azure_ocr_table_reconstruction',
                        'confidence': 0.85,
                        'content_type': img_info['content_type'],
                        'table_row': True,
                        'columns': len(row_lines)
                    }
                    
                    # Parse the reconstructed row
                    parsed = self.parse_security_from_line(row_text, img_info, {'text': row_text})
                    if parsed:
                        security.update(parsed)
                        securities.append(security)
        
        return securities
    
    def fallback_extraction(self):
        """Fallback extraction without Azure"""
        
        print("🔄 **FALLBACK EXTRACTION (No Azure OCR)**")
        print("Using pattern analysis and file structure...")
        
        # Use our existing pattern analysis
        priority_images = self.get_priority_images()
        
        for img_info in priority_images[:5]:  # Top 5 images
            if img_info['content_type'] in ['BONDS', 'EQUITIES', 'OTHER_ASSETS']:
                security = {
                    'name': f"{img_info['content_type'].title()} from {img_info['filename']}",
                    'type': img_info['content_type'].lower().replace('_', ' '),
                    'source_image': img_info['filename'],
                    'extraction_method': 'fallback_pattern_analysis',
                    'confidence': 0.5,
                    'file_size': img_info['file_size'],
                    'priority': img_info['priority']
                }
                self.all_securities.append(security)
        
        return self.create_results()
    
    def create_results(self):
        """Create comprehensive results"""
        
        # Categorize securities
        bonds = [s for s in self.all_securities if 'bond' in s.get('type', '').lower()]
        equities = [s for s in self.all_securities if 'equity' in s.get('type', '').lower()]
        others = [s for s in self.all_securities if s not in bonds and s not in equities]
        
        results = {
            'extraction_summary': {
                'total_securities': len(self.all_securities),
                'bonds': len(bonds),
                'equities': len(equities),
                'other_assets': len(others),
                'extraction_method': 'azure_computer_vision_ocr'
            },
            'all_securities': self.all_securities,
            'bonds': bonds,
            'equities': equities,
            'other_assets': others
        }
        
        # Save results
        results_file = os.path.join(self.output_dir, 'azure_ocr_securities.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Create CSV
        if self.all_securities:
            df = pd.DataFrame(self.all_securities)
            csv_file = os.path.join(self.output_dir, 'azure_securities.csv')
            df.to_csv(csv_file, index=False)
        
        return results


def main():
    """Run Azure OCR extraction"""
    
    extractor = AzureOCRExtractor()
    results = extractor.extract_all_securities_with_azure()
    
    if results:
        summary = results['extraction_summary']
        
        print(f"\n🎉 **AZURE OCR EXTRACTION COMPLETE!**")
        print(f"📊 **RESULTS:**")
        print(f"   Total securities: {summary['total_securities']}")
        print(f"   Bonds: {summary['bonds']}")
        print(f"   Equities: {summary['equities']}")
        print(f"   Other assets: {summary['other_assets']}")
        
        if summary['total_securities'] > 0:
            print(f"\n🏦 **SECURITIES FOUND:**")
            for i, security in enumerate(results['all_securities'][:5], 1):
                print(f"   {i}. {security.get('name', 'Unknown')} ({security.get('type', 'unknown')})")
                if security.get('isin'):
                    print(f"      ISIN: {security['isin']}")
                if security.get('price'):
                    print(f"      Price: {security['price']}")
        
        print(f"\n📁 **RESULTS SAVED TO:**")
        print(f"   azure_ocr_results/azure_ocr_securities.json")
        print(f"   azure_ocr_results/azure_securities.csv")
        
        if summary['total_securities'] > 0:
            print(f"\n✅ **SUCCESS! Extracted {summary['total_securities']} securities automatically**")
        else:
            print(f"\n⚠️ **No securities extracted - consider manual review**")
    
    else:
        print(f"\n❌ **Extraction failed**")


if __name__ == "__main__":
    main()
