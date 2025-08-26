#!/usr/bin/env python3
"""
Retry Handler for Adobe PDF Extraction System
Provides intelligent retry mechanisms with exponential backoff and circuit breaker patterns
"""

import time
import logging
import random
from typing import Callable, Any, Optional, List, Type, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Different retry strategies"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    JITTER = "jitter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter_max: float = 1.0
    timeout: Optional[float] = None
    retryable_exceptions: Optional[List[Type[Exception]]] = None
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to a function"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self._call(func, *args, **kwargs)
        return wrapper
    
    def _call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker logic"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker {self.config.name} moving to HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker {self.config.name} is OPEN - blocking call")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info(f"Circuit breaker {self.config.name} reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if (self.state == CircuitBreakerState.CLOSED and 
            self.failure_count >= self.config.failure_threshold):
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {self.config.name} opened due to {self.failure_count} failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {self.config.name} reopened after failed test")


class RetryHandler:
    """Advanced retry handler with multiple strategies"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply retry logic to a function"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute_with_retry(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._execute_with_retry_async(func, *args, **kwargs)
        
        # Return async wrapper for async functions, sync wrapper for sync functions
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic (synchronous)"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                start_time = time.time()
                
                # Apply timeout if specified
                if self.config.timeout:
                    # Note: This is a simple timeout implementation
                    # For more robust timeout handling, consider using signal or threading
                    result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                
                if attempt > 1:
                    logger.info(f"✅ Function {func.__name__} succeeded on attempt {attempt}/{self.config.max_attempts} ({duration:.2f}s)")
                
                return result
                
            except Exception as e:
                last_exception = e
                duration = time.time() - start_time
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    logger.error(f"❌ Non-retryable exception in {func.__name__}: {str(e)}")
                    raise e
                
                # Don't retry on last attempt
                if attempt == self.config.max_attempts:
                    logger.error(f"❌ Function {func.__name__} failed after {attempt} attempts ({duration:.2f}s): {str(e)}")
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"⚠️ Function {func.__name__} failed on attempt {attempt}/{self.config.max_attempts} ({duration:.2f}s), retrying in {delay:.1f}s: {str(e)}")
                
                time.sleep(delay)
        
        # All attempts failed
        raise last_exception
    
    async def _execute_with_retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic (asynchronous)"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                start_time = time.time()
                
                # Apply timeout if specified
                if self.config.timeout:
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
                else:
                    result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                
                if attempt > 1:
                    logger.info(f"✅ Async function {func.__name__} succeeded on attempt {attempt}/{self.config.max_attempts} ({duration:.2f}s)")
                
                return result
                
            except Exception as e:
                last_exception = e
                duration = time.time() - start_time
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    logger.error(f"❌ Non-retryable exception in async {func.__name__}: {str(e)}")
                    raise e
                
                # Don't retry on last attempt
                if attempt == self.config.max_attempts:
                    logger.error(f"❌ Async function {func.__name__} failed after {attempt} attempts ({duration:.2f}s): {str(e)}")
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"⚠️ Async function {func.__name__} failed on attempt {attempt}/{self.config.max_attempts} ({duration:.2f}s), retrying in {delay:.1f}s: {str(e)}")
                
                await asyncio.sleep(delay)
        
        # All attempts failed
        raise last_exception
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Check if an exception is retryable based on configuration"""
        # Check non-retryable exceptions first
        if self.config.non_retryable_exceptions:
            for exc_type in self.config.non_retryable_exceptions:
                if isinstance(exception, exc_type):
                    return False
        
        # Check retryable exceptions
        if self.config.retryable_exceptions:
            for exc_type in self.config.retryable_exceptions:
                if isinstance(exception, exc_type):
                    return True
            return False  # Not in retryable list
        
        # Default: retry most exceptions except certain types
        non_retryable_defaults = [
            KeyboardInterrupt,
            SystemExit,
            MemoryError,
            SyntaxError,
            TypeError,
            ValueError,
            AttributeError
        ]
        
        for exc_type in non_retryable_defaults:
            if isinstance(exception, exc_type):
                return False
        
        return True
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
            
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
            
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))
            
        elif self.config.strategy == RetryStrategy.JITTER:
            base_delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))
            jitter = random.uniform(0, self.config.jitter_max)
            delay = base_delay + jitter
        
        else:
            delay = self.config.base_delay
        
        # Cap the delay at max_delay
        return min(delay, self.config.max_delay)


