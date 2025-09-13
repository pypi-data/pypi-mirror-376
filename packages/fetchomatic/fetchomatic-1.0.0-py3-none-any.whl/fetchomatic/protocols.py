"""
SmartFetch Protocol Detection and Routing
"""

import urllib.parse
from enum import Enum
from typing import Dict, Any, Optional, Tuple, Type
from .exceptions import ProtocolNotSupportedError, ValidationError


class Protocol(Enum):
    """Supported protocols"""
    HTTP = "http"
    HTTPS = "https"
    UDP = "udp"
    WEBSOCKET = "ws"
    WEBSOCKET_SECURE = "wss"
    FTP = "ftp"
    FTPS = "ftps"


class ProtocolDetector:
    """Detects and validates protocols from URLs"""
    
    SUPPORTED_PROTOCOLS = {
        Protocol.HTTP,
        Protocol.HTTPS,
        Protocol.UDP,
        Protocol.WEBSOCKET,
        Protocol.WEBSOCKET_SECURE
    }
    
    # Protocol aliases
    PROTOCOL_ALIASES = {
        'http': Protocol.HTTP,
        'https': Protocol.HTTPS,
        'udp': Protocol.UDP,
        'ws': Protocol.WEBSOCKET,
        'wss': Protocol.WEBSOCKET_SECURE,
        'websocket': Protocol.WEBSOCKET,
        'websockets': Protocol.WEBSOCKET_SECURE
    }
    
    @classmethod
    def detect_protocol(cls, url: str) -> Protocol:
        """Detect protocol from URL"""
        if not url:
            raise ValidationError("URL cannot be empty")
        
        try:
            parsed = urllib.parse.urlparse(url)
            scheme = parsed.scheme.lower()
            
            if not scheme:
                # Default to HTTPS if no scheme provided
                return Protocol.HTTPS
            
            if scheme in cls.PROTOCOL_ALIASES:
                protocol = cls.PROTOCOL_ALIASES[scheme]
                
                if protocol not in cls.SUPPORTED_PROTOCOLS:
                    raise ProtocolNotSupportedError(
                        f"Protocol '{scheme}' is not supported. "
                        f"Supported protocols: {[p.value for p in cls.SUPPORTED_PROTOCOLS]}"
                    )
                
                return protocol
            else:
                raise ProtocolNotSupportedError(
                    f"Unknown protocol '{scheme}'. "
                    f"Supported protocols: {[p.value for p in cls.SUPPORTED_PROTOCOLS]}"
                )
        
        except ValueError as e:
            raise ValidationError(f"Invalid URL format: {e}")
    
    @classmethod
    def is_secure_protocol(cls, protocol: Protocol) -> bool:
        """Check if protocol is secure"""
        return protocol in {Protocol.HTTPS, Protocol.WEBSOCKET_SECURE}
    
    @classmethod
    def get_default_port(cls, protocol: Protocol) -> int:
        """Get default port for protocol"""
        port_map = {
            Protocol.HTTP: 80,
            Protocol.HTTPS: 443,
            Protocol.WEBSOCKET: 80,
            Protocol.WEBSOCKET_SECURE: 443,
            Protocol.UDP: 53,  # DNS default, but UDP can use any port
        }
        return port_map.get(protocol, 80)
    
    @classmethod
    def normalize_url(cls, url: str) -> Tuple[str, Protocol]:
        """Normalize URL and return with detected protocol"""
        protocol = cls.detect_protocol(url)
        
        parsed = urllib.parse.urlparse(url)
        
        # If no scheme was provided, add it
        if not parsed.scheme:
            scheme = protocol.value
            url = f"{scheme}://{url}"
            parsed = urllib.parse.urlparse(url)
        
        # Normalize the URL
        normalized = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or '/',
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return normalized, protocol
    
    @classmethod
    def validate_url_for_protocol(cls, url: str, protocol: Protocol) -> bool:
        """Validate URL format for specific protocol"""
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Basic validation
            if not parsed.netloc:
                return False
            
            # Protocol-specific validation
            if protocol in {Protocol.HTTP, Protocol.HTTPS}:
                return cls._validate_http_url(parsed)
            elif protocol == Protocol.UDP:
                return cls._validate_udp_url(parsed)
            elif protocol in {Protocol.WEBSOCKET, Protocol.WEBSOCKET_SECURE}:
                return cls._validate_websocket_url(parsed)
            
            return True
        
        except Exception:
            return False
    
    @classmethod
    def _validate_http_url(cls, parsed: urllib.parse.ParseResult) -> bool:
        """Validate HTTP/HTTPS URL"""
        # Must have netloc (domain/IP)
        if not parsed.netloc:
            return False
        
        # Port validation if specified
        if ':' in parsed.netloc:
            try:
                port = int(parsed.netloc.split(':')[-1])
                if not (1 <= port <= 65535):
                    return False
            except ValueError:
                return False
        
        return True
    
    @classmethod
    def _validate_udp_url(cls, parsed: urllib.parse.ParseResult) -> bool:
        """Validate UDP URL"""
        # UDP requires host and port
        if ':' not in parsed.netloc:
            return False
        
        try:
            port = int(parsed.netloc.split(':')[-1])
            if not (1 <= port <= 65535):
                return False
        except ValueError:
            return False
        
        return True
    
    @classmethod
    def _validate_websocket_url(cls, parsed: urllib.parse.ParseResult) -> bool:
        """Validate WebSocket URL"""
        return cls._validate_http_url(parsed)


