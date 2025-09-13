"""
SmartFetch Utility Functions
"""

import json
import xml.etree.ElementTree as ET
import yaml
import urllib.parse
import time
import random
import re
import hashlib
from typing import Any, Dict, Optional, Union, Callable
from .exceptions import ParsingError, ValidationError


def parse_json(data: Union[str, bytes]) -> Any:
    """Parse JSON data with error handling"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParsingError(f"Failed to parse JSON: {e}")


def parse_xml(data: Union[str, bytes]) -> ET.Element:
    """Parse XML data with error handling"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return ET.fromstring(data)
    except (ET.ParseError, UnicodeDecodeError) as e:
        raise ParsingError(f"Failed to parse XML: {e}")


def parse_yaml(data: Union[str, bytes]) -> Any:
    """Parse YAML data with error handling"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return yaml.safe_load(data)
    except (yaml.YAMLError, UnicodeDecodeError) as e:
        raise ParsingError(f"Failed to parse YAML: {e}")


def url_encode(params: Dict[str, Any]) -> str:
    """URL encode parameters"""
    return urllib.parse.urlencode(params, safe='', quote_via=urllib.parse.quote)


def url_decode(encoded_string: str) -> Dict[str, str]:
    """URL decode parameters"""
    return dict(urllib.parse.parse_qsl(encoded_string))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = re.compile(
        r'^(?:http|ftp|udp|ws|wss)s?://'  # http:// or https:// or ftp:// or udp:// or ws://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None


def format_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Format and validate headers"""
    if not headers:
        return {}
    
    formatted = {}
    for key, value in headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValidationError(f"Header key and value must be strings: {key}={value}")
        formatted[key.strip()] = value.strip()
    
    return formatted


def detect_content_type(data: Union[str, bytes, dict]) -> str:
    """Automatically detect content type"""
    if isinstance(data, dict):
        return 'application/json'
    elif isinstance(data, (str, bytes)):
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8')
            except UnicodeDecodeError:
                return 'application/octet-stream'
        
        data = data.strip()
        if data.startswith('{') or data.startswith('['):
            return 'application/json'
        elif data.startswith('<'):
            return 'application/xml'
        elif '=' in data and '&' in data:
            return 'application/x-www-form-urlencoded'
        else:
            return 'text/plain'
    else:
        return 'application/octet-stream'


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0, 
                       jitter: bool = True) -> float:
    """Calculate exponential backoff delay"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    if jitter:
        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
    return delay


def create_cache_key(*args, **kwargs) -> str:
    """Create a cache key from arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    # Ensure it's not empty
    return sanitized or 'unnamed_file'


def format_bytes(num_bytes: int) -> str:
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries, with later ones taking precedence"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def is_success_status(status_code: int) -> bool:
    """Check if HTTP status code indicates success"""
    return 200 <= status_code < 300


def is_redirect_status(status_code: int) -> bool:
    """Check if HTTP status code indicates redirect"""
    return 300 <= status_code < 400


def is_client_error_status(status_code: int) -> bool:
    """Check if HTTP status code indicates client error"""
    return 400 <= status_code < 500


def is_server_error_status(status_code: int) -> bool:
    """Check if HTTP status code indicates server error"""
    return 500 <= status_code < 600


class RetryHelper:
    """Helper class for retry logic with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if we should retry based on attempt count and exception type"""
        if attempt >= self.max_attempts:
            return False
        
        # Retry on network errors, timeouts, and 5xx status codes
        from .exceptions import NetworkError, TimeoutError, RequestFailedError
        
        if isinstance(exception, (NetworkError, TimeoutError)):
            return True
        
        if isinstance(exception, RequestFailedError):
            # Retry on 5xx status codes and some 4xx codes
            if hasattr(exception, 'status_code'):
                return exception.status_code in [408, 429, 500, 502, 503, 504]
        
        return False
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt"""
        return exponential_backoff(attempt, self.base_delay, self.max_delay)
    
    async def async_sleep(self, delay: float):
        """Async sleep utility"""
        import asyncio
        await asyncio.sleep(delay)
    
    def sync_sleep(self, delay: float):
        """Sync sleep utility"""
        time.sleep(delay)


def create_user_agent(name: str = "SmartFetch", version: str = "1.0.0") -> str:
    """Create a user agent string"""
    import platform
    import sys
    
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    system = platform.system()
    
    return f"{name}/{version} (Python/{python_version}; {system})"


def validate_timeout(timeout: Union[int, float, tuple, None]) -> Union[float, tuple, None]:
    """Validate and normalize timeout values"""
    if timeout is None:
        return None
    
    if isinstance(timeout, (int, float)):
        if timeout <= 0:
            raise ValidationError("Timeout must be positive")
        return float(timeout)
    
    if isinstance(timeout, tuple):
        if len(timeout) != 2:
            raise ValidationError("Timeout tuple must have exactly 2 elements")
        connect_timeout, read_timeout = timeout
        if connect_timeout <= 0 or read_timeout <= 0:
            raise ValidationError("Timeout values must be positive")
        return (float(connect_timeout), float(read_timeout))
    
    raise ValidationError("Timeout must be a number, tuple, or None")


def chunk_data(data: bytes, chunk_size: int = 8192):
    """Generator to chunk data into smaller pieces"""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def safe_join_url(base: str, path: str) -> str:
    """Safely join base URL with path"""
    if not base.endswith('/') and not path.startswith('/'):
        return f"{base}/{path}"
    elif base.endswith('/') and path.startswith('/'):
        return f"{base}{path[1:]}"
    else:
        return f"{base}{path}"