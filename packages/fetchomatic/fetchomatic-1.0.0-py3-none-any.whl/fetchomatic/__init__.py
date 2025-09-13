"""
Fetchomatic - A comprehensive networking framework with semantic methods
"""

__version__ = "1.0.0"
__author__ = "Aayush Bohora"
__description__ = "Advanced networking framework with protocol detection and semantic methods"

from fetchomatic.core import SmartFetch
from fetchomatic.exceptions import (
    SmartFetchError,
    ProtocolNotSupportedError,
    RequestFailedError,
    TimeoutError as SmartFetchTimeoutError,
    NetworkError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)
from fetchomatic.middleware import (
    LoggingMiddleware,
    CachingMiddleware,
    AuthMiddleware,
    RateLimitingMiddleware,
    MetricsMiddleware,
    RetryMiddleware
)
from fetchomatic.utils import (
    parse_json,
    parse_xml,
    parse_yaml,
    url_encode,
    url_decode,
    validate_url,
    format_headers
)

# Default instance for convenience
default = SmartFetch()

# Expose semantic methods at module level
fetch = default.fetch
send = default.send
update = default.update
modify = default.modify
remove = default.remove
info = default.info
probe = default.probe

__all__ = [
    'SmartFetch',
    'SmartFetchError',
    'ProtocolNotSupportedError',
    'RequestFailedError',
    'SmartFetchTimeoutError',
    'NetworkError',
    'ValidationError',
    'AuthenticationError',
    'RateLimitError',
    'LoggingMiddleware',
    'CachingMiddleware',
    'AuthMiddleware',
    'RateLimitingMiddleware',
    'MetricsMiddleware',
    'RetryMiddleware',
    'parse_json',
    'parse_xml',
    'parse_yaml',
    'url_encode',
    'url_decode',
    'validate_url',
    'format_headers',
    'default',
    'fetch',
    'send',
    'update',
    'modify',
    'remove',
    'info',
    'probe'
]
