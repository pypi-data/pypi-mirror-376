"""
SmartFetch Core - Main dispatcher and orchestrator
"""

import asyncio
from typing import Any, Dict, Optional, Union, List, Type
from .protocols import (
    Protocol, ProtocolDetector, ProtocolRouter, ProtocolConfig,
    detect_protocol, normalize_url, get_client_for_url
)
from .middleware import MiddlewareManager, BaseMiddleware, create_default_middleware
from .http_client import HTTPClient, HTTPResponse
from .udp_client import UDPClient, UDPResponse
from .websocket_client import WebSocketClient, WebSocketMessage
from .exceptions import (
    SmartFetchError, ProtocolNotSupportedError, ValidationError,
    MiddlewareError
)
from .utils import validate_url, format_headers, RetryHelper


class SmartFetchResponse:
    """Unified response wrapper for all protocols"""
    
    def __init__(self, response: Any, protocol: Protocol, url: str):
        self._response = response
        self._protocol = protocol
        self._url = url
        self._cached_data = {}
    
    @property
    def protocol(self) -> Protocol:
        """Get the protocol used for this response"""
        return self._protocol
    
    @property
    def url(self) -> str:
        """Get the request URL"""
        return self._url
    
    @property
    def raw_response(self) -> Any:
        """Get the raw response object"""
        return self._response
    
    # Common interface methods
    def data(self) -> Union[str, bytes]:
        """Get response data (unified interface)"""
        if 'data' not in self._cached_data:
            if isinstance(self._response, HTTPResponse):
                self._cached_data['data'] = self._response.content()
            elif isinstance(self._response, UDPResponse):
                self._cached_data['data'] = self._response.data
            elif isinstance(self._response, WebSocketMessage):
                self._cached_data['data'] = self._response.data
            else:
                self._cached_data['data'] = str(self._response)
        
        return self._cached_data['data']
    
    async def adata(self) -> Union[str, bytes]:
        """Get response data (unified async interface)"""
        if 'data' not in self._cached_data:
            if isinstance(self._response, HTTPResponse):
                self._cached_data['data'] = await self._response.acontent()
            elif isinstance(self._response, UDPResponse):
                self._cached_data['data'] = self._response.data
            elif isinstance(self._response, WebSocketMessage):
                self._cached_data['data'] = self._response.data
            else:
                self._cached_data['data'] = str(self._response)
        
        return self._cached_data['data']
    
    def text(self) -> str:
        """Get response as text"""
        if 'text' not in self._cached_data:
            if isinstance(self._response, HTTPResponse):
                self._cached_data['text'] = self._response.text()
            elif isinstance(self._response, UDPResponse):
                self._cached_data['text'] = self._response.text()
            elif isinstance(self._response, WebSocketMessage):
                self._cached_data['text'] = self._response.text()
            else:
                self._cached_data['text'] = str(self._response)
        
        return self._cached_data['text']
    
    async def atext(self) -> str:
        """Get response as text (async)"""
        if 'text' not in self._cached_data:
            if isinstance(self._response, HTTPResponse):
                self._cached_data['text'] = await self._response.atext()
            elif isinstance(self._response, UDPResponse):
                self._cached_data['text'] = self._response.text()
            elif isinstance(self._response, WebSocketMessage):
                self._cached_data['text'] = self._response.text()
            else:
                self._cached_data['text'] = str(self._response)
        
        return self._cached_data['text']
    
    def json(self) -> Any:
        """Parse response as JSON"""
        if 'json' not in self._cached_data:
            if isinstance(self._response, HTTPResponse):
                self._cached_data['json'] = self._response.json()
            elif isinstance(self._response, UDPResponse):
                self._cached_data['json'] = self._response.json()
            elif isinstance(self._response, WebSocketMessage):
                self._cached_data['json'] = self._response.json()
            else:
                import json as json_module
                self._cached_data['json'] = json_module.loads(str(self._response))
        
        return self._cached_data['json']
    
    async def ajson(self) -> Any:
        """Parse response as JSON (async)"""
        if 'json' not in self._cached_data:
            if isinstance(self._response, HTTPResponse):
                self._cached_data['json'] = await self._response.ajson()
            elif isinstance(self._response, UDPResponse):
                self._cached_data['json'] = self._response.json()
            elif isinstance(self._response, WebSocketMessage):
                self._cached_data['json'] = self._response.json()
            else:
                import json as json_module
                self._cached_data['json'] = json_module.loads(str(self._response))
        
        return self._cached_data['json']
    
    # Protocol-specific attributes
    @property
    def status_code(self) -> Optional[int]:
        """Get HTTP status code (HTTP only)"""
        if isinstance(self._response, HTTPResponse):
            return self._response.status_code
        return None
    
    @property
    def headers(self) -> Optional[Dict[str, str]]:
        """Get HTTP headers (HTTP only)"""
        if isinstance(self._response, HTTPResponse):
            return self._response.headers
        return None
    
    @property
    def ok(self) -> bool:
        """Check if response is successful"""
        if isinstance(self._response, HTTPResponse):
            return self._response.ok
        # For other protocols, assume success if we got a response
        return True
    
    @property
    def size(self) -> int:
        """Get response size"""
        if hasattr(self._response, 'size'):
            return self._response.size
        elif hasattr(self._response, '__len__'):
            return len(self._response)
        else:
            return len(str(self._response))
    
    def validate(self, validator_func: callable) -> 'SmartFetchResponse':
        """Validate response using custom validator"""
        if not validator_func(self):
            raise ValidationError("Response validation failed")
        return self
    
    def parse_json(self) -> 'SmartFetchResponse':
        """Parse JSON and return self for chaining"""
        self.json()  # This will cache the parsed JSON
        return self
    
    async def aparse_json(self) -> 'SmartFetchResponse':
        """Parse JSON and return self for chaining (async)"""
        await self.ajson()  # This will cache the parsed JSON
        return self
    
    def save_to_file(self, filepath: str) -> 'SmartFetchResponse':
        """Save response to file"""
        if isinstance(self._response, HTTPResponse):
            self._response.save_to_file(filepath)
        else:
            with open(filepath, 'wb') as f:
                data = self.data()
                if isinstance(data, str):
                    f.write(data.encode('utf-8'))
                else:
                    f.write(data)
        return self
    
    async def asave_to_file(self, filepath: str) -> 'SmartFetchResponse':
        """Save response to file (async)"""
        if isinstance(self._response, HTTPResponse):
            await self._response.asave_to_file(filepath)
        else:
            with open(filepath, 'wb') as f:
                data = await self.adata()
                if isinstance(data, str):
                    f.write(data.encode('utf-8'))
                else:
                    f.write(data)
        return self
    
    def __str__(self) -> str:
        return f"SmartFetchResponse(protocol={self._protocol.value}, url={self._url}, size={self.size})"
    
    def __repr__(self) -> str:
        return self.__str__()


