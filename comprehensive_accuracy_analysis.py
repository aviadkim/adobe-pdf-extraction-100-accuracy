#!/usr/bin/env python3
"""
Comprehensive Accuracy Analysis for PDF Extraction
Analyzes extraction results and calculates accuracy metrics for achieving 100% data extraction
"""

import os
import json
import pandas as pd
from pathlib import Path
import re
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveAccuracyAnalyzer:
    """Analyzes PDF extraction accuracy and identifies gaps toward 100% accuracy"""
    
    def __init__(self):
        """Initialize the accuracy analyzer"""
        self.pdf_path = "messos 30.5.pdf"
        self.baseline_results_dir = "baseline_test_results/messos 30.5"
        self.output_dir = "accuracy_analysis_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Expected data types for financial documents
        self.expected_data_types = {
            'securities': ['security_name', 'isin', 'currency', 'units', 'price', 'market_value'],
            'portfolio_info': ['client_number', 'valuation_date', 'currency', 'total_value'],
            'asset_allocation': ['asset_class', 'percentage', 'value'],
            'financial_figures': ['amounts', 'percentages', 'dates'],
            'tables': ['structured_data', 'rows', 'columns'],
            'text_elements': ['headers', 'labels', 'identifiers']
        }
        
    def analyze_baseline_extraction(self) -> Dict[str, Any]:
        """Analyze the baseline Adobe extraction results"""
        logger.info("Analyzing baseline Adobe extraction results...")
        
        structured_data_path = os.path.join(self.baseline_results_dir, "structuredData.json")
        
        if not os.path.exists(structured_data_path):
            logger.error(f"Structured data not found: {structured_data_path}")
            return {"error": "No baseline results found"}
        
        with open(structured_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis = {
            'total_elements': len(data.get('elements', [])),
            'pages': data.get('extended_metadata', {}).get('page_count', 0),
            'extraction_version': data.get('version', {}),
            'element_types': {},
            'text_content': [],
            'figures': [],
            'tables': [],
            'financial_data': {
                'client_numbers': [],
                'dates': [],
                'currencies': [],
                'amounts': [],
                'securities': []
            }
        }
        
        # Analyze each element
        for element in data.get('elements', []):
            element_path = element.get('Path', '')
            element_type = element_path.split('/')[-1] if '/' in element_path else 'unknown'
            
            analysis['element_types'][element_type] = analysis['element_types'].get(element_type, 0) + 1
            
            # Extract text content
            text = element.get('Text', '').strip()
            if text:
                analysis['text_content'].append({
                    'text': text,
                    'type': element_type,
                    'page': element.get('Page', 0),
                    'bounds': element.get('Bounds', [])
                })
                
                # Look for financial patterns
                self._extract_financial_patterns(text, analysis['financial_data'])
        
        # Calculate coverage metrics
        coverage = self._calculate_coverage_metrics(analysis)
        analysis['coverage_metrics'] = coverage
        
        return analysis
    
    def _extract_financial_patterns(self, text: str, financial_data: Dict):
        """Extract financial patterns from text"""
        
        # Client numbers
        client_match = re.search(r'Client\s+Number[:\s/]+(\d+)', text, re.IGNORECASE)
        if client_match:
            financial_data['client_numbers'].append(client_match.group(1))
        
        # Dates
        date_patterns = [
            r'\d{1,2}[./]\d{1,2}[./]\d{4}',
            r'\d{4}[./]\d{1,2}[./]\d{1,2}',
            r'\d{1,2}\s+[A-Za-z]+\s+\d{4}'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            financial_data['dates'].extend(dates)
        
        # Currencies
        currencies = re.findall(r'\b(USD|EUR|CHF|GBP|JPY)\b', text, re.IGNORECASE)
        financial_data['currencies'].extend(currencies)
        
        # Amounts (with commas, decimals)
        amounts = re.findall(r'\$?[\d,]+\.?\d*', text)
        financial_data['amounts'].extend([amt for amt in amounts if len(amt) > 2])
        
        # Security identifiers (ISINs, etc.)
        isin_pattern = r'\b[A-Z]{2}[A-Z0-9]{9}\d\b'
        isins = re.findall(isin_pattern, text)
        financial_data['securities'].extend(isins)
    
    def _calculate_coverage_metrics(self, analysis: Dict) -> Dict[str, float]:
        """Calculate data coverage metrics"""
        
        coverage = {
            'client_info_coverage': 0.0,
            'date_coverage': 0.0,
            'financial_figures_coverage': 0.0,
            'securities_coverage': 0.0,
            'table_coverage': 0.0,
            'overall_coverage': 0.0
        }
        
        financial_data = analysis['financial_data']
        
        # Client info
        if financial_data['client_numbers']:
            coverage['client_info_coverage'] = min(len(financial_data['client_numbers']) / 1.0, 1.0) * 100
        
        # Dates
        if financial_data['dates']:
            coverage['date_coverage'] = min(len(financial_data['dates']) / 5.0, 1.0) * 100  # Expect ~5 dates
        
        # Financial figures
        if financial_data['amounts']:
            coverage['financial_figures_coverage'] = min(len(financial_data['amounts']) / 50.0, 1.0) * 100  # Expect ~50 amounts
        
        # Securities
        if financial_data['securities']:
            coverage['securities_coverage'] = min(len(financial_data['securities']) / 20.0, 1.0) * 100  # Expect ~20 securities
        
        # Tables (based on element types)
        table_elements = analysis['element_types'].get('Table', 0)
        if table_elements > 0:
            coverage['table_coverage'] = min(table_elements / 10.0, 1.0) * 100  # Expect ~10 tables
        
        # Overall coverage (average)
        coverage['overall_coverage'] = sum([
            coverage['client_info_coverage'],
            coverage['date_coverage'],
            coverage['financial_figures_coverage'],
            coverage['securities_coverage'],
            coverage['table_coverage']
        ]) / 5.0
        
        return coverage
    
    def analyze_existing_results(self) -> Dict[str, Any]:
        """Analyze all existing extraction results for comparison"""
        logger.info("Analyzing existing extraction results...")
        
        results_dirs = [
            "output/messos 30.5",
            "output_advanced/messos 30.5", 
            "output_ocr/messos 30.5",
            "adobe_securities_results",
            "all_securities_extracted"
        ]
        
        comparison = {
            'methods': {},
            'best_performing': None,
            'gaps_identified': []
        }
        
        for results_dir in results_dirs:
            if os.path.exists(results_dir):
                method_name = results_dir.replace('/', '_').replace('\\', '_')
                comparison['methods'][method_name] = self._analyze_method_results(results_dir)
        
        # Identify best performing method
        best_coverage = 0
        for method, results in comparison['methods'].items():
            if results.get('coverage_metrics', {}).get('overall_coverage', 0) > best_coverage:
                best_coverage = results['coverage_metrics']['overall_coverage']
                comparison['best_performing'] = method
        
        return comparison
    
    def _analyze_method_results(self, results_dir: str) -> Dict[str, Any]:
        """Analyze results from a specific extraction method"""
        
        structured_data_files = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                if file == 'structuredData.json':
                    structured_data_files.append(os.path.join(root, file))
        
        if not structured_data_files:
            return {"error": "No structured data found"}
        
        # Analyze the most recent/complete file
        latest_file = max(structured_data_files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analysis = {
                'file_path': latest_file,
                'total_elements': len(data.get('elements', [])),
                'element_types': {},
                'financial_data_found': 0,
                'text_elements': 0
            }
            
            for element in data.get('elements', []):
                element_path = element.get('Path', '')
                element_type = element_path.split('/')[-1] if '/' in element_path else 'unknown'
                analysis['element_types'][element_type] = analysis['element_types'].get(element_type, 0) + 1
                
                if element.get('Text'):
                    analysis['text_elements'] += 1
                    if self._contains_financial_data(element.get('Text', '')):
                        analysis['financial_data_found'] += 1
            
            # Calculate coverage for this method
            coverage = self._calculate_method_coverage(analysis)
            analysis['coverage_metrics'] = coverage
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def _contains_financial_data(self, text: str) -> bool:
        """Check if text contains financial data patterns"""
        financial_patterns = [
            r'\d+[,.]?\d*\s*(USD|EUR|CHF|GBP)',  # Amounts with currency
            r'\b\d{1,2}[./]\d{1,2}[./]\d{4}\b',  # Dates
            r'\b[A-Z]{2}[A-Z0-9]{9}\d\b',       # ISINs
            r'Client\s+Number',                  # Client identifiers
            r'\$[\d,]+\.?\d*'                    # Dollar amounts
        ]
        
        for pattern in financial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _calculate_method_coverage(self, analysis: Dict) -> Dict[str, float]:
        """Calculate coverage metrics for a specific method"""
        
        total_elements = analysis.get('total_elements', 0)
        financial_elements = analysis.get('financial_data_found', 0)
        text_elements = analysis.get('text_elements', 0)
        
        if total_elements == 0:
            return {'overall_coverage': 0.0}
        
        coverage = {
            'text_extraction_rate': (text_elements / total_elements) * 100 if total_elements > 0 else 0,
            'financial_data_rate': (financial_elements / text_elements) * 100 if text_elements > 0 else 0,
            'overall_coverage': (financial_elements / total_elements) * 100 if total_elements > 0 else 0
        }
        
        return coverage
    
    def identify_accuracy_gaps(self, baseline_analysis: Dict, comparison: Dict) -> Dict[str, Any]:
        """Identify gaps preventing 100% accuracy"""
        logger.info("Identifying accuracy gaps...")
        
        gaps = {
            'missing_data_types': [],
            'low_confidence_areas': [],
            'extraction_failures': [],
            'recommendations': []
        }
        
        baseline_coverage = baseline_analysis.get('coverage_metrics', {})
        
        # Identify missing data types
        for data_type, expected in self.expected_data_types.items():
            if data_type not in baseline_analysis.get('financial_data', {}):
                gaps['missing_data_types'].append(data_type)
        
        # Identify low confidence areas
        for metric, score in baseline_coverage.items():
            if score < 80.0:  # Less than 80% coverage
                gaps['low_confidence_areas'].append({
                    'metric': metric,
                    'score': score,
                    'target': 100.0
                })
        
        # Generate recommendations
        if baseline_coverage.get('securities_coverage', 0) < 90:
            gaps['recommendations'].append("Implement specialized securities extraction with ISIN pattern matching")
        
        if baseline_coverage.get('table_coverage', 0) < 90:
            gaps['recommendations'].append("Add table structure analysis and cell-by-cell extraction")
        
        if baseline_coverage.get('financial_figures_coverage', 0) < 90:
            gaps['recommendations'].append("Enhance numerical pattern recognition for amounts and percentages")
        
        if baseline_coverage.get('overall_coverage', 0) < 95:
            gaps['recommendations'].append("Implement multi-pass extraction with different parameters")
            gaps['recommendations'].append("Add spatial analysis for table reconstruction")
            gaps['recommendations'].append("Include OCR processing for image-based content")
        
        return gaps
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive accuracy analysis report"""
        logger.info("Generating comprehensive accuracy report...")
        
        # Run all analyses
        baseline_analysis = self.analyze_baseline_extraction()
        existing_comparison = self.analyze_existing_results()
        accuracy_gaps = self.identify_accuracy_gaps(baseline_analysis, existing_comparison)
        
        # Create comprehensive report
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'document_analyzed': self.pdf_path,
            'baseline_analysis': baseline_analysis,
            'method_comparison': existing_comparison,
            'accuracy_gaps': accuracy_gaps,
            'path_to_100_percent': self._create_improvement_plan(accuracy_gaps, baseline_analysis)
        }
        
        # Save detailed report
        report_path = os.path.join(self.output_dir, f"comprehensive_accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate summary HTML report
        html_report_path = self._generate_html_report(report)
        
        logger.info(f"Comprehensive report saved: {report_path}")
        logger.info(f"HTML summary report: {html_report_path}")
        
        return report_path
    
    def _create_improvement_plan(self, gaps: Dict, baseline: Dict) -> Dict[str, Any]:
        """Create specific plan to achieve 100% accuracy"""
        
        current_coverage = baseline.get('coverage_metrics', {}).get('overall_coverage', 0)
        gap_to_100 = 100.0 - current_coverage
        
        plan = {
            'current_accuracy': f"{current_coverage:.1f}%",
            'gap_to_100_percent': f"{gap_to_100:.1f}%",
            'priority_improvements': [],
            'implementation_steps': [],
            'expected_accuracy_gain': {}
        }
        
        # Priority improvements based on gaps
        for area in gaps['low_confidence_areas']:
            metric = area['metric']
            current_score = area['score']
            improvement_needed = 100.0 - current_score
            
            plan['priority_improvements'].append({
                'area': metric.replace('_', ' ').title(),
                'current_score': f"{current_score:.1f}%",
                'improvement_needed': f"{improvement_needed:.1f}%",
                'priority': 'High' if improvement_needed > 30 else 'Medium'
            })
        
        # Implementation steps
        plan['implementation_steps'] = [
            "1. Implement enhanced table detection and structure analysis",
            "2. Add specialized securities data extraction patterns",
            "3. Integrate OCR processing for image-based tables",
            "4. Implement multi-pass extraction with different parameters",
            "5. Add spatial analysis for element relationships",
            "6. Create validation and correction workflows",
            "7. Implement confidence scoring and quality metrics"
        ]
        
        # Expected accuracy gains
        plan['expected_accuracy_gain'] = {
            'enhanced_table_extraction': '15-25%',
            'securities_pattern_matching': '10-15%',
            'ocr_integration': '20-30%',
            'multi_pass_extraction': '5-10%',
            'spatial_analysis': '10-15%',
            'validation_workflows': '5-10%'
        }
        
        return plan
    
    def _generate_html_report(self, report: Dict) -> str:
        """Generate HTML summary report"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PDF Extraction Accuracy Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .metric {{ background: #e8f4fd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .gap {{ background: #fff2e8; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .recommendation {{ background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .progress-bar {{ width: 100%; background: #ddd; height: 20px; border-radius: 10px; }}
        .progress-fill {{ height: 20px; border-radius: 10px; text-align: center; line-height: 20px; }}
        .high {{ background: #ff6b6b; }}
        .medium {{ background: #feca57; }}
        .good {{ background: #48dbfb; }}
        .excellent {{ background: #0be881; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Extraction Accuracy Analysis</h1>
        <p><strong>Document:</strong> {report.get('document_analyzed', 'N/A')}</p>
        <p><strong>Analysis Date:</strong> {report.get('analysis_timestamp', 'N/A')}</p>
    </div>
    
    <h2>Current Accuracy Metrics</h2>
"""
        
        # Add coverage metrics
        baseline_coverage = report.get('baseline_analysis', {}).get('coverage_metrics', {})
        for metric, score in baseline_coverage.items():
            css_class = 'excellent' if score >= 90 else 'good' if score >= 70 else 'medium' if score >= 50 else 'high'
            html_content += f"""
    <div class="metric">
        <strong>{metric.replace('_', ' ').title()}:</strong> {score:.1f}%
        <div class="progress-bar">
            <div class="progress-fill {css_class}" style="width: {score}%">{score:.1f}%</div>
        </div>
    </div>
"""
        
        # Add improvement plan
        improvement_plan = report.get('path_to_100_percent', {})
        html_content += f"""
    <h2>Path to 100% Accuracy</h2>
    <div class="metric">
        <strong>Current Overall Accuracy:</strong> {improvement_plan.get('current_accuracy', 'N/A')}
    </div>
    <div class="gap">
        <strong>Gap to 100%:</strong> {improvement_plan.get('gap_to_100_percent', 'N/A')}
    </div>
    
    <h3>Implementation Steps</h3>
"""
        
        for step in improvement_plan.get('implementation_steps', []):
            html_content += f'<div class="recommendation">{step}</div>'
        
        html_content += """
    <h3>Expected Accuracy Gains</h3>
"""
        
        for improvement, gain in improvement_plan.get('expected_accuracy_gain', {}).items():
            html_content += f'<div class="metric"><strong>{improvement.replace("_", " ").title()}:</strong> {gain}</div>'
        
        html_content += """
</body>
</html>
"""
        
        html_report_path = os.path.join(self.output_dir, f"accuracy_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_report_path


def main():
    """Main analysis function"""
    print("=== COMPREHENSIVE ACCURACY ANALYSIS ===")
    print("Analyzing PDF extraction accuracy and path to 100%...")
    
    analyzer = ComprehensiveAccuracyAnalyzer()
    
    try:
        # Generate comprehensive analysis
        report_path = analyzer.generate_comprehensive_report()
        
        print(f"\\nAnalysis complete!")
        print(f"Detailed report: {report_path}")
        
        # Load and display key metrics
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        baseline_coverage = report.get('baseline_analysis', {}).get('coverage_metrics', {})
        improvement_plan = report.get('path_to_100_percent', {})
        
        print(f"\\n=== KEY RESULTS ===")
        print(f"Current Overall Accuracy: {improvement_plan.get('current_accuracy', 'N/A')}")
        print(f"Gap to 100%: {improvement_plan.get('gap_to_100_percent', 'N/A')}")
        
        print(f"\\n=== COVERAGE BREAKDOWN ===")
        for metric, score in baseline_coverage.items():
            print(f"{metric.replace('_', ' ').title()}: {score:.1f}%")
        
        print(f"\\n=== PRIORITY IMPROVEMENTS ===")
        for improvement in improvement_plan.get('priority_improvements', [])[:3]:
            print(f"• {improvement.get('area', 'N/A')}: {improvement.get('improvement_needed', 'N/A')} improvement needed")
        
        print(f"\\n=== NEXT STEPS ===")
        for i, step in enumerate(improvement_plan.get('implementation_steps', [])[:5], 1):
            print(f"{i}. {step}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()