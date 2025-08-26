#!/usr/bin/env python3
"""
Enhanced Adobe PDF Processor - Maximum Quality without Azure
Optimizes Adobe PDF Services API for best possible extraction results
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import time
from pathlib import Path

# Import existing components
try:
    from pdf_extractor import PDFExtractor
    from advanced_pdf_extractor import AdvancedPDFExtractor
    from optimized_spatial_analysis import create_spatial_analyzer, analyze_spatial_structure
    from complete_data_extractor import CompleteDataExtractor
    from securities_extractor import SecuritiesExtractor
    from performance_monitor import monitor_performance
    from exceptions import TableExtractionError, OCRError
    from retry_handler import with_retry
except ImportError:
    logging.warning("Some modules not available")

logger = logging.getLogger(__name__)


class EnhancedAdobeProcessor:
    """
    Enhanced Adobe PDF processor that maximizes extraction quality
    using only Adobe PDF Services API with advanced post-processing
    """
    
    def __init__(self, credentials_path: str):
        """
        Initialize enhanced Adobe processor
        
        Args:
            credentials_path: Path to Adobe PDF Services credentials
        """
        self.credentials_path = credentials_path
        
        # Initialize extractors
        self.basic_extractor = PDFExtractor(credentials_path)
        try:
            self.advanced_extractor = AdvancedPDFExtractor(credentials_path)
            self.has_advanced = True
        except ImportError:
            self.has_advanced = False
            logger.warning("Advanced extractor not available, using basic extractor only")
        
        # Initialize analyzers
        self.spatial_analyzer = create_spatial_analyzer(enable_parallel=True)
        
        # Quality enhancement settings
        self.quality_settings = {
            'enable_multiple_passes': True,
            'enable_spatial_enhancement': True,
            'enable_confidence_boosting': True,
            'min_confidence_threshold': 0.3
        }
    
    @monitor_performance(cache_ttl=3600)
    def extract_with_maximum_quality(self, pdf_path: str, 
                                   output_dir: str = "enhanced_output") -> Dict[str, Any]:
        """
        Extract PDF data with maximum quality using enhanced Adobe processing
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory for results
            
        Returns:
            Enhanced extraction results
        """
        logger.info(f"🚀 Starting enhanced Adobe extraction: {os.path.basename(pdf_path)}")
        start_time = time.time()
        
        # Step 1: Multi-pass extraction
        extraction_results = self._multi_pass_extraction(pdf_path, output_dir)
        
        # Step 2: Enhanced spatial analysis
        if extraction_results['success'] and self.quality_settings['enable_spatial_enhancement']:
            extraction_results = self._enhance_with_spatial_analysis(extraction_results)
        
        # Step 3: Confidence boosting
        if self.quality_settings['enable_confidence_boosting']:
            extraction_results = self._boost_extraction_confidence(extraction_results)
        
        # Step 4: Quality validation
        extraction_results = self._validate_extraction_quality(extraction_results)
        
        extraction_results['total_processing_time'] = time.time() - start_time
        extraction_results['enhancement_applied'] = True
        
        logger.info(f"✅ Enhanced extraction completed in {extraction_results['total_processing_time']:.2f}s")
        
        return extraction_results
    
    @with_retry('api_calls')
    def _multi_pass_extraction(self, pdf_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Perform multi-pass extraction to get best results
        """
        passes = []
        
        # Pass 1: Basic extraction with OCR enabled
        logger.info("📋 Pass 1: Basic extraction with OCR")
        try:
            result_basic = self.basic_extractor.extract_tables(
                input_pdf_path=pdf_path,
                output_dir=f"{output_dir}/pass1_basic",
                table_format="csv",
                extract_text=True,
                enable_ocr=True
            )
            result_basic['pass_type'] = 'basic_ocr'
            passes.append(result_basic)
        except Exception as e:
            logger.error(f"Basic extraction failed: {e}")
            passes.append({'success': False, 'pass_type': 'basic_ocr', 'error': str(e)})
        
        # Pass 2: Advanced extraction with renditions (if available)
        if self.has_advanced:
            logger.info("📋 Pass 2: Advanced extraction with renditions")
            try:
                result_advanced = self.advanced_extractor.extract_with_renditions(
                    input_pdf_path=pdf_path,
                    output_dir=f"{output_dir}/pass2_advanced",
                    table_format="csv",
                    extract_text=True,
                    extract_figures=True,
                    extract_tables=True
                )
                result_advanced['pass_type'] = 'advanced_renditions'
                passes.append(result_advanced)
            except Exception as e:
                logger.error(f"Advanced extraction failed: {e}")
                passes.append({'success': False, 'pass_type': 'advanced_renditions', 'error': str(e)})
        
        # Pass 3: Excel format extraction (different parser might catch different tables)
        logger.info("📋 Pass 3: Excel format extraction")
        try:
            result_excel = self.basic_extractor.extract_tables(
                input_pdf_path=pdf_path,
                output_dir=f"{output_dir}/pass3_excel",
                table_format="xlsx",
                extract_text=True,
                enable_ocr=True
            )
            result_excel['pass_type'] = 'excel_format'
            passes.append(result_excel)
        except Exception as e:
            logger.error(f"Excel format extraction failed: {e}")
            passes.append({'success': False, 'pass_type': 'excel_format', 'error': str(e)})
        
        # Select best result from all passes
        best_result = self._select_best_extraction_pass(passes)
        best_result['all_passes'] = passes
        
        return best_result
    
    def _select_best_extraction_pass(self, passes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best extraction result from multiple passes"""
        successful_passes = [p for p in passes if p.get('success', False)]
        
        if not successful_passes:
            # All passes failed, return the first one with error info
            return passes[0] if passes else {'success': False, 'error': 'No extraction passes completed'}
        
        # Score each successful pass
        best_pass = None
        best_score = 0
        
        for pass_result in successful_passes:
            score = self._calculate_extraction_score(pass_result)
            logger.info(f"📊 {pass_result['pass_type']} score: {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_pass = pass_result
        
        logger.info(f"🏆 Selected best pass: {best_pass['pass_type']} (score: {best_score:.3f})")
        return best_pass
    
    def _calculate_extraction_score(self, pass_result: Dict[str, Any]) -> float:
        """Calculate quality score for an extraction pass"""
        if not pass_result.get('success', False):
            return 0.0
        
        score = 0.5  # Base score
        
        # Bonus for having extracted files
        extracted_files = pass_result.get('extracted_files', {})
        if extracted_files:
            score += 0.3
            
            # Extra bonus for multiple file types
            if len(extracted_files) > 1:
                score += 0.1
        
        # Bonus for renditions (advanced extraction)
        if pass_result.get('renditions_extracted', False):
            score += 0.2
        
        # Bonus for specific pass types
        pass_type = pass_result.get('pass_type', '')
        if pass_type == 'advanced_renditions':
            score += 0.1
        elif pass_type == 'excel_format':
            score += 0.05
        
        return min(1.0, score)
    
    def _enhance_with_spatial_analysis(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance extraction with spatial analysis post-processing"""
        logger.info("🔍 Enhancing with spatial analysis")
        
        try:
            # Load extracted JSON data for spatial analysis
            extracted_files = extraction_result.get('extracted_files', {})
            json_file = extracted_files.get('json')
            
            if json_file and os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    structured_data = json.load(f)
                
                # Get elements for spatial analysis
                elements_data = structured_data.get('elements', [])
                
                if elements_data:
                    # Perform spatial analysis
                    spatial_results = self.spatial_analyzer.analyze_document(elements_data)
                    
                    # Enhance extraction result with spatial analysis
                    extraction_result['spatial_analysis'] = spatial_results
                    extraction_result['spatial_tables_found'] = len(spatial_results.get('tables', []))
                    extraction_result['spatial_confidence'] = spatial_results.get('performance_score', 0)
                    
                    # Use spatial analysis to improve table detection confidence
                    if spatial_results.get('tables'):
                        extraction_result['enhanced_table_confidence'] = True
                        logger.info(f"✅ Spatial analysis found {len(spatial_results['tables'])} additional table structures")
                    
        except Exception as e:
            logger.error(f"Spatial analysis enhancement failed: {e}")
            extraction_result['spatial_analysis_error'] = str(e)
        
        return extraction_result
    
    def _boost_extraction_confidence(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply confidence boosting techniques"""
        logger.info("📈 Applying confidence boosting")
        
        confidence_factors = []
        
        # Factor 1: Successful extraction
        if extraction_result.get('success', False):
            confidence_factors.append(0.6)
        
        # Factor 2: Multiple file types extracted
        extracted_files = extraction_result.get('extracted_files', {})
        if len(extracted_files) > 1:
            confidence_factors.append(0.2)
        
        # Factor 3: Spatial analysis success
        spatial_tables = extraction_result.get('spatial_tables_found', 0)
        if spatial_tables > 0:
            confidence_factors.append(0.3)
        
        # Factor 4: Advanced features used
        if extraction_result.get('renditions_extracted', False):
            confidence_factors.append(0.2)
        
        # Factor 5: File size and complexity indicators
        if extraction_result.get('pass_type') == 'advanced_renditions':
            confidence_factors.append(0.1)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.3
        overall_confidence = min(1.0, overall_confidence)
        
        extraction_result['extraction_confidence'] = overall_confidence
        extraction_result['confidence_factors'] = confidence_factors
        
        logger.info(f"📊 Overall extraction confidence: {overall_confidence:.3f}")
        
        return extraction_result
    
    def _validate_extraction_quality(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and report extraction quality"""
        logger.info("🔍 Validating extraction quality")
        
        quality_checks = {
            'has_extracted_files': bool(extraction_result.get('extracted_files')),
            'has_json_output': 'json' in extraction_result.get('extracted_files', {}),
            'has_table_output': any(k in extraction_result.get('extracted_files', {}) for k in ['csv', 'xlsx']),
            'spatial_analysis_success': 'spatial_analysis' in extraction_result,
            'confidence_above_threshold': extraction_result.get('extraction_confidence', 0) > self.quality_settings['min_confidence_threshold']
        }
        
        passed_checks = sum(quality_checks.values())
        total_checks = len(quality_checks)
        quality_score = passed_checks / total_checks
        
        extraction_result['quality_validation'] = {
            'checks': quality_checks,
            'passed': passed_checks,
            'total': total_checks,
            'score': quality_score,
            'grade': self._get_quality_grade(quality_score)
        }
        
        logger.info(f"🎯 Quality validation: {passed_checks}/{total_checks} checks passed ({quality_score:.1%})")
        logger.info(f"📝 Quality grade: {self._get_quality_grade(quality_score)}")
        
        return extraction_result
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 0.9:
            return "A+ (Excellent)"
        elif score >= 0.8:
            return "A (Very Good)"
        elif score >= 0.7:
            return "B (Good)"
        elif score >= 0.6:
            return "C (Fair)"
        elif score >= 0.5:
            return "D (Poor)"
        else:
            return "F (Failed)"
    
    def extract_securities_enhanced(self, pdf_path: str) -> Dict[str, Any]:
        """
        Enhanced securities extraction combining multiple techniques
        """
        logger.info("🏦 Starting enhanced securities extraction")
        
        # First get basic extraction
        basic_result = self.extract_with_maximum_quality(pdf_path)
        
        if not basic_result['success']:
            return basic_result
        
        # Use securities extractor for specialized analysis
        try:
            securities_extractor = SecuritiesExtractor()
            
            # Mock the paths for the securities extractor based on our results
            extracted_files = basic_result.get('extracted_files', {})
            if 'json' in extracted_files:
                securities_extractor.json_file = extracted_files['json']
                securities_extractor.figures_dir = os.path.dirname(extracted_files['json']) + "/figures"
            
            securities_report = securities_extractor.create_comprehensive_securities_report()
            
            # Combine results
            basic_result['securities_analysis'] = securities_report
            basic_result['securities_found'] = securities_report.get('extraction_summary', {}).get('total_securities_identified', 0)
            
            logger.info(f"🏦 Securities analysis completed: {basic_result['securities_found']} securities identified")
            
        except Exception as e:
            logger.error(f"Securities analysis failed: {e}")
            basic_result['securities_analysis_error'] = str(e)
        
        return basic_result
    
    def create_enhanced_report(self, extraction_result: Dict[str, Any]) -> str:
        """Create a comprehensive HTML report of extraction results"""
        
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Adobe PDF Extraction Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; border-radius: 8px 8px 0 0; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ background: #d4edda; border-color: #c3e6cb; }}
                .warning {{ background: #fff3cd; border-color: #ffeaa7; }}
                .info {{ background: #d1ecf1; border-color: #bee5eb; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }}
                .grade-A {{ color: #28a745; font-weight: bold; }}
                .grade-B {{ color: #ffc107; font-weight: bold; }}
                .grade-C {{ color: #fd7e14; font-weight: bold; }}
                .grade-D {{ color: #dc3545; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Enhanced Adobe PDF Extraction Report</h1>
                    <p>Advanced processing with spatial analysis and confidence boosting</p>
                </div>
                
                <div class="section {'success' if extraction_result.get('success') else 'warning'}">
                    <h2>📊 Extraction Summary</h2>
                    <div class="metric">
                        <strong>Status:</strong> {'✅ Success' if extraction_result.get('success') else '❌ Failed'}
                    </div>
                    <div class="metric">
                        <strong>Processing Time:</strong> {extraction_result.get('total_processing_time', 0):.2f}s
                    </div>
                    <div class="metric">
                        <strong>Confidence:</strong> {extraction_result.get('extraction_confidence', 0):.1%}
                    </div>
                </div>
                
                <div class="section info">
                    <h2>🔍 Quality Assessment</h2>
        """
        
        quality_val = extraction_result.get('quality_validation', {})
        quality_score = quality_val.get('score', 0)
        quality_grade = quality_val.get('grade', 'Unknown')
        
        grade_class = 'grade-A' if quality_score >= 0.8 else 'grade-B' if quality_score >= 0.6 else 'grade-C' if quality_score >= 0.4 else 'grade-D'
        
        report_html += f"""
                    <p class="{grade_class}">Quality Grade: {quality_grade}</p>
                    <p>Quality Score: {quality_score:.1%} ({quality_val.get('passed', 0)}/{quality_val.get('total', 0)} checks passed)</p>
                    
                    <h3>Quality Checks:</h3>
                    <ul>
        """
        
        for check, passed in quality_val.get('checks', {}).items():
            status = '✅' if passed else '❌'
            report_html += f"<li>{status} {check.replace('_', ' ').title()}</li>"
        
        report_html += "</ul></div>"
        
        # Add spatial analysis section if available
        spatial_analysis = extraction_result.get('spatial_analysis')
        if spatial_analysis:
            report_html += f"""
                <div class="section info">
                    <h2>🗺️ Spatial Analysis Results</h2>
                    <div class="metric">
                        <strong>Elements Processed:</strong> {spatial_analysis.get('elements_processed', 0)}
                    </div>
                    <div class="metric">
                        <strong>Tables Found:</strong> {len(spatial_analysis.get('tables', []))}
                    </div>
                    <div class="metric">
                        <strong>Analysis Time:</strong> {spatial_analysis.get('analysis_time', 0):.2f}s
                    </div>
                    <div class="metric">
                        <strong>Performance Score:</strong> {spatial_analysis.get('performance_score', 0):.3f}
                    </div>
                </div>
            """
        
        # Add extraction passes information
        passes = extraction_result.get('all_passes', [])
        if passes:
            report_html += """
                <div class="section info">
                    <h2>📋 Extraction Passes</h2>
                    <table>
                        <tr><th>Pass Type</th><th>Status</th><th>Files Extracted</th><th>Score</th></tr>
            """
            
            for pass_result in passes:
                status = '✅ Success' if pass_result.get('success') else '❌ Failed'
                files_count = len(pass_result.get('extracted_files', {}))
                score = self._calculate_extraction_score(pass_result)
                
                report_html += f"""
                        <tr>
                            <td>{pass_result.get('pass_type', 'Unknown')}</td>
                            <td>{status}</td>
                            <td>{files_count}</td>
                            <td>{score:.3f}</td>
                        </tr>
                """
            
            report_html += "</table></div>"
        
        report_html += """
                <div class="section success">
                    <h2>📁 Output Files</h2>
        """
        
        extracted_files = extraction_result.get('extracted_files', {})
        if extracted_files:
            report_html += "<ul>"
            for file_type, file_path in extracted_files.items():
                report_html += f"<li><strong>{file_type.upper()}:</strong> {file_path}</li>"
            report_html += "</ul>"
        else:
            report_html += "<p>No files extracted</p>"
        
        report_html += """
                </div>
                
                <div class="section info">
                    <h2>💡 Recommendations</h2>
        """
        
        # Add recommendations based on results
        recommendations = []
        
        if extraction_result.get('extraction_confidence', 0) < 0.6:
            recommendations.append("Consider manual validation of extracted data due to low confidence score")
        
        if not spatial_analysis:
            recommendations.append("Spatial analysis could not be performed - check input file quality")
        
        if len(passes) == 1:
            recommendations.append("Only one extraction pass completed - document may benefit from multiple approaches")
        
        if not extracted_files:
            recommendations.append("No files were extracted - check PDF format and Adobe API connectivity")
        
        if not recommendations:
            recommendations.append("Extraction completed successfully with high quality results")
        
        for rec in recommendations:
            report_html += f"<p>• {rec}</p>"
        
        report_html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save report
        report_path = "enhanced_extraction_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        logger.info(f"📄 Enhanced report saved: {report_path}")
        return report_path


# Convenience functions
def extract_pdf_enhanced(pdf_path: str, credentials_path: str) -> Dict[str, Any]:
    """
    Convenience function for enhanced PDF extraction
    """
    processor = EnhancedAdobeProcessor(credentials_path)
    return processor.extract_with_maximum_quality(pdf_path)


def extract_securities_enhanced(pdf_path: str, credentials_path: str) -> Dict[str, Any]:
    """
    Convenience function for enhanced securities extraction
    """
    processor = EnhancedAdobeProcessor(credentials_path)
    return processor.extract_securities_enhanced(pdf_path)


if __name__ == "__main__":
    # Example usage
    processor = EnhancedAdobeProcessor("credentials/pdfservices-api-credentials.json")
    
    test_pdf = "input_pdfs/sample.pdf"  # Replace with your test file
    
    if os.path.exists(test_pdf):
        # Enhanced extraction
        result = processor.extract_with_maximum_quality(test_pdf)
        
        print(f"✅ Enhanced extraction completed!")
        print(f"Success: {result['success']}")
        print(f"Confidence: {result.get('extraction_confidence', 0):.1%}")
        print(f"Quality Grade: {result.get('quality_validation', {}).get('grade', 'Unknown')}")
        print(f"Processing Time: {result.get('total_processing_time', 0):.2f}s")
        
        # Create report
        report_path = processor.create_enhanced_report(result)
        print(f"📄 Report created: {report_path}")
        
    else:
        print(f"Test file not found: {test_pdf}")
        print("Place a PDF file in input_pdfs/ directory to test enhanced extraction")