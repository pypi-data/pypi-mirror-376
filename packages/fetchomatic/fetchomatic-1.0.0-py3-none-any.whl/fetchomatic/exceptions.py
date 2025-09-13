"""
SmartFetch Exception Classes
"""


class SmartFetchError(Exception):
    """Base exception for all SmartFetch errors"""
    def __init__(self, message, code=None, response=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.response = response

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ProtocolNotSupportedError(SmartFetchError):
    """Raised when an unsupported protocol is used"""
    pass


class RequestFailedError(SmartFetchError):
    """Raised when a request fails"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message, status_code, response)
        self.status_code = status_code


class TimeoutError(SmartFetchError):
    """Raised when a request times out"""
    pass


class NetworkError(SmartFetchError):
    """Raised for network-related errors"""
    pass


class ValidationError(SmartFetchError):
    """Raised when input validation fails"""
    pass


class AuthenticationError(SmartFetchError):
    """Raised for authentication failures"""
    pass


class RateLimitError(SmartFetchError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class MiddlewareError(SmartFetchError):
    """Raised for middleware-related errors"""
    pass


class ParsingError(SmartFetchError):
    """Raised when response parsing fails"""
    pass


class ConnectionError(SmartFetchError):
    """Raised for connection-related errors"""
    pass


class SSLError(SmartFetchError):
    """Raised for SSL-related errors"""
    pass


class ProxyError(SmartFetchError):
    """Raised for proxy-related errors"""
    pass


# HTTP status code to exception mapping
STATUS_CODE_EXCEPTIONS = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: RequestFailedError,
    408: TimeoutError,
    429: RateLimitError,
    500: RequestFailedError,
    502: NetworkError,
    503: NetworkError,
    504: TimeoutError
}


def get_exception_for_status_code(status_code, message="", response=None):
    """Get appropriate exception class for HTTP status code"""
    exception_class = STATUS_CODE_EXCEPTIONS.get(status_code, RequestFailedError)
    
    if exception_class == RateLimitError:
        retry_after = None
        if response and hasattr(response, 'headers'):
            retry_after = response.headers.get('Retry-After')
        return exception_class(message, retry_after)
    elif exception_class in [RequestFailedError, ValidationError, AuthenticationError]:
        return exception_class(message, status_code, response)
    else:
        return exception_class(message, status_code, response)