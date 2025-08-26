#!/usr/bin/env python3
"""
Performance Monitoring and Caching System for Adobe PDF Extraction
Provides comprehensive performance tracking, caching, and optimization features
"""

import time
import hashlib
import json
import logging
import os
import pickle
from typing import Any, Dict, Optional, Callable, Union, List
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psutil
import threading
from pathlib import Path
import diskcache
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    function_name: str
    execution_time: float
    memory_before: float  # MB
    memory_after: float   # MB
    memory_peak: float    # MB
    cpu_percent_avg: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    cache_hit: bool = False
    input_size: Optional[int] = None  # bytes
    output_size: Optional[int] = None  # bytes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class MemoryProfiler:
    """Memory usage profiler"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.peak_memory = 0.0
        self.samples = []
        self._monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self, interval: float = 0.1):
        """Start continuous memory monitoring"""
        self._monitoring = True
        self.peak_memory = 0.0
        self.samples = []
        
        def monitor():
            while self._monitoring:
                try:
                    memory_mb = self.process.memory_info().rss / 1024 / 1024
                    self.samples.append(memory_mb)
                    self.peak_memory = max(self.peak_memory, memory_mb)
                    time.sleep(interval)
                except:
                    break
        
        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> float:
        """Stop monitoring and return peak memory"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        return self.peak_memory
    
    def get_current_memory(self) -> float:
        """Get current memory usage in MB"""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except:
            return 0.0


