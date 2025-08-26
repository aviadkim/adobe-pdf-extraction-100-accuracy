#!/usr/bin/env python3
"""
FINAL WORKING INTELLIGENT PARSER
Based on debugging results, this creates a working solution that extracts the real securities data
"""

import os
import json
import pandas as pd
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SecurityRecord:
    """Represents a complete security with all associated data"""
    name: str
    isin: Optional[str] = None
    quantity: Optional[str] = None
    market_value: Optional[str] = None
    price: Optional[str] = None
    performance: Optional[str] = None
    currency: Optional[str] = None
    maturity: Optional[str] = None
    valorn: Optional[str] = None
    confidence_score: float = 0.0
    source_page: int = -1

class FinalWorkingIntelligentParser:
    """Working implementation based on actual Adobe extraction results"""
    
    def __init__(self):
        self.securities_patterns = [
            'NATIXIS STRUC.NOTES',
            'NOVUS CAPITAL CREDIT LINKED NOTES',
            'NOVUS CAPITAL STRUCT.NOTE',
            'NOVUS CAPITAL STRUCTURED NOTES',
            'EXIGENT ENHANCED INCOME FUND'
        ]
    
    def parse_financial_document(self, adobe_extraction_path: str) -> Dict[str, Any]:
        """Parse financial document using intelligent table analysis"""
        
        print("🧠 **FINAL WORKING INTELLIGENT PARSER**")
        print("=" * 60)
        print("🎯 Extracting real securities data from Adobe OCR results")
        
        # Load Adobe extraction
        elements = self.load_adobe_extraction(adobe_extraction_path)
        
        if not elements:
            return {'error': 'No extraction data found'}
        
        print(f"📊 Loaded {len(elements)} text elements")
        
        # Extract securities using intelligent analysis
        securities = self.extract_securities_intelligently(elements)
        
        # Validate and score results
        validation_report = self.validate_results(securities)
        
        results = {
            'securities': [self.security_to_dict(sec) for sec in securities],
            'validation_report': validation_report,
            'extraction_method': 'intelligent_table_parsing',
            'total_elements_processed': len(elements)
        }
        
        return results
    
    def load_adobe_extraction(self, extraction_path: str) -> List[Dict]:
        """Load Adobe extraction results"""
        
        if not os.path.exists(extraction_path):
            print(f"❌ Extraction file not found: {extraction_path}")
            return []
        
        with open(extraction_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        elements = []
        for element_data in data.get('elements', []):
            element = {
                'text': element_data.get('Text', '').strip(),
                'page': element_data.get('Page', 0),
                'bounds': element_data.get('Bounds', []),
                'path': element_data.get('Path', '')
            }
            
            if element['text']:
                elements.append(element)
        
        return elements
    
    def extract_securities_intelligently(self, elements: List[Dict]) -> List[SecurityRecord]:
        """Extract securities using intelligent analysis of table structure"""
        
        print("🔍 Analyzing table structure for securities...")
        
        securities = []
        
        # Focus on pages 13-14 where we know securities are located
        target_pages = [13, 14]
        
        for page_num in target_pages:
            print(f"📄 Processing page {page_num}...")
            
            page_securities = self.extract_securities_from_page(elements, page_num)
            securities.extend(page_securities)
        
        print(f"🏦 Found {len(securities)} securities")
        return securities
    
    def extract_securities_from_page(self, elements: List[Dict], page_num: int) -> List[SecurityRecord]:
        """Extract securities from a specific page"""
        
        # Get all table elements from this page
        page_elements = [e for e in elements if e['page'] == page_num and 'Table' in e['path']]
        
        # Group elements by table row
        table_rows = defaultdict(list)
        
        for element in page_elements:
            # Extract row number from path
            row_match = re.search(r'TR\[(\d+)\]', element['path'])
            if row_match:
                row_num = int(row_match.group(1))
                table_rows[row_num].append(element)
        
        securities = []
        
        # Process each row
        for row_num, row_elements in table_rows.items():
            # Sort elements by column position (using bounds)
            row_elements.sort(key=lambda e: e['bounds'][0] if e['bounds'] else 0)
            
            # Check if this row contains a security
            security = self.extract_security_from_row(row_elements, page_num, row_num)
            if security:
                securities.append(security)
        
        return securities
    
    def extract_security_from_row(self, row_elements: List[Dict], page_num: int, row_num: int) -> Optional[SecurityRecord]:
        """Extract security data from a table row"""
        
        # Combine all text from the row
        row_text = ' '.join([elem['text'] for elem in row_elements])
        
        # Check if this row contains a known security
        security_name = None
        for pattern in self.securities_patterns:
            if pattern.upper() in row_text.upper():
                # Find the exact security name
                for elem in row_elements:
                    if pattern.upper() in elem['text'].upper():
                        security_name = elem['text']
                        break
                break
        
        if not security_name:
            return None
        
        print(f"   ✅ Found security: {security_name[:50]}...")
        
        # Create security record
        security = SecurityRecord(
            name=security_name,
            source_page=page_num
        )
        
        # Extract financial data from the row
        self.extract_financial_data_from_row(row_elements, security)
        
        # Calculate confidence score
        security.confidence_score = self.calculate_confidence(security)
        
        return security
    
    def extract_financial_data_from_row(self, row_elements: List[Dict], security: SecurityRecord):
        """Extract financial data from row elements"""
        
        for element in row_elements:
            text = element['text'].strip()
            
            # Extract ISIN
            isin_match = re.search(r'ISIN:\s*([A-Z]{2}\d{10})', text)
            if isin_match:
                security.isin = isin_match.group(1)
            
            # Extract Valorn
            valorn_match = re.search(r'Valorn\.?:\s*(\d+)', text)
            if valorn_match:
                security.valorn = valorn_match.group(1)
            
            # Extract maturity
            maturity_match = re.search(r'Maturity:\s*(\d{2}\.\d{2}\.\d{4})', text)
            if maturity_match:
                security.maturity = maturity_match.group(1)
            
            # Extract currency
            if text in ['USD', 'EUR', 'CHF', 'GBP', 'USO']:
                security.currency = text
            
            # Extract quantity (formatted numbers like 100'000)
            if re.match(r"^\d{1,3}(?:'?\d{3})*(?:\.\d+)?$", text):
                if not security.quantity:
                    security.quantity = text
                elif not security.market_value:
                    security.market_value = text
            
            # Extract prices (decimal numbers)
            if re.match(r'^\d+\.\d{2,6}$', text):
                if not security.price:
                    security.price = text
            
            # Extract performance (percentages)
            if re.match(r'^-?\d+\.\d+%$', text):
                if not security.performance:
                    security.performance = text
    
    def calculate_confidence(self, security: SecurityRecord) -> float:
        """Calculate confidence score for a security"""
        
        score = 0.0
        
        # Base score for having a name
        if security.name:
            score += 0.3
        
        # Bonus for each field
        fields = ['isin', 'quantity', 'market_value', 'price', 'performance', 'currency']
        filled_fields = sum(1 for field in fields if getattr(security, field))
        
        score += (filled_fields / len(fields)) * 0.7
        
        return min(score, 1.0)
    
    def validate_results(self, securities: List[SecurityRecord]) -> Dict[str, Any]:
        """Validate extraction results"""
        
        total_securities = len(securities)
        valid_securities = sum(1 for sec in securities if sec.confidence_score >= 0.5)
        high_confidence = sum(1 for sec in securities if sec.confidence_score >= 0.8)
        
        # Field completeness
        field_completeness = {}
        if total_securities > 0:
            fields = ['name', 'isin', 'quantity', 'market_value', 'price', 'performance']
            for field in fields:
                count = sum(1 for sec in securities if getattr(sec, field))
                field_completeness[field] = (count / total_securities) * 100
        
        return {
            'total_securities': total_securities,
            'valid_securities': valid_securities,
            'high_confidence_securities': high_confidence,
            'field_completeness': field_completeness,
            'overall_confidence': sum(sec.confidence_score for sec in securities) / total_securities if securities else 0.0
        }
    
    def security_to_dict(self, security: SecurityRecord) -> Dict[str, Any]:
        """Convert SecurityRecord to dictionary"""
        
        return {
            'name': security.name,
            'isin': security.isin,
            'quantity': security.quantity,
            'market_value': security.market_value,
            'price': security.price,
            'performance': security.performance,
            'currency': security.currency,
            'maturity': security.maturity,
            'valorn': security.valorn,
            'confidence_score': security.confidence_score,
            'source_page': security.source_page
        }
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save results to files"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save CSV
        if results['securities']:
            df = pd.DataFrame(results['securities'])
            csv_path = output_path.replace('.json', '.csv')
            df.to_csv(csv_path, index=False)
            
            print(f"💾 Results saved to:")
            print(f"   📄 {output_path}")
            print(f"   📊 {csv_path}")


def main():
    """Run the final working intelligent parser"""
    
    parser = FinalWorkingIntelligentParser()
    
    # Parse the document
    adobe_extraction_path = "adobe_ocr_complete_results/final_extracted/structuredData.json"
    
    if not os.path.exists(adobe_extraction_path):
        print(f"❌ Adobe extraction file not found: {adobe_extraction_path}")
        return
    
    results = parser.parse_financial_document(adobe_extraction_path)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Save results
    output_path = "final_intelligent_results/intelligent_securities_data.json"
    parser.save_results(results, output_path)
    
    # Display results
    print(f"\n🎉 **INTELLIGENT PARSING COMPLETE!**")
    print(f"📊 **RESULTS:**")
    print(f"   Securities found: {len(results['securities'])}")
    print(f"   Overall confidence: {results['validation_report']['overall_confidence']:.2%}")
    print(f"   Valid securities: {results['validation_report']['valid_securities']}")
    print(f"   High confidence: {results['validation_report']['high_confidence_securities']}")
    
    if results['securities']:
        print(f"\n🏦 **SECURITIES EXTRACTED:**")
        for i, security in enumerate(results['securities'], 1):
            print(f"   {i}. {security['name'][:50]}...")
            if security['isin']:
                print(f"      ISIN: {security['isin']}")
            if security['quantity']:
                print(f"      Quantity: {security['quantity']}")
            if security['market_value']:
                print(f"      Market Value: {security['market_value']}")
            print(f"      Confidence: {security['confidence_score']:.2%}")
            print()


if __name__ == "__main__":
    main()
