#!/usr/bin/env python3
"""
WORKING UNIVERSAL FINANCIAL PDF PARSER
Uses existing Adobe extraction + universal parsing logic to handle ANY financial PDF format
"""

import os
import json
import pandas as pd
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class UniversalSecurityRecord:
    """Universal security record that works across all document types"""
    name: str
    isin: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    ticker: Optional[str] = None
    quantity: Optional[str] = None
    market_value: Optional[str] = None
    unit_price: Optional[str] = None
    performance_ytd: Optional[str] = None
    performance_total: Optional[str] = None
    currency: Optional[str] = None
    maturity_date: Optional[str] = None
    coupon_rate: Optional[str] = None
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    valorn: Optional[str] = None  # Swiss
    wkn: Optional[str] = None     # German
    confidence_score: float = 0.0
    extraction_method: str = ""
    source_page: int = -1
    validation_flags: List[str] = field(default_factory=list)

class WorkingUniversalParser:
    """Working universal parser using existing Adobe extraction"""
    
    def __init__(self):
        self.universal_patterns = self.load_universal_patterns()
        self.institution_configs = self.load_institution_configs()
        self.security_name_patterns = self.load_security_name_patterns()
    
    def load_universal_patterns(self) -> Dict:
        """Load universal patterns for different document types and regions"""
        
        return {
            'identifiers': {
                'isin': r'[A-Z]{2}\d{10}',
                'cusip': r'[A-Z0-9]{9}',
                'sedol': r'[A-Z0-9]{7}',
                'valorn': r'\d{6,12}',
                'wkn': r'[A-Z0-9]{6}',
                'ticker': r'[A-Z]{1,5}'
            },
            'financial_data': {
                'currency_amount_us': r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
                'currency_amount_eu': r'\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€',
                'currency_amount_swiss': r"\d{1,3}(?:'\d{3})*(?:\.\d{2})?",
                'percentage': r'-?\d+\.\d+%',
                'decimal_price': r'\d+\.\d{2,6}',
                'date_us': r'\d{1,2}/\d{1,2}/\d{4}',
                'date_eu': r'\d{1,2}\.\d{1,2}\.\d{4}',
                'date_iso': r'\d{4}-\d{2}-\d{2}'
            },
            'security_types': {
                'bonds': r'\b(bond|note|bill|obligation|anleihe|notes)\b',
                'equities': r'\b(stock|share|equity|aktie|action)\b',
                'funds': r'\b(fund|etf|mutual|fonds)\b',
                'derivatives': r'\b(option|future|swap|derivative)\b',
                'structured': r'\b(structured|struct)\b'
            }
        }
    
    def load_institution_configs(self) -> Dict:
        """Load configurations for different financial institutions"""
        
        return {
            'swiss_banks': {
                'indicators': ['valorn', 'chf', 'schweiz', 'swiss', 'structured products'],
                'number_format': 'swiss',  # Uses apostrophes
                'date_format': 'dd.mm.yyyy',
                'currency_symbols': ['CHF', 'USD', 'EUR']
            },
            'us_banks': {
                'indicators': ['cusip', 'usd', 'united states', 'shares', 'dollars'],
                'number_format': 'us',  # Uses commas
                'date_format': 'mm/dd/yyyy',
                'currency_symbols': ['USD', 'EUR', 'GBP']
            },
            'european_banks': {
                'indicators': ['isin', 'eur', 'wkn', 'depot', 'wertpapiere'],
                'number_format': 'european',  # Uses dots and commas
                'date_format': 'dd.mm.yyyy',
                'currency_symbols': ['EUR', 'USD', 'GBP']
            },
            'asian_banks': {
                'indicators': ['jpy', 'yen', 'hkd', 'sgd', 'asia'],
                'number_format': 'asian',
                'date_format': 'yyyy/mm/dd',
                'currency_symbols': ['JPY', 'HKD', 'SGD', 'USD']
            }
        }
    
    def load_security_name_patterns(self) -> List[str]:
        """Load patterns for recognizing security names"""
        
        return [
            # Bank names
            r'\b(GOLDMAN SACHS|BANK OF AMERICA|JPMORGAN|CITIGROUP|WELLS FARGO|DEUTSCHE BANK)\b',
            r'\b(UBS|CREDIT SUISSE|BNP PARIBAS|HSBC|BARCLAYS|STANDARD CHARTERED)\b',
            
            # Common security patterns
            r'\b[A-Z\s]+(?:NOTES?|BONDS?|FUND|EQUITY|STRUCTURED)\b',
            r'\b[A-Z\s]+(?:CAPITAL|GROUP|CORP|LTD|INC|AG|SA)\b.*(?:NOTES?|BONDS?)\b',
            
            # Specific patterns we know work
            r'NATIXIS.*NOTES',
            r'NOVUS CAPITAL.*NOTES',
            r'EXIGENT.*FUND',
            r'.*ENHANCED.*FUND',
            r'.*STRUCTURED.*NOTES',
            r'.*CREDIT LINKED.*NOTES'
        ]
    
    def parse_any_financial_pdf(self, adobe_extraction_path: str) -> Dict[str, Any]:
        """Parse ANY financial PDF using universal logic"""
        
        print("🌍 **WORKING UNIVERSAL FINANCIAL PDF PARSER**")
        print("=" * 60)
        print("🎯 Using Adobe extraction + universal parsing logic")
        
        # Load Adobe extraction
        extraction_data = self.load_adobe_extraction(adobe_extraction_path)
        
        if not extraction_data:
            return {'error': 'No Adobe extraction data found'}
        
        print(f"📊 Loaded {len(extraction_data)} text elements")
        
        # Step 1: Analyze document format
        document_analysis = self.analyze_document_format(extraction_data)
        
        # Step 2: Apply universal parsing
        securities = self.apply_universal_parsing(extraction_data, document_analysis)
        
        # Step 3: Validate and enhance
        validated_securities = self.validate_and_enhance_results(securities)
        
        # Step 4: Generate results
        results = self.generate_comprehensive_results(validated_securities, document_analysis)
        
        return results
    
    def load_adobe_extraction(self, extraction_path: str) -> List[Dict]:
        """Load Adobe extraction results"""
        
        if not os.path.exists(extraction_path):
            print(f"❌ Adobe extraction file not found: {extraction_path}")
            return []
        
        with open(extraction_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        elements = []
        for element_data in data.get('elements', []):
            element = {
                'text': element_data.get('Text', '').strip(),
                'page': element_data.get('Page', 0),
                'bounds': element_data.get('Bounds', []),
                'path': element_data.get('Path', ''),
                'font_size': element_data.get('TextSize', 0)
            }
            
            if element['text']:
                elements.append(element)
        
        return elements
    
    def analyze_document_format(self, elements: List[Dict]) -> Dict:
        """Analyze document format universally"""
        
        print("🔍 Analyzing document format universally...")
        
        # Combine all text for analysis
        all_text = ' '.join([elem['text'] for elem in elements]).lower()
        
        analysis = {
            'detected_format': 'unknown',
            'detected_region': 'unknown',
            'detected_language': 'english',
            'detected_institution_type': 'unknown',
            'confidence': 0.0,
            'format_indicators': []
        }
        
        # Detect format based on universal patterns
        for format_name, config in self.institution_configs.items():
            matches = sum(1 for indicator in config['indicators'] if indicator in all_text)
            
            if matches > 0:
                confidence = matches / len(config['indicators'])
                
                if confidence > analysis['confidence']:
                    analysis['detected_format'] = format_name
                    analysis['confidence'] = confidence
                    analysis['format_indicators'] = [ind for ind in config['indicators'] if ind in all_text]
        
        # Detect specific patterns
        if 'valorn' in all_text or "'" in all_text:
            analysis['detected_region'] = 'switzerland'
            analysis['detected_format'] = 'swiss_banks'
        elif 'cusip' in all_text or '$' in all_text:
            analysis['detected_region'] = 'united_states'
            analysis['detected_format'] = 'us_banks'
        elif 'wkn' in all_text or '€' in all_text:
            analysis['detected_region'] = 'europe'
            analysis['detected_format'] = 'european_banks'
        
        print(f"📊 Detected: {analysis['detected_format']} ({analysis['confidence']:.2%} confidence)")
        print(f"🔍 Indicators found: {analysis['format_indicators']}")
        
        return analysis
    
    def apply_universal_parsing(self, elements: List[Dict], document_analysis: Dict) -> List[UniversalSecurityRecord]:
        """Apply universal parsing logic"""
        
        print("🧠 Applying universal parsing logic...")
        
        securities = []
        
        # Group elements by page and table structure
        page_groups = defaultdict(list)
        for element in elements:
            if 'Table' in element['path']:  # Focus on table elements
                page_groups[element['page']].append(element)
        
        # Process each page
        for page_num, page_elements in page_groups.items():
            print(f"📄 Processing page {page_num} with {len(page_elements)} table elements")
            
            page_securities = self.extract_securities_from_page_universal(page_elements, page_num, document_analysis)
            securities.extend(page_securities)
        
        print(f"🏦 Found {len(securities)} securities using universal parsing")
        return securities
    
    def extract_securities_from_page_universal(self, page_elements: List[Dict], page_num: int, document_analysis: Dict) -> List[UniversalSecurityRecord]:
        """Extract securities from a page using universal logic"""
        
        securities = []
        
        # Group elements by table row
        table_rows = defaultdict(list)
        
        for element in page_elements:
            # Extract row number from path
            row_match = re.search(r'TR\[(\d+)\]', element['path'])
            if row_match:
                row_num = int(row_match.group(1))
                table_rows[row_num].append(element)
        
        # Process each row
        for row_num, row_elements in table_rows.items():
            # Sort elements by column position
            row_elements.sort(key=lambda e: e['bounds'][0] if e['bounds'] else 0)
            
            # Check if this row contains a security
            security = self.extract_security_from_row_universal(row_elements, page_num, row_num, document_analysis)
            if security:
                securities.append(security)
        
        return securities
    
    def extract_security_from_row_universal(self, row_elements: List[Dict], page_num: int, row_num: int, document_analysis: Dict) -> Optional[UniversalSecurityRecord]:
        """Extract security from a row using universal patterns"""
        
        # Combine all text from the row
        row_text = ' '.join([elem['text'] for elem in row_elements])
        
        # Check if this row contains a security using universal patterns
        security_name = self.find_security_name_universal(row_elements, row_text)
        
        if not security_name:
            return None
        
        print(f"   ✅ Found security: {security_name[:50]}...")
        
        # Create universal security record
        security = UniversalSecurityRecord(
            name=security_name,
            source_page=page_num,
            extraction_method='universal_parsing'
        )
        
        # Extract all possible financial data using universal patterns
        self.extract_financial_data_universal(row_elements, row_text, security, document_analysis)
        
        # Calculate confidence
        security.confidence_score = self.calculate_universal_confidence(security)
        
        return security
    
    def find_security_name_universal(self, row_elements: List[Dict], row_text: str) -> Optional[str]:
        """Find security name using universal patterns"""
        
        # Try specific patterns first
        for pattern in self.security_name_patterns:
            match = re.search(pattern, row_text, re.IGNORECASE)
            if match:
                # Find the exact element containing this text
                for element in row_elements:
                    if pattern.replace(r'\b', '').replace(r'.*', '').replace(r'(?:', '').replace(r')', '') in element['text'].upper():
                        return element['text']
        
        # Try general security type patterns
        for sec_type, pattern in self.universal_patterns['security_types'].items():
            if re.search(pattern, row_text, re.IGNORECASE):
                # Look for the longest text element that might be the security name
                longest_element = max(row_elements, key=lambda e: len(e['text']), default=None)
                if longest_element and len(longest_element['text']) > 20:
                    return longest_element['text']
        
        return None
    
    def extract_financial_data_universal(self, row_elements: List[Dict], row_text: str, security: UniversalSecurityRecord, document_analysis: Dict) -> None:
        """Extract financial data using universal patterns"""
        
        detected_format = document_analysis['detected_format']
        
        for element in row_elements:
            text = element['text'].strip()
            
            # Extract identifiers using universal patterns
            for id_type, pattern in self.universal_patterns['identifiers'].items():
                if re.match(pattern, text):
                    setattr(security, id_type, text)
            
            # Extract ISIN with label
            isin_match = re.search(r'ISIN:\s*([A-Z]{2}\d{10})', text)
            if isin_match:
                security.isin = isin_match.group(1)
            
            # Extract Valorn (Swiss)
            valorn_match = re.search(r'Valorn\.?:\s*(\d+)', text)
            if valorn_match:
                security.valorn = valorn_match.group(1)
            
            # Extract maturity date
            for date_pattern in self.universal_patterns['financial_data'].values():
                if 'date' in date_pattern:
                    date_match = re.search(date_pattern, text)
                    if date_match:
                        security.maturity_date = date_match.group()
            
            # Extract currency
            if text in ['USD', 'EUR', 'CHF', 'GBP', 'JPY', 'USO']:
                security.currency = text
            
            # Extract quantities based on detected format
            if detected_format == 'swiss_banks':
                # Swiss format: 100'000
                if re.match(r"^\d{1,3}(?:'\d{3})*(?:\.\d+)?$", text):
                    if not security.quantity:
                        security.quantity = text
                    elif not security.market_value:
                        security.market_value = text
            else:
                # US/European format: 100,000
                if re.match(r"^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$", text):
                    if not security.quantity:
                        security.quantity = text
                    elif not security.market_value:
                        security.market_value = text
            
            # Extract prices (decimal numbers)
            if re.match(r'^\d+\.\d{2,6}$', text):
                if not security.unit_price:
                    security.unit_price = text
            
            # Extract performance (percentages)
            if re.match(r'^-?\d+\.\d+%$', text):
                if not security.performance_ytd:
                    security.performance_ytd = text
                elif not security.performance_total:
                    security.performance_total = text
            
            # Extract coupon rate
            if re.search(r'\d+\.\d+%.*coupon', text, re.IGNORECASE):
                security.coupon_rate = text
        
        # Determine asset class
        name_lower = security.name.lower()
        if any(bond_word in name_lower for bond_word in ['note', 'bond', 'bill']):
            security.asset_class = 'bonds'
        elif any(equity_word in name_lower for equity_word in ['equity', 'stock', 'share']):
            security.asset_class = 'equities'
        elif any(fund_word in name_lower for fund_word in ['fund', 'etf']):
            security.asset_class = 'funds'
        elif 'structured' in name_lower:
            security.asset_class = 'structured_products'
        else:
            security.asset_class = 'other'
    
    def calculate_universal_confidence(self, security: UniversalSecurityRecord) -> float:
        """Calculate confidence score universally"""
        
        score = 0.0
        
        # Base score for having a name
        if security.name:
            score += 0.2
        
        # Bonus for identifiers (any type)
        if security.isin:
            score += 0.3
        elif security.cusip:
            score += 0.3
        elif security.sedol:
            score += 0.3
        elif security.valorn:
            score += 0.2
        elif security.wkn:
            score += 0.2
        
        # Bonus for financial data
        if security.quantity:
            score += 0.15
        if security.market_value:
            score += 0.2
        if security.unit_price:
            score += 0.1
        if security.currency:
            score += 0.05
        
        # Bonus for additional data
        if security.performance_ytd or security.performance_total:
            score += 0.1
        if security.maturity_date:
            score += 0.05
        if security.asset_class and security.asset_class != 'other':
            score += 0.05
        
        return min(score, 1.0)
    
    def validate_and_enhance_results(self, securities: List[UniversalSecurityRecord]) -> List[UniversalSecurityRecord]:
        """Validate and enhance results universally"""
        
        print("✅ Validating and enhancing results...")
        
        validated_securities = []
        
        for security in securities:
            # Validate identifiers
            if security.isin and not re.match(self.universal_patterns['identifiers']['isin'], security.isin):
                security.validation_flags.append('invalid_isin')
            
            if security.cusip and not re.match(self.universal_patterns['identifiers']['cusip'], security.cusip):
                security.validation_flags.append('invalid_cusip')
            
            # Only include securities with reasonable confidence
            if security.confidence_score >= 0.3:
                validated_securities.append(security)
        
        return validated_securities
    
    def generate_comprehensive_results(self, securities: List[UniversalSecurityRecord], document_analysis: Dict) -> Dict[str, Any]:
        """Generate comprehensive results"""
        
        return {
            'document_analysis': document_analysis,
            'securities': [self.security_to_dict(sec) for sec in securities],
            'summary': {
                'total_securities': len(securities),
                'high_confidence_securities': sum(1 for sec in securities if sec.confidence_score >= 0.8),
                'by_asset_class': self.group_by_asset_class(securities),
                'by_currency': self.group_by_currency(securities),
                'detected_format': document_analysis['detected_format'],
                'detected_region': document_analysis['detected_region']
            },
            'parser_info': {
                'version': '1.0',
                'universal_parser': True,
                'supported_formats': ['swiss_banks', 'us_banks', 'european_banks', 'asian_banks'],
                'supported_identifiers': ['isin', 'cusip', 'sedol', 'valorn', 'wkn'],
                'extraction_method': 'adobe_ocr_universal_parsing'
            }
        }
    
    def group_by_asset_class(self, securities: List[UniversalSecurityRecord]) -> Dict[str, int]:
        """Group securities by asset class"""
        
        groups = defaultdict(int)
        for security in securities:
            groups[security.asset_class or 'unknown'] += 1
        return dict(groups)
    
    def group_by_currency(self, securities: List[UniversalSecurityRecord]) -> Dict[str, int]:
        """Group securities by currency"""
        
        groups = defaultdict(int)
        for security in securities:
            groups[security.currency or 'unknown'] += 1
        return dict(groups)
    
    def security_to_dict(self, security: UniversalSecurityRecord) -> Dict[str, Any]:
        """Convert security to dictionary"""
        
        return {
            'name': security.name,
            'isin': security.isin,
            'cusip': security.cusip,
            'sedol': security.sedol,
            'ticker': security.ticker,
            'quantity': security.quantity,
            'market_value': security.market_value,
            'unit_price': security.unit_price,
            'performance_ytd': security.performance_ytd,
            'performance_total': security.performance_total,
            'currency': security.currency,
            'maturity_date': security.maturity_date,
            'coupon_rate': security.coupon_rate,
            'asset_class': security.asset_class,
            'sector': security.sector,
            'country': security.country,
            'valorn': security.valorn,
            'wkn': security.wkn,
            'confidence_score': security.confidence_score,
            'extraction_method': security.extraction_method,
            'source_page': security.source_page,
            'validation_flags': security.validation_flags
        }


def main():
    """Test the working universal parser"""
    
    parser = WorkingUniversalParser()
    
    # Use existing Adobe extraction
    adobe_extraction_path = "adobe_ocr_complete_results/final_extracted/structuredData.json"
    
    if not os.path.exists(adobe_extraction_path):
        print(f"❌ Adobe extraction file not found: {adobe_extraction_path}")
        return
    
    # Parse using universal logic
    results = parser.parse_any_financial_pdf(adobe_extraction_path)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Save results
    output_path = "working_universal_results/universal_securities_data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    if results['securities']:
        df = pd.DataFrame(results['securities'])
        csv_path = output_path.replace('.json', '.csv')
        df.to_csv(csv_path, index=False)
    
    # Display results
    print(f"\n🎉 **UNIVERSAL PARSING COMPLETE!**")
    print(f"📊 **RESULTS:**")
    print(f"   Document format: {results['document_analysis']['detected_format']}")
    print(f"   Region: {results['document_analysis']['detected_region']}")
    print(f"   Securities found: {results['summary']['total_securities']}")
    print(f"   High confidence: {results['summary']['high_confidence_securities']}")
    print(f"   By asset class: {results['summary']['by_asset_class']}")
    print(f"   By currency: {results['summary']['by_currency']}")
    
    if results['securities']:
        print(f"\n🏦 **SECURITIES EXTRACTED:**")
        for i, security in enumerate(results['securities'], 1):
            print(f"   {i}. {security['name'][:50]}...")
            if security['isin']:
                print(f"      ISIN: {security['isin']}")
            if security['valorn']:
                print(f"      Valorn: {security['valorn']}")
            if security['quantity']:
                print(f"      Quantity: {security['quantity']}")
            if security['market_value']:
                print(f"      Market Value: {security['market_value']}")
            print(f"      Asset Class: {security['asset_class']}")
            print(f"      Confidence: {security['confidence_score']:.2%}")
            print()
    
    print(f"\n📁 **RESULTS SAVED TO:**")
    print(f"   📄 {output_path}")
    if results['securities']:
        print(f"   📊 {csv_path}")


if __name__ == "__main__":
    main()