class SmartFetch:
    """Main SmartFetch class - the primary interface for all network operations"""
    
    def __init__(self, base_url: Optional[str] = None, 
                 middleware: Optional[List[BaseMiddleware]] = None,
                 default_timeout: Union[int, float] = 30.0,
                 default_headers: Optional[Dict[str, str]] = None,
                 auto_detect_protocol: bool = True,
                 enable_middleware: bool = True,
                 debug: bool = False):
        
        # Core configuration
        self.base_url = base_url.rstrip('/') if base_url else None
        self.default_timeout = default_timeout
        self.default_headers = format_headers(default_headers) if default_headers else {}
        self.auto_detect_protocol = auto_detect_protocol
        self.enable_middleware = enable_middleware
        self.debug = debug
        
        # Protocol handling
        self.protocol_detector = ProtocolDetector()
        self.protocol_router = ProtocolRouter()
        self.protocol_config = ProtocolConfig()
        
        # Middleware system
        self.middleware_manager = MiddlewareManager()
        if enable_middleware:
            # Add default middleware if none provided
            middleware = middleware or create_default_middleware()
            for mw in middleware:
                self.middleware_manager.add_middleware(mw)
        
        # Client instances cache
        self._client_cache = {}
    
    def _prepare_url(self, url: str) -> str:
        """Prepare URL by joining with base URL if needed"""
        if self.base_url and not url.startswith(('http://', 'https://', 'udp://', 'ws://', 'wss://')):
            if self.base_url.startswith(('ws://', 'wss://')):
                # WebSocket base URL
                separator = '/' if not self.base_url.endswith('/') and not url.startswith('/') else ''
                return f"{self.base_url}{separator}{url}"
            else:
                # HTTP base URL
                from urllib.parse import urljoin
                return urljoin(self.base_url, url)
        return url
    
    def _get_client(self, protocol: Protocol, **kwargs) -> Any:
        """Get or create client for protocol"""
        # Merge default configuration with protocol-specific config
        config = self.protocol_config.get_config(protocol)
        config.update(kwargs)
        
        # Add default headers if not specified
        if 'headers' not in config and self.default_headers:
            config['headers'] = self.default_headers.copy()
        
        # Add default timeout if not specified
        if 'timeout' not in config:
            config['timeout'] = self.default_timeout
        
        # Create client
        client_class = self.protocol_router.get_client_class(protocol)
        return client_class(**config)
    
    def _create_request_context(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Create request context for middleware processing"""
        return {
            'method': method,
            'url': url,
            'headers': kwargs.get('headers', {}),
            'params': kwargs.get('params', {}),
            'data': kwargs.get('data'),
            'json': kwargs.get('json'),
            'files': kwargs.get('files'),
            'timeout': kwargs.get('timeout'),
            'protocol': None,  # Will be set after detection
            'client_kwargs': kwargs
        }
    
    def _process_middleware_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through middleware"""
        if self.enable_middleware:
            return self.middleware_manager.process_request(request_context)
        return request_context
    
    def _process_middleware_response(self, response: Any, request_context: Dict[str, Any]) -> Any:
        """Process response through middleware"""
        if self.enable_middleware:
            response_context = {
                'response': response,
                'request_context': request_context
            }
            response_context = self.middleware_manager.process_response(response_context)
            return response_context.get('response', response)
        return response
    
    def _process_middleware_error(self, error: Exception, request_context: Dict[str, Any]) -> Exception:
        """Process error through middleware"""
        if self.enable_middleware:
            error_context = {
                'error': error,
                'request_context': request_context
            }
            error_context = self.middleware_manager.process_error(error_context)
            return error_context.get('error', error)
        return error
    
    def _make_request(self, method: str, url: str, **kwargs) -> SmartFetchResponse:
        """Make request using appropriate protocol client"""
        # Prepare URL
        url = self._prepare_url(url)
        
        # Validate URL
        if not validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        # Create request context
        request_context = self._create_request_context(method, url, **kwargs)
        
        try:
            # Detect protocol
            normalized_url, protocol = normalize_url(url)
            request_context['url'] = normalized_url
            request_context['protocol'] = protocol
            
            # Check for cached response from middleware
            request_context = self._process_middleware_request(request_context)
            if '_cached_response' in request_context:
                cached_response = request_context['_cached_response']
                return SmartFetchResponse(cached_response, protocol, normalized_url)
            
            # Get appropriate client
            client = self._get_client(protocol, **request_context['client_kwargs'])
            
            # Make request based on protocol
            if protocol in {Protocol.HTTP, Protocol.HTTPS}:
                response = self._make_http_request(client, method, request_context)
            elif protocol == Protocol.UDP:
                response = self._make_udp_request(client, method, request_context)
            elif protocol in {Protocol.WEBSOCKET, Protocol.WEBSOCKET_SECURE}:
                response = self._make_websocket_request(client, method, request_context)
            else:
                raise ProtocolNotSupportedError(f"Protocol {protocol.value} not supported")
            
            # Process response through middleware
            response = self._process_middleware_response(response, request_context)
            
            return SmartFetchResponse(response, protocol, normalized_url)
        
        except Exception as e:
            # Process error through middleware
            e = self._process_middleware_error(e, request_context)
            raise e
    
    def _make_http_request(self, client: HTTPClient, method: str, context: Dict[str, Any]) -> HTTPResponse:
        """Make HTTP request"""
        return client.request(
            method=method,
            url=context['url'],
            headers=context.get('headers'),
            params=context.get('params'),
            data=context.get('data'),
            json_data=context.get('json'),
            files=context.get('files'),
            timeout=context.get('timeout')
        )
    
    def _make_udp_request(self, client: UDPClient, method: str, context: Dict[str, Any]) -> UDPResponse:
        """Make UDP request"""
        # UDP doesn't have different methods like HTTP, so we just send data
        return client.send(context['url'], context.get('data'))
    
    def _make_websocket_request(self, client: WebSocketClient, method: str, context: Dict[str, Any]) -> WebSocketMessage:
        """Make WebSocket request"""
        # WebSocket is bidirectional, so we send data and expect a response
        return client.send(context['url'], context.get('data'))
    
    # Async version of _make_request
    async def _amake_request(self, method: str, url: str, **kwargs) -> SmartFetchResponse:
        """Make request using appropriate protocol client (async)"""
        # Prepare URL
        url = self._prepare_url(url)
        
        # Validate URL
        if not validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        # Create request context
        request_context = self._create_request_context(method, url, **kwargs)
        
        try:
            # Detect protocol
            normalized_url, protocol = normalize_url(url)
            request_context['url'] = normalized_url
            request_context['protocol'] = protocol
            
            # Process through middleware
            request_context = self._process_middleware_request(request_context)
            if '_cached_response' in request_context:
                cached_response = request_context['_cached_response']
                return SmartFetchResponse(cached_response, protocol, normalized_url)
            
            # Get appropriate client
            client = self._get_client(protocol, **request_context['client_kwargs'])
            
            # Make async request based on protocol
            if protocol in {Protocol.HTTP, Protocol.HTTPS}:
                response = await self._amake_http_request(client, method, request_context)
            elif protocol == Protocol.UDP:
                response = await self._amake_udp_request(client, method, request_context)
            elif protocol in {Protocol.WEBSOCKET, Protocol.WEBSOCKET_SECURE}:
                response = await self._amake_websocket_request(client, method, request_context)
            else:
                raise ProtocolNotSupportedError(f"Protocol {protocol.value} not supported")
            
            # Process response through middleware
            response = self._process_middleware_response(response, request_context)
            
            return SmartFetchResponse(response, protocol, normalized_url)
        
        except Exception as e:
            # Process error through middleware
            e = self._process_middleware_error(e, request_context)
            raise e
    
    async def _amake_http_request(self, client: HTTPClient, method: str, context: Dict[str, Any]) -> HTTPResponse:
        """Make HTTP request (async)"""
        return await client.arequest(
            method=method,
            url=context['url'],
            headers=context.get('headers'),
            params=context.get('params'),
            data=context.get('data'),
            json_data=context.get('json'),
            timeout=context.get('timeout')
        )
    
    async def _amake_udp_request(self, client: UDPClient, method: str, context: Dict[str, Any]) -> UDPResponse:
        """Make UDP request (async)"""
        return await client.asend(context['url'], context.get('data'))
    
    async def _amake_websocket_request(self, client: WebSocketClient, method: str, context: Dict[str, Any]) -> WebSocketMessage:
        """Make WebSocket request (async)"""
        return await client.asend(context['url'], context.get('data'))
    
    # Semantic HTTP methods (sync)
    def fetch(self, url: str, **kwargs) -> SmartFetchResponse:
        """GET request - fetch data from server"""
        return self._make_request('GET', url, **kwargs)
    
    def send(self, url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
        """POST request - send data to server"""
        return self._make_request('POST', url, data=data, **kwargs)
    
    def update(self, url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
        """PUT request - update resource on server"""
        return self._make_request('PUT', url, data=data, **kwargs)
    
    def modify(self, url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
        """PATCH request - partially modify resource on server"""
        return self._make_request('PATCH', url, data=data, **kwargs)
    
    def remove(self, url: str, **kwargs) -> SmartFetchResponse:
        """DELETE request - remove resource from server"""
        return self._make_request('DELETE', url, **kwargs)
    
    def info(self, url: str, **kwargs) -> SmartFetchResponse:
        """HEAD request - get metadata about resource"""
        return self._make_request('HEAD', url, **kwargs)
    
    def probe(self, url: str, **kwargs) -> SmartFetchResponse:
        """OPTIONS request - probe server capabilities"""
        return self._make_request('OPTIONS', url, **kwargs)
    
    # Semantic HTTP methods (async)
    async def afetch(self, url: str, **kwargs) -> SmartFetchResponse:
        """GET request - fetch data from server (async)"""
        return await self._amake_request('GET', url, **kwargs)
    
    async def asend(self, url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
        """POST request - send data to server (async)"""
        return await self._amake_request('POST', url, data=data, **kwargs)
    
    async def aupdate(self, url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
        """PUT request - update resource on server (async)"""
        return await self._amake_request('PUT', url, data=data, **kwargs)
    
    async def amodify(self, url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
        """PATCH request - partially modify resource on server (async)"""
        return await self._amake_request('PATCH', url, data=data, **kwargs)
    
    async def aremove(self, url: str, **kwargs) -> SmartFetchResponse:
        """DELETE request - remove resource from server (async)"""
        return await self._amake_request('DELETE', url, **kwargs)
    
    async def ainfo(self, url: str, **kwargs) -> SmartFetchResponse:
        """HEAD request - get metadata about resource (async)"""
        return await self._amake_request('HEAD', url, **kwargs)
    
    async def aprobe(self, url: str, **kwargs) -> SmartFetchResponse:
        """OPTIONS request - probe server capabilities (async)"""
        return await self._amake_request('OPTIONS', url, **kwargs)
    
    # Generic request method
    def request(self, method: str, url: str, **kwargs) -> SmartFetchResponse:
        """Make request with specific HTTP method"""
        return self._make_request(method.upper(), url, **kwargs)
    
    async def arequest(self, method: str, url: str, **kwargs) -> SmartFetchResponse:
        """Make request with specific HTTP method (async)"""
        return await self._amake_request(method.upper(), url, **kwargs)
    
    # Configuration methods
    def add_middleware(self, middleware: BaseMiddleware) -> 'SmartFetch':
        """Add middleware to the pipeline"""
        self.middleware_manager.add_middleware(middleware)
        return self
    
    def remove_middleware(self, middleware_class: Type[BaseMiddleware]) -> 'SmartFetch':
        """Remove middleware from the pipeline"""
        self.middleware_manager.remove_middleware(middleware_class)
        return self
    
    def set_base_url(self, base_url: str) -> 'SmartFetch':
        """Set base URL"""
        self.base_url = base_url.rstrip('/') if base_url else None
        return self
    
    def set_default_headers(self, headers: Dict[str, str]) -> 'SmartFetch':
        """Set default headers"""
        self.default_headers = format_headers(headers)
        return self
    
    def set_timeout(self, timeout: Union[int, float]) -> 'SmartFetch':
        """Set default timeout"""
        self.default_timeout = timeout
        return self
    
    def configure_protocol(self, protocol: Protocol, **config) -> 'SmartFetch':
        """Configure protocol-specific settings"""
        self.protocol_config.update_config(protocol, config)
        return self
    
    # Utility methods
    def detect_protocol(self, url: str) -> Protocol:
        """Detect protocol for URL"""
        return self.protocol_detector.detect_protocol(url)
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL"""
        normalized, _ = normalize_url(url)
        return normalized
    
    # Context manager support
    def __enter__(self) -> 'SmartFetch':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup any resources
        pass
    
    async def __aenter__(self) -> 'SmartFetch':
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup any async resources
        pass


class SmartFetchBuilder:
    """Builder pattern for SmartFetch configuration"""
    
    def __init__(self):
        self._config = {}
        self._middleware = []
    
    def base_url(self, url: str) -> 'SmartFetchBuilder':
        """Set base URL"""
        self._config['base_url'] = url
        return self
    
    def timeout(self, timeout: Union[int, float]) -> 'SmartFetchBuilder':
        """Set default timeout"""
        self._config['default_timeout'] = timeout
        return self
    
    def headers(self, headers: Dict[str, str]) -> 'SmartFetchBuilder':
        """Set default headers"""
        self._config['default_headers'] = headers
        return self
    
    def middleware(self, middleware: BaseMiddleware) -> 'SmartFetchBuilder':
        """Add middleware"""
        self._middleware.append(middleware)
        return self
    
    def debug(self, enabled: bool = True) -> 'SmartFetchBuilder':
        """Enable debug mode"""
        self._config['debug'] = enabled
        return self
    
    def auto_detect_protocol(self, enabled: bool = True) -> 'SmartFetchBuilder':
        """Enable/disable auto protocol detection"""
        self._config['auto_detect_protocol'] = enabled
        return self
    
    def build(self) -> SmartFetch:
        """Build SmartFetch instance"""
        if self._middleware:
            self._config['middleware'] = self._middleware
        return SmartFetch(**self._config)


# Convenience functions
def create(**kwargs) -> SmartFetch:
    """Create SmartFetch instance"""
    return SmartFetch(**kwargs)


def builder() -> SmartFetchBuilder:
    """Create SmartFetch builder"""
    return SmartFetchBuilder()


# Module-level convenience instance
_default_instance = None


def get_default() -> SmartFetch:
    """Get default SmartFetch instance"""
    global _default_instance
    if _default_instance is None:
        _default_instance = SmartFetch()
    return _default_instance


# Module-level semantic methods using default instance
def fetch(url: str, **kwargs) -> SmartFetchResponse:
    """Fetch data using default instance"""
    return get_default().fetch(url, **kwargs)


def send(url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
    """Send data using default instance"""
    return get_default().send(url, data, **kwargs)


def update(url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
    """Update resource using default instance"""
    return get_default().update(url, data, **kwargs)


def modify(url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
    """Modify resource using default instance"""
    return get_default().modify(url, data, **kwargs)


def remove(url: str, **kwargs) -> SmartFetchResponse:
    """Remove resource using default instance"""
    return get_default().remove(url, **kwargs)


def info(url: str, **kwargs) -> SmartFetchResponse:
    """Get resource info using default instance"""
    return get_default().info(url, **kwargs)


def probe(url: str, **kwargs) -> SmartFetchResponse:
    """Probe server using default instance"""
    return get_default().probe(url, **kwargs)


# Async versions
async def afetch(url: str, **kwargs) -> SmartFetchResponse:
    """Fetch data using default instance (async)"""
    return await get_default().afetch(url, **kwargs)


async def asend(url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
    """Send data using default instance (async)"""
    return await get_default().asend(url, data, **kwargs)


async def aupdate(url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
    """Update resource using default instance (async)"""
    return await get_default().aupdate(url, data, **kwargs)


async def amodify(url: str, data: Any = None, **kwargs) -> SmartFetchResponse:
    """Modify resource using default instance (async)"""
    return await get_default().amodify(url, data, **kwargs)


async def aremove(url: str, **kwargs) -> SmartFetchResponse:
    """Remove resource using default instance (async)"""
    return await get_default().aremove(url, **kwargs)


async def ainfo(url: str, **kwargs) -> SmartFetchResponse:
    """Get resource info using default instance (async)"""
    return await get_default().ainfo(url, **kwargs)


async def aprobe(url: str, **kwargs) -> SmartFetchResponse:
    """Probe server using default instance (async)"""
    return await get_default().aprobe(url, **kwargs)