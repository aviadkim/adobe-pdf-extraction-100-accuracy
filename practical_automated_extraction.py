#!/usr/bin/env python3
"""
Practical Automated Securities Extraction
Use free OCR.space API to extract securities data automatically
"""

import os
import json
import requests
import pandas as pd
import time
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PracticalAutomatedExtractor:
    """Practical automated extraction using free OCR services"""
    
    def __init__(self):
        """Initialize practical extractor"""
        self.figures_dir = "output_advanced/messos 30.5/figures"
        self.output_dir = "practical_extraction_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # OCR.space API (free tier: 25,000 requests/month)
        self.ocr_api_key = "K87899142388957"  # Free public key
        self.ocr_url = "https://api.ocr.space/parse/image"
        
        self.all_securities = []
        self.extraction_stats = {
            'images_processed': 0,
            'securities_found': 0,
            'text_lines_extracted': 0
        }
    
    def extract_all_securities_automatically(self):
        """Extract all securities automatically using free OCR"""
        
        print("🤖 **PRACTICAL AUTOMATED SECURITIES EXTRACTION**")
        print("=" * 70)
        print("🎯 Using FREE OCR.space API to extract ALL securities automatically")
        print("⚡ Processing high-priority images with table recognition...")
        
        if not os.path.exists(self.figures_dir):
            print("❌ Figures directory not found")
            return None
        
        # Get priority images for securities
        priority_images = self.get_securities_priority_images()
        
        print(f"📊 Found {len(priority_images)} high-priority images for securities extraction")
        
        # Process each image with OCR
        for img_info in priority_images:
            print(f"\n🔍 Processing {img_info['filename']} ({img_info['content_type']})...")
            
            securities = self.extract_securities_from_image_ocr(img_info)
            
            if securities:
                self.all_securities.extend(securities)
                self.extraction_stats['securities_found'] += len(securities)
                print(f"✅ Found {len(securities)} securities in {img_info['filename']}")
            else:
                print(f"⚠️ No securities found in {img_info['filename']}")
            
            self.extraction_stats['images_processed'] += 1
            
            # Small delay to respect API limits
            time.sleep(2)
        
        # Create comprehensive results
        results = self.create_comprehensive_results()
        
        return results
    
    def get_securities_priority_images(self):
        """Get images most likely to contain securities data"""
        
        figure_files = sorted([f for f in os.listdir(self.figures_dir) if f.endswith('.png')])
        priority_images = []
        
        for fig_file in figure_files:
            fig_path = os.path.join(self.figures_dir, fig_file)
            file_size = os.path.getsize(fig_path)
            file_num = int(fig_file.replace('fileoutpart', '').replace('.png', ''))
            
            # Prioritize based on our document analysis
            priority = 0
            content_type = "Unknown"
            expected_securities = 0
            
            if file_num == 6:  # Bonds section
                priority = 10
                content_type = "BONDS_SECTION"
                expected_securities = 5  # Estimate based on typical portfolios
            elif file_num == 10:  # Equities section
                priority = 10
                content_type = "EQUITIES_SECTION"
                expected_securities = 8
            elif file_num == 11:  # Structured products
                priority = 9
                content_type = "STRUCTURED_PRODUCTS"
                expected_securities = 3
            elif file_num == 12:  # Other assets
                priority = 8
                content_type = "OTHER_ASSETS"
                expected_securities = 2
            elif file_num == 13:  # Additional assets
                priority = 8
                content_type = "ADDITIONAL_ASSETS"
                expected_securities = 2
            elif file_num == 1 and file_size > 1000000:  # Large summary
                priority = 7
                content_type = "SUMMARY_TABLE"
                expected_securities = 10
            elif file_size > 500000:  # Large files likely contain detailed tables
                priority = 6
                content_type = "DETAILED_TABLE"
                expected_securities = 3
            
            if priority >= 6:  # Only process medium priority and above
                priority_images.append({
                    'filename': fig_file,
                    'path': fig_path,
                    'file_number': file_num,
                    'file_size': file_size,
                    'size_kb': round(file_size / 1024, 1),
                    'priority': priority,
                    'content_type': content_type,
                    'expected_securities': expected_securities
                })
        
        # Sort by priority (highest first)
        priority_images.sort(key=lambda x: x['priority'], reverse=True)
        
        return priority_images
    
    def extract_securities_from_image_ocr(self, img_info):
        """Extract securities from image using OCR.space API"""
        
        try:
            # Prepare image for OCR
            with open(img_info['path'], 'rb') as image_file:
                
                # OCR.space API parameters
                payload = {
                    'apikey': self.ocr_api_key,
                    'language': 'eng',
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'isTable': True,  # Enable table detection
                    'OCREngine': 2,   # Use advanced OCR engine
                    'scale': True,    # Auto-scale for better recognition
                    'isSearchablePdfHideTextLayer': False
                }
                
                files = {'file': image_file}
                
                # Make OCR request
                response = requests.post(self.ocr_url, files=files, data=payload, timeout=60)
                
                if response.status_code == 200:
                    ocr_result = response.json()
                    
                    if ocr_result.get('IsErroredOnProcessing', False):
                        print(f"❌ OCR processing error: {ocr_result.get('ErrorMessage', 'Unknown error')}")
                        return []
                    
                    # Extract text from OCR result
                    extracted_text = ""
                    parsed_results = ocr_result.get('ParsedResults', [])
                    
                    for result in parsed_results:
                        text = result.get('ParsedText', '')
                        if text:
                            extracted_text += text + "\n"
                    
                    if extracted_text:
                        print(f"📝 OCR extracted {len(extracted_text)} characters of text")
                        self.extraction_stats['text_lines_extracted'] += len(extracted_text.split('\n'))
                        
                        # Parse the extracted text for securities
                        securities = self.parse_text_for_securities(extracted_text, img_info)
                        return securities
                    else:
                        print(f"⚠️ No text extracted from {img_info['filename']}")
                        return []
                
                else:
                    print(f"❌ OCR API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error processing {img_info['filename']}: {e}")
            return []
    
    def parse_text_for_securities(self, text, img_info):
        """Parse extracted text to find securities information"""
        
        securities = []
        lines = text.split('\n')
        
        print(f"🔍 Analyzing {len(lines)} text lines for securities...")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            if len(line) < 10:  # Skip very short lines
                continue
            
            # Check if line contains security information
            if self.is_security_line(line):
                security = self.parse_security_from_line(line, img_info, line_num)
                if security:
                    securities.append(security)
        
        # Try to reconstruct table rows from adjacent lines
        table_securities = self.reconstruct_table_rows(lines, img_info)
        securities.extend(table_securities)
        
        # Remove duplicates
        unique_securities = self.remove_duplicate_securities(securities)
        
        return unique_securities
    
    def is_security_line(self, line):
        """Check if a line contains security information"""
        
        # Security indicators
        security_patterns = [
            r'bond|equity|fund|stock|share|note|bill',  # Security types
            r'government|corporate|treasury|municipal',  # Bond types
            r'[A-Z]{2}\d{10}',  # ISIN codes
            r'\d+\.\d{2,4}',    # Prices with decimals
            r'USD|EUR|CHF|GBP', # Currencies
            r'\d{1,3}(?:,\d{3})+(?:\.\d{2})?',  # Large formatted numbers
            r'maturity|coupon|yield',  # Bond terms
            r'dividend|shares|units'   # Equity terms
        ]
        
        line_lower = line.lower()
        
        # Count matches
        matches = 0
        for pattern in security_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                matches += 1
        
        # Need at least 2 indicators for a security line
        return matches >= 2
    
    def parse_security_from_line(self, line, img_info, line_num):
        """Parse a single line to extract security information"""
        
        security = {
            'source_image': img_info['filename'],
            'source_line': line_num,
            'source_text': line,
            'extraction_method': 'ocr_space_api',
            'confidence': 0.8,
            'content_type': img_info['content_type']
        }
        
        # Extract ISIN code
        isin_match = re.search(r'[A-Z]{2}\d{10}', line)
        if isin_match:
            security['isin'] = isin_match.group()
        
        # Extract currency
        currency_match = re.search(r'\b(USD|EUR|CHF|GBP)\b', line)
        if currency_match:
            security['currency'] = currency_match.group()
        
        # Extract prices (decimal numbers)
        price_matches = re.findall(r'\d+\.\d{2,4}', line)
        if price_matches:
            # First price is usually the unit price
            security['price'] = price_matches[0]
            # Last price might be market value
            if len(price_matches) > 1:
                security['market_value'] = price_matches[-1]
        
        # Extract large numbers (market values)
        value_matches = re.findall(r'\d{1,3}(?:,\d{3})+(?:\.\d{2})?', line)
        if value_matches:
            security['market_value'] = value_matches[-1]  # Usually the last large number
        
        # Determine security type
        line_lower = line.lower()
        if any(word in line_lower for word in ['bond', 'note', 'bill', 'treasury', 'government']):
            security['type'] = 'bond'
        elif any(word in line_lower for word in ['equity', 'stock', 'share']):
            security['type'] = 'equity'
        elif any(word in line_lower for word in ['fund', 'etf']):
            security['type'] = 'fund'
        else:
            security['type'] = 'other'
        
        # Extract security name (text before ISIN or first large number)
        name_parts = line.split()
        name_words = []
        
        for word in name_parts:
            # Stop at ISIN, price, or large number
            if (re.match(r'[A-Z]{2}\d{10}', word) or 
                re.match(r'\d+\.\d{2}', word) or 
                re.match(r'\d{1,3}(?:,\d{3})+', word)):
                break
            name_words.append(word)
        
        if name_words:
            security['name'] = ' '.join(name_words)
        
        # Only return if we extracted meaningful data
        return security if len(security) > 6 else None
    
    def reconstruct_table_rows(self, lines, img_info):
        """Try to reconstruct table rows from multiple lines"""
        
        securities = []
        
        # Look for patterns where security data might be split across lines
        for i in range(len(lines) - 2):
            # Try combining 2-3 adjacent lines
            combined_2 = f"{lines[i]} {lines[i+1]}".strip()
            combined_3 = f"{lines[i]} {lines[i+1]} {lines[i+2]}".strip()
            
            # Check if combined lines form a security
            for combined in [combined_2, combined_3]:
                if self.is_security_line(combined) and len(combined) > 30:
                    security = self.parse_security_from_line(combined, img_info, i)
                    if security:
                        security['extraction_method'] = 'ocr_line_reconstruction'
                        security['confidence'] = 0.7
                        securities.append(security)
                        break
        
        return securities
    
    def remove_duplicate_securities(self, securities):
        """Remove duplicate securities based on similarity"""
        
        unique_securities = []
        seen_names = set()
        seen_isins = set()
        
        for security in securities:
            name = security.get('name', '').lower()
            isin = security.get('isin', '')
            
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
                if name:
                    seen_names.add(name)
                if isin:
                    seen_isins.add(isin)
        
        return unique_securities
    
    def create_comprehensive_results(self):
        """Create comprehensive results with all extracted data"""
        
        # Categorize securities
        bonds = [s for s in self.all_securities if s.get('type') == 'bond']
        equities = [s for s in self.all_securities if s.get('type') == 'equity']
        funds = [s for s in self.all_securities if s.get('type') == 'fund']
        others = [s for s in self.all_securities if s.get('type') == 'other']
        
        results = {
            'extraction_summary': {
                'total_securities_found': len(self.all_securities),
                'bonds_found': len(bonds),
                'equities_found': len(equities),
                'funds_found': len(funds),
                'other_assets_found': len(others),
                'images_processed': self.extraction_stats['images_processed'],
                'text_lines_extracted': self.extraction_stats['text_lines_extracted'],
                'extraction_method': 'ocr_space_api_automated'
            },
            'all_securities': self.all_securities,
            'bonds': bonds,
            'equities': equities,
            'funds': funds,
            'other_assets': others,
            'extraction_stats': self.extraction_stats
        }
        
        # Save results
        results_file = os.path.join(self.output_dir, 'practical_automated_extraction.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Create detailed CSV
        if self.all_securities:
            df = pd.DataFrame(self.all_securities)
            csv_file = os.path.join(self.output_dir, 'extracted_securities_detailed.csv')
            df.to_csv(csv_file, index=False)
            
            # Create summary CSV
            summary_data = []
            for security in self.all_securities:
                summary_data.append({
                    'Name': security.get('name', 'Unknown'),
                    'Type': security.get('type', 'Unknown'),
                    'ISIN': security.get('isin', ''),
                    'Price': security.get('price', ''),
                    'Market_Value': security.get('market_value', ''),
                    'Currency': security.get('currency', ''),
                    'Source_Image': security.get('source_image', ''),
                    'Confidence': security.get('confidence', 0)
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_csv = os.path.join(self.output_dir, 'securities_summary.csv')
            summary_df.to_csv(summary_csv, index=False)
        
        return results


def main():
    """Run practical automated extraction"""
    
    print("🤖 **PRACTICAL AUTOMATED SECURITIES EXTRACTION**")
    print("=" * 70)
    print("🎯 Using FREE OCR.space API to extract ALL securities automatically")
    print("💡 No setup required - works immediately!")
    
    extractor = PracticalAutomatedExtractor()
    results = extractor.extract_all_securities_automatically()
    
    if results:
        summary = results['extraction_summary']
        
        print(f"\n🎉 **PRACTICAL AUTOMATED EXTRACTION COMPLETE!**")
        print(f"📊 **RESULTS:**")
        print(f"   Total securities found: {summary['total_securities_found']}")
        print(f"   Bonds: {summary['bonds_found']}")
        print(f"   Equities: {summary['equities_found']}")
        print(f"   Funds: {summary['funds_found']}")
        print(f"   Other assets: {summary['other_assets_found']}")
        print(f"   Images processed: {summary['images_processed']}")
        print(f"   Text lines extracted: {summary['text_lines_extracted']}")
        
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
        print(f"   practical_extraction_results/practical_automated_extraction.json")
        print(f"   practical_extraction_results/extracted_securities_detailed.csv")
        print(f"   practical_extraction_results/securities_summary.csv")
        
        if summary['total_securities_found'] > 0:
            print(f"\n✅ **SUCCESS! Automatically extracted {summary['total_securities_found']} securities**")
            print(f"🔧 Review the CSV files for complete data")
        else:
            print(f"\n⚠️ **No securities automatically extracted**")
            print(f"💡 The images may need higher resolution or manual processing")
    
    else:
        print(f"\n❌ **Practical extraction failed**")


if __name__ == "__main__":
    main()
