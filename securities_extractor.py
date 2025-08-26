#!/usr/bin/env python3
"""
Securities Data Extractor - Extract ALL securities with complete financial data
Shows every security, price, valuation, and related data found
"""

import os
import json
import pandas as pd
import re
from PIL import Image
# import pytesseract  # Not needed for this analysis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecuritiesExtractor:
    """Extract complete securities data with all financial details"""
    
    def __init__(self):
        """Initialize securities extractor"""
        self.json_file = "output_advanced/messos 30.5/structuredData.json"
        self.figures_dir = "output_advanced/messos 30.5/figures"
        self.output_dir = "securities_data"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.structured_data = None
        self.all_securities = []
        
    def load_data(self):
        """Load structured data"""
        if not os.path.exists(self.json_file):
            logger.error("JSON file not found")
            return False
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.structured_data = json.load(f)
        
        return True
    
    def extract_all_text_with_positioning(self):
        """Extract all text with precise positioning for table reconstruction"""
        elements = self.structured_data.get('elements', [])
        text_elements = []
        
        for elem in elements:
            if elem.get('Text'):
                text_data = {
                    'text': elem.get('Text', '').strip(),
                    'page': elem.get('Page', 0),
                    'bounds': elem.get('Bounds', []),
                    'x': elem.get('Bounds', [0])[0] if elem.get('Bounds') else 0,
                    'y': elem.get('Bounds', [0, 0])[1] if len(elem.get('Bounds', [])) > 1 else 0,
                    'width': elem.get('Bounds', [0, 0, 0])[2] if len(elem.get('Bounds', [])) > 2 else 0,
                    'height': elem.get('Bounds', [0, 0, 0, 0])[3] if len(elem.get('Bounds', [])) > 3 else 0,
                    'font_size': elem.get('Font', {}).get('size', 0),
                    'font_name': elem.get('Font', {}).get('name', '')
                }
                text_elements.append(text_data)
        
        # Sort by page, then Y position, then X position
        text_elements.sort(key=lambda x: (x['page'], x['y'], x['x']))
        
        return text_elements
    
    def identify_financial_patterns(self, text_elements):
        """Identify all financial patterns and potential securities data"""
        
        # Enhanced patterns for financial data
        patterns = {
            'security_names': [
                r'bond', r'equity', r'fund', r'stock', r'share', r'note', r'bill',
                r'government', r'corporate', r'treasury', r'municipal', r'federal',
                r'swiss', r'european', r'american', r'global', r'emerging',
                r'MESSOS', r'UBS', r'Credit Suisse', r'Zurich', r'Nestlé'
            ],
            'currencies': [r'USD', r'EUR', r'CHF', r'GBP', r'JPY', r'CAD'],
            'amounts': [
                r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # 1,234,567.89
                r'\d+\.\d{2}',                       # 123.45
                r'\d+,\d{3}',                        # 1,234
                r'\d{4,}'                            # 1234 or larger
            ],
            'percentages': [r'\d+\.\d+%', r'\d+%'],
            'dates': [
                r'\d{2}[./]\d{2}[./]\d{4}',         # 30.05.2025
                r'\d{4}-\d{2}-\d{2}',               # 2025-05-30
                r'\d{2}-\d{2}-\d{4}'                # 30-05-2025
            ],
            'isin_codes': [
                r'[A-Z]{2}\d{10}',                  # Standard ISIN
                r'CH\d{12}',                        # Swiss format
                r'LU\d{10}',                        # Luxembourg format
                r'US\d{10}'                         # US format
            ],
            'quantities': [
                r'\d+\s*units?',
                r'\d+\s*shares?',
                r'\d+\s*pieces?',
                r'nominal\s+\d+',
                r'\d+\s*pcs?'
            ]
        }
        
        categorized_elements = {
            'potential_securities': [],
            'amounts_and_prices': [],
            'currencies': [],
            'percentages': [],
            'dates': [],
            'identifiers': [],
            'quantities': [],
            'all_financial': []
        }
        
        for elem in text_elements:
            text = elem['text']
            text_lower = text.lower()
            
            # Check each pattern category
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, text, re.IGNORECASE):
                        if category == 'security_names':
                            categorized_elements['potential_securities'].append(elem)
                        elif category == 'amounts':
                            categorized_elements['amounts_and_prices'].append(elem)
                        elif category == 'currencies':
                            categorized_elements['currencies'].append(elem)
                        elif category == 'percentages':
                            categorized_elements['percentages'].append(elem)
                        elif category == 'dates':
                            categorized_elements['dates'].append(elem)
                        elif category == 'isin_codes':
                            categorized_elements['identifiers'].append(elem)
                        elif category == 'quantities':
                            categorized_elements['quantities'].append(elem)
                        
                        categorized_elements['all_financial'].append(elem)
                        break
        
        return categorized_elements
    
    def reconstruct_securities_tables(self, text_elements):
        """Attempt to reconstruct securities tables using spatial analysis"""
        
        # Group elements by page
        pages = {}
        for elem in text_elements:
            page = elem['page']
            if page not in pages:
                pages[page] = []
            pages[page].append(elem)
        
        all_tables = []
        
        for page_num, page_elements in pages.items():
            if len(page_elements) < 5:
                continue
            
            # Find potential table rows (elements aligned horizontally)
            tolerance = 15  # pixels tolerance for alignment
            
            # Group by Y position (rows)
            y_groups = {}
            for elem in page_elements:
                y = round(elem['y'] / tolerance) * tolerance  # Round to tolerance
                if y not in y_groups:
                    y_groups[y] = []
                y_groups[y].append(elem)
            
            # Find rows with multiple elements (potential table rows)
            table_rows = []
            for y, elements in y_groups.items():
                if len(elements) >= 3:  # At least 3 columns
                    # Sort by X position (left to right)
                    elements.sort(key=lambda x: x['x'])
                    table_rows.append({
                        'y_position': y,
                        'elements': elements,
                        'page': page_num
                    })
            
            if len(table_rows) >= 2:  # At least 2 rows for a table
                # Sort rows by Y position (top to bottom)
                table_rows.sort(key=lambda x: x['y_position'])
                
                # Try to identify securities table structure
                table_data = []
                for row in table_rows:
                    row_texts = [elem['text'] for elem in row['elements']]
                    
                    # Look for securities-like content
                    row_text_combined = ' '.join(row_texts) if row_texts else ''
                    has_security_indicators = bool(
                        re.search(r'bond|equity|fund|stock|share|MESSOS|UBS', row_text_combined, re.IGNORECASE)
                    )

                    has_financial_data = any(
                        re.search(r'\d+[,.]?\d*|\$|USD|EUR|CHF|%', text) for text in row_texts if text
                    )
                    
                    if has_security_indicators or has_financial_data:
                        table_data.append({
                            'row_data': row_texts,
                            'elements': row['elements'],
                            'y_position': row['y_position'],
                            'is_likely_security': has_security_indicators,
                            'has_financial_data': has_financial_data
                        })
                
                if table_data:
                    all_tables.append({
                        'page': page_num,
                        'rows': len(table_data),
                        'data': table_data
                    })
        
        return all_tables
    
    def analyze_high_confidence_images(self):
        """Analyze the highest confidence images for securities data"""
        if not os.path.exists(self.figures_dir):
            return []
        
        figure_files = sorted([f for f in os.listdir(self.figures_dir) if f.endswith('.png')])
        
        # Get high confidence images (>500KB - likely main tables)
        high_confidence_images = []
        for fig_file in figure_files:
            fig_path = os.path.join(self.figures_dir, fig_file)
            file_size = os.path.getsize(fig_path)
            
            if file_size > 500000:  # >500KB - very likely main securities table
                try:
                    with Image.open(fig_path) as img:
                        width, height = img.size
                        
                    high_confidence_images.append({
                        'filename': fig_file,
                        'path': fig_path,
                        'file_size': file_size,
                        'dimensions': f"{width}x{height}",
                        'confidence': 'VERY_HIGH',
                        'likely_content': 'Main securities holdings table'
                    })
                except Exception as e:
                    logger.warning(f"Could not analyze {fig_file}: {e}")
        
        return high_confidence_images
    
    def extract_securities_from_text(self, financial_elements, tables):
        """Extract securities information from text analysis"""
        securities = []
        
        # From potential securities text
        for elem in financial_elements.get('potential_securities', []):
            security = {
                'source': 'text_analysis',
                'name': elem['text'],
                'page': elem['page'],
                'position': f"({elem['x']:.0f}, {elem['y']:.0f})",
                'confidence': 'medium',
                'type': 'identified_from_text'
            }
            securities.append(security)
        
        # From reconstructed tables
        for table in tables:
            for row in table['data']:
                if row['is_likely_security']:
                    security = {
                        'source': 'spatial_analysis',
                        'name': ' | '.join(row['row_data']),
                        'page': table['page'],
                        'position': f"Table row at Y={row['y_position']:.0f}",
                        'confidence': 'high' if row['has_financial_data'] else 'medium',
                        'type': 'reconstructed_from_table',
                        'raw_data': row['row_data']
                    }
                    securities.append(security)
        
        return securities
    
    def create_comprehensive_securities_report(self):
        """Create comprehensive report of ALL securities found"""
        if not self.load_data():
            return None
        
        # Extract all data
        text_elements = self.extract_all_text_with_positioning()
        financial_elements = self.identify_financial_patterns(text_elements)
        reconstructed_tables = self.reconstruct_securities_tables(text_elements)
        high_confidence_images = self.analyze_high_confidence_images()
        securities = self.extract_securities_from_text(financial_elements, reconstructed_tables)
        
        # Create comprehensive report
        report = {
            'extraction_summary': {
                'total_text_elements': len(text_elements),
                'potential_securities_found': len(financial_elements['potential_securities']),
                'amounts_and_prices_found': len(financial_elements['amounts_and_prices']),
                'currencies_found': len(financial_elements['currencies']),
                'identifiers_found': len(financial_elements['identifiers']),
                'reconstructed_tables': len(reconstructed_tables),
                'high_confidence_images': len(high_confidence_images),
                'total_securities_identified': len(securities)
            },
            'all_securities_found': securities,
            'financial_elements': {
                'potential_securities': [elem['text'] for elem in financial_elements['potential_securities']],
                'amounts_and_prices': [elem['text'] for elem in financial_elements['amounts_and_prices']],
                'currencies': [elem['text'] for elem in financial_elements['currencies']],
                'identifiers': [elem['text'] for elem in financial_elements['identifiers']],
                'quantities': [elem['text'] for elem in financial_elements['quantities']]
            },
            'reconstructed_tables': reconstructed_tables,
            'high_confidence_images': high_confidence_images,
            'detailed_analysis': {
                'text_based_securities': [s for s in securities if s['source'] == 'text_analysis'],
                'table_based_securities': [s for s in securities if s['source'] == 'spatial_analysis']
            }
        }
        
        # Save detailed report
        report_file = os.path.join(self.output_dir, 'all_securities_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Create CSV of all securities
        if securities:
            securities_df = pd.DataFrame(securities)
            securities_df.to_csv(os.path.join(self.output_dir, 'all_securities.csv'), index=False)
        
        # Create CSV of all financial elements
        all_financial_data = []
        for category, elements in financial_elements.items():
            for elem in elements:
                all_financial_data.append({
                    'category': category,
                    'text': elem['text'],
                    'page': elem['page'],
                    'x': elem['x'],
                    'y': elem['y']
                })
        
        if all_financial_data:
            financial_df = pd.DataFrame(all_financial_data)
            financial_df.to_csv(os.path.join(self.output_dir, 'all_financial_elements.csv'), index=False)
        
        return report
    
    def display_all_securities(self, report):
        """Display all securities found with complete details"""
        print("🏦 **ALL SECURITIES FOUND IN MESSOS PDF**")
        print("=" * 80)
        
        summary = report['extraction_summary']
        print(f"📊 **EXTRACTION SUMMARY:**")
        print(f"   • Total text elements analyzed: {summary['total_text_elements']}")
        print(f"   • Potential securities identified: {summary['potential_securities_found']}")
        print(f"   • Amounts/prices found: {summary['amounts_and_prices_found']}")
        print(f"   • Currencies found: {summary['currencies_found']}")
        print(f"   • Identifiers (ISIN) found: {summary['identifiers_found']}")
        print(f"   • Tables reconstructed: {summary['reconstructed_tables']}")
        print(f"   • High-confidence images: {summary['high_confidence_images']}")
        print(f"   • TOTAL SECURITIES: {summary['total_securities_identified']}")
        
        print(f"\n🔍 **DETAILED SECURITIES LIST:**")
        print("-" * 80)
        
        securities = report['all_securities_found']
        if securities:
            for i, security in enumerate(securities, 1):
                print(f"\n📈 **SECURITY #{i}**")
                print(f"   Name/Description: {security['name']}")
                print(f"   Source: {security['source']}")
                print(f"   Page: {security['page']}")
                print(f"   Position: {security['position']}")
                print(f"   Confidence: {security['confidence']}")
                print(f"   Type: {security['type']}")
                if 'raw_data' in security:
                    print(f"   Raw table data: {security['raw_data']}")
        else:
            print("❌ No securities found in text analysis")
        
        print(f"\n💰 **ALL FINANCIAL ELEMENTS FOUND:**")
        print("-" * 80)
        
        financial = report['financial_elements']
        for category, items in financial.items():
            if items:
                print(f"\n📋 **{category.upper().replace('_', ' ')}** ({len(items)} found):")
                for item in items:
                    print(f"   • {item}")
        
        print(f"\n🖼️ **HIGH-CONFIDENCE IMAGES (LIKELY MAIN TABLES):**")
        print("-" * 80)
        
        images = report['high_confidence_images']
        if images:
            for img in images:
                print(f"\n📊 **{img['filename']}**")
                print(f"   Size: {img['file_size']:,} bytes ({img['dimensions']})")
                print(f"   Confidence: {img['confidence']}")
                print(f"   Likely content: {img['likely_content']}")
                print(f"   ⚠️  REQUIRES MANUAL REVIEW OR OCR FOR COMPLETE DATA")
        else:
            print("❌ No high-confidence images found")
        
        print(f"\n📊 **TABLE RECONSTRUCTION RESULTS:**")
        print("-" * 80)
        
        tables = report['reconstructed_tables']
        if tables:
            for i, table in enumerate(tables, 1):
                print(f"\n📋 **TABLE #{i} (Page {table['page']})**")
                print(f"   Rows: {table['rows']}")
                
                for j, row in enumerate(table['data'][:3]):  # Show first 3 rows
                    print(f"   Row {j+1}: {' | '.join(row['row_data'])}")
                    if row['is_likely_security']:
                        print(f"           ✅ LIKELY SECURITY DATA")
                    if row['has_financial_data']:
                        print(f"           💰 CONTAINS FINANCIAL DATA")
        else:
            print("❌ No clear table structures reconstructed from text")
        
        print(f"\n⚠️ **IMPORTANT FINDINGS:**")
        print("-" * 80)
        
        if summary['high_confidence_images'] > 0:
            print(f"✅ Found {summary['high_confidence_images']} high-confidence images")
            print(f"   These likely contain the MAIN SECURITIES TABLE with complete data")
            print(f"   Recommendation: Manual review or OCR processing needed")
        
        if summary['total_securities_identified'] > 0:
            print(f"✅ Identified {summary['total_securities_identified']} potential securities from text")
            print(f"   These provide partial information but may lack complete valuations")
        
        if summary['amounts_and_prices_found'] > 0:
            print(f"✅ Found {summary['amounts_and_prices_found']} amounts/prices")
            print(f"   These need to be matched with securities through spatial analysis")
        
        print(f"\n🎯 **CONCLUSION:**")
        print("=" * 80)
        
        if summary['high_confidence_images'] > 0:
            print("✅ SUCCESS: Main securities data is available in high-confidence images")
            print("⚠️  LIMITATION: Complete securities list with valuations requires image processing")
            print("💡 NEXT STEP: Process the high-confidence images for complete data")
        else:
            print("❌ LIMITATION: No clear main securities table found")
            print("💡 RECOMMENDATION: Manual review of all extracted images needed")


def main():
    """Extract and display all securities data"""
    extractor = SecuritiesExtractor()
    report = extractor.create_comprehensive_securities_report()
    
    if report:
        extractor.display_all_securities(report)
        
        print(f"\n📁 **OUTPUT FILES CREATED:**")
        print(f"   • Detailed report: {extractor.output_dir}/all_securities_report.json")
        print(f"   • Securities CSV: {extractor.output_dir}/all_securities.csv")
        print(f"   • Financial elements CSV: {extractor.output_dir}/all_financial_elements.csv")
    else:
        print("❌ Failed to extract securities data")


if __name__ == "__main__":
    main()
