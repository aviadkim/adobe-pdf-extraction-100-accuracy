#!/usr/bin/env python3
"""
DEBUG VERSION: Intelligent Financial Table Parser
Let's see what's happening in the table detection and why securities aren't being found
"""

import os
import json
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class TextElement:
    """Represents a single text element from Adobe's extraction"""
    text: str
    page: int
    bounds: List[float]  # [x1, y1, x2, y2]
    font_size: float
    path: str
    confidence: float = 1.0

def load_adobe_extraction(extraction_path: str) -> List[TextElement]:
    """Load and convert Adobe extraction results to TextElement objects"""
    
    if not os.path.exists(extraction_path):
        print(f"❌ Extraction file not found: {extraction_path}")
        return []
    
    with open(extraction_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    elements = []
    for element_data in data.get('elements', []):
        element = TextElement(
            text=element_data.get('Text', '').strip(),
            page=element_data.get('Page', 0),
            bounds=element_data.get('Bounds', []),
            font_size=element_data.get('TextSize', 0),
            path=element_data.get('Path', ''),
            confidence=1.0  # Adobe OCR is highly accurate
        )
        
        if element.text:  # Only include non-empty elements
            elements.append(element)
    
    print(f"📊 Loaded {len(elements)} text elements from Adobe extraction")
    return elements

def debug_table_detection(elements: List[TextElement]):
    """Debug what's happening in table detection"""
    
    print("\n🔍 **DEBUGGING TABLE DETECTION**")
    print("=" * 50)
    
    # Check table elements
    table_elements = []
    for element in elements:
        if 'Table' in element.path:
            table_elements.append(element)
    
    print(f"📊 Found {len(table_elements)} table elements")
    
    # Group by page
    pages = defaultdict(list)
    for element in table_elements:
        pages[element.page].append(element)
    
    print(f"📄 Table elements across {len(pages)} pages:")
    for page_num, page_elements in pages.items():
        print(f"   Page {page_num}: {len(page_elements)} elements")
    
    # Look for securities-related text
    print(f"\n🏦 **LOOKING FOR SECURITIES TEXT**")
    securities_keywords = ['NATIXIS', 'NOVUS', 'EXIGENT', 'GOLDMAN', 'BANK', 'NOTES', 'FUND']
    
    securities_elements = []
    for element in table_elements:
        text_upper = element.text.upper()
        if any(keyword in text_upper for keyword in securities_keywords):
            securities_elements.append(element)
    
    print(f"🎯 Found {len(securities_elements)} elements with securities keywords:")
    
    for i, element in enumerate(securities_elements[:10], 1):  # Show first 10
        print(f"   {i}. Page {element.page}: '{element.text[:60]}...'")
        print(f"      Path: {element.path}")
        print(f"      Bounds: {element.bounds}")
    
    return securities_elements

def debug_pattern_recognition(elements: List[TextElement]):
    """Debug pattern recognition for securities"""
    
    print(f"\n🧠 **DEBUGGING PATTERN RECOGNITION**")
    print("=" * 50)
    
    security_keywords = [
        'notes', 'bonds', 'fund', 'equity', 'structured', 'treasury',
        'corporate', 'government', 'municipal', 'convertible'
    ]
    
    potential_securities = []
    
    for element in elements:
        text_lower = element.text.lower()
        
        # Check for security keywords
        keyword_matches = sum(1 for keyword in security_keywords if keyword in text_lower)
        
        # Check for typical security name patterns
        has_issuer = bool(re.search(r'\b(bank|capital|group|corp|ltd|inc|ag|sa)\b', text_lower))
        has_instrument = bool(re.search(r'\b(notes?|bonds?|fund|equity|structured)\b', text_lower))
        has_date = bool(re.search(r'\d{2,4}[-\.]\d{2}[-\.]\d{2,4}', element.text))
        has_percentage = bool(re.search(r'\d+\.?\d*%', element.text))
        
        # Calculate confidence
        confidence = 0.0
        if keyword_matches > 0:
            confidence += min(keyword_matches * 0.3, 0.6)
        if has_issuer:
            confidence += 0.2
        if has_instrument:
            confidence += 0.3
        if has_date:
            confidence += 0.1
        if has_percentage:
            confidence += 0.1
        
        # Length and complexity bonus
        if 20 <= len(element.text) <= 100:
            confidence += 0.1
        
        if confidence >= 0.4:
            potential_securities.append((element, confidence))
    
    print(f"🎯 Found {len(potential_securities)} potential securities:")
    
    for i, (element, confidence) in enumerate(potential_securities[:10], 1):
        print(f"   {i}. Confidence: {confidence:.2f}")
        print(f"      Text: '{element.text}'")
        print(f"      Page: {element.page}, Path: {element.path}")
        print()

def debug_specific_securities(elements: List[TextElement]):
    """Debug specific securities we know should be there"""
    
    print(f"\n🎯 **DEBUGGING SPECIFIC KNOWN SECURITIES**")
    print("=" * 50)
    
    known_securities = [
        'NATIXIS STRUC.NOTES',
        'NOVUS CAPITAL CREDIT LINKED NOTES',
        'NOVUS CAPITAL STRUCT.NOTE',
        'NOVUS CAPITAL STRUCTURED NOTES',
        'EXIGENT ENHANCED INCOME FUND'
    ]
    
    for security_name in known_securities:
        print(f"\n🔍 Looking for: {security_name}")
        
        found_elements = []
        for element in elements:
            if security_name.upper() in element.text.upper():
                found_elements.append(element)
        
        if found_elements:
            print(f"   ✅ Found {len(found_elements)} matches:")
            for element in found_elements:
                print(f"      Page {element.page}: '{element.text}'")
                print(f"      Path: {element.path}")
                print(f"      Bounds: {element.bounds}")
        else:
            print(f"   ❌ Not found")

def debug_table_structure(elements: List[TextElement]):
    """Debug table structure analysis"""
    
    print(f"\n📊 **DEBUGGING TABLE STRUCTURE**")
    print("=" * 50)
    
    # Focus on pages 13-14 where we know securities are
    target_pages = [13, 14]
    
    for page_num in target_pages:
        print(f"\n📄 **PAGE {page_num} ANALYSIS:**")
        
        page_elements = [e for e in elements if e.page == page_num and 'Table' in e.path]
        print(f"   Table elements: {len(page_elements)}")
        
        # Group by table and row
        table_structure = defaultdict(lambda: defaultdict(list))
        
        for element in page_elements:
            # Extract table and row info from path
            table_match = re.search(r'Table\[(\d+)\]', element.path)
            row_match = re.search(r'TR\[(\d+)\]', element.path)
            
            if table_match and row_match:
                table_num = table_match.group(1)
                row_num = row_match.group(1)
                table_structure[table_num][row_num].append(element)
        
        print(f"   Tables found: {list(table_structure.keys())}")
        
        for table_num, table_rows in table_structure.items():
            print(f"\n   📋 Table {table_num}:")
            print(f"      Rows: {len(table_rows)}")
            
            # Show a few sample rows
            for row_num in sorted(table_rows.keys())[:5]:
                row_elements = table_rows[row_num]
                row_text = ' | '.join([e.text[:30] for e in row_elements])
                print(f"      Row {row_num}: {row_text}")

def main():
    """Debug the intelligent financial table parser"""
    
    print("🔍 **DEBUGGING INTELLIGENT FINANCIAL TABLE PARSER**")
    print("=" * 60)
    
    # Load Adobe extraction results
    adobe_extraction_path = "adobe_ocr_complete_results/final_extracted/structuredData.json"
    
    if not os.path.exists(adobe_extraction_path):
        print(f"❌ Adobe extraction file not found: {adobe_extraction_path}")
        return
    
    elements = load_adobe_extraction(adobe_extraction_path)
    
    if not elements:
        print("❌ No elements loaded")
        return
    
    # Run debugging functions
    securities_elements = debug_table_detection(elements)
    debug_pattern_recognition(elements)
    debug_specific_securities(elements)
    debug_table_structure(elements)
    
    print(f"\n✅ **DEBUGGING COMPLETE**")
    print(f"💡 Check the output above to understand why securities aren't being detected")

if __name__ == "__main__":
    main()
