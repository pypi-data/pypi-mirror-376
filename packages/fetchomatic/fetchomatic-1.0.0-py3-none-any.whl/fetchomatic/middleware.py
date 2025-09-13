"""
SmartFetch Middleware System
"""

import time
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List, Union
from .exceptions import MiddlewareError, RateLimitError
from .utils import create_cache_key, exponential_backoff


class BaseMiddleware(ABC):
    """Base class for all middleware"""
    
    @abstractmethod
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process request before sending"""
        pass
    
    @abstractmethod
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process response after receiving"""
        pass
    
    def on_error(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors (optional)"""
        return error_context


class LoggingMiddleware(BaseMiddleware):
    """Middleware for request/response logging"""
    
    def __init__(self, logger: Optional[logging.Logger] = None, 
                 log_request_body: bool = False, log_response_body: bool = False,
                 max_body_length: int = 1000):
        self.logger = logger or logging.getLogger(__name__)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_length = max_body_length
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Log request details"""
        method = request_context.get('method', 'UNKNOWN')
        url = request_context.get('url', 'UNKNOWN')
        
        log_msg = f"[REQUEST] {method} {url}"
        
        if self.log_request_body and 'data' in request_context:
            data = str(request_context['data'])[:self.max_body_length]
            log_msg += f" | Body: {data}"
        
        self.logger.info(log_msg)
        request_context['_start_time'] = time.time()
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Log response details"""
        request_ctx = response_context.get('request_context', {})
        response = response_context.get('response')
        
        duration = time.time() - request_ctx.get('_start_time', time.time())
        method = request_ctx.get('method', 'UNKNOWN')
        url = request_ctx.get('url', 'UNKNOWN')
        
        status_code = getattr(response, 'status_code', 'UNKNOWN')
        log_msg = f"[RESPONSE] {method} {url} | {status_code} | {duration:.3f}s"
        
        if self.log_response_body and hasattr(response, 'text'):
            text = str(response.text)[:self.max_body_length]
            log_msg += f" | Body: {text}"
        
        self.logger.info(log_msg)
        return response_context
    
    def on_error(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Log errors"""
        request_ctx = error_context.get('request_context', {})
        error = error_context.get('error')
        
        method = request_ctx.get('method', 'UNKNOWN')
        url = request_ctx.get('url', 'UNKNOWN')
        
        self.logger.error(f"[ERROR] {method} {url} | {type(error).__name__}: {error}")
        return error_context


class CachingMiddleware(BaseMiddleware):
    """Middleware for response caching"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.cache_times = {}
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
    
    def _is_cacheable(self, request_context: Dict[str, Any]) -> bool:
        """Determine if request is cacheable"""
        method = request_context.get('method', '').upper()
        return method in ['GET', 'HEAD', 'OPTIONS']
    
    def _create_cache_key(self, request_context: Dict[str, Any]) -> str:
        """Create cache key for request"""
        url = request_context.get('url', '')
        method = request_context.get('method', '')
        headers = request_context.get('headers', {})
        params = request_context.get('params', {})
        
        # Include relevant headers that might affect response
        cache_headers = {k: v for k, v in headers.items() 
                        if k.lower() in ['accept', 'accept-language', 'authorization']}
        
        return create_cache_key(method, url, cache_headers, params)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid"""
        if cache_key not in self.cache_times:
            return False
        
        cache_time = self.cache_times[cache_key]
        return (time.time() - cache_time) < self.ttl
    
    def _evict_old_entries(self):
        """Remove old cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, cache_time in self.cache_times.items()
            if (current_time - cache_time) >= self.ttl
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_times.pop(key, None)
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check cache before making request"""
        if not self._is_cacheable(request_context):
            return request_context
        
        cache_key = self._create_cache_key(request_context)
        
        if self._is_cache_valid(cache_key):
            # Return cached response
            cached_response = self.cache[cache_key]
            request_context['_cached_response'] = cached_response
            request_context['_cache_hit'] = True
        
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Cache response if applicable"""
        request_ctx = response_context.get('request_context', {})
        
        # If we had a cache hit, don't cache again
        if request_ctx.get('_cache_hit'):
            return response_context
        
        if not self._is_cacheable(request_ctx):
            return response_context
        
        response = response_context.get('response')
        if not response or not hasattr(response, 'status_code'):
            return response_context
        
        # Only cache successful responses
        if 200 <= response.status_code < 300:
            # Clean up old entries if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_old_entries()
                
                # If still full after cleanup, remove oldest entry
                if len(self.cache) >= self.max_size:
                    oldest_key = min(self.cache_times.keys(), 
                                   key=lambda k: self.cache_times[k])
                    self.cache.pop(oldest_key, None)
                    self.cache_times.pop(oldest_key, None)
            
            cache_key = self._create_cache_key(request_ctx)
            self.cache[cache_key] = response
            self.cache_times[cache_key] = time.time()
        
        return response_context


class AuthMiddleware(BaseMiddleware):
    """Middleware for authentication"""
    
    def __init__(self, auth_type: str = 'bearer', token: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 api_key_header: str = 'X-API-Key'):
        self.auth_type = auth_type.lower()
        self.token = token
        self.username = username
        self.password = password
        self.api_key_header = api_key_header
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Add authentication headers"""
        headers = request_context.get('headers', {})
        
        if self.auth_type == 'bearer' and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        elif self.auth_type == 'basic' and self.username and self.password:
            import base64
            credentials = base64.b64encode(
                f'{self.username}:{self.password}'.encode()
            ).decode()
            headers['Authorization'] = f'Basic {credentials}'
        elif self.auth_type == 'api_key' and self.token:
            headers[self.api_key_header] = self.token
        
        request_context['headers'] = headers
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication responses"""
        return response_context


class RateLimitingMiddleware(BaseMiddleware):
    """Middleware for rate limiting"""
    
    def __init__(self, requests_per_second: float = 10.0, 
                 requests_per_minute: float = 600.0):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.last_request_time = 0
    
    def _clean_old_requests(self):
        """Remove request times older than 1 minute"""
        current_time = time.time()
        self.request_times = [
            t for t in self.request_times 
            if (current_time - t) <= 60
        ]
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rate limiting"""
        current_time = time.time()
        self._clean_old_requests()
        
        # Check per-second rate limit
        if current_time - self.last_request_time < (1.0 / self.requests_per_second):
            delay = (1.0 / self.requests_per_second) - (current_time - self.last_request_time)
            time.sleep(delay)
            current_time = time.time()
        
        # Check per-minute rate limit
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = min(self.request_times)
            delay = 60 - (current_time - oldest_request)
            if delay > 0:
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {delay:.1f} seconds",
                    retry_after=delay
                )
        
        self.request_times.append(current_time)
        self.last_request_time = current_time
        
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limit responses"""
        response = response_context.get('response')
        
        # Respect server-side rate limiting
        if response and hasattr(response, 'status_code') and response.status_code == 429:
            retry_after = None
            if hasattr(response, 'headers'):
                retry_after = response.headers.get('Retry-After')
            
            raise RateLimitError(
                "Server rate limit exceeded",
                retry_after=retry_after
            )
        
        return response_context


class MetricsMiddleware(BaseMiddleware):
    """Middleware for collecting metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'status_codes': {},
            'error_types': {}
        }
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Start timing request"""
        request_context['_metrics_start_time'] = time.time()
        self.metrics['total_requests'] += 1
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Record response metrics"""
        request_ctx = response_context.get('request_context', {})
        response = response_context.get('response')
        
        start_time = request_ctx.get('_metrics_start_time')
        if start_time:
            response_time = time.time() - start_time
            self.metrics['total_response_time'] += response_time
        
        if response and hasattr(response, 'status_code'):
            status_code = response.status_code
            self.metrics['status_codes'][status_code] = \
                self.metrics['status_codes'].get(status_code, 0) + 1
            
            if 200 <= status_code < 300:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
        
        return response_context
    
    def on_error(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Record error metrics"""
        error = error_context.get('error')
        if error:
            error_type = type(error).__name__
            self.metrics['error_types'][error_type] = \
                self.metrics['error_types'].get(error_type, 0) + 1
            self.metrics['failed_requests'] += 1
        
        return error_context
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        metrics = self.metrics.copy()
        if metrics['total_requests'] > 0:
            metrics['average_response_time'] = \
                metrics['total_response_time'] / metrics['total_requests']
            metrics['success_rate'] = \
                metrics['successful_requests'] / metrics['total_requests']
        else:
            metrics['average_response_time'] = 0.0
            metrics['success_rate'] = 0.0
        
        return metrics


class RetryMiddleware(BaseMiddleware):
    """Middleware for automatic retries with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize retry context"""
        request_context['_retry_attempt'] = 0
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle response for retry logic"""
        return response_context
    
    def on_error(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors with retry logic"""
        from .exceptions import NetworkError, TimeoutError, RequestFailedError
        
        request_ctx = error_context.get('request_context', {})
        error = error_context.get('error')
        attempt = request_ctx.get('_retry_attempt', 0)
        
        # Check if we should retry
        should_retry = (
            attempt < self.max_attempts - 1 and
            isinstance(error, (NetworkError, TimeoutError)) or
            (isinstance(error, RequestFailedError) and 
             hasattr(error, 'status_code') and 
             error.status_code in [408, 429, 500, 502, 503, 504])
        )
        
        if should_retry:
            delay = exponential_backoff(
                attempt, self.base_delay, self.max_delay
            )
            time.sleep(delay)
            request_ctx['_retry_attempt'] = attempt + 1
            error_context['_should_retry'] = True
        
        return error_context


class CompressionMiddleware(BaseMiddleware):
    """Middleware for request/response compression"""
    
    def __init__(self, compression_types: List[str] = None):
        self.compression_types = compression_types or ['gzip', 'deflate', 'br']
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Add compression headers to request"""
        headers = request_context.get('headers', {})
        
        # Add Accept-Encoding header for response compression
        if 'Accept-Encoding' not in headers:
            headers['Accept-Encoding'] = ', '.join(self.compression_types)
        
        # Compress request body if it's large enough
        data = request_context.get('data')
        if data and len(str(data)) > 1024:  # Only compress if > 1KB
            import gzip
            if isinstance(data, str):
                compressed_data = gzip.compress(data.encode('utf-8'))
                headers['Content-Encoding'] = 'gzip'
                headers['Content-Type'] = headers.get('Content-Type', 'text/plain')
                request_context['data'] = compressed_data
        
        request_context['headers'] = headers
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle compressed responses"""
        # Response decompression is typically handled by the HTTP client
        return response_context


class SecurityMiddleware(BaseMiddleware):
    """Middleware for security enhancements"""
    
    def __init__(self, verify_ssl: bool = True, cert_pinning: Dict[str, str] = None):
        self.verify_ssl = verify_ssl
        self.cert_pinning = cert_pinning or {}
    
    def before_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Add security configurations"""
        request_context['verify_ssl'] = self.verify_ssl
        
        # Add security headers
        headers = request_context.get('headers', {})
        
        # Add common security headers if not present
        security_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',  # Do Not Track
        }
        
        for header, value in security_headers.items():
            if header not in headers:
                headers[header] = value
        
        request_context['headers'] = headers
        return request_context
    
    def after_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response security"""
        response = response_context.get('response')
        
        if response and hasattr(response, 'headers'):
            # Check for security headers in response
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            
            missing_headers = [
                header for header in security_headers
                if header not in response.headers
            ]
            
            if missing_headers:
                # Log warning about missing security headers
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Response missing security headers: {missing_headers}"
                )
        
        return response_context


class MiddlewareManager:
    """Manages middleware execution pipeline"""
    
    def __init__(self):
        self.middlewares: List[BaseMiddleware] = []
    
    def add_middleware(self, middleware: BaseMiddleware):
        """Add middleware to the pipeline"""
        if not isinstance(middleware, BaseMiddleware):
            raise MiddlewareError("Middleware must inherit from BaseMiddleware")
        self.middlewares.append(middleware)
    
    def remove_middleware(self, middleware_class):
        """Remove middleware of specific type"""
        self.middlewares = [
            mw for mw in self.middlewares
            if not isinstance(mw, middleware_class)
        ]
    
    def process_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through all middleware"""
        for middleware in self.middlewares:
            try:
                # Check for cached response from CachingMiddleware
                if '_cached_response' in request_context:
                    return request_context
                
                request_context = middleware.before_request(request_context)
            except Exception as e:
                raise MiddlewareError(f"Error in {type(middleware).__name__}: {e}")
        
        return request_context
    
    def process_response(self, response_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process response through all middleware (in reverse order)"""
        for middleware in reversed(self.middlewares):
            try:
                response_context = middleware.after_response(response_context)
            except Exception as e:
                raise MiddlewareError(f"Error in {type(middleware).__name__}: {e}")
        
        return response_context
    
    def process_error(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process error through all middleware"""
        for middleware in self.middlewares:
            try:
                error_context = middleware.on_error(error_context)
            except Exception as e:
                # Don't let middleware errors mask the original error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in middleware {type(middleware).__name__}: {e}")
        
        return error_context


# Convenience functions for creating common middleware combinations
def create_default_middleware() -> List[BaseMiddleware]:
    """Create default middleware stack"""
    return [
        SecurityMiddleware(),
        RetryMiddleware(max_attempts=3),
        CompressionMiddleware(),
        LoggingMiddleware()
    ]


def create_caching_middleware(ttl: int = 3600, max_size: int = 1000) -> CachingMiddleware:
    """Create caching middleware with custom settings"""
    return CachingMiddleware(max_size=max_size, ttl=ttl)


def create_auth_middleware(auth_type: str, **kwargs) -> AuthMiddleware:
    """Create authentication middleware"""
    return AuthMiddleware(auth_type=auth_type, **kwargs)


def create_rate_limiting_middleware(rps: float = 10.0, rpm: float = 600.0) -> RateLimitingMiddleware:
    """Create rate limiting middleware"""
    return RateLimitingMiddleware(requests_per_second=rps, requests_per_minute=rpm)