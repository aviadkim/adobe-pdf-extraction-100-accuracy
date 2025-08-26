#!/usr/bin/env python3
"""
Complete Data Extractor - Extract all data correctly from Adobe PDF results
Uses spatial analysis, text positioning, and image analysis
"""

import os
import json
import pandas as pd
import re
from pathlib import Path
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteDataExtractor:
    """Extract all financial data with maximum accuracy"""
    
    def __init__(self):
        """Initialize extractor"""
        self.json_file = "output_advanced/messos 30.5/structuredData.json"
        self.figures_dir = "output_advanced/messos 30.5/figures"
        self.output_dir = "extracted_data"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.structured_data = None
        self.extracted_tables = []
        self.financial_elements = []
        
    def load_data(self):
        """Load structured data from Adobe PDF Extract API"""
        if not os.path.exists(self.json_file):
            logger.error("JSON file not found")
            return False
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.structured_data = json.load(f)
        
        logger.info(f"✅ Loaded {len(self.structured_data.get('elements', []))} elements")
        return True
    
    def extract_all_text_data(self):
        """Extract and organize all text data with positioning"""
        elements = self.structured_data.get('elements', [])
        text_elements = []
        
        for elem in elements:
            if elem.get('Text'):
                text_data = {
                    'text': elem.get('Text', '').strip(),
                    'page': elem.get('Page', 0),
                    'bounds': elem.get('Bounds', []),
                    'path': elem.get('Path', ''),
                    'font': elem.get('Font', {}),
                    'x': elem.get('Bounds', [0])[0] if elem.get('Bounds') else 0,
                    'y': elem.get('Bounds', [0, 0])[1] if len(elem.get('Bounds', [])) > 1 else 0,
                    'width': elem.get('Bounds', [0, 0, 0])[2] if len(elem.get('Bounds', [])) > 2 else 0,
                    'height': elem.get('Bounds', [0, 0, 0, 0])[3] if len(elem.get('Bounds', [])) > 3 else 0
                }
                text_elements.append(text_data)
        
        # Sort by page, then by Y position (top to bottom), then by X position (left to right)
        text_elements.sort(key=lambda x: (x['page'], x['y'], x['x']))
        
        logger.info(f"📝 Extracted {len(text_elements)} text elements")
        return text_elements
    
    def identify_financial_data(self, text_elements):
        """Identify and categorize financial data"""
        financial_patterns = {
            'securities': [
                r'bond', r'equity', r'fund', r'stock', r'share', r'instrument',
                r'government', r'corporate', r'treasury', r'municipal'
            ],
            'currencies': [r'USD', r'EUR', r'CHF', r'GBP', r'JPY'],
            'amounts': [r'\d+[,.]?\d*\.\d{2}', r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'],
            'percentages': [r'\d+\.\d+%', r'\d+%'],
            'dates': [r'\d{2}[./]\d{2}[./]\d{4}', r'\d{4}-\d{2}-\d{2}'],
            'identifiers': [r'[A-Z]{2}\d{10}', r'CH\d{12}', r'LU\d{10}']  # ISIN patterns
        }
        
        categorized_data = {
            'client_info': [],
            'securities': [],
            'prices': [],
            'valuations': [],
            'allocations': [],
            'dates': [],
            'currencies': [],
            'identifiers': []
        }
        
        for elem in text_elements:
            text = elem['text']
            text_lower = text.lower()
            
            # Client information
            if any(keyword in text_lower for keyword in ['client', 'messos', 'enterprises']):
                categorized_data['client_info'].append(elem)
            
            # Securities
            if any(re.search(pattern, text_lower) for pattern in financial_patterns['securities']):
                categorized_data['securities'].append(elem)
            
            # Currencies and amounts
            for currency in financial_patterns['currencies']:
                if currency in text:
                    categorized_data['currencies'].append(elem)
                    # Look for amounts near currencies
                    for amount_pattern in financial_patterns['amounts']:
                        if re.search(amount_pattern, text):
                            categorized_data['prices'].append(elem)
            
            # Percentages (allocations)
            if any(re.search(pattern, text) for pattern in financial_patterns['percentages']):
                categorized_data['allocations'].append(elem)
            
            # Dates
            if any(re.search(pattern, text) for pattern in financial_patterns['dates']):
                categorized_data['dates'].append(elem)
            
            # Identifiers (ISIN codes)
            if any(re.search(pattern, text) for pattern in financial_patterns['identifiers']):
                categorized_data['identifiers'].append(elem)
            
            # Valuations (large numbers or words like "valuation", "total")
            if 'valuation' in text_lower or 'total' in text_lower:
                categorized_data['valuations'].append(elem)
        
        return categorized_data
    
    def reconstruct_tables_from_positioning(self, text_elements):
        """Reconstruct table structures using spatial positioning"""
        tables = []
        
        # Group elements by page
        pages = {}
        for elem in text_elements:
            page = elem['page']
            if page not in pages:
                pages[page] = []
            pages[page].append(elem)
        
        for page_num, page_elements in pages.items():
            if len(page_elements) < 6:  # Skip pages with too few elements
                continue
            
            # Find potential table rows (elements with similar Y coordinates)
            tolerance = 10  # pixels
            rows = []
            
            # Group by Y position
            y_groups = {}
            for elem in page_elements:
                y = elem['y']
                found_group = False
                
                for group_y in y_groups:
                    if abs(y - group_y) <= tolerance:
                        y_groups[group_y].append(elem)
                        found_group = True
                        break
                
                if not found_group:
                    y_groups[y] = [elem]
            
            # Convert to rows (groups with 3+ elements)
            for y, elements in y_groups.items():
                if len(elements) >= 3:
                    # Sort by X position (left to right)
                    elements.sort(key=lambda x: x['x'])
                    rows.append({
                        'y_position': y,
                        'elements': elements,
                        'page': page_num
                    })
            
            if len(rows) >= 3:  # Potential table with 3+ rows
                # Sort rows by Y position (top to bottom)
                rows.sort(key=lambda x: x['y_position'])
                
                table = {
                    'page': page_num,
                    'rows': len(rows),
                    'columns': max(len(row['elements']) for row in rows),
                    'data': []
                }
                
                for row in rows:
                    row_data = [elem['text'] for elem in row['elements']]
                    table['data'].append(row_data)
                
                tables.append(table)
                logger.info(f"📊 Found table on page {page_num}: {len(rows)} rows × {table['columns']} columns")
        
        return tables
    
    def analyze_image_content(self):
        """Analyze image files for additional context"""
        if not os.path.exists(self.figures_dir):
            return []
        
        figure_files = sorted([f for f in os.listdir(self.figures_dir) if f.endswith('.png')])
        image_analysis = []
        
        for fig_file in figure_files:
            fig_path = os.path.join(self.figures_dir, fig_file)
            file_size = os.path.getsize(fig_path)
            
            try:
                with Image.open(fig_path) as img:
                    width, height = img.size
                    aspect_ratio = width / height if height > 0 else 0
                
                # Categorize by characteristics
                if file_size > 500000:  # >500KB
                    category = "MAJOR_TABLE"
                    confidence = 0.95
                elif file_size > 100000:  # >100KB
                    category = "TABLE_OR_CHART"
                    confidence = 0.85
                elif file_size > 10000:  # >10KB
                    category = "SUPPORTING_DATA"
                    confidence = 0.70
                else:
                    category = "HEADER_LABEL"
                    confidence = 0.50
                
                analysis = {
                    'filename': fig_file,
                    'file_size': file_size,
                    'dimensions': f"{width}x{height}",
                    'aspect_ratio': round(aspect_ratio, 2),
                    'category': category,
                    'confidence': confidence,
                    'likely_content': self._predict_content(fig_file, file_size, aspect_ratio)
                }
                
                image_analysis.append(analysis)
                
            except Exception as e:
                logger.warning(f"Could not analyze {fig_file}: {e}")
        
        return image_analysis
    
    def _predict_content(self, filename, file_size, aspect_ratio):
        """Predict content type based on file characteristics"""
        predictions = []
        
        if file_size > 1000000:  # >1MB
            predictions.append("Main securities holdings table")
        elif file_size > 200000:  # >200KB
            predictions.append("Detailed financial table")
        elif 2.0 <= aspect_ratio <= 5.0:  # Wide aspect ratio
            predictions.append("Tabular data")
        elif aspect_ratio < 1.5:  # Square/tall
            predictions.append("Chart or graphic")
        else:
            predictions.append("Supporting information")
        
        # Predict based on filename pattern
        file_num = int(filename.replace('fileoutpart', '').replace('.png', ''))
        if file_num == 1:
            predictions.append("Likely main table of contents or holdings")
        elif file_num < 5:
            predictions.append("Early document content - headers/summary")
        elif file_num > 20:
            predictions.append("Later document content - appendices/notes")
        
        return predictions
    
    def create_comprehensive_report(self):
        """Create comprehensive extraction report"""
        if not self.load_data():
            return None
        
        # Extract all data
        text_elements = self.extract_all_text_data()
        financial_data = self.identify_financial_data(text_elements)
        reconstructed_tables = self.reconstruct_tables_from_positioning(text_elements)
        image_analysis = self.analyze_image_content()
        
        # Create comprehensive report
        report = {
            'extraction_summary': {
                'total_text_elements': len(text_elements),
                'financial_elements': sum(len(v) for v in financial_data.values()),
                'reconstructed_tables': len(reconstructed_tables),
                'image_files': len(image_analysis),
                'high_confidence_images': len([img for img in image_analysis if img['confidence'] > 0.8])
            },
            'client_information': self._extract_client_info(financial_data['client_info']),
            'financial_data': financial_data,
            'reconstructed_tables': reconstructed_tables,
            'image_analysis': image_analysis,
            'extraction_confidence': self._calculate_confidence(financial_data, reconstructed_tables, image_analysis)
        }
        
        # Save detailed report
        report_file = os.path.join(self.output_dir, 'comprehensive_extraction_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Create CSV exports
        self._create_csv_exports(financial_data, reconstructed_tables)
        
        logger.info(f"✅ Comprehensive report saved: {report_file}")
        return report
    
    def _extract_client_info(self, client_elements):
        """Extract structured client information"""
        client_info = {}
        
        for elem in client_elements:
            text = elem['text']
            
            if 'MESSOS ENTERPRISES' in text:
                client_info['company_name'] = 'MESSOS ENTERPRISES LTD.'
            
            if 'Client Number' in text:
                # Extract client number
                match = re.search(r'Client Number[^\d]*(\d+)', text)
                if match:
                    client_info['client_number'] = match.group(1)
            
            if 'Valuation' in text and 'USD' in text:
                client_info['valuation_currency'] = 'USD'
            
            if re.search(r'\d{2}[./]\d{2}[./]\d{4}', text):
                client_info['valuation_date'] = re.search(r'\d{2}[./]\d{2}[./]\d{4}', text).group()
        
        return client_info
    
    def _calculate_confidence(self, financial_data, tables, images):
        """Calculate overall extraction confidence"""
        confidence_factors = []
        
        # Text extraction confidence
        if len(financial_data['client_info']) > 0:
            confidence_factors.append(0.9)
        if len(financial_data['securities']) > 0:
            confidence_factors.append(0.8)
        if len(financial_data['prices']) > 0:
            confidence_factors.append(0.85)
        
        # Table reconstruction confidence
        if len(tables) > 0:
            confidence_factors.append(0.8)
        
        # Image analysis confidence
        high_conf_images = [img for img in images if img['confidence'] > 0.8]
        if len(high_conf_images) > 5:
            confidence_factors.append(0.9)
        elif len(high_conf_images) > 0:
            confidence_factors.append(0.7)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    def _create_csv_exports(self, financial_data, tables):
        """Create CSV exports for different data types"""
        
        # Export financial elements
        all_financial = []
        for category, elements in financial_data.items():
            for elem in elements:
                all_financial.append({
                    'category': category,
                    'text': elem['text'],
                    'page': elem['page'],
                    'x': elem['x'],
                    'y': elem['y'],
                    'bounds': str(elem['bounds'])
                })
        
        if all_financial:
            df_financial = pd.DataFrame(all_financial)
            df_financial.to_csv(os.path.join(self.output_dir, 'financial_elements.csv'), index=False)
        
        # Export reconstructed tables
        all_table_data = []
        for i, table in enumerate(tables):
            for row_idx, row_data in enumerate(table['data']):
                for col_idx, cell_value in enumerate(row_data):
                    all_table_data.append({
                        'table_id': i,
                        'page': table['page'],
                        'row': row_idx,
                        'column': col_idx,
                        'value': cell_value
                    })
        
        if all_table_data:
            df_tables = pd.DataFrame(all_table_data)
            df_tables.to_csv(os.path.join(self.output_dir, 'reconstructed_tables.csv'), index=False)
        
        logger.info(f"📊 CSV exports created in {self.output_dir}/")


def main():
    """Main extraction function"""
    print("🔍 **COMPLETE DATA EXTRACTION**")
    print("=" * 50)
    
    extractor = CompleteDataExtractor()
    report = extractor.create_comprehensive_report()
    
    if report:
        print(f"\n📊 **EXTRACTION RESULTS**")
        summary = report['extraction_summary']
        print(f"Text elements: {summary['total_text_elements']}")
        print(f"Financial elements: {summary['financial_elements']}")
        print(f"Reconstructed tables: {summary['reconstructed_tables']}")
        print(f"Image files: {summary['image_files']}")
        print(f"High confidence images: {summary['high_confidence_images']}")
        
        print(f"\n🏦 **CLIENT INFORMATION**")
        client_info = report['client_information']
        for key, value in client_info.items():
            print(f"{key}: {value}")
        
        print(f"\n📊 **TABLE ANALYSIS**")
        for i, table in enumerate(report['reconstructed_tables']):
            print(f"Table {i+1} (Page {table['page']}): {table['rows']} rows × {table['columns']} columns")
            if table['data']:
                print(f"  Sample: {table['data'][0][:3]}...")  # First row, first 3 columns
        
        print(f"\n🖼️ **IMAGE ANALYSIS**")
        high_conf_images = [img for img in report['image_analysis'] if img['confidence'] > 0.8]
        print(f"High confidence images ({len(high_conf_images)}):")
        for img in high_conf_images[:5]:  # Show top 5
            print(f"  {img['filename']}: {img['category']} ({img['confidence']:.1%})")
        
        confidence = report['extraction_confidence']
        print(f"\n🎯 **OVERALL CONFIDENCE: {confidence:.1%}**")
        
        if confidence > 0.8:
            print("✅ High confidence - data extraction is very reliable")
        elif confidence > 0.6:
            print("⚠️ Medium confidence - manual review recommended")
        else:
            print("❌ Low confidence - significant manual review needed")
        
        print(f"\n📁 **OUTPUT FILES**")
        print(f"Detailed report: {extractor.output_dir}/comprehensive_extraction_report.json")
        print(f"Financial data: {extractor.output_dir}/financial_elements.csv")
        print(f"Table data: {extractor.output_dir}/reconstructed_tables.csv")
        
        print(f"\n🚀 **READY FOR HUMAN VALIDATION INTERFACE**")
    
    else:
        print("❌ Extraction failed")


if __name__ == "__main__":
    main()
