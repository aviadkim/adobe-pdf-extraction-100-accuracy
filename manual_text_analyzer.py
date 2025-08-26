#!/usr/bin/env python3
"""
Manual Text Analyzer for PDF Content
Analyzes the actual text content from PDF extraction to identify securities patterns
"""

import os
import json
import re
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualTextAnalyzer:
    """Analyze extracted text manually to identify patterns"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.baseline_dir = "baseline_test_results/messos 30.5"
        self.structured_data_path = os.path.join(self.baseline_dir, "structuredData.json")
        
    def analyze_text_content(self) -> Dict[str, Any]:
        """Analyze all text content to understand structure"""
        
        if not os.path.exists(self.structured_data_path):
            return {"error": "No structured data found"}
        
        try:
            with open(self.structured_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            return {"error": str(e)}
        
        analysis = {
            'total_elements': len(data.get('elements', [])),
            'text_elements': [],
            'page_text': {},
            'potential_securities': [],
            'financial_data': [],
            'table_candidates': []
        }
        
        # Extract and analyze text by page
        for element in data.get('elements', []):
            text = element.get('Text', '').strip()
            page = element.get('Page', 0)
            
            if text:
                text_element = {
                    'text': text,
                    'page': page,
                    'path': element.get('Path', ''),
                    'bounds': element.get('Bounds', [])
                }
                analysis['text_elements'].append(text_element)
                
                # Group by page
                if page not in analysis['page_text']:
                    analysis['page_text'][page] = []
                analysis['page_text'][page].append(text)
                
                # Look for potential securities data
                if self._looks_like_security_data(text):
                    analysis['potential_securities'].append(text_element)
                
                # Look for financial data
                if self._contains_financial_data(text):
                    analysis['financial_data'].append(text_element)
                
                # Look for table structures
                if self._looks_like_table_data(text):
                    analysis['table_candidates'].append(text_element)
        
        return analysis
    
    def _looks_like_security_data(self, text: str) -> bool:
        """Check if text looks like security/investment data"""
        security_indicators = [
            r'[A-Z]{2}[A-Z0-9]{9}\d',  # ISIN pattern
            r'\b(BOND|EQUITY|FUND|STOCK|SHARE|SECURITY)\b',
            r'\b(USD|EUR|CHF|GBP|JPY)\s+[\d,]+',  # Currency + amount
            r'[\d,]+\.\d{2}\s*(USD|EUR|CHF)',  # Amount + currency
        ]
        
        for pattern in security_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _contains_financial_data(self, text: str) -> bool:
        """Check if text contains financial data"""
        financial_patterns = [
            r'\$[\d,]+\.?\d*',  # Dollar amounts
            r'[\d,]+\.\d{2}',   # Decimal amounts
            r'\d{1,3}\.?\d*%',  # Percentages
            r'\b\d{1,2}[./]\d{1,2}[./]\d{4}\b',  # Dates
            r'Client\s+Number',  # Client info
        ]
        
        for pattern in financial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _looks_like_table_data(self, text: str) -> bool:
        """Check if text looks like table data"""
        # Look for multiple data items separated by spaces
        parts = text.split()
        if len(parts) >= 3:
            # Check for patterns like: Name ISIN Currency Amount
            has_alpha = any(re.match(r'^[A-Za-z]', part) for part in parts)
            has_numeric = any(re.match(r'^[\d,]+\.?\d*$', part.replace(',', '')) for part in parts)
            has_currency = any(part.upper() in ['USD', 'EUR', 'CHF', 'GBP', 'JPY'] for part in parts)
            
            return has_alpha and has_numeric and (has_currency or len(parts) >= 5)
        return False
    
    def find_securities_patterns(self) -> List[Dict]:
        """Specifically look for securities patterns"""
        analysis = self.analyze_text_content()
        
        securities_found = []
        
        # Look through all text for securities patterns
        for text_element in analysis.get('text_elements', []):
            text = text_element['text']
            
            # Pattern 1: Look for ISIN codes and surrounding data
            isin_matches = re.finditer(r'([A-Z\s&]{10,50})\s*([A-Z]{2}[A-Z0-9]{9}\d)\s*([A-Z]{3})?\s*([\d,]+(?:\.\d{2})?)', text)
            for match in isin_matches:
                security = {
                    'name': match.group(1).strip(),
                    'isin': match.group(2),
                    'currency': match.group(3) or '',
                    'amount': match.group(4),
                    'page': text_element['page'],
                    'source_text': text
                }
                securities_found.append(security)
            
            # Pattern 2: Look for financial instruments by name patterns
            instrument_patterns = [
                r'([A-Z\s&]{5,40}(?:BOND|EQUITY|FUND|CORP|LTD|INC))\s+([A-Z]{2}[A-Z0-9]{9}\d)',
                r'([A-Z\s]{5,40})\s+([A-Z]{2}[A-Z0-9]{9}\d)\s+(USD|EUR|CHF|GBP)',
            ]
            
            for pattern in instrument_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    security = {
                        'name': match.group(1).strip(),
                        'isin': match.group(2) if len(match.groups()) > 1 else '',
                        'currency': match.group(3) if len(match.groups()) > 2 else '',
                        'page': text_element['page'],
                        'source_text': text
                    }
                    securities_found.append(security)
        
        return securities_found
    
    def create_detailed_report(self) -> str:
        """Create detailed analysis report"""
        
        analysis = self.analyze_text_content()
        securities = self.find_securities_patterns()
        
        # Create report
        report_lines = [
            "=== MANUAL TEXT ANALYSIS REPORT ===",
            f"Total elements: {analysis['total_elements']}",
            f"Text elements: {len(analysis['text_elements'])}",
            f"Potential securities: {len(analysis['potential_securities'])}",
            f"Financial data elements: {len(analysis['financial_data'])}",
            f"Table candidates: {len(analysis['table_candidates'])}",
            f"Securities found: {len(securities)}",
            "",
            "=== PAGE BREAKDOWN ===",
        ]
        
        for page, texts in analysis['page_text'].items():
            report_lines.append(f"Page {page}: {len(texts)} text elements")
        
        report_lines.extend([
            "",
            "=== SAMPLE TEXT ELEMENTS ===",
        ])
        
        for i, element in enumerate(analysis['text_elements'][:20]):
            report_lines.append(f"{i+1}. [Page {element['page']}] {element['text'][:100]}...")
        
        if securities:
            report_lines.extend([
                "",
                "=== SECURITIES FOUND ===",
            ])
            for i, security in enumerate(securities):
                report_lines.append(f"{i+1}. {security['name']} - {security.get('isin', 'No ISIN')}")
        
        # Look for patterns in potential securities
        report_lines.extend([
            "",
            "=== POTENTIAL SECURITIES PATTERNS ===",
        ])
        
        for element in analysis['potential_securities'][:10]:
            report_lines.append(f"[Page {element['page']}] {element['text']}")
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = "manual_analysis_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(report_content)
        return report_file


def main():
    """Main analysis function"""
    analyzer = ManualTextAnalyzer()
    report_file = analyzer.create_detailed_report()
    print(f"\\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    main()