#!/usr/bin/env python3
"""
Quick analysis of Adobe PDF Extract API results
"""

import json
import os
from collections import Counter

def analyze_extraction_results(json_file_path):
    """Analyze the extraction results from Adobe PDF Extract API"""
    
    print(f"🔍 Analyzing extraction results from: {json_file_path}")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📊 **Adobe PDF Extract API Results Analysis**")
        print(f"=" * 50)
        
        # Basic document info
        metadata = data.get('extended_metadata', {})
        print(f"📄 **Document Information:**")
        print(f"   • Pages: {metadata.get('page_count', 'Unknown')}")
        print(f"   • Language: {metadata.get('language', 'Unknown')}")
        print(f"   • PDF Version: {metadata.get('pdf_version', 'Unknown')}")
        print(f"   • Encrypted: {metadata.get('is_encrypted', 'Unknown')}")
        print(f"   • Scanned: {any(page.get('is_scanned', False) for page in data.get('pages', []))}")
        
        # Analyze elements
        elements = data.get('elements', [])
        print(f"\n🔍 **Content Analysis:**")
        print(f"   • Total elements found: {len(elements)}")
        
        # Count element types
        element_paths = [elem.get('Path', 'Unknown') for elem in elements]
        path_counts = Counter(element_paths)
        
        print(f"\n📋 **Element Types:**")
        for path, count in path_counts.most_common():
            print(f"   • {path}: {count}")
        
        # Look for tables specifically
        table_elements = [elem for elem in elements if 'Table' in elem.get('Path', '')]
        print(f"\n📊 **Table Analysis:**")
        print(f"   • Table elements found: {len(table_elements)}")
        
        if table_elements:
            for i, table in enumerate(table_elements):
                page = table.get('Page', 'Unknown')
                bounds = table.get('Bounds', [])
                print(f"   • Table {i+1}: Page {page}, Bounds: {bounds}")
        else:
            print(f"   • ⚠️  No structured tables detected")
        
        # Analyze text content
        text_elements = [elem for elem in elements if elem.get('Text')]
        print(f"\n📝 **Text Content:**")
        print(f"   • Text elements: {len(text_elements)}")
        
        if text_elements:
            # Show some sample text
            sample_texts = [elem.get('Text', '').strip() for elem in text_elements[:5]]
            print(f"   • Sample text content:")
            for i, text in enumerate(sample_texts):
                if text:
                    print(f"     {i+1}. \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
        
        # Look for financial/numerical content
        financial_keywords = ['USD', 'EUR', 'CHF', 'valuation', 'portfolio', 'asset', 'bond', 'equity']
        financial_elements = []
        
        for elem in text_elements:
            text = elem.get('Text', '').lower()
            if any(keyword in text for keyword in financial_keywords):
                financial_elements.append(elem)
        
        print(f"\n💰 **Financial Content:**")
        print(f"   • Elements with financial keywords: {len(financial_elements)}")
        
        if financial_elements:
            print(f"   • Sample financial content:")
            for i, elem in enumerate(financial_elements[:3]):
                text = elem.get('Text', '').strip()
                page = elem.get('Page', 'Unknown')
                if text:
                    print(f"     {i+1}. Page {page}: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
        
        # Check for figures (which might contain table images)
        figure_elements = [elem for elem in elements if 'Figure' in elem.get('Path', '')]
        print(f"\n🖼️  **Figures/Images:**")
        print(f"   • Figure elements: {len(figure_elements)}")
        print(f"   • Note: Tables in images cannot be extracted as structured data")
        
        # Pages analysis
        pages = data.get('pages', [])
        scanned_pages = [p for p in pages if p.get('is_scanned', False)]
        print(f"\n📄 **Page Analysis:**")
        print(f"   • Total pages: {len(pages)}")
        print(f"   • Scanned pages: {len(scanned_pages)}")
        print(f"   • Text-based pages: {len(pages) - len(scanned_pages)}")
        
        if scanned_pages:
            print(f"   • ⚠️  Scanned pages may have limited table extraction")
        
        # Recommendations
        print(f"\n💡 **Recommendations:**")
        if len(table_elements) == 0:
            print(f"   • No structured tables found - document may contain:")
            print(f"     - Tables as images (scanned)")
            print(f"     - Tables with complex formatting")
            print(f"     - Data in non-table format")
        
        if len(figure_elements) > len(table_elements):
            print(f"   • Many figures detected - consider OCR for image-based tables")
        
        if len(scanned_pages) > 0:
            print(f"   • Document contains scanned pages - OCR preprocessing may help")
        
        print(f"\n✅ **Analysis Complete!**")
        
    except Exception as e:
        print(f"❌ Error analyzing extraction results: {e}")

if __name__ == "__main__":
    import sys

    # Allow command line argument for different output directories
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "output/messos 30.5/structuredData.json"

    if os.path.exists(json_file):
        analyze_extraction_results(json_file)
    else:
        print(f"❌ JSON file not found: {json_file}")
        print(f"Usage: python analyze_extraction.py [path_to_json_file]")