class SmartCache:
    """Smart caching system with TTL and size limits"""
    
    def __init__(self, cache_dir: str = "cache", max_size_gb: float = 1.0, 
                 default_ttl_hours: int = 24):
        """
        Initialize smart cache
        
        Args:
            cache_dir: Directory for cache storage
            max_size_gb: Maximum cache size in GB
            default_ttl_hours: Default TTL in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize disk cache
        max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.cache = diskcache.Cache(
            str(self.cache_dir),
            size_limit=max_size_bytes
        )
        
        self.default_ttl = default_ttl_hours * 3600  # Convert to seconds
        self.stats = {
            'hits': 0,
            'misses': 0,
            'stores': 0,
            'evictions': 0
        }
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments"""
        # Create a deterministic key from function name and arguments
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': json.dumps(kwargs, sort_keys=True, default=str)
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def get(self, func_name: str, args: tuple, kwargs: dict) -> tuple[bool, Any]:
        """
        Get value from cache
        
        Returns:
            Tuple of (cache_hit, value)
        """
        key = self._generate_key(func_name, args, kwargs)
        
        try:
            value = self.cache.get(key)
            if value is not None:
                self.stats['hits'] += 1
                logger.debug(f"Cache hit for {func_name}")
                return True, value
            else:
                self.stats['misses'] += 1
                logger.debug(f"Cache miss for {func_name}")
                return False, None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats['misses'] += 1
            return False, None
    
    def set(self, func_name: str, args: tuple, kwargs: dict, value: Any, 
            ttl: Optional[int] = None) -> bool:
        """
        Store value in cache
        
        Args:
            func_name: Function name
            args: Function arguments
            kwargs: Function keyword arguments  
            value: Value to store
            ttl: Time to live in seconds
            
        Returns:
            True if stored successfully
        """
        key = self._generate_key(func_name, args, kwargs)
        ttl = ttl or self.default_ttl
        
        try:
            success = self.cache.set(key, value, expire=ttl)
            if success:
                self.stats['stores'] += 1
                logger.debug(f"Cached result for {func_name}")
            return success
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_info = {
            'size': len(self.cache),
            'volume': self.cache.volume(),
            'directory': str(self.cache_dir)
        }
        return {**self.stats, **cache_info}
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.stats['hits'] + self.stats['misses']
        if total == 0:
            return 0.0
        return self.stats['hits'] / total


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, cache: Optional[SmartCache] = None, 
                 metrics_file: Optional[str] = None):
        """
        Initialize performance monitor
        
        Args:
            cache: Cache instance to use
            metrics_file: File to store performance metrics
        """
        self.cache = cache or SmartCache()
        self.metrics_file = metrics_file or "logs/performance_metrics.json"
        self.metrics_history: List[PerformanceMetrics] = []
        self.profiler = MemoryProfiler()
        
        # Ensure metrics directory exists
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        
        # Load existing metrics
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    # Convert back to PerformanceMetrics objects
                    for item in metrics_data:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        self.metrics_history.append(PerformanceMetrics(**item))
        except Exception as e:
            logger.warning(f"Could not load performance metrics: {e}")
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            metrics_data = [metric.to_dict() for metric in self.metrics_history]
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save performance metrics: {e}")
    
    def monitor_performance(self, cache_ttl: Optional[int] = None, 
                          enable_cache: bool = True,
                          track_memory: bool = True):
        """
        Decorator for monitoring function performance
        
        Args:
            cache_ttl: Cache time-to-live in seconds
            enable_cache: Whether to enable caching
            track_memory: Whether to track memory usage
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_monitoring(
                    func, args, kwargs, cache_ttl, enable_cache, track_memory
                )
            return wrapper
        return decorator
    
    def _execute_with_monitoring(self, func: Callable, args: tuple, kwargs: dict,
                               cache_ttl: Optional[int], enable_cache: bool,
                               track_memory: bool) -> Any:
        """Execute function with comprehensive monitoring"""
        func_name = func.__name__
        start_time = time.time()
        cache_hit = False
        result = None
        error_message = None
        
        # Get input size estimate
        input_size = self._estimate_size(args) + self._estimate_size(kwargs)
        
        # Memory tracking setup
        memory_before = self.profiler.get_current_memory() if track_memory else 0.0
        if track_memory:
            self.profiler.start_monitoring()
        
        # CPU monitoring setup
        cpu_samples = []
        
        def cpu_monitor():
            while True:
                try:
                    cpu_samples.append(psutil.cpu_percent())
                    time.sleep(0.1)
                except:
                    break
        
        cpu_thread = threading.Thread(target=cpu_monitor, daemon=True)
        cpu_thread.start()
        
        try:
            # Try cache first if enabled
            if enable_cache and self.cache:
                cache_hit, cached_result = self.cache.get(func_name, args, kwargs)
                if cache_hit:
                    result = cached_result
                else:
                    # Execute function
                    result = func(*args, **kwargs)
                    # Cache the result
                    self.cache.set(func_name, args, kwargs, result, cache_ttl)
            else:
                # Execute function without caching
                result = func(*args, **kwargs)
            
            success = True
            
        except Exception as e:
            error_message = str(e)
            success = False
            logger.error(f"Function {func_name} failed: {error_message}")
            raise
            
        finally:
            # Stop monitoring
            execution_time = time.time() - start_time
            memory_after = self.profiler.get_current_memory() if track_memory else 0.0
            memory_peak = self.profiler.stop_monitoring() if track_memory else 0.0
            
            # Calculate average CPU usage
            cpu_avg = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
            
            # Get output size estimate
            output_size = self._estimate_size(result) if result is not None else 0
            
            # Create performance metrics
            metrics = PerformanceMetrics(
                function_name=func_name,
                execution_time=execution_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                cpu_percent_avg=cpu_avg,
                timestamp=datetime.now(),
                success=success,
                error_message=error_message,
                cache_hit=cache_hit,
                input_size=input_size,
                output_size=output_size
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Log performance
            self._log_performance(metrics)
            
            # Save metrics periodically
            if len(self.metrics_history) % 10 == 0:
                self._save_metrics()
        
        return result
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate size of object in bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            return len(str(obj).encode('utf-8'))
    
    def _log_performance(self, metrics: PerformanceMetrics):
        """Log performance metrics"""
        status = "✅" if metrics.success else "❌"
        cache_info = " (cached)" if metrics.cache_hit else ""
        
        logger.info(
            f"{status} {metrics.function_name}: {metrics.execution_time:.2f}s, "
            f"Memory: {metrics.memory_peak:.1f}MB peak, "
            f"CPU: {metrics.cpu_percent_avg:.1f}%{cache_info}"
        )
        
        if not metrics.success:
            logger.error(f"Error in {metrics.function_name}: {metrics.error_message}")
    
    @contextmanager
    def measure(self, operation_name: str):
        """Context manager for measuring operation performance"""
        start_time = time.time()
        memory_before = self.profiler.get_current_memory()
        self.profiler.start_monitoring()
        
        try:
            yield
            success = True
            error_msg = None
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            execution_time = time.time() - start_time
            memory_after = self.profiler.get_current_memory()
            memory_peak = self.profiler.stop_monitoring()
            
            logger.info(
                f"⏱️  {operation_name}: {execution_time:.2f}s, "
                f"Memory: {memory_peak:.1f}MB peak"
            )
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No recent performance data"}
        
        # Calculate statistics
        execution_times = [m.execution_time for m in recent_metrics]
        memory_peaks = [m.memory_peak for m in recent_metrics]
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        
        # Function performance breakdown
        func_stats = {}
        for metrics in recent_metrics:
            func_name = metrics.function_name
            if func_name not in func_stats:
                func_stats[func_name] = {
                    'call_count': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'success_count': 0,
                    'cache_hits': 0
                }
            
            func_stats[func_name]['call_count'] += 1
            func_stats[func_name]['total_time'] += metrics.execution_time
            if metrics.success:
                func_stats[func_name]['success_count'] += 1
            if metrics.cache_hit:
                func_stats[func_name]['cache_hits'] += 1
        
        # Calculate averages
        for stats in func_stats.values():
            if stats['call_count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['call_count']
                stats['success_rate'] = stats['success_count'] / stats['call_count']
                stats['cache_hit_rate'] = stats['cache_hits'] / stats['call_count']
        
        return {
            'period_hours': hours,
            'total_operations': len(recent_metrics),
            'success_rate': success_rate,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'avg_memory_peak': sum(memory_peaks) / len(memory_peaks),
            'max_memory_peak': max(memory_peaks),
            'cache_stats': self.cache.get_stats() if self.cache else None,
            'function_breakdown': func_stats
        }
    
    def cleanup_old_metrics(self, days: int = 30):
        """Clean up metrics older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        old_count = len(self.metrics_history)
        
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        removed_count = old_count - len(self.metrics_history)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old performance metrics")
            self._save_metrics()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience decorators
def monitor_performance(cache_ttl: Optional[int] = None, enable_cache: bool = True, 
                       track_memory: bool = True):
    """Convenience decorator for performance monitoring"""
    return performance_monitor.monitor_performance(cache_ttl, enable_cache, track_memory)


def cached(ttl_hours: int = 24):
    """Convenience decorator for caching with TTL"""
    return monitor_performance(cache_ttl=ttl_hours * 3600, enable_cache=True)


if __name__ == "__main__":
    # Test performance monitoring
    @monitor_performance(cache_ttl=3600, enable_cache=True)
    def test_function(n: int = 1000000):
        """Test function for performance monitoring"""
        return sum(range(n))
    
    print("Testing performance monitoring...")
    
    # First call (should cache)
    result1 = test_function(1000000)
    print(f"First call result: {result1}")
    
    # Second call (should hit cache)
    result2 = test_function(1000000)
    print(f"Second call result: {result2}")
    
    # Get performance summary
    summary = performance_monitor.get_performance_summary(1)
    print("\nPerformance Summary:")
    print(json.dumps(summary, indent=2, default=str))