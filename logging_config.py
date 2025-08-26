#!/usr/bin/env python3
"""
Advanced Logging Configuration for Adobe PDF Extraction System
Provides structured logging with performance monitoring and different output formats
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import colorlog
import json
from datetime import datetime
import psutil


class PerformanceFilter(logging.Filter):
    """Add performance metrics to log records"""
    
    def __init__(self):
        super().__init__()
        self.process = psutil.Process()
        
    def filter(self, record):
        try:
            # Add memory and CPU usage to log record
            record.memory_mb = self.process.memory_info().rss / 1024 / 1024
            record.cpu_percent = self.process.cpu_percent()
        except:
            record.memory_mb = 0
            record.cpu_percent = 0
        return True


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add performance metrics if available
        if hasattr(record, 'memory_mb'):
            log_entry['performance'] = {
                'memory_mb': round(record.memory_mb, 2),
                'cpu_percent': record.cpu_percent
            }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'memory_mb', 'cpu_percent']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class LoggingConfig:
    """Advanced logging configuration manager"""
    
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Default configuration
        self.config = {
            'console': {
                'enabled': True,
                'level': 'INFO',
                'format': 'colored',  # 'simple', 'detailed', 'colored', 'json'
                'show_performance': False
            },
            'file': {
                'enabled': True,
                'level': 'DEBUG',
                'format': 'detailed',
                'max_bytes': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5,
                'filename': 'adobe_extraction.log'
            },
            'json_file': {
                'enabled': True,
                'level': 'INFO',
                'max_bytes': 10 * 1024 * 1024,  # 10MB
                'backup_count': 3,
                'filename': 'adobe_extraction.json'
            },
            'performance': {
                'enabled': True,
                'level': 'INFO',
                'filename': 'performance.log'
            },
            'error_file': {
                'enabled': True,
                'level': 'ERROR',
                'filename': 'errors.log'
            }
        }
    
    def setup_logging(self, config_override: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """
        Setup advanced logging configuration
        
        Args:
            config_override: Optional configuration override
            
        Returns:
            Configured root logger
        """
        if config_override:
            self._merge_config(self.config, config_override)
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set root logger level to DEBUG (handlers will filter)
        root_logger.setLevel(logging.DEBUG)
        
        # Setup console handler
        if self.config['console']['enabled']:
            self._setup_console_handler(root_logger)
        
        # Setup file handler
        if self.config['file']['enabled']:
            self._setup_file_handler(root_logger)
        
        # Setup JSON file handler
        if self.config['json_file']['enabled']:
            self._setup_json_file_handler(root_logger)
        
        # Setup performance handler
        if self.config['performance']['enabled']:
            self._setup_performance_handler(root_logger)
        
        # Setup error file handler
        if self.config['error_file']['enabled']:
            self._setup_error_file_handler(root_logger)
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info("🚀 Logging system initialized")
        logger.info(f"📁 Log files location: {self.logs_dir.absolute()}")
        
        return root_logger
    
    def _setup_console_handler(self, logger: logging.Logger):
        """Setup console handler with appropriate formatting"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.LEVELS[self.config['console']['level']])
        
        format_type = self.config['console']['format']
        
        if format_type == 'colored':
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        elif format_type == 'detailed':
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
            if self.config['console']['show_performance']:
                fmt += ' [MEM: %(memory_mb).1fMB CPU: %(cpu_percent).1f%%]'
            formatter = logging.Formatter(fmt)
        elif format_type == 'json':
            formatter = JSONFormatter()
        else:  # simple
            formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        handler.setFormatter(formatter)
        
        if self.config['console']['show_performance']:
            handler.addFilter(PerformanceFilter())
        
        logger.addHandler(handler)
    
    def _setup_file_handler(self, logger: logging.Logger):
        """Setup rotating file handler"""
        log_file = self.logs_dir / self.config['file']['filename']
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config['file']['max_bytes'],
            backupCount=self.config['file']['backup_count']
        )
        handler.setLevel(self.LEVELS[self.config['file']['level']])
        
        format_type = self.config['file']['format']
        if format_type == 'detailed':
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
            )
        else:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def _setup_json_file_handler(self, logger: logging.Logger):
        """Setup JSON file handler for structured logging"""
        log_file = self.logs_dir / self.config['json_file']['filename']
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config['json_file']['max_bytes'],
            backupCount=self.config['json_file']['backup_count']
        )
        handler.setLevel(self.LEVELS[self.config['json_file']['level']])
        handler.setFormatter(JSONFormatter())
        handler.addFilter(PerformanceFilter())
        
        logger.addHandler(handler)
    
    def _setup_performance_handler(self, logger: logging.Logger):
        """Setup performance-specific handler"""
        log_file = self.logs_dir / self.config['performance']['filename']
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(self.LEVELS[self.config['performance']['level']])
        
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s [MEM: %(memory_mb).1fMB CPU: %(cpu_percent).1f%%]'
        )
        handler.setFormatter(formatter)
        handler.addFilter(PerformanceFilter())
        
        # Only add performance-related logs
        class PerformanceOnlyFilter(logging.Filter):
            def filter(self, record):
                return 'performance' in record.getMessage().lower() or 'extract' in record.getMessage().lower()
        
        handler.addFilter(PerformanceOnlyFilter())
        logger.addHandler(handler)
    
    def _setup_error_file_handler(self, logger: logging.Logger):
        """Setup error-only file handler"""
        log_file = self.logs_dir / self.config['error_file']['filename']
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(self.LEVELS[self.config['error_file']['level']])
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d\n'
            'MESSAGE: %(message)s\n'
            'EXCEPTION: %(exc_text)s\n' + '-' * 80
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value


# Global logging instance
logging_config = LoggingConfig()


def setup_logging(config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Setup logging with optional configuration override
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured logger
    """
    return logging_config.setup_logging(config)


def get_performance_logger() -> logging.Logger:
    """Get a logger specifically for performance monitoring"""
    logger = logging.getLogger('performance')
    return logger


def log_performance(func):
    """Decorator to log function performance"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        perf_logger = get_performance_logger()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            perf_logger.info(f"Performance: {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            perf_logger.error(f"Performance: {func.__name__} failed after {duration:.2f}s - {str(e)}")
            raise
    
    return wrapper


if __name__ == "__main__":
    # Test logging configuration
    logger = setup_logging({
        'console': {'level': 'DEBUG', 'format': 'colored', 'show_performance': True}
    })
    
    test_logger = logging.getLogger('test')
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        test_logger.exception("Exception occurred")
    
    perf_logger = get_performance_logger()
    perf_logger.info("Performance test message")
    
    print(f"Log files created in: {logging_config.logs_dir}")