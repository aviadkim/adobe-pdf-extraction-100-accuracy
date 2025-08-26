#!/usr/bin/env python3
"""
Hybrid OCR Processor - Adobe PDF Services + Azure Document Intelligence
Combines the best of both services for optimal table extraction accuracy
"""

import os
import json
import pandas as pd
import requests
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

# Import existing components
try:
    from pdf_extractor import PDFExtractor
    from advanced_pdf_extractor import AdvancedPDFExtractor
    from performance_monitor import monitor_performance
    from exceptions import OCRError, ProcessingError
    from retry_handler import with_retry
except ImportError:
    logging.warning("Some modules not available")

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Container for extraction results from different services"""
    source: str  # 'adobe' or 'azure' or 'hybrid'
    success: bool
    confidence: float
    tables: List[Dict[str, Any]]
    text_elements: List[Dict[str, Any]]
    processing_time: float
    error_message: Optional[str] = None


class HybridOCRProcessor:
    """
    Hybrid OCR processor that intelligently chooses between Adobe and Azure
    based on document characteristics and quality requirements
    """
    
    def __init__(self, adobe_credentials_path: str, azure_endpoint: str = None, 
                 azure_api_key: str = None):
        """
        Initialize hybrid processor
        
        Args:
            adobe_credentials_path: Path to Adobe PDF Services credentials
            azure_endpoint: Azure Document Intelligence endpoint
            azure_api_key: Azure Document Intelligence API key
        """
        self.adobe_credentials_path = adobe_credentials_path
        self.azure_endpoint = azure_endpoint
        self.azure_api_key = azure_api_key
        
        # Initialize Adobe extractors
        self.adobe_basic = PDFExtractor(adobe_credentials_path)
        try:
            self.adobe_advanced = AdvancedPDFExtractor(adobe_credentials_path)
        except ImportError:
            self.adobe_advanced = None
        
        # Configuration
        self.azure_available = bool(azure_endpoint and azure_api_key)
        self.confidence_threshold = 0.7
        self.processing_stats = {
            'adobe_used': 0,
            'azure_used': 0,
            'hybrid_used': 0,
            'total_processed': 0
        }
    
    @monitor_performance(cache_ttl=3600)
    def extract_tables_optimal(self, pdf_path: str, 
                             strategy: str = "auto") -> ExtractionResult:
        """
        Extract tables using optimal strategy based on document analysis
        
        Args:
            pdf_path: Path to PDF file
            strategy: 'adobe', 'azure', 'hybrid', or 'auto'
            
        Returns:
            ExtractionResult with best available extraction
        """
        self.processing_stats['total_processed'] += 1
        
        if strategy == "auto":
            strategy = self._determine_optimal_strategy(pdf_path)
        
        logger.info(f"📊 Using {strategy} strategy for {os.path.basename(pdf_path)}")
        
        if strategy == "adobe":
            return self._extract_with_adobe(pdf_path)
        elif strategy == "azure" and self.azure_available:
            return self._extract_with_azure(pdf_path)
        elif strategy == "hybrid":
            return self._extract_hybrid(pdf_path)
        else:
            # Fallback to Adobe if Azure not available
            return self._extract_with_adobe(pdf_path)
    
    def _determine_optimal_strategy(self, pdf_path: str) -> str:
        """
        Determine optimal extraction strategy based on document analysis
        
        Returns:
            Strategy name ('adobe', 'azure', or 'hybrid')
        """
        try:
            # Quick document analysis
            file_size = os.path.getsize(pdf_path)
            
            # Strategy decision logic
            if not self.azure_available:
                return "adobe"
            
            # Large files or complex documents benefit from hybrid approach
            if file_size > 10 * 1024 * 1024:  # >10MB
                return "hybrid"
            
            # For standard documents, try Adobe first (included in your plan)
            return "adobe"
            
        except Exception as e:
            logger.warning(f"Could not analyze document for strategy: {e}")
            return "adobe"  # Safe fallback
    
    @with_retry('api_calls')
    def _extract_with_adobe(self, pdf_path: str) -> ExtractionResult:
        """Extract using Adobe PDF Services API"""
        start_time = time.time()
        
        try:
            # Try advanced extractor first if available
            if self.adobe_advanced:
                result = self.adobe_advanced.extract_with_renditions(
                    input_pdf_path=pdf_path,
                    output_dir=f"temp_adobe_{int(time.time())}",
                    extract_tables=True,
                    extract_figures=True
                )
            else:
                result = self.adobe_basic.extract_tables(
                    input_pdf_path=pdf_path,
                    output_dir=f"temp_adobe_{int(time.time())}",
                    enable_ocr=True
                )
            
            processing_time = time.time() - start_time
            self.processing_stats['adobe_used'] += 1
            
            if result.get('success', False):
                # Convert Adobe result to standardized format
                tables = self._parse_adobe_tables(result.get('extracted_files', {}))
                confidence = self._calculate_adobe_confidence(tables)
                
                return ExtractionResult(
                    source='adobe',
                    success=True,
                    confidence=confidence,
                    tables=tables,
                    text_elements=[],
                    processing_time=processing_time
                )
            else:
                return ExtractionResult(
                    source='adobe',
                    success=False,
                    confidence=0.0,
                    tables=[],
                    text_elements=[],
                    processing_time=processing_time,
                    error_message=result.get('error', 'Adobe extraction failed')
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Adobe extraction failed: {e}")
            
            return ExtractionResult(
                source='adobe',
                success=False,
                confidence=0.0,
                tables=[],
                text_elements=[],
                processing_time=processing_time,
                error_message=str(e)
            )
    
    @with_retry('api_calls')
    def _extract_with_azure(self, pdf_path: str) -> ExtractionResult:
        """Extract using Azure Document Intelligence"""
        if not self.azure_available:
            raise OCRError(pdf_path, "Azure", "Azure credentials not configured")
        
        start_time = time.time()
        
        try:
            # Azure Document Intelligence API call
            headers = {
                "Ocp-Apim-Subscription-Key": self.azure_api_key,
                "Content-Type": "application/octet-stream"
            }
            
            # Read PDF file
            with open(pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
            
            # Submit for analysis
            analyze_url = f"{self.azure_endpoint}/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31"
            
            response = requests.post(analyze_url, headers=headers, data=pdf_data)
            response.raise_for_status()
            
            # Get operation location
            operation_location = response.headers.get("Operation-Location")
            if not operation_location:
                raise OCRError(pdf_path, "Azure", "No operation location returned")
            
            # Poll for results
            result = self._poll_azure_results(operation_location)
            
            processing_time = time.time() - start_time
            self.processing_stats['azure_used'] += 1
            
            if result['success']:
                return ExtractionResult(
                    source='azure',
                    success=True,
                    confidence=result['confidence'],
                    tables=result['tables'],
                    text_elements=result['text_elements'],
                    processing_time=processing_time
                )
            else:
                return ExtractionResult(
                    source='azure',
                    success=False,
                    confidence=0.0,
                    tables=[],
                    text_elements=[],
                    processing_time=processing_time,
                    error_message=result.get('error', 'Azure extraction failed')
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Azure extraction failed: {e}")
            
            return ExtractionResult(
                source='azure',
                success=False,
                confidence=0.0,
                tables=[],
                text_elements=[],
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _extract_hybrid(self, pdf_path: str) -> ExtractionResult:
        """
        Hybrid extraction using both Adobe and Azure, selecting best results
        """
        start_time = time.time()
        self.processing_stats['hybrid_used'] += 1
        
        logger.info(f"🔄 Starting hybrid extraction for {os.path.basename(pdf_path)}")
        
        # Extract with both services
        adobe_result = self._extract_with_adobe(pdf_path)
        azure_result = None
        
        if self.azure_available:
            azure_result = self._extract_with_azure(pdf_path)
        
        # Select best result
        best_result = self._select_best_result(adobe_result, azure_result)
        
        # Mark as hybrid and update timing
        best_result.source = 'hybrid'
        best_result.processing_time = time.time() - start_time
        
        logger.info(f"✅ Hybrid extraction completed, selected: {adobe_result.source if best_result == adobe_result else azure_result.source if azure_result else 'adobe'}")
        
        return best_result
    
    def _poll_azure_results(self, operation_location: str, timeout: int = 120) -> Dict[str, Any]:
        """Poll Azure for results with timeout"""
        headers = {"Ocp-Apim-Subscription-Key": self.azure_api_key}
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(operation_location, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result["status"] == "succeeded":
                return self._parse_azure_results(result)
            elif result["status"] == "failed":
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Azure processing failed")
                }
            
            time.sleep(2)  # Wait before next poll
        
        return {"success": False, "error": "Timeout waiting for Azure results"}
    
    def _parse_azure_results(self, azure_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Azure Document Intelligence results"""
        try:
            analyze_result = azure_result.get("analyzeResult", {})
            
            # Extract tables
            tables = []
            for table in analyze_result.get("tables", []):
                table_data = {
                    "rows": table.get("rowCount", 0),
                    "columns": table.get("columnCount", 0),
                    "cells": [],
                    "confidence": 0.9  # Azure typically has high confidence
                }
                
                for cell in table.get("cells", []):
                    table_data["cells"].append({
                        "row": cell.get("rowIndex", 0),
                        "column": cell.get("columnIndex", 0),
                        "content": cell.get("content", ""),
                        "confidence": cell.get("confidence", 0.8)
                    })
                
                tables.append(table_data)
            
            # Extract text elements
            text_elements = []
            for paragraph in analyze_result.get("paragraphs", []):
                text_elements.append({
                    "content": paragraph.get("content", ""),
                    "bounding_regions": paragraph.get("boundingRegions", []),
                    "confidence": 0.9
                })
            
            # Calculate overall confidence
            overall_confidence = self._calculate_azure_confidence(tables, text_elements)
            
            return {
                "success": True,
                "confidence": overall_confidence,
                "tables": tables,
                "text_elements": text_elements
            }
            
        except Exception as e:
            logger.error(f"Error parsing Azure results: {e}")
            return {"success": False, "error": f"Failed to parse Azure results: {str(e)}"}
    
    def _parse_adobe_tables(self, extracted_files: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Adobe extraction results into standardized format"""
        tables = []
        
        # Handle different Adobe output formats
        if 'json' in extracted_files:
            try:
                # Load structured data
                json_path = extracted_files['json']
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        structured_data = json.load(f)
                    
                    # Extract table information from elements
                    # This is a simplified implementation - you might need to adapt
                    # based on your actual Adobe output format
                    tables.append({
                        "rows": len(structured_data.get('elements', [])),
                        "columns": 1,  # Simplified
                        "cells": [],
                        "confidence": 0.7  # Adobe baseline confidence
                    })
                    
            except Exception as e:
                logger.warning(f"Could not parse Adobe JSON: {e}")
        
        return tables
    
    def _calculate_adobe_confidence(self, tables: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for Adobe extraction"""
        if not tables:
            return 0.0
        
        # Adobe confidence factors
        factors = []
        
        for table in tables:
            row_count = table.get('rows', 0)
            col_count = table.get('columns', 0)
            
            # More rows/columns generally indicate better structure detection
            structure_score = min(1.0, (row_count * col_count) / 20)  # Normalize to 0-1
            factors.append(structure_score)
        
        return np.mean(factors) if factors else 0.5
    
    def _calculate_azure_confidence(self, tables: List[Dict[str, Any]], 
                                   text_elements: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for Azure extraction"""
        confidence_scores = []
        
        # Table confidence
        for table in tables:
            table_confidence = table.get('confidence', 0.8)
            confidence_scores.append(table_confidence)
        
        # Text confidence
        for text in text_elements:
            text_confidence = text.get('confidence', 0.8)
            confidence_scores.append(text_confidence)
        
        return np.mean(confidence_scores) if confidence_scores else 0.8
    
    def _select_best_result(self, adobe_result: ExtractionResult, 
                           azure_result: Optional[ExtractionResult]) -> ExtractionResult:
        """Select the best result from Adobe and Azure extractions"""
        
        # If only one service succeeded, use it
        if adobe_result.success and (not azure_result or not azure_result.success):
            return adobe_result
        
        if azure_result and azure_result.success and not adobe_result.success:
            return azure_result
        
        # If both succeeded, compare confidence and table quality
        if adobe_result.success and azure_result and azure_result.success:
            adobe_score = self._calculate_result_score(adobe_result)
            azure_score = self._calculate_result_score(azure_result)
            
            logger.info(f"🔍 Comparison scores - Adobe: {adobe_score:.3f}, Azure: {azure_score:.3f}")
            
            return azure_result if azure_score > adobe_score else adobe_result
        
        # Both failed - return Adobe result with error info
        return adobe_result
    
    def _calculate_result_score(self, result: ExtractionResult) -> float:
        """Calculate overall score for result selection"""
        if not result.success:
            return 0.0
        
        # Base confidence
        score = result.confidence
        
        # Bonus for more tables found
        table_bonus = min(0.2, len(result.tables) * 0.05)
        score += table_bonus
        
        # Penalty for long processing time (prefer faster results if similar quality)
        time_penalty = min(0.1, result.processing_time / 100.0)  # Seconds to penalty ratio
        score -= time_penalty
        
        return max(0.0, min(1.0, score))
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.processing_stats.copy()
        
        if stats['total_processed'] > 0:
            stats['adobe_percentage'] = (stats['adobe_used'] / stats['total_processed']) * 100
            stats['azure_percentage'] = (stats['azure_used'] / stats['total_processed']) * 100
            stats['hybrid_percentage'] = (stats['hybrid_used'] / stats['total_processed']) * 100
        
        return stats
    
    def benchmark_services(self, test_pdf_path: str) -> Dict[str, Any]:
        """
        Benchmark both services on a test document
        
        Returns:
            Comparison report
        """
        logger.info(f"🔬 Benchmarking services on {os.path.basename(test_pdf_path)}")
        
        # Test Adobe
        adobe_result = self._extract_with_adobe(test_pdf_path)
        
        # Test Azure (if available)
        azure_result = None
        if self.azure_available:
            azure_result = self._extract_with_azure(test_pdf_path)
        
        # Create comparison report
        report = {
            'test_file': os.path.basename(test_pdf_path),
            'timestamp': time.time(),
            'adobe': {
                'success': adobe_result.success,
                'confidence': adobe_result.confidence,
                'processing_time': adobe_result.processing_time,
                'tables_found': len(adobe_result.tables),
                'error': adobe_result.error_message
            }
        }
        
        if azure_result:
            report['azure'] = {
                'success': azure_result.success,
                'confidence': azure_result.confidence,
                'processing_time': azure_result.processing_time,
                'tables_found': len(azure_result.tables),
                'error': azure_result.error_message
            }
            
            # Winner determination
            if adobe_result.success and azure_result.success:
                adobe_score = self._calculate_result_score(adobe_result)
                azure_score = self._calculate_result_score(azure_result)
                report['winner'] = 'azure' if azure_score > adobe_score else 'adobe'
                report['score_difference'] = abs(azure_score - adobe_score)
            elif azure_result.success:
                report['winner'] = 'azure'
            elif adobe_result.success:
                report['winner'] = 'adobe'
            else:
                report['winner'] = 'none'
        
        return report


# Convenience functions
def create_hybrid_processor(adobe_credentials_path: str, 
                          azure_endpoint: str = None, 
                          azure_api_key: str = None) -> HybridOCRProcessor:
    """Create hybrid processor with provided credentials"""
    return HybridOCRProcessor(adobe_credentials_path, azure_endpoint, azure_api_key)


def extract_tables_best_quality(pdf_path: str, 
                               adobe_credentials_path: str,
                               azure_endpoint: str = None,
                               azure_api_key: str = None) -> ExtractionResult:
    """
    Convenience function to extract tables with best available quality
    """
    processor = create_hybrid_processor(adobe_credentials_path, azure_endpoint, azure_api_key)
    return processor.extract_tables_optimal(pdf_path, strategy="auto")


if __name__ == "__main__":
    # Example usage and benchmarking
    processor = HybridOCRProcessor(
        adobe_credentials_path="credentials/pdfservices-api-credentials.json",
        # azure_endpoint="your_azure_endpoint",
        # azure_api_key="your_azure_key"
    )
    
    test_pdf = "input_pdfs/sample.pdf"  # Replace with actual test file
    
    if os.path.exists(test_pdf):
        # Benchmark both services
        benchmark = processor.benchmark_services(test_pdf)
        print(f"📊 Benchmark Results:")
        print(json.dumps(benchmark, indent=2, default=str))
        
        # Extract with optimal strategy
        result = processor.extract_tables_optimal(test_pdf)
        
        print(f"\n🎯 Optimal Extraction Results:")
        print(f"Source: {result.source}")
        print(f"Success: {result.success}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Tables: {len(result.tables)}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        
        # Show processing stats
        stats = processor.get_processing_stats()
        print(f"\n📈 Processing Statistics:")
        print(json.dumps(stats, indent=2))
    else:
        print(f"Test file not found: {test_pdf}")