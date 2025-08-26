#!/usr/bin/env python3
"""
HONEST EXTRACTION: Get REAL financial data from Adobe's table structure
This will extract the actual market values, performance, and prices from the PDF tables
"""

import os
import json
import pandas as pd
import re
from collections import defaultdict

class RealFinancialDataExtractor:
    """Extract REAL financial data from Adobe's table structure"""
    
    def __init__(self):
        self.extract_dir = "adobe_ocr_complete_results/final_extracted"
        self.structured_data_file = None
        self.find_structured_data_file()
    
    def find_structured_data_file(self):
        """Find the structured data JSON file"""
        for root, dirs, files in os.walk(self.extract_dir):
            for file in files:
                if file == 'structuredData.json':
                    self.structured_data_file = os.path.join(root, file)
                    break
        
        if not self.structured_data_file:
            print("❌ No structured data file found")
            return False
        
        print(f"✅ Found structured data: {self.structured_data_file}")
        return True
    
    def extract_real_table_data(self):
        """Extract REAL financial data from table structures"""
        
        print("🔍 **EXTRACTING REAL FINANCIAL DATA FROM TABLES**")
        print("=" * 60)
        
        if not self.structured_data_file:
            print("❌ No structured data file available")
            return None
        
        # Load the structured data
        with open(self.structured_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract table elements
        tables = self.extract_table_elements(data)
        
        # Parse securities tables
        securities_data = self.parse_securities_tables(tables)
        
        # Extract portfolio summary
        portfolio_summary = self.extract_portfolio_summary(data)
        
        return {
            'securities': securities_data,
            'portfolio_summary': portfolio_summary,
            'extraction_method': 'real_table_parsing'
        }
    
    def extract_table_elements(self, data):
        """Extract all table elements from structured data"""
        
        tables = []
        elements = data.get('elements', [])
        
        for element in elements:
            if 'Table' in element.get('Path', ''):
                tables.append({
                    'text': element.get('Text', '').strip(),
                    'page': element.get('Page', 0),
                    'path': element.get('Path', ''),
                    'bounds': element.get('Bounds', []),
                    'font_size': element.get('TextSize', 0)
                })
        
        print(f"📊 Found {len(tables)} table elements")
        return tables
    
    def parse_securities_tables(self, tables):
        """Parse securities tables to extract real financial data"""
        
        print("🔍 Parsing securities tables for real financial data...")
        
        # Group table elements by page and table
        tables_by_page = defaultdict(lambda: defaultdict(list))
        
        for table in tables:
            page = table['page']
            # Extract table number from path
            table_match = re.search(r'Table\[(\d+)\]', table['path'])
            table_num = table_match.group(1) if table_match else '0'
            
            tables_by_page[page][table_num].append(table)
        
        securities = []
        
        # Process each page's tables
        for page, page_tables in tables_by_page.items():
            print(f"📄 Processing page {page} tables...")
            
            for table_num, table_elements in page_tables.items():
                # Sort elements by position (top to bottom, left to right)
                table_elements.sort(key=lambda x: (x['bounds'][1] if x['bounds'] else 0, x['bounds'][0] if x['bounds'] else 0))
                
                # Parse this table for securities
                table_securities = self.parse_single_table(table_elements, page, table_num)
                securities.extend(table_securities)
        
        print(f"🏦 Extracted {len(securities)} securities with real data")
        return securities
    
    def parse_single_table(self, table_elements, page, table_num):
        """Parse a single table to extract securities data"""
        
        securities = []
        current_security = None
        
        for element in table_elements:
            text = element['text']
            
            # Check if this is a security name
            if self.is_security_name(text):
                # Save previous security if exists
                if current_security and self.is_complete_security(current_security):
                    securities.append(current_security)
                
                # Start new security
                current_security = {
                    'name': text,
                    'page': page,
                    'table': table_num,
                    'extraction_method': 'real_table_parsing'
                }
            
            elif current_security:
                # Try to extract financial data for current security
                self.extract_financial_data_from_text(text, current_security)
        
        # Don't forget the last security
        if current_security and self.is_complete_security(current_security):
            securities.append(current_security)
        
        return securities
    
    def is_security_name(self, text):
        """Check if text is a security name"""
        
        # Look for patterns that indicate security names
        security_patterns = [
            r'NATIXIS.*NOTES',
            r'NOVUS CAPITAL.*NOTES',
            r'EXIGENT.*FUND',
            r'GOLDMAN SACHS.*NOTES',
            r'BANK OF AMERICA.*NOTES',
            r'JPMORGAN.*NOTES',
            r'CITIGROUP.*NOTES',
            r'WELLS FARGO.*NOTES',
            r'DEUTSCHE BANK.*NOTES',
            r'.*NOTES.*\d{2}-\d{2}\.\d{2}\.\d{2,4}',  # Notes with dates
            r'.*FUND.*LTD',
            r'.*STRUCTURED.*NOTES'
        ]
        
        for pattern in security_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def extract_financial_data_from_text(self, text, security):
        """Extract financial data from text and add to security"""
        
        # Extract ISIN
        isin_match = re.search(r'ISIN:\s*([A-Z]{2}\d{10})', text)
        if isin_match:
            security['isin'] = isin_match.group(1)
        
        # Extract Valorn
        valorn_match = re.search(r'Valorn\.?:\s*(\d+)', text)
        if valorn_match:
            security['valorn'] = valorn_match.group(1)
        
        # Extract maturity date
        maturity_match = re.search(r'Maturity:\s*(\d{2}\.\d{2}\.\d{4})', text)
        if maturity_match:
            security['maturity'] = maturity_match.group(1)
        
        # Extract quantities (look for large numbers)
        quantity_matches = re.findall(r"(\d{1,3}(?:'?\d{3})*(?:\.\d+)?)", text)
        for match in quantity_matches:
            # Clean the number
            clean_number = match.replace("'", "").replace(",", "")
            try:
                num_value = float(clean_number)
                if num_value >= 1000:  # Likely a quantity or market value
                    if 'quantity' not in security:
                        security['quantity'] = clean_number
                    elif 'market_value' not in security:
                        security['market_value'] = clean_number
            except ValueError:
                continue
        
        # Extract percentages (performance data)
        percentage_matches = re.findall(r'(-?\d+\.\d+)%', text)
        for match in percentage_matches:
            if 'performance' not in security:
                security['performance'] = f"{match}%"
        
        # Extract prices
        price_matches = re.findall(r'(\d+\.\d{2,6})', text)
        for match in price_matches:
            try:
                price_value = float(match)
                if 50 <= price_value <= 200:  # Likely a price
                    if 'price' not in security:
                        security['price'] = match
            except ValueError:
                continue
        
        # Extract currency
        currency_match = re.search(r'\b(USD|EUR|CHF|GBP)\b', text)
        if currency_match:
            security['currency'] = currency_match.group(1)
    
    def is_complete_security(self, security):
        """Check if security has enough data to be considered complete"""
        
        required_fields = ['name']
        optional_fields = ['isin', 'quantity', 'market_value', 'price']
        
        # Must have name
        if not all(field in security for field in required_fields):
            return False
        
        # Must have at least one optional field
        if not any(field in security for field in optional_fields):
            return False
        
        return True
    
    def extract_portfolio_summary(self, data):
        """Extract real portfolio summary data"""
        
        print("📊 Extracting real portfolio summary...")
        
        summary = {}
        elements = data.get('elements', [])
        
        for element in elements:
            text = element.get('Text', '').strip()
            
            # Look for total portfolio value
            total_match = re.search(r'Total.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
            if total_match:
                summary['total_value'] = total_match.group(1)
            
            # Look for asset allocation percentages
            allocation_match = re.search(r'(\w+).*?(\d+\.\d{2})%', text)
            if allocation_match:
                asset_type = allocation_match.group(1)
                percentage = allocation_match.group(2)
                if 'asset_allocation' not in summary:
                    summary['asset_allocation'] = {}
                summary['asset_allocation'][asset_type] = f"{percentage}%"
        
        return summary
    
    def save_real_results(self, results):
        """Save the real extracted results"""
        
        output_dir = "real_financial_data_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON results
        json_file = os.path.join(output_dir, 'real_financial_data.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save CSV of securities
        if results['securities']:
            df = pd.DataFrame(results['securities'])
            csv_file = os.path.join(output_dir, 'real_securities_data.csv')
            df.to_csv(csv_file, index=False)
            
            print(f"✅ Real results saved:")
            print(f"   📄 {json_file}")
            print(f"   📊 {csv_file}")
        
        return results
    
    def display_real_results(self, results):
        """Display the real extracted results"""
        
        print("\n🎯 **REAL FINANCIAL DATA EXTRACTED:**")
        print("=" * 50)
        
        securities = results['securities']
        
        if not securities:
            print("❌ No complete securities data found")
            return
        
        print(f"📊 Found {len(securities)} securities with real data:")
        
        for i, security in enumerate(securities, 1):
            print(f"\n{i}. **{security['name'][:60]}**")
            
            if 'isin' in security:
                print(f"   ISIN: {security['isin']}")
            
            if 'quantity' in security:
                print(f"   Quantity: {security['quantity']}")
            
            if 'market_value' in security:
                print(f"   Market Value: {security['market_value']}")
            
            if 'price' in security:
                print(f"   Price: {security['price']}")
            
            if 'performance' in security:
                print(f"   Performance: {security['performance']}")
            
            if 'maturity' in security:
                print(f"   Maturity: {security['maturity']}")
        
        # Display portfolio summary
        if results['portfolio_summary']:
            print(f"\n💰 **PORTFOLIO SUMMARY:**")
            summary = results['portfolio_summary']
            
            if 'total_value' in summary:
                print(f"   Total Value: {summary['total_value']}")
            
            if 'asset_allocation' in summary:
                print(f"   Asset Allocation:")
                for asset, percentage in summary['asset_allocation'].items():
                    print(f"     {asset}: {percentage}")


def main():
    """Extract real financial data from Adobe's table structure"""
    
    print("🔍 **EXTRACTING REAL FINANCIAL DATA FROM PDF TABLES**")
    print("=" * 60)
    print("🎯 This will extract the ACTUAL market values, prices, and performance")
    print("📊 Using Adobe's table structure data (no estimates!)")
    
    extractor = RealFinancialDataExtractor()
    
    if not extractor.structured_data_file:
        print("❌ No Adobe extraction results found")
        print("💡 Run the Adobe OCR extraction first")
        return
    
    # Extract real data
    results = extractor.extract_real_table_data()
    
    if results:
        # Save results
        extractor.save_real_results(results)
        
        # Display results
        extractor.display_real_results(results)
        
        print(f"\n✅ **REAL DATA EXTRACTION COMPLETE**")
        print(f"📁 Results saved to: real_financial_data_results/")
    else:
        print(f"❌ Failed to extract real financial data")


if __name__ == "__main__":
    main()