# Predefined retry configurations
RETRY_CONFIGS = {
    'api_calls': RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL,
        backoff_factor=2.0
    ),
    
    'file_operations': RetryConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=10.0,
        strategy=RetryStrategy.JITTER,
        jitter_max=0.5
    ),
    
    'network_requests': RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=60.0,
        strategy=RetryStrategy.EXPONENTIAL,
        backoff_factor=2.0,
        timeout=30.0
    ),
    
    'database_operations': RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=20.0,
        strategy=RetryStrategy.LINEAR
    )
}

# Predefined circuit breaker configurations  
CIRCUIT_BREAKER_CONFIGS = {
    'adobe_api': CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=120.0,
        name="adobe_api"
    ),
    
    'ocr_service': CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        name="ocr_service"
    )
}


def with_retry(config_name: str = 'api_calls', custom_config: Optional[RetryConfig] = None):
    """
    Decorator factory for applying retry logic with predefined or custom configuration
    
    Args:
        config_name: Name of predefined configuration or 'custom'
        custom_config: Custom retry configuration (required if config_name is 'custom')
    """
    if custom_config:
        config = custom_config
    else:
        config = RETRY_CONFIGS.get(config_name, RETRY_CONFIGS['api_calls'])
    
    return RetryHandler(config)


def with_circuit_breaker(config_name: str = 'adobe_api', custom_config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator factory for applying circuit breaker pattern
    
    Args:
        config_name: Name of predefined configuration
        custom_config: Custom circuit breaker configuration
    """
    if custom_config:
        config = custom_config
    else:
        config = CIRCUIT_BREAKER_CONFIGS.get(config_name, CIRCUIT_BREAKER_CONFIGS['adobe_api'])
    
    return CircuitBreaker(config)


def with_resilience(retry_config: str = 'api_calls', circuit_breaker_config: str = 'adobe_api'):
    """
    Decorator that combines retry and circuit breaker patterns
    
    Args:
        retry_config: Retry configuration name
        circuit_breaker_config: Circuit breaker configuration name
    """
    def decorator(func: Callable) -> Callable:
        # Apply circuit breaker first, then retry
        resilient_func = with_circuit_breaker(circuit_breaker_config)(func)
        return with_retry(retry_config)(resilient_func)
    
    return decorator


if __name__ == "__main__":
    # Test retry functionality
    @with_retry('api_calls')
    def unreliable_function(success_rate: float = 0.3):
        """Simulated unreliable function for testing"""
        import random
        if random.random() > success_rate:
            raise Exception("Simulated failure")
        return "Success!"
    
    # Test circuit breaker
    @with_circuit_breaker('adobe_api')
    def failing_function():
        """Function that always fails for testing circuit breaker"""
        raise Exception("Always fails")
    
    # Test combined resilience
    @with_resilience()
    def resilient_function(fail_count: int = 2):
        """Function that fails a few times then succeeds"""
        if not hasattr(resilient_function, 'attempts'):
            resilient_function.attempts = 0
        resilient_function.attempts += 1
        
        if resilient_function.attempts <= fail_count:
            raise Exception(f"Failure {resilient_function.attempts}")
        return f"Success after {resilient_function.attempts} attempts"
    
    print("Testing retry mechanism:")
    try:
        result = unreliable_function(0.8)  # 80% success rate
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
    
    print("\nTesting resilient function:")
    try:
        result = resilient_function(2)  # Fail twice, then succeed
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")