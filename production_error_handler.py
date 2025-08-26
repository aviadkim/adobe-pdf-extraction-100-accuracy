#!/usr/bin/env python3
"""
PRODUCTION ERROR HANDLING & RETRY LOGIC
Robust error handling system for 100% accuracy extraction pipeline
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_logs/extraction.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Ensure log directory exists
os.makedirs('production_logs', exist_ok=True)

class ProductionError(Exception):
    """Base class for production errors"""
    pass

class ExtractionError(ProductionError):
    """Error during data extraction"""
    pass

class ValidationError(ProductionError):
    """Error during data validation"""
    pass

class APIError(ProductionError):
    """Error with external API calls"""
    pass

class RetryHandler:
    """Advanced retry handler with exponential backoff and circuit breaker"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.failure_count = {}
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = 300  # 5 minutes
    
    def retry(self, exceptions=(Exception,), on_failure=None):
        """Decorator for retry functionality"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_retry(func, args, kwargs, exceptions, on_failure)
            return wrapper
        return decorator
    
    def _execute_with_retry(self, func, args, kwargs, exceptions, on_failure):
        """Execute function with retry logic"""
        
        func_name = func.__name__
        
        # Check circuit breaker
        if self._is_circuit_open(func_name):
            logger.error(f"Circuit breaker open for {func_name}")
            raise ProductionError(f"Circuit breaker open for {func_name}")
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Success - reset failure count
                if func_name in self.failure_count:
                    del self.failure_count[func_name]
                
                return result
                
            except exceptions as e:
                last_exception = e
                self._record_failure(func_name)
                
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries + 1} failed for {func_name}: {str(e)}")
                
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.info(f"Retrying {func_name} in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {func_name}")
                    
                    if on_failure:
                        return on_failure(last_exception)
        
        # If we get here, all retries failed
        raise last_exception
    
    def _record_failure(self, func_name: str):
        """Record function failure for circuit breaker"""
        now = datetime.now()
        
        if func_name not in self.failure_count:
            self.failure_count[func_name] = []
        
        self.failure_count[func_name].append(now)
        
        # Clean old failures (older than reset time)
        cutoff = now - timedelta(seconds=self.circuit_breaker_reset_time)
        self.failure_count[func_name] = [
            failure_time for failure_time in self.failure_count[func_name]
            if failure_time > cutoff
        ]
    
    def _is_circuit_open(self, func_name: str) -> bool:
        """Check if circuit breaker is open"""
        if func_name not in self.failure_count:
            return False
        
        recent_failures = len(self.failure_count[func_name])
        return recent_failures >= self.circuit_breaker_threshold

class ProductionErrorHandler:
    """Production-ready error handling system"""
    
    def __init__(self):
        self.retry_handler = RetryHandler()
        self.error_log = []
        self.recovery_strategies = {
            'adobe_api_error': self._handle_adobe_api_error,
            'azure_api_error': self._handle_azure_api_error,
            'network_error': self._handle_network_error,
            'file_error': self._handle_file_error,
            'validation_error': self._handle_validation_error,
            'unknown_error': self._handle_unknown_error
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main error handling entry point"""
        
        error_info = self._classify_error(error, context)
        
        # Log error
        self._log_error(error_info, context)
        
        # Try recovery strategy
        recovery_result = self._attempt_recovery(error_info, context)
        
        # Save error report
        self._save_error_report(error_info, context, recovery_result)
        
        return recovery_result
    
    def _classify_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify error type and severity"""
        
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Classify by error content
        if 'adobe' in error_str or 'pdf services' in error_str:
            category = 'adobe_api_error'
            severity = 'HIGH' if '401' in error_str or '403' in error_str else 'MEDIUM'
        
        elif 'azure' in error_str or 'computer vision' in error_str:
            category = 'azure_api_error'
            severity = 'MEDIUM'
        
        elif any(net_error in error_str for net_error in ['connection', 'timeout', 'network', 'dns']):
            category = 'network_error'
            severity = 'MEDIUM'
        
        elif any(file_error in error_str for file_error in ['file not found', 'permission', 'io']):
            category = 'file_error'
            severity = 'LOW'
        
        elif 'validation' in error_str:
            category = 'validation_error'
            severity = 'HIGH'
        
        else:
            category = 'unknown_error'
            severity = 'HIGH'
        
        return {
            'category': category,
            'severity': severity,
            'error_type': error_type,
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_adobe_api_error(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Handle Adobe API specific errors"""
        
        logger.info("🔧 Handling Adobe API error...")
        
        error_msg = error_info['message'].lower()
        
        # Authentication errors
        if '401' in error_msg or '403' in error_msg:
            return {
                'strategy': 'credential_refresh',
                'success': False,
                'message': 'Adobe credentials need refresh',
                'recommendation': 'Check Adobe API credentials and quotas'
            }
        
        # Rate limiting
        if '429' in error_msg or 'rate limit' in error_msg:
            return {
                'strategy': 'rate_limit_backoff',
                'success': False,
                'message': 'Adobe API rate limited',
                'recommendation': 'Wait and retry with exponential backoff'
            }
        
        # Quota exceeded
        if 'quota' in error_msg or 'limit exceeded' in error_msg:
            return {
                'strategy': 'fallback_to_azure',
                'success': False,
                'message': 'Adobe quota exceeded',
                'recommendation': 'Switch to Azure Computer Vision API'
            }
        
        # Service unavailable
        if '503' in error_msg or 'service unavailable' in error_msg:
            return {
                'strategy': 'service_retry',
                'success': False,
                'message': 'Adobe service temporarily unavailable',
                'recommendation': 'Retry after delay or use Azure backup'
            }
        
        return {
            'strategy': 'generic_adobe_recovery',
            'success': False,
            'message': 'Generic Adobe API error',
            'recommendation': 'Check API status and credentials'
        }
    
    def _handle_azure_api_error(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Handle Azure API specific errors"""
        
        logger.info("🌐 Handling Azure API error...")
        
        error_msg = error_info['message'].lower()
        
        # Authentication errors
        if 'invalid subscription key' in error_msg:
            return {
                'strategy': 'azure_credential_check',
                'success': False,
                'message': 'Azure subscription key invalid',
                'recommendation': 'Verify Azure Computer Vision credentials'
            }
        
        # Rate limiting
        if 'rate limit' in error_msg:
            return {
                'strategy': 'azure_rate_backoff',
                'success': False,
                'message': 'Azure API rate limited',
                'recommendation': 'Wait and retry or fall back to Adobe'
            }
        
        return {
            'strategy': 'azure_fallback',
            'success': False,
            'message': 'Azure API error - falling back to Adobe',
            'recommendation': 'Use Adobe as primary extraction method'
        }
    
    def _handle_network_error(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Handle network connectivity errors"""
        
        logger.info("🌐 Handling network error...")
        
        # Test connectivity
        connectivity_ok = self._test_connectivity()
        
        if connectivity_ok:
            return {
                'strategy': 'network_retry',
                'success': True,
                'message': 'Network connectivity restored',
                'recommendation': 'Retry the operation'
            }
        else:
            return {
                'strategy': 'offline_mode',
                'success': False,
                'message': 'Network connectivity issues',
                'recommendation': 'Use cached data or offline processing'
            }
    
    def _handle_file_error(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Handle file system errors"""
        
        logger.info("📁 Handling file error...")
        
        # Try to create missing directories
        try:
            required_dirs = ['input_pdfs', 'production_results', 'production_logs']
            for dir_name in required_dirs:
                os.makedirs(dir_name, exist_ok=True)
            
            return {
                'strategy': 'directory_creation',
                'success': True,
                'message': 'Created missing directories',
                'recommendation': 'Retry the operation'
            }
            
        except Exception as e:
            return {
                'strategy': 'file_system_check',
                'success': False,
                'message': f'File system error persists: {str(e)}',
                'recommendation': 'Check file permissions and disk space'
            }
    
    def _handle_validation_error(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Handle data validation errors"""
        
        logger.info("🔍 Handling validation error...")
        
        return {
            'strategy': 'manual_review',
            'success': False,
            'message': 'Data validation failed',
            'recommendation': 'Manual review required for accuracy verification'
        }
    
    def _handle_unknown_error(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Handle unknown errors"""
        
        logger.warning("❓ Handling unknown error...")
        
        return {
            'strategy': 'failsafe_mode',
            'success': False,
            'message': 'Unknown error - engaging failsafe protocols',
            'recommendation': 'Switch to manual processing mode'
        }
    
    def _attempt_recovery(self, error_info: Dict, context: Dict) -> Dict[str, Any]:
        """Attempt error recovery using appropriate strategy"""
        
        category = error_info['category']
        recovery_func = self.recovery_strategies.get(category, self.recovery_strategies['unknown_error'])
        
        try:
            return recovery_func(error_info, context)
        except Exception as e:
            logger.error(f"Recovery attempt failed: {str(e)}")
            return {
                'strategy': 'recovery_failed',
                'success': False,
                'message': f'Recovery attempt failed: {str(e)}',
                'recommendation': 'Manual intervention required'
            }
    
    def _test_connectivity(self) -> bool:
        """Test network connectivity"""
        try:
            response = requests.get('https://httpbin.org/status/200', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _log_error(self, error_info: Dict, context: Dict):
        """Log error details"""
        
        self.error_log.append({
            'error_info': error_info,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
        # Log to file
        log_entry = {
            'timestamp': error_info['timestamp'],
            'severity': error_info['severity'],
            'category': error_info['category'],
            'message': error_info['message'],
            'context': context
        }
        
        if error_info['severity'] == 'HIGH':
            logger.error(f"HIGH SEVERITY ERROR: {error_info['message']}")
        elif error_info['severity'] == 'MEDIUM':
            logger.warning(f"MEDIUM SEVERITY ERROR: {error_info['message']}")
        else:
            logger.info(f"LOW SEVERITY ERROR: {error_info['message']}")
    
    def _save_error_report(self, error_info: Dict, context: Dict, recovery_result: Dict):
        """Save detailed error report"""
        
        report = {
            'error_details': error_info,
            'context': context,
            'recovery_attempt': recovery_result,
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'python_version': os.sys.version,
                'platform': os.name,
                'working_directory': os.getcwd()
            }
        }
        
        # Save to file
        error_file = f"production_logs/error_report_{int(time.time())}.json"
        with open(error_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Error report saved: {error_file}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        
        if not self.error_log:
            return {'total_errors': 0, 'summary': 'No errors recorded'}
        
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        category_counts = {}
        
        for entry in self.error_log:
            error_info = entry['error_info']
            severity = error_info.get('severity', 'UNKNOWN')
            category = error_info.get('category', 'unknown')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'most_recent_error': self.error_log[-1]['error_info']['timestamp']
        }

# Global error handler instance
error_handler = ProductionErrorHandler()

def handle_production_error(func):
    """Decorator to handle production errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function': func.__name__,
                'args': str(args)[:200],  # Limit context size
                'kwargs': str(kwargs)[:200]
            }
            
            recovery_result = error_handler.handle_error(e, context)
            
            # If recovery was successful, we can continue
            if recovery_result.get('success'):
                logger.info(f"Error recovered for {func.__name__}: {recovery_result['message']}")
                # You might want to retry the function here
                return func(*args, **kwargs)
            else:
                logger.error(f"Error recovery failed for {func.__name__}: {recovery_result['message']}")
                raise e
    
    return wrapper

def safe_execute(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Safely execute a function with error handling"""
    
    try:
        result = func(*args, **kwargs)
        return {
            'success': True,
            'result': result,
            'error': None
        }
    except Exception as e:
        context = {
            'function': func.__name__ if hasattr(func, '__name__') else 'unknown',
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        }
        
        recovery_result = error_handler.handle_error(e, context)
        
        return {
            'success': False,
            'result': None,
            'error': str(e),
            'recovery_attempt': recovery_result
        }

if __name__ == "__main__":
    # Test the error handler
    @handle_production_error
    def test_function():
        raise Exception("Test error")
    
    try:
        test_function()
    except Exception as e:
        print(f"Handled error: {e}")
    
    # Print error summary
    summary = error_handler.get_error_summary()
    print(f"Error summary: {summary}")