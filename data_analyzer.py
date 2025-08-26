#!/usr/bin/env python3
"""
Comprehensive Data Analyzer for Adobe PDF Extract API Results
Shows all extracted data and analyzes table structure for financial accuracy
"""

import os
import json
import pandas as pd
from pathlib import Path
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialDataAnalyzer:
    """Analyze extracted financial data for accuracy and structure"""
    
    def __init__(self, extraction_dir: str):
        """
        Initialize analyzer
        
        Args:
            extraction_dir: Directory containing extraction results
        """
        self.extraction_dir = extraction_dir
        self.json_file = None
        self.figures_dir = None
        self.structured_data = None
        self._find_files()
    
    def _find_files(self):
        """Find JSON and figures directory"""
        for root, dirs, files in os.walk(self.extraction_dir):
            for file in files:
                if file == 'structuredData.json':
                    self.json_file = os.path.join(root, file)
            for dir_name in dirs:
                if dir_name == 'figures':
                    self.figures_dir = os.path.join(root, dir_name)
    
    def load_structured_data(self):
        """Load and parse the structured JSON data"""
        if not self.json_file:
            logger.error("No structuredData.json found")
            return False
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.structured_data = json.load(f)
            logger.info(f"✅ Loaded structured data from {self.json_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading JSON: {e}")
            return False
    
    def analyze_all_data(self):
        """Comprehensive analysis of all extracted data"""
        print("🔍 **COMPREHENSIVE FINANCIAL DATA ANALYSIS**")
        print("=" * 60)
        
        if not self.load_structured_data():
            return
        
        # 1. Document Overview
        self._analyze_document_overview()
        
        # 2. Text Elements Analysis
        self._analyze_text_elements()
        
        # 3. Figure Analysis
        self._analyze_figures()
        
        # 4. Financial Data Extraction
        self._extract_financial_data()
        
        # 5. Table Structure Analysis
        self._analyze_table_structures()
        
        # 6. OCR Feasibility Assessment
        self._assess_ocr_feasibility()
    
    def _analyze_document_overview(self):
        """Analyze document metadata and structure"""
        print("\n📄 **DOCUMENT OVERVIEW**")
        print("-" * 30)
        
        # Basic document info
        elements = self.structured_data.get('elements', [])
        pages = self.structured_data.get('pages', [])
        
        print(f"📊 Total elements: {len(elements)}")
        print(f"📄 Total pages: {len(pages)}")
        
        # Element types
        element_types = {}
        for element in elements:
            path = element.get('Path', 'Unknown')
            element_types[path] = element_types.get(path, 0) + 1
        
        print(f"\n📋 Element breakdown:")
        for elem_type, count in sorted(element_types.items()):
            print(f"   • {elem_type}: {count}")
    
    def _analyze_text_elements(self):
        """Analyze text elements for financial keywords"""
        print("\n📝 **TEXT ELEMENTS ANALYSIS**")
        print("-" * 30)
        
        elements = self.structured_data.get('elements', [])
        text_elements = [elem for elem in elements if elem.get('Text')]
        
        print(f"📝 Text elements found: {len(text_elements)}")
        
        # Financial keywords to look for
        financial_keywords = [
            'USD', 'EUR', 'CHF', 'valuation', 'portfolio', 'asset', 'bond', 
            'equity', 'price', 'value', 'total', 'market', 'shares', 'units',
            'MESSOS', 'Client', 'Number', 'security', 'instrument'
        ]
        
        financial_texts = []
        for elem in text_elements:
            text = elem.get('Text', '').strip()
            page = elem.get('Page', 'Unknown')
            bounds = elem.get('Bounds', [])
            
            # Check for financial keywords
            if any(keyword.lower() in text.lower() for keyword in financial_keywords):
                financial_texts.append({
                    'text': text,
                    'page': page,
                    'bounds': bounds,
                    'path': elem.get('Path', '')
                })
        
        print(f"💰 Financial text elements: {len(financial_texts)}")
        print(f"\n🔍 Sample financial text content:")
        for i, item in enumerate(financial_texts[:10]):  # Show first 10
            print(f"   {i+1}. Page {item['page']}: \"{item['text'][:80]}{'...' if len(item['text']) > 80 else ''}\"")
    
    def _analyze_figures(self):
        """Analyze extracted figure images"""
        print("\n🖼️  **FIGURE ANALYSIS**")
        print("-" * 30)
        
        if not self.figures_dir or not os.path.exists(self.figures_dir):
            print("❌ No figures directory found")
            return
        
        figure_files = [f for f in os.listdir(self.figures_dir) if f.endswith('.png')]
        figure_files.sort()
        
        print(f"🖼️  Total figure images: {len(figure_files)}")
        
        # Analyze image sizes and properties
        figure_analysis = []
        for fig_file in figure_files:
            fig_path = os.path.join(self.figures_dir, fig_file)
            try:
                # Get file size
                file_size = os.path.getsize(fig_path)
                
                # Get image dimensions
                with Image.open(fig_path) as img:
                    width, height = img.size
                    mode = img.mode
                
                figure_analysis.append({
                    'file': fig_file,
                    'size_bytes': file_size,
                    'dimensions': f"{width}x{height}",
                    'mode': mode,
                    'aspect_ratio': round(width/height, 2) if height > 0 else 0
                })
            except Exception as e:
                logger.warning(f"Could not analyze {fig_file}: {e}")
        
        # Categorize by size and aspect ratio
        small_images = [f for f in figure_analysis if f['size_bytes'] < 2000]
        medium_images = [f for f in figure_analysis if 2000 <= f['size_bytes'] < 10000]
        large_images = [f for f in figure_analysis if f['size_bytes'] >= 10000]
        
        print(f"\n📊 Image size distribution:")
        print(f"   • Small images (<2KB): {len(small_images)} - likely headers/labels")
        print(f"   • Medium images (2-10KB): {len(medium_images)} - likely tables/charts")
        print(f"   • Large images (>10KB): {len(large_images)} - likely complex tables")
        
        # Show detailed analysis for medium/large images (most likely to contain tables)
        table_candidates = medium_images + large_images
        if table_candidates:
            print(f"\n📋 Table candidates ({len(table_candidates)} images):")
            for img in table_candidates[:10]:  # Show first 10
                print(f"   • {img['file']}: {img['size_bytes']} bytes, {img['dimensions']}, ratio: {img['aspect_ratio']}")
    
    def _extract_financial_data(self):
        """Extract and organize financial data from text elements"""
        print("\n💰 **FINANCIAL DATA EXTRACTION**")
        print("-" * 30)
        
        elements = self.structured_data.get('elements', [])
        
        # Look for specific financial patterns
        securities = []
        prices = []
        valuations = []
        
        for elem in elements:
            text = elem.get('Text', '').strip()
            page = elem.get('Page', 'Unknown')
            bounds = elem.get('Bounds', [])
            
            # Security names (look for patterns)
            if any(keyword in text.upper() for keyword in ['BOND', 'EQUITY', 'FUND', 'STOCK', 'SHARE']):
                securities.append({'text': text, 'page': page, 'bounds': bounds})
            
            # Prices (look for currency patterns)
            if any(curr in text for curr in ['USD', 'EUR', 'CHF']) and any(char.isdigit() for char in text):
                prices.append({'text': text, 'page': page, 'bounds': bounds})
            
            # Valuations (look for large numbers)
            if 'valuation' in text.lower() or ('total' in text.lower() and any(char.isdigit() for char in text)):
                valuations.append({'text': text, 'page': page, 'bounds': bounds})
        
        print(f"🏦 Securities identified: {len(securities)}")
        print(f"💵 Price elements: {len(prices)}")
        print(f"📊 Valuation elements: {len(valuations)}")
        
        if securities:
            print(f"\n🏦 Sample securities:")
            for i, sec in enumerate(securities[:5]):
                print(f"   {i+1}. Page {sec['page']}: \"{sec['text'][:60]}\"")
        
        if prices:
            print(f"\n💵 Sample prices:")
            for i, price in enumerate(prices[:5]):
                print(f"   {i+1}. Page {price['page']}: \"{price['text'][:60]}\"")
    
    def _analyze_table_structures(self):
        """Analyze potential table structures from positioning"""
        print("\n📊 **TABLE STRUCTURE ANALYSIS**")
        print("-" * 30)
        
        elements = self.structured_data.get('elements', [])
        text_elements = [elem for elem in elements if elem.get('Text') and elem.get('Bounds')]
        
        # Group elements by page
        pages_data = {}
        for elem in text_elements:
            page = elem.get('Page', 1)
            if page not in pages_data:
                pages_data[page] = []
            pages_data[page].append(elem)
        
        print(f"📄 Analyzing {len(pages_data)} pages for table structures")
        
        for page_num, page_elements in pages_data.items():
            if len(page_elements) < 5:  # Skip pages with too few elements
                continue
            
            # Sort by Y position (top to bottom)
            page_elements.sort(key=lambda x: x.get('Bounds', [0, 0, 0, 0])[1])
            
            # Look for aligned elements (potential table rows)
            y_positions = [elem.get('Bounds', [0, 0, 0, 0])[1] for elem in page_elements]
            
            # Find elements that are horizontally aligned (same Y position, ±5 pixels)
            aligned_groups = []
            tolerance = 5
            
            for i, y_pos in enumerate(y_positions):
                aligned = [page_elements[i]]
                for j, other_y in enumerate(y_positions):
                    if i != j and abs(y_pos - other_y) <= tolerance:
                        aligned.append(page_elements[j])
                
                if len(aligned) >= 3:  # Potential table row (3+ columns)
                    aligned_groups.append(aligned)
            
            if aligned_groups:
                print(f"\n📊 Page {page_num}: Found {len(aligned_groups)} potential table rows")
                
                # Show sample of what might be a table
                if len(aligned_groups) >= 2:
                    print(f"   Sample table structure:")
                    for i, row in enumerate(aligned_groups[:3]):  # Show first 3 rows
                        row_texts = [elem.get('Text', '')[:20] for elem in row]
                        print(f"   Row {i+1}: {' | '.join(row_texts)}")
    
    def _assess_ocr_feasibility(self):
        """Assess OCR feasibility for accurate financial data extraction"""
        print("\n🤖 **OCR FEASIBILITY ASSESSMENT**")
        print("-" * 30)
        
        # Count figure images by size (proxy for complexity)
        if not self.figures_dir or not os.path.exists(self.figures_dir):
            print("❌ No figures to analyze for OCR")
            return
        
        figure_files = [f for f in os.listdir(self.figures_dir) if f.endswith('.png')]
        
        ocr_candidates = []
        for fig_file in figure_files:
            fig_path = os.path.join(self.figures_dir, fig_file)
            try:
                file_size = os.path.getsize(fig_path)
                with Image.open(fig_path) as img:
                    width, height = img.size
                    aspect_ratio = width/height if height > 0 else 0
                
                # Assess OCR suitability
                ocr_score = 0
                notes = []
                
                # Size assessment
                if file_size > 2000:
                    ocr_score += 2
                    notes.append("Good size for OCR")
                else:
                    notes.append("Small image - may be header/label")
                
                # Aspect ratio assessment (tables are usually wider than tall)
                if 1.5 <= aspect_ratio <= 5.0:
                    ocr_score += 2
                    notes.append("Table-like aspect ratio")
                elif aspect_ratio > 5.0:
                    ocr_score += 1
                    notes.append("Very wide - possible table")
                else:
                    notes.append("Square/tall - likely chart/graphic")
                
                # Dimension assessment
                if width > 300 and height > 100:
                    ocr_score += 1
                    notes.append("Good dimensions for text")
                
                ocr_candidates.append({
                    'file': fig_file,
                    'score': ocr_score,
                    'size': file_size,
                    'dimensions': f"{width}x{height}",
                    'aspect_ratio': round(aspect_ratio, 2),
                    'notes': notes
                })
                
            except Exception as e:
                logger.warning(f"Could not assess {fig_file}: {e}")
        
        # Sort by OCR score
        ocr_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        high_potential = [c for c in ocr_candidates if c['score'] >= 4]
        medium_potential = [c for c in ocr_candidates if 2 <= c['score'] < 4]
        low_potential = [c for c in ocr_candidates if c['score'] < 2]
        
        print(f"🎯 OCR Assessment Results:")
        print(f"   • High potential (score ≥4): {len(high_potential)} images")
        print(f"   • Medium potential (score 2-3): {len(medium_potential)} images")
        print(f"   • Low potential (score <2): {len(low_potential)} images")
        
        print(f"\n🏆 Top OCR candidates:")
        for i, candidate in enumerate(high_potential[:5]):
            print(f"   {i+1}. {candidate['file']} (score: {candidate['score']})")
            print(f"      Size: {candidate['size']} bytes, {candidate['dimensions']}")
            print(f"      Notes: {', '.join(candidate['notes'])}")
        
        # Security-Price matching assessment
        print(f"\n🔗 **SECURITY-PRICE MATCHING ASSESSMENT**")
        print(f"   For accurate financial data extraction:")
        print(f"   ✅ Spatial positioning preserved in JSON")
        print(f"   ✅ Page numbers available for context")
        print(f"   ✅ Bounding boxes can align securities with prices")
        print(f"   ⚠️  OCR accuracy depends on image quality")
        print(f"   ⚠️  Table structure recognition needed")
        
        recommendation = "RECOMMENDED" if len(high_potential) >= 3 else "PROCEED WITH CAUTION"
        print(f"\n💡 **OCR RECOMMENDATION: {recommendation}**")
        
        if len(high_potential) >= 3:
            print(f"   • {len(high_potential)} high-quality table images detected")
            print(f"   • Good chance of accurate security-price matching")
            print(f"   • Estimated cost: ${len(high_potential) * 0.02:.2f} for high-potential images")
        else:
            print(f"   • Limited high-quality table images")
            print(f"   • Manual review recommended before OCR")
            print(f"   • Consider hybrid approach: manual + selective OCR")


def main():
    """Main analysis function"""
    extraction_dir = "output_advanced"
    
    if not os.path.exists(extraction_dir):
        print(f"❌ Extraction directory not found: {extraction_dir}")
        return
    
    analyzer = FinancialDataAnalyzer(extraction_dir)
    analyzer.analyze_all_data()


if __name__ == "__main__":
    main()