class ProtocolRouter:
    """Routes requests to appropriate client based on protocol"""
    
    def __init__(self):
        self.client_map = {}
        self._register_default_clients()
    
    def _register_default_clients(self):
        """Register default client mappings"""
        from .http_client import HTTPClient
        from .udp_client import UDPClient
        from .websocket_client import WebSocketClient
        
        # HTTP protocols
        self.client_map[Protocol.HTTP] = HTTPClient
        self.client_map[Protocol.HTTPS] = HTTPClient
        
        # UDP protocol
        self.client_map[Protocol.UDP] = UDPClient
        
        # WebSocket protocols
        self.client_map[Protocol.WEBSOCKET] = WebSocketClient
        self.client_map[Protocol.WEBSOCKET_SECURE] = WebSocketClient
    
    def register_client(self, protocol: Protocol, client_class: Type):
        """Register custom client for protocol"""
        self.client_map[protocol] = client_class
    
    def get_client_class(self, protocol: Protocol) -> Type:
        """Get client class for protocol"""
        if protocol not in self.client_map:
            raise ProtocolNotSupportedError(
                f"No client registered for protocol: {protocol.value}"
            )
        
        return self.client_map[protocol]
    
    def create_client(self, protocol: Protocol, **kwargs) -> Any:
        """Create client instance for protocol"""
        client_class = self.get_client_class(protocol)
        return client_class(**kwargs)


class ProtocolConfig:
    """Configuration for protocol-specific settings"""
    
    def __init__(self):
        self.configs = {
            Protocol.HTTP: {
                'timeout': 30.0,
                'max_redirects': 5,
                'verify_ssl': True,
                'allow_redirects': True,
                'stream': False
            },
            Protocol.HTTPS: {
                'timeout': 30.0,
                'max_redirects': 5,
                'verify_ssl': True,
                'allow_redirects': True,
                'stream': False
            },
            Protocol.UDP: {
                'timeout': 10.0,
                'buffer_size': 8192,
                'retries': 3
            },
            Protocol.WEBSOCKET: {
                'timeout': 30.0,
                'ping_interval': 20,
                'ping_timeout': 10,
                'close_timeout': 10
            },
            Protocol.WEBSOCKET_SECURE: {
                'timeout': 30.0,
                'ping_interval': 20,
                'ping_timeout': 10,
                'close_timeout': 10,
                'verify_ssl': True
            }
        }
    
    def get_config(self, protocol: Protocol) -> Dict[str, Any]:
        """Get configuration for protocol"""
        return self.configs.get(protocol, {}).copy()
    
    def set_config(self, protocol: Protocol, key: str, value: Any):
        """Set configuration value for protocol"""
        if protocol not in self.configs:
            self.configs[protocol] = {}
        self.configs[protocol][key] = value
    
    def update_config(self, protocol: Protocol, config: Dict[str, Any]):
        """Update configuration for protocol"""
        if protocol not in self.configs:
            self.configs[protocol] = {}
        self.configs[protocol].update(config)


class ProtocolAdapterRegistry:
    """Registry for protocol adapters and converters"""
    
    def __init__(self):
        self.adapters = {}
        self.converters = {}
    
    def register_adapter(self, from_protocol: Protocol, to_protocol: Protocol,
                        adapter_func: callable):
        """Register protocol adapter function"""
        key = (from_protocol, to_protocol)
        self.adapters[key] = adapter_func
    
    def register_converter(self, protocol: Protocol, content_type: str,
                          converter_func: callable):
        """Register content converter for protocol"""
        key = (protocol, content_type)
        self.converters[key] = converter_func
    
    def adapt_request(self, request_context: Dict[str, Any],
                     from_protocol: Protocol, to_protocol: Protocol) -> Dict[str, Any]:
        """Adapt request from one protocol to another"""
        key = (from_protocol, to_protocol)
        
        if key in self.adapters:
            return self.adapters[key](request_context)
        
        # Default behavior: pass through
        return request_context
    
    def convert_content(self, content: Any, protocol: Protocol,
                       content_type: str) -> Any:
        """Convert content for specific protocol"""
        key = (protocol, content_type)
        
        if key in self.converters:
            return self.converters[key](content)
        
        # Default behavior: pass through
        return content


# Global instances
protocol_detector = ProtocolDetector()
protocol_router = ProtocolRouter()
protocol_config = ProtocolConfig()
protocol_adapter_registry = ProtocolAdapterRegistry()


def detect_protocol(url: str) -> Protocol:
    """Convenience function to detect protocol"""
    return protocol_detector.detect_protocol(url)


def normalize_url(url: str) -> Tuple[str, Protocol]:
    """Convenience function to normalize URL"""
    return protocol_detector.normalize_url(url)


def get_client_for_url(url: str, **kwargs) -> Any:
    """Get appropriate client for URL"""
    protocol = detect_protocol(url)
    return protocol_router.create_client(protocol, **kwargs)


def is_secure_protocol(url: str) -> bool:
    """Check if URL uses secure protocol"""
    protocol = detect_protocol(url)
    return protocol_detector.is_secure_protocol(protocol)


# Register default protocol adapters
def _register_default_adapters():
    """Register default protocol adapters"""
    
    def http_to_websocket(request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt HTTP request to WebSocket"""
        # Convert HTTP URL to WebSocket URL
        url = request_context.get('url', '')
        if url.startswith('http://'):
            request_context['url'] = url.replace('http://', 'ws://', 1)
        elif url.startswith('https://'):
            request_context['url'] = url.replace('https://', 'wss://', 1)
        
        return request_context
    
    protocol_adapter_registry.register_adapter(
        Protocol.HTTP, Protocol.WEBSOCKET, http_to_websocket
    )
    protocol_adapter_registry.register_adapter(
        Protocol.HTTPS, Protocol.WEBSOCKET_SECURE, http_to_websocket
    )


# Initialize default adapters
_register_default_adapters()