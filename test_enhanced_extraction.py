#!/usr/bin/env python3
"""
Test script for Enhanced Adobe Processor
Tests extraction capabilities and generates comprehensive quality reports
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our enhanced components
try:
    from enhanced_adobe_processor import EnhancedAdobeProcessor
    from optimized_spatial_analysis import analyze_spatial_structure
    from complete_data_extractor import CompleteDataExtractor
    from securities_extractor import SecuritiesExtractor
    from human_validation_interface import HumanValidationInterface
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all enhanced modules are available")
    sys.exit(1)


class ComprehensiveExtractionTester:
    """
    Comprehensive tester for maximum data extraction accuracy
    """
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.test_results = {}
        self.extraction_methods = {}
        
    def run_complete_extraction_test(self, pdf_path: str) -> dict:
        """
        Run comprehensive extraction test using all available methods
        """
        logger.info(f"🚀 Starting comprehensive extraction test for: {os.path.basename(pdf_path)}")
        
        test_results = {
            'pdf_file': pdf_path,
            'pdf_name': os.path.basename(pdf_path),
            'test_timestamp': time.time(),
            'methods_tested': [],
            'extraction_results': {},
            'quality_metrics': {},
            'recommendations': [],
            'final_confidence': 0.0
        }
        
        # Method 1: Enhanced Adobe Processor
        logger.info("📊 Method 1: Enhanced Adobe Processor")
        try:
            enhanced_processor = EnhancedAdobeProcessor(self.credentials_path)
            enhanced_result = enhanced_processor.extract_with_maximum_quality(
                pdf_path, 
                output_dir="test_output/enhanced"
            )
            
            test_results['methods_tested'].append('enhanced_adobe')
            test_results['extraction_results']['enhanced_adobe'] = enhanced_result
            
            if enhanced_result['success']:
                logger.info(f"✅ Enhanced Adobe: Success - Confidence: {enhanced_result.get('extraction_confidence', 0):.1%}")
            else:
                logger.warning(f"❌ Enhanced Adobe: Failed - {enhanced_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Enhanced Adobe extraction failed: {e}")
            test_results['extraction_results']['enhanced_adobe'] = {'success': False, 'error': str(e)}
        
        # Method 2: Securities-Specific Extraction
        logger.info("📊 Method 2: Securities-Specific Extraction")
        try:
            enhanced_processor = EnhancedAdobeProcessor(self.credentials_path)
            securities_result = enhanced_processor.extract_securities_enhanced(pdf_path)
            
            test_results['methods_tested'].append('securities_enhanced')
            test_results['extraction_results']['securities_enhanced'] = securities_result
            
            securities_found = securities_result.get('securities_found', 0)
            logger.info(f"🏦 Securities extraction: {securities_found} securities identified")
            
        except Exception as e:
            logger.error(f"Securities extraction failed: {e}")
            test_results['extraction_results']['securities_enhanced'] = {'success': False, 'error': str(e)}
        
        # Method 3: Complete Data Extractor (Multi-modal)
        logger.info("📊 Method 3: Complete Multi-modal Extraction")
        try:
            # First ensure we have Adobe output to analyze
            enhanced_result = test_results['extraction_results'].get('enhanced_adobe')
            if enhanced_result and enhanced_result['success']:
                
                complete_extractor = CompleteDataExtractor()
                
                # Mock the paths based on enhanced extraction results
                extracted_files = enhanced_result.get('extracted_files', {})
                if 'json' in extracted_files:
                    json_path = extracted_files['json']
                    output_dir = os.path.dirname(json_path)
                    
                    # Update paths for complete extractor
                    complete_extractor.json_file = json_path
                    complete_extractor.figures_dir = os.path.join(os.path.dirname(output_dir), "figures")
                    complete_extractor.output_dir = "test_output/complete"
                    os.makedirs(complete_extractor.output_dir, exist_ok=True)
                    
                    complete_result = complete_extractor.create_comprehensive_report()
                    
                    test_results['methods_tested'].append('complete_multimodal')
                    test_results['extraction_results']['complete_multimodal'] = complete_result
                    
                    if complete_result:
                        confidence = complete_result.get('extraction_confidence', 0)
                        logger.info(f"✅ Complete extraction: Confidence: {confidence:.1%}")
                    else:
                        logger.warning("❌ Complete extraction: No results")
                        
        except Exception as e:
            logger.error(f"Complete extraction failed: {e}")
            test_results['extraction_results']['complete_multimodal'] = {'success': False, 'error': str(e)}
        
        # Analyze and score all methods
        test_results['quality_metrics'] = self._analyze_extraction_quality(test_results)
        test_results['recommendations'] = self._generate_recommendations(test_results)
        test_results['final_confidence'] = self._calculate_final_confidence(test_results)
        
        # Generate comprehensive report
        self._generate_comprehensive_report(test_results)
        
        return test_results
    
    def _analyze_extraction_quality(self, test_results: dict) -> dict:
        """
        Analyze quality metrics across all extraction methods
        """
        quality_metrics = {
            'methods_successful': 0,
            'total_methods': len(test_results['methods_tested']),
            'best_method': None,
            'best_confidence': 0.0,
            'data_coverage': {},
            'consistency_score': 0.0
        }
        
        method_confidences = {}
        
        for method_name in test_results['methods_tested']:
            result = test_results['extraction_results'].get(method_name, {})
            
            if result.get('success', False):
                quality_metrics['methods_successful'] += 1
                
                # Get confidence for this method
                confidence = 0.0
                if method_name == 'enhanced_adobe':
                    confidence = result.get('extraction_confidence', 0)
                elif method_name == 'complete_multimodal':
                    confidence = result.get('extraction_confidence', 0)
                elif method_name == 'securities_enhanced':
                    # Calculate securities confidence based on findings
                    securities_found = result.get('securities_found', 0)
                    confidence = min(0.9, securities_found * 0.1) if securities_found > 0 else 0.3
                
                method_confidences[method_name] = confidence
                
                if confidence > quality_metrics['best_confidence']:
                    quality_metrics['best_confidence'] = confidence
                    quality_metrics['best_method'] = method_name
        
        # Calculate data coverage
        quality_metrics['data_coverage'] = self._calculate_data_coverage(test_results)
        
        # Calculate consistency score (how well methods agree)
        quality_metrics['consistency_score'] = self._calculate_consistency_score(test_results)
        
        quality_metrics['method_confidences'] = method_confidences
        
        return quality_metrics
    
    def _calculate_data_coverage(self, test_results: dict) -> dict:
        """
        Calculate what percentage of expected data types were found
        """
        coverage = {
            'client_information': False,
            'securities_data': False,
            'financial_amounts': False,
            'table_structures': False,
            'document_images': False,
            'text_elements': False
        }
        
        # Check enhanced adobe results
        enhanced_result = test_results['extraction_results'].get('enhanced_adobe', {})
        if enhanced_result.get('success'):
            extracted_files = enhanced_result.get('extracted_files', {})
            if extracted_files:
                coverage['text_elements'] = True
                if 'csv' in extracted_files or 'xlsx' in extracted_files:
                    coverage['table_structures'] = True
        
        # Check complete multimodal results
        complete_result = test_results['extraction_results'].get('complete_multimodal', {})
        if complete_result:
            client_info = complete_result.get('client_information', {})
            if client_info and any(client_info.values()):
                coverage['client_information'] = True
            
            image_analysis = complete_result.get('image_analysis', [])
            if image_analysis:
                coverage['document_images'] = True
        
        # Check securities results
        securities_result = test_results['extraction_results'].get('securities_enhanced', {})
        if securities_result and securities_result.get('securities_found', 0) > 0:
            coverage['securities_data'] = True
            coverage['financial_amounts'] = True
        
        # Calculate overall coverage percentage
        coverage_count = sum(1 for v in coverage.values() if v)
        coverage['overall_percentage'] = (coverage_count / len([k for k in coverage.keys() if k != 'overall_percentage'])) * 100
        
        return coverage
    
    def _calculate_consistency_score(self, test_results: dict) -> float:
        """
        Calculate how consistent results are across methods
        """
        successful_methods = [
            method for method in test_results['methods_tested']
            if test_results['extraction_results'].get(method, {}).get('success', False)
        ]
        
        if len(successful_methods) < 2:
            return 1.0 if len(successful_methods) == 1 else 0.0
        
        # For now, simple consistency based on success rate
        success_rate = len(successful_methods) / len(test_results['methods_tested'])
        return success_rate
    
    def _calculate_final_confidence(self, test_results: dict) -> float:
        """
        Calculate overall confidence in extraction results
        """
        quality_metrics = test_results['quality_metrics']
        
        # Base confidence from best method
        base_confidence = quality_metrics.get('best_confidence', 0.0)
        
        # Bonus for multiple successful methods
        methods_bonus = (quality_metrics.get('methods_successful', 0) - 1) * 0.1
        
        # Coverage bonus
        coverage_bonus = quality_metrics.get('data_coverage', {}).get('overall_percentage', 0) / 100 * 0.2
        
        # Consistency bonus
        consistency_bonus = quality_metrics.get('consistency_score', 0) * 0.1
        
        final_confidence = base_confidence + methods_bonus + coverage_bonus + consistency_bonus
        
        return min(1.0, final_confidence)
    
    def _generate_recommendations(self, test_results: dict) -> list:
        """
        Generate recommendations for improving extraction accuracy
        """
        recommendations = []
        quality_metrics = test_results['quality_metrics']
        
        # Success rate recommendations
        success_rate = quality_metrics.get('methods_successful', 0) / quality_metrics.get('total_methods', 1)
        
        if success_rate < 0.5:
            recommendations.append("❌ Low success rate - Check Adobe API credentials and document format")
        elif success_rate < 0.8:
            recommendations.append("⚠️ Moderate success rate - Some extraction methods failed, consider document quality")
        else:
            recommendations.append("✅ High success rate - Extraction methods are working well")
        
        # Confidence recommendations
        final_confidence = test_results.get('final_confidence', 0)
        
        if final_confidence < 0.6:
            recommendations.append("🔍 Low confidence - Manual validation strongly recommended")
        elif final_confidence < 0.8:
            recommendations.append("📝 Moderate confidence - Spot check key data points")
        else:
            recommendations.append("✅ High confidence - Results are likely accurate")
        
        # Coverage recommendations
        coverage = quality_metrics.get('data_coverage', {})
        coverage_pct = coverage.get('overall_percentage', 0)
        
        if coverage_pct < 60:
            recommendations.append("📊 Low data coverage - Consider additional extraction methods")
        elif coverage_pct < 80:
            recommendations.append("📈 Good data coverage - Minor gaps remain")
        else:
            recommendations.append("🎯 Excellent data coverage - Most data types detected")
        
        # Specific missing data recommendations
        if not coverage.get('client_information'):
            recommendations.append("🏢 Missing client information - Check document header/footer")
        if not coverage.get('securities_data'):
            recommendations.append("🏦 No securities detected - Document may not contain securities data")
        if not coverage.get('table_structures'):
            recommendations.append("📋 No table structures found - Document may be text-only or require OCR")
        
        # Method-specific recommendations
        enhanced_result = test_results['extraction_results'].get('enhanced_adobe')
        if enhanced_result and not enhanced_result.get('success'):
            recommendations.append("🔧 Enhanced Adobe extraction failed - Check credentials and file format")
        
        return recommendations
    
    def _generate_comprehensive_report(self, test_results: dict) -> str:
        """
        Generate comprehensive HTML report
        """
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Extraction Test Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8f9fa; }}
                .container {{ max-width: 1400px; margin: 0 auto; background: white; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 2.5em; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .section {{ margin: 20px; padding: 25px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .metric-label {{ color: #6c757d; margin-top: 5px; }}
                .success {{ border-left-color: #28a745; }}
                .success .metric-value {{ color: #28a745; }}
                .warning {{ border-left-color: #ffc107; }}
                .warning .metric-value {{ color: #ffc107; }}
                .danger {{ border-left-color: #dc3545; }}
                .danger .metric-value {{ color: #dc3545; }}
                .method-card {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #17a2b8; }}
                .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }}
                .status-success {{ background: #d4edda; color: #155724; }}
                .status-failed {{ background: #f8d7da; color: #721c24; }}
                .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; }}
                .recommendations ul {{ margin: 0; }}
                .coverage-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
                .coverage-item {{ display: flex; align-items: center; padding: 10px; }}
                .coverage-icon {{ font-size: 1.5em; margin-right: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                th {{ background: #f8f9fa; font-weight: 600; }}
                .confidence-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
                .confidence-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); transition: width 0.3s; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Comprehensive Extraction Test Report</h1>
                    <p>Advanced PDF Data Extraction Analysis - {test_results['pdf_name']}</p>
                    <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(test_results['test_timestamp']))}</p>
                </div>
        """
        
        # Overall metrics
        quality_metrics = test_results['quality_metrics']
        final_confidence = test_results['final_confidence']
        
        confidence_class = 'success' if final_confidence >= 0.8 else 'warning' if final_confidence >= 0.6 else 'danger'
        
        report_html += f"""
                <div class="section">
                    <h2>🎯 Overall Results</h2>
                    <div class="metric-grid">
                        <div class="metric-card {confidence_class}">
                            <div class="metric-value">{final_confidence:.1%}</div>
                            <div class="metric-label">Final Confidence</div>
                        </div>
                        <div class="metric-card {'success' if quality_metrics.get('methods_successful', 0) > 0 else 'danger'}">
                            <div class="metric-value">{quality_metrics.get('methods_successful', 0)}/{quality_metrics.get('total_methods', 0)}</div>
                            <div class="metric-label">Methods Successful</div>
                        </div>
                        <div class="metric-card {'success' if quality_metrics.get('data_coverage', {}).get('overall_percentage', 0) >= 70 else 'warning'}">
                            <div class="metric-value">{quality_metrics.get('data_coverage', {}).get('overall_percentage', 0):.0f}%</div>
                            <div class="metric-label">Data Coverage</div>
                        </div>
                        <div class="metric-card {'success' if quality_metrics.get('consistency_score', 0) >= 0.8 else 'warning'}">
                            <div class="metric-value">{quality_metrics.get('consistency_score', 0):.1%}</div>
                            <div class="metric-label">Consistency Score</div>
                        </div>
                    </div>
                    
                    <h3>🎖️ Confidence Breakdown</h3>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {final_confidence * 100}%;"></div>
                    </div>
                    <p style="text-align: center; margin-top: 10px; color: #6c757d;">
                        {final_confidence:.1%} Overall Confidence
                    </p>
                </div>
        """
        
        # Method results
        report_html += """
                <div class="section">
                    <h2>🔬 Extraction Method Results</h2>
        """
        
        for method_name in test_results['methods_tested']:
            result = test_results['extraction_results'].get(method_name, {})
            success = result.get('success', False)
            
            method_display_name = {
                'enhanced_adobe': '🚀 Enhanced Adobe Processor',
                'securities_enhanced': '🏦 Securities-Specific Extraction',
                'complete_multimodal': '🎭 Complete Multi-modal Extraction'
            }.get(method_name, method_name)
            
            confidence = quality_metrics.get('method_confidences', {}).get(method_name, 0)
            
            report_html += f"""
                    <div class="method-card">
                        <h3>{method_display_name} 
                            <span class="status-badge {'status-success' if success else 'status-failed'}">
                                {'✅ SUCCESS' if success else '❌ FAILED'}
                            </span>
                        </h3>
            """
            
            if success:
                report_html += f"""
                        <p><strong>Confidence:</strong> {confidence:.1%}</p>
                        <p><strong>Processing Time:</strong> {result.get('total_processing_time', 0):.2f}s</p>
                """
                
                # Method-specific details
                if method_name == 'enhanced_adobe':
                    extracted_files = result.get('extracted_files', {})
                    quality_grade = result.get('quality_validation', {}).get('grade', 'Unknown')
                    report_html += f"""
                        <p><strong>Quality Grade:</strong> {quality_grade}</p>
                        <p><strong>Files Extracted:</strong> {len(extracted_files)}</p>
                    """
                    
                elif method_name == 'securities_enhanced':
                    securities_found = result.get('securities_found', 0)
                    report_html += f"""
                        <p><strong>Securities Found:</strong> {securities_found}</p>
                    """
                    
                elif method_name == 'complete_multimodal':
                    if result.get('extraction_summary'):
                        summary = result['extraction_summary']
                        report_html += f"""
                        <p><strong>Text Elements:</strong> {summary.get('total_text_elements', 0)}</p>
                        <p><strong>Financial Elements:</strong> {summary.get('financial_elements', 0)}</p>
                        <p><strong>Images Analyzed:</strong> {summary.get('image_files', 0)}</p>
                        """
            else:
                error_msg = result.get('error', 'Unknown error')
                report_html += f'<p style="color: #dc3545;"><strong>Error:</strong> {error_msg}</p>'
            
            report_html += "</div>"
        
        # Data coverage
        coverage = quality_metrics.get('data_coverage', {})
        report_html += """
                </div>
                
                <div class="section">
                    <h2>📊 Data Coverage Analysis</h2>
                    <div class="coverage-grid">
        """
        
        coverage_items = [
            ('client_information', '🏢', 'Client Information'),
            ('securities_data', '🏦', 'Securities Data'),
            ('financial_amounts', '💰', 'Financial Amounts'),
            ('table_structures', '📋', 'Table Structures'),
            ('document_images', '🖼️', 'Document Images'),
            ('text_elements', '📝', 'Text Elements')
        ]
        
        for key, icon, label in coverage_items:
            found = coverage.get(key, False)
            status_icon = '✅' if found else '❌'
            
            report_html += f"""
                        <div class="coverage-item">
                            <span class="coverage-icon">{icon}</span>
                            <div>
                                <strong>{label}</strong><br>
                                <span style="color: {'#28a745' if found else '#dc3545'};">{status_icon} {'Found' if found else 'Not Found'}</span>
                            </div>
                        </div>
            """
        
        # Recommendations
        recommendations = test_results.get('recommendations', [])
        report_html += f"""
                    </div>
                </div>
                
                <div class="section">
                    <h2>💡 Recommendations</h2>
                    <div class="recommendations">
                        <ul>
        """
        
        for rec in recommendations:
            report_html += f"<li>{rec}</li>"
        
        report_html += """
                        </ul>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📁 Generated Files</h2>
        """
        
        # List all generated files
        all_files = []
        for method_result in test_results['extraction_results'].values():
            if method_result.get('success') and 'extracted_files' in method_result:
                extracted_files = method_result['extracted_files']
                for file_type, file_path in extracted_files.items():
                    if isinstance(file_path, str):
                        all_files.append((file_type, file_path))
        
        if all_files:
            report_html += "<ul>"
            for file_type, file_path in all_files:
                report_html += f"<li><strong>{file_type.upper()}:</strong> {file_path}</li>"
            report_html += "</ul>"
        else:
            report_html += "<p>No output files generated</p>"
        
        # Next steps section
        next_steps = []
        
        if final_confidence >= 0.9:
            next_steps.append("🎉 Excellent results! Data is ready for production use")
        elif final_confidence >= 0.7:
            next_steps.append("✅ Good results with minor validation needed")
        else:
            next_steps.append("⚠️ Results need significant validation before use")
        
        if not coverage.get('securities_data'):
            next_steps.append("🏦 Consider manual securities identification if document contains financial instruments")
        
        if quality_metrics.get('methods_successful', 0) < quality_metrics.get('total_methods', 0):
            next_steps.append("🔧 Investigate failed extraction methods for potential improvements")
        
        report_html += f"""
                </div>
                
                <div class="section">
                    <h2>🚀 Next Steps</h2>
                    <ul>
        """
        
        for step in next_steps:
            report_html += f"<li>{step}</li>"
        
        report_html += """
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save report
        report_path = f"comprehensive_test_report_{int(time.time())}.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        logger.info(f"📄 Comprehensive report saved: {report_path}")
        
        return report_path


def main():
    """
    Main test function
    """
    print("🚀 **COMPREHENSIVE EXTRACTION TEST**")
    print("=" * 60)
    
    # Configuration
    credentials_path = "credentials/pdfservices-api-credentials.json"
    test_pdf = "input_pdfs/messos 30.5.pdf"
    
    # Check prerequisites
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials not found: {credentials_path}")
        print("Please ensure Adobe PDF Services credentials are available")
        return
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        print("Please ensure the test PDF file is available")
        return
    
    # Run comprehensive test
    try:
        tester = ComprehensiveExtractionTester(credentials_path)
        results = tester.run_complete_extraction_test(test_pdf)
        
        print(f"\n📊 **FINAL RESULTS**")
        print(f"Final Confidence: {results['final_confidence']:.1%}")
        print(f"Methods Successful: {results['quality_metrics']['methods_successful']}/{results['quality_metrics']['total_methods']}")
        print(f"Data Coverage: {results['quality_metrics']['data_coverage']['overall_percentage']:.0f}%")
        print(f"Best Method: {results['quality_metrics']['best_method']}")
        
        print(f"\n💡 **KEY RECOMMENDATIONS:**")
        for i, rec in enumerate(results['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\n✅ **TEST COMPLETED SUCCESSFULLY**")
        print(f"Check the generated HTML report for detailed analysis")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test execution failed")


if __name__ == "__main__":
    main()