#!/usr/bin/env python3
"""
Async Batch Processing for Adobe PDF Extraction System
Provides high-performance async processing for multiple PDF files with rate limiting and progress tracking
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable, Union, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
from asyncio_throttle import Throttler
from contextlib import asynccontextmanager

# Import our custom modules
try:
    from pdf_extractor import PDFExtractor
    from advanced_pdf_extractor import AdvancedPDFExtractor
    from exceptions import PDFNotFoundError, APIQuotaExceededError, TemporaryAPIError
    from performance_monitor import PerformanceMonitor, monitor_performance
    from retry_handler import with_retry, RetryConfig, RetryStrategy
    from logging_config import get_performance_logger
except ImportError as e:
    logging.warning(f"Some modules not available for async processing: {e}")

logger = logging.getLogger(__name__)
perf_logger = get_performance_logger()


@dataclass
class BatchJobConfig:
    """Configuration for batch processing jobs"""
    max_concurrent_jobs: int = 5
    rate_limit_per_minute: int = 30
    chunk_size: int = 10
    enable_caching: bool = True
    output_base_dir: str = "batch_output"
    table_format: str = "csv"
    extract_text: bool = True
    enable_ocr: bool = True
    advanced_extraction: bool = False
    progress_callback: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        result = asdict(self)
        result.pop('progress_callback', None)  # Remove non-serializable callback
        return result


@dataclass
class BatchJobResult:
    """Result of a single PDF processing job"""
    pdf_path: str
    success: bool
    output_files: Dict[str, str] = None
    error_message: str = None
    processing_time: float = 0.0
    file_size_mb: float = 0.0
    pages_processed: int = 0
    tables_found: int = 0
    extraction_confidence: float = 0.0
    cache_hit: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.output_files is None:
            self.output_files = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class BatchProcessingReport:
    """Comprehensive report for batch processing session"""
    total_files: int
    successful_extractions: int
    failed_extractions: int
    total_processing_time: float
    avg_processing_time: float
    total_file_size_mb: float
    total_tables_found: int
    cache_hit_rate: float
    start_time: datetime
    end_time: datetime
    config: BatchJobConfig
    results: List[BatchJobResult]
    errors_by_type: Dict[str, int]
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.successful_extractions / self.total_files) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        result['success_rate'] = self.get_success_rate()
        result['config'] = self.config.to_dict()
        result['results'] = [r.to_dict() for r in self.results]
        return result


class ProgressTracker:
    """Thread-safe progress tracker for batch operations"""
    
    def __init__(self, total_items: int):
        self.total_items = total_items
        self.completed_items = 0
        self.failed_items = 0
        self.lock = asyncio.Lock()
        self.callbacks: List[Callable] = []
    
    async def update(self, success: bool = True):
        """Update progress counters"""
        async with self.lock:
            self.completed_items += 1
            if not success:
                self.failed_items += 1
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self.get_progress_info())
                    else:
                        callback(self.get_progress_info())
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information"""
        return {
            'total': self.total_items,
            'completed': self.completed_items,
            'failed': self.failed_items,
            'success': self.completed_items - self.failed_items,
            'percentage': (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0,
            'remaining': self.total_items - self.completed_items
        }
    
    def add_callback(self, callback: Callable):
        """Add progress callback"""
        self.callbacks.append(callback)


class AsyncPDFProcessor:
    """Async wrapper for PDF processing with rate limiting"""
    
    def __init__(self, extractor: Union[PDFExtractor, AdvancedPDFExtractor], 
                 throttler: Throttler):
        self.extractor = extractor
        self.throttler = throttler
        self.performance_monitor = PerformanceMonitor()
    
    @with_retry('api_calls')
    async def process_pdf_async(self, pdf_path: str, config: BatchJobConfig) -> BatchJobResult:
        """Process single PDF asynchronously with throttling"""
        start_time = time.time()
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            return BatchJobResult(
                pdf_path=pdf_path,
                success=False,
                error_message=f"PDF file not found: {pdf_path}",
                processing_time=time.time() - start_time
            )
        
        # Get file size
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        
        try:
            # Apply rate limiting
            async with self.throttler:
                # Run extraction in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    if config.advanced_extraction and isinstance(self.extractor, AdvancedPDFExtractor):
                        extraction_func = self.extractor.extract_with_renditions
                        extraction_args = {
                            'input_pdf_path': pdf_path,
                            'output_dir': os.path.join(config.output_base_dir, Path(pdf_path).stem),
                            'table_format': config.table_format,
                            'extract_text': config.extract_text,
                            'extract_figures': True,
                            'extract_tables': True
                        }
                    else:
                        extraction_func = self.extractor.extract_tables
                        extraction_args = {
                            'input_pdf_path': pdf_path,
                            'output_dir': os.path.join(config.output_base_dir, Path(pdf_path).stem),
                            'table_format': config.table_format,
                            'extract_text': config.extract_text,
                            'enable_ocr': config.enable_ocr
                        }
                    
                    # Execute extraction
                    result = await loop.run_in_executor(
                        executor, 
                        lambda: extraction_func(**extraction_args)
                    )
            
            processing_time = time.time() - start_time
            
            if result.get('success', False):
                # Extract additional metadata
                extracted_files = result.get('extracted_files', {})
                tables_found = len([f for f in extracted_files.values() 
                                  if isinstance(f, list)]) or (1 if extracted_files else 0)
                
                return BatchJobResult(
                    pdf_path=pdf_path,
                    success=True,
                    output_files=extracted_files,
                    processing_time=processing_time,
                    file_size_mb=file_size_mb,
                    tables_found=tables_found,
                    extraction_confidence=0.85  # Default confidence
                )
            else:
                return BatchJobResult(
                    pdf_path=pdf_path,
                    success=False,
                    error_message=result.get('error', 'Unknown extraction error'),
                    processing_time=processing_time,
                    file_size_mb=file_size_mb
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            # Check if it's a retryable error
            if any(keyword in error_msg.lower() for keyword in ['timeout', 'connection', 'temporary']):
                raise TemporaryAPIError(f"Temporary error processing {pdf_path}: {error_msg}")
            
            return BatchJobResult(
                pdf_path=pdf_path,
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                file_size_mb=file_size_mb
            )


class AsyncBatchProcessor:
    """High-performance async batch processor for PDF extraction"""
    
    def __init__(self, credentials_path: str, config: Optional[BatchJobConfig] = None):
        """
        Initialize async batch processor
        
        Args:
            credentials_path: Path to Adobe API credentials
            config: Batch processing configuration
        """
        self.credentials_path = credentials_path
        self.config = config or BatchJobConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize extractors
        if self.config.advanced_extraction:
            try:
                self.extractor = AdvancedPDFExtractor(credentials_path)
            except ImportError:
                logger.warning("Advanced extractor not available, falling back to basic extractor")
                self.extractor = PDFExtractor(credentials_path)
        else:
            self.extractor = PDFExtractor(credentials_path)
        
        # Setup rate limiting
        rate_per_second = self.config.rate_limit_per_minute / 60.0
        self.throttler = Throttler(rate_limit=rate_per_second)
        
        # Initialize processor
        self.processor = AsyncPDFProcessor(self.extractor, self.throttler)
    
    async def process_batch(self, pdf_files: List[str], 
                          progress_callback: Optional[Callable] = None) -> BatchProcessingReport:
        """
        Process a batch of PDF files asynchronously
        
        Args:
            pdf_files: List of PDF file paths to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Batch processing report with results and statistics
        """
        start_time = datetime.now()
        
        # Setup progress tracking
        progress_tracker = ProgressTracker(len(pdf_files))
        if progress_callback:
            progress_tracker.add_callback(progress_callback)
        if self.config.progress_callback:
            progress_tracker.add_callback(self.config.progress_callback)
        
        # Create output directory
        os.makedirs(self.config.output_base_dir, exist_ok=True)
        
        logger.info(f"🚀 Starting batch processing of {len(pdf_files)} PDF files")
        logger.info(f"📋 Config: {self.config.max_concurrent_jobs} concurrent, {self.config.rate_limit_per_minute}/min rate limit")
        
        # Process files in chunks to manage memory
        all_results = []
        total_processing_time = 0.0
        cache_hits = 0
        errors_by_type = {}
        
        # Process files in chunks
        for chunk_start in range(0, len(pdf_files), self.config.chunk_size):
            chunk_end = min(chunk_start + self.config.chunk_size, len(pdf_files))
            chunk_files = pdf_files[chunk_start:chunk_end]
            
            logger.info(f"📦 Processing chunk {chunk_start//self.config.chunk_size + 1}: files {chunk_start+1}-{chunk_end}")
            
            # Process chunk concurrently
            semaphore = asyncio.Semaphore(self.config.max_concurrent_jobs)
            
            async def process_with_semaphore(pdf_path: str) -> BatchJobResult:
                async with semaphore:
                    result = await self.processor.process_pdf_async(pdf_path, self.config)
                    await progress_tracker.update(result.success)
                    return result
            
            # Execute chunk
            chunk_tasks = [process_with_semaphore(pdf_path) for pdf_path in chunk_files]
            chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            for result in chunk_results:
                if isinstance(result, Exception):
                    # Handle exception
                    error_type = type(result).__name__
                    errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
                    
                    # Create error result
                    failed_result = BatchJobResult(
                        pdf_path="unknown",
                        success=False,
                        error_message=str(result),
                        processing_time=0.0
                    )
                    all_results.append(failed_result)
                else:
                    all_results.append(result)
                    total_processing_time += result.processing_time
                    if result.cache_hit:
                        cache_hits += 1
                    
                    # Track error types
                    if not result.success and result.error_message:
                        error_type = "ExtractionError"
                        if "not found" in result.error_message.lower():
                            error_type = "FileNotFound"
                        elif "credentials" in result.error_message.lower():
                            error_type = "CredentialsError"
                        elif "api" in result.error_message.lower():
                            error_type = "APIError"
                        
                        errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
            
            # Small delay between chunks to be respectful to API
            if chunk_end < len(pdf_files):
                await asyncio.sleep(1.0)
        
        end_time = datetime.now()
        
        # Calculate statistics
        successful_count = sum(1 for r in all_results if r.success)
        failed_count = len(all_results) - successful_count
        avg_processing_time = total_processing_time / len(all_results) if all_results else 0.0
        total_file_size_mb = sum(r.file_size_mb for r in all_results)
        total_tables_found = sum(r.tables_found for r in all_results if r.success)
        cache_hit_rate = (cache_hits / len(all_results)) * 100 if all_results else 0.0
        
        # Create comprehensive report
        report = BatchProcessingReport(
            total_files=len(pdf_files),
            successful_extractions=successful_count,
            failed_extractions=failed_count,
            total_processing_time=(end_time - start_time).total_seconds(),
            avg_processing_time=avg_processing_time,
            total_file_size_mb=total_file_size_mb,
            total_tables_found=total_tables_found,
            cache_hit_rate=cache_hit_rate,
            start_time=start_time,
            end_time=end_time,
            config=self.config,
            results=all_results,
            errors_by_type=errors_by_type
        )
        
        # Log summary
        logger.info(f"✅ Batch processing completed!")
        logger.info(f"📊 Results: {successful_count}/{len(pdf_files)} successful ({report.get_success_rate():.1f}%)")
        logger.info(f"⏱️  Total time: {report.total_processing_time:.1f}s, Avg: {avg_processing_time:.1f}s per file")
        logger.info(f"💾 Cache hit rate: {cache_hit_rate:.1f}%")
        logger.info(f"📋 Tables found: {total_tables_found}")
        
        if errors_by_type:
            logger.warning(f"❌ Errors by type: {errors_by_type}")
        
        # Save report
        await self._save_batch_report(report)
        
        return report
    
    async def _save_batch_report(self, report: BatchProcessingReport):
        """Save batch processing report to file"""
        try:
            report_file = os.path.join(
                self.config.output_base_dir, 
                f"batch_report_{report.start_time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Batch report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save batch report: {e}")
    
    async def process_directory(self, directory: str, pattern: str = "*.pdf",
                              recursive: bool = True, 
                              progress_callback: Optional[Callable] = None) -> BatchProcessingReport:
        """
        Process all PDF files in a directory
        
        Args:
            directory: Directory to scan for PDF files
            pattern: File pattern to match (default: "*.pdf")
            recursive: Whether to scan subdirectories
            progress_callback: Optional progress callback
            
        Returns:
            Batch processing report
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find PDF files
        if recursive:
            pdf_files = list(directory_path.rglob(pattern))
        else:
            pdf_files = list(directory_path.glob(pattern))
        
        pdf_paths = [str(p) for p in pdf_files]
        
        logger.info(f"📁 Found {len(pdf_paths)} PDF files in {directory}")
        
        if not pdf_paths:
            logger.warning(f"No PDF files found in {directory} with pattern {pattern}")
            return BatchProcessingReport(
                total_files=0,
                successful_extractions=0,
                failed_extractions=0,
                total_processing_time=0.0,
                avg_processing_time=0.0,
                total_file_size_mb=0.0,
                total_tables_found=0,
                cache_hit_rate=0.0,
                start_time=datetime.now(),
                end_time=datetime.now(),
                config=self.config,
                results=[],
                errors_by_type={}
            )
        
        return await self.process_batch(pdf_paths, progress_callback)
    
    @asynccontextmanager
    async def batch_session(self):
        """Context manager for batch processing sessions"""
        session_start = time.time()
        logger.info("🔄 Starting batch processing session")
        
        try:
            yield self
        finally:
            session_duration = time.time() - session_start
            logger.info(f"🏁 Batch processing session completed in {session_duration:.1f}s")


# Convenience functions
async def process_pdf_batch(pdf_files: List[str], credentials_path: str,
                          config: Optional[BatchJobConfig] = None,
                          progress_callback: Optional[Callable] = None) -> BatchProcessingReport:
    """
    Convenience function for batch processing PDF files
    
    Args:
        pdf_files: List of PDF file paths
        credentials_path: Path to Adobe API credentials
        config: Optional batch configuration
        progress_callback: Optional progress callback
        
    Returns:
        Batch processing report
    """
    processor = AsyncBatchProcessor(credentials_path, config)
    return await processor.process_batch(pdf_files, progress_callback)


async def process_pdf_directory(directory: str, credentials_path: str,
                              config: Optional[BatchJobConfig] = None,
                              pattern: str = "*.pdf",
                              recursive: bool = True,
                              progress_callback: Optional[Callable] = None) -> BatchProcessingReport:
    """
    Convenience function for batch processing PDF directory
    
    Args:
        directory: Directory containing PDF files
        credentials_path: Path to Adobe API credentials
        config: Optional batch configuration
        pattern: File pattern to match
        recursive: Whether to scan subdirectories
        progress_callback: Optional progress callback
        
    Returns:
        Batch processing report
    """
    processor = AsyncBatchProcessor(credentials_path, config)
    return await processor.process_directory(directory, pattern, recursive, progress_callback)


# CLI and testing
async def main():
    """Main function for testing async batch processing"""
    # Example usage
    config = BatchJobConfig(
        max_concurrent_jobs=3,
        rate_limit_per_minute=20,
        chunk_size=5,
        output_base_dir="async_batch_output",
        advanced_extraction=False
    )
    
    def progress_callback(progress_info):
        print(f"Progress: {progress_info['completed']}/{progress_info['total']} "
              f"({progress_info['percentage']:.1f}%) - "
              f"Success: {progress_info['success']}, Failed: {progress_info['failed']}")
    
    # Test with sample files
    pdf_files = ["input_pdfs/sample1.pdf", "input_pdfs/sample2.pdf"]  # Replace with actual files
    
    try:
        processor = AsyncBatchProcessor(
            credentials_path="credentials/pdfservices-api-credentials.json",
            config=config
        )
        
        async with processor.batch_session():
            report = await processor.process_batch(pdf_files, progress_callback)
            
            print(f"\n📊 Batch Processing Results:")
            print(f"Success Rate: {report.get_success_rate():.1f}%")
            print(f"Total Time: {report.total_processing_time:.1f}s")
            print(f"Average Time: {report.avg_processing_time:.1f}s per file")
            print(f"Tables Found: {report.total_tables_found}")
            print(f"Cache Hit Rate: {report.cache_hit_rate:.1f}%")
            
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())