"""
SmartFetch HTTP Client
Handles HTTP/HTTPS requests with both sync and async support
"""

import requests
import aiohttp
import asyncio
import json
import time
from typing import Any, Dict, Optional, Union, AsyncGenerator, Generator
from urllib.parse import urljoin
from .exceptions import (
    RequestFailedError, TimeoutError, NetworkError, ValidationError,
    ParsingError, get_exception_for_status_code
)
from .utils import (
    format_headers, detect_content_type, validate_timeout,
    create_user_agent, is_success_status, RetryHelper
)


class HTTPResponse:
    """Wrapper for HTTP responses with unified interface"""
    
    def __init__(self, response, is_async: bool = False):
        self._response = response
        self._is_async = is_async
        self._content = None
        self._text = None
        self._json = None
    
    @property
    def status_code(self) -> int:
        """Get response status code"""
        return self._response.status if self._is_async else self._response.status_code
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get response headers"""
        if self._is_async:
            return dict(self._response.headers)
        return dict(self._response.headers)
    
    @property
    def url(self) -> str:
        """Get final URL after redirects"""
        return str(self._response.url)
    
    @property
    def ok(self) -> bool:
        """Check if response is successful"""
        return is_success_status(self.status_code)
    
    @property
    def encoding(self) -> Optional[str]:
        """Get response encoding"""
        if self._is_async:
            return self._response.charset
        return self._response.encoding
    
    def content(self) -> bytes:
        """Get response content as bytes"""
        if self._content is None:
            if self._is_async:
                raise RuntimeError("Use await response.acontent() for async responses")
            self._content = self._response.content
        return self._content
    
    async def acontent(self) -> bytes:
        """Get response content as bytes (async)"""
        if self._content is None:
            if not self._is_async:
                raise RuntimeError("Use response.content() for sync responses")
            self._content = await self._response.read()
        return self._content
    
    def text(self) -> str:
        """Get response content as text"""
        if self._text is None:
            if self._is_async:
                raise RuntimeError("Use await response.atext() for async responses")
            self._text = self._response.text
        return self._text
    
    async def atext(self) -> str:
        """Get response content as text (async)"""
        if self._text is None:
            if not self._is_async:
                raise RuntimeError("Use response.text() for sync responses")
            self._text = await self._response.text()
        return self._text
    
    def json(self) -> Any:
        """Parse response as JSON"""
        if self._json is None:
            if self._is_async:
                raise RuntimeError("Use await response.ajson() for async responses")
            try:
                self._json = self._response.json()
            except (ValueError, json.JSONDecodeError) as e:
                raise ParsingError(f"Failed to parse JSON: {e}")
        return self._json
    
    async def ajson(self) -> Any:
        """Parse response as JSON (async)"""
        if self._json is None:
            if not self._is_async:
                raise RuntimeError("Use response.json() for sync responses")
            try:
                self._json = await self._response.json()
            except (ValueError, json.JSONDecodeError) as e:
                raise ParsingError(f"Failed to parse JSON: {e}")
        return self._json
    
    def iter_content(self, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """Iterate over response content in chunks"""
        if self._is_async:
            raise RuntimeError("Use response.aiter_content() for async responses")
        
        for chunk in self._response.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk
    
    async def aiter_content(self, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """Iterate over response content in chunks (async)"""
        if not self._is_async:
            raise RuntimeError("Use response.iter_content() for sync responses")
        
        async for chunk in self._response.content.iter_chunked(chunk_size):
            if chunk:
                yield chunk
    
    def save_to_file(self, filepath: str, chunk_size: int = 8192):
        """Save response content to file"""
        with open(filepath, 'wb') as f:
            for chunk in self.iter_content(chunk_size):
                f.write(chunk)
    
    async def asave_to_file(self, filepath: str, chunk_size: int = 8192):
        """Save response content to file (async)"""
        with open(filepath, 'wb') as f:
            async for chunk in self.aiter_content(chunk_size):
                f.write(chunk)
    
    def raise_for_status(self):
        """Raise exception for HTTP error status codes"""
        if not self.ok:
            error_msg = f"HTTP {self.status_code} Error"
            if hasattr(self._response, 'reason'):
                error_msg += f": {self._response.reason}"
            
            exception = get_exception_for_status_code(
                self.status_code, error_msg, self
            )
            raise exception
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self._response, 'close'):
            self._response.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self._response, 'close'):
            await self._response.close()


class HTTPClient:
    """HTTP client with sync and async support"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Union[int, float, tuple] = 30,
                 headers: Optional[Dict[str, str]] = None, verify_ssl: bool = True,
                 proxy: Optional[str] = None, max_redirects: int = 5,
                 allow_redirects: bool = True, cookies: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/') if base_url else None
        self.timeout = validate_timeout(timeout)
        self.default_headers = format_headers(headers) if headers else {}
        self.verify_ssl = verify_ssl
        self.proxy = proxy
        self.max_redirects = max_redirects
        self.allow_redirects = allow_redirects
        self.cookies = cookies or {}
        
        # Add default User-Agent if not provided
        if 'User-Agent' not in self.default_headers:
            self.default_headers['User-Agent'] = create_user_agent()
        
        # Session for connection pooling
        self._session = None
        self._async_session = None
        self._retry_helper = RetryHelper()
    
    def _get_session(self) -> requests.Session:
        """Get or create requests session"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self.default_headers)
            self._session.verify = self.verify_ssl
            self._session.max_redirects = self.max_redirects
            
            if self.proxy:
                self._session.proxies = {'http': self.proxy, 'https': self.proxy}
            
            if self.cookies:
                self._session.cookies.update(self.cookies)
        
        return self._session
    
    async def _get_async_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._async_session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                verify_ssl=self.verify_ssl,
                limit=100,  # Connection pool limit
                limit_per_host=30
            )
            
            self._async_session = aiohttp.ClientSession(
                headers=self.default_headers,
                timeout=timeout,
                connector=connector,
                cookie_jar=aiohttp.CookieJar()
            )
            
            if self.cookies:
                for key, value in self.cookies.items():
                    self._async_session.cookie_jar.update_cookies({key: value})
        
        return self._async_session
    
    def _prepare_url(self, url: str) -> str:
        """Prepare URL by joining with base URL if needed"""
        if self.base_url and not url.startswith(('http://', 'https://')):
            return urljoin(self.base_url, url)
        return url
    
    def _prepare_request_data(self, data: Any, headers: Dict[str, str]) -> tuple:
        """Prepare request data and update headers"""
        if data is None:
            return None, headers
        
        headers = headers.copy()
        
        if isinstance(data, dict):
            # Auto-detect content type if not specified
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            # Convert to JSON if content type is JSON
            if headers.get('Content-Type', '').startswith('application/json'):
                data = json.dumps(data)
        
        elif isinstance(data, (str, bytes)):
            if 'Content-Type' not in headers:
                headers['Content-Type'] = detect_content_type(data)
        
        return data, headers
    
    def _handle_response_errors(self, response: HTTPResponse, raise_for_status: bool = True):
        """Handle response errors"""
        if raise_for_status and not response.ok:
            response.raise_for_status()
    
    # Synchronous methods
    def request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                params: Optional[Dict[str, Any]] = None, data: Any = None,
                json_data: Optional[Dict[str, Any]] = None, files: Optional[Dict] = None,
                timeout: Optional[Union[int, float, tuple]] = None,
                stream: bool = False, raise_for_status: bool = True,
                **kwargs) -> HTTPResponse:
        """Make HTTP request (sync)"""
        
        url = self._prepare_url(url)
        headers = format_headers(headers) if headers else {}
        timeout = validate_timeout(timeout) if timeout is not None else self.timeout
        
        # Handle JSON data
        if json_data is not None:
            if data is not None:
                raise ValidationError("Cannot specify both 'data' and 'json_data'")
            data = json.dumps(json_data)
            headers['Content-Type'] = 'application/json'
        
        # Prepare data and headers
        data, headers = self._prepare_request_data(data, headers)
        
        session = self._get_session()
        
        # Retry logic
        last_exception = None
        for attempt in range(self._retry_helper.max_attempts):
            try:
                response = session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    files=files,
                    timeout=timeout,
                    stream=stream,
                    allow_redirects=self.allow_redirects,
                    **kwargs
                )
                
                http_response = HTTPResponse(response, is_async=False)
                self._handle_response_errors(http_response, raise_for_status)
                return http_response
                
            except Exception as e:
                last_exception = e
                
                # Convert requests exceptions to our exceptions
                if isinstance(e, requests.exceptions.Timeout):
                    e = TimeoutError(f"Request timed out: {e}")
                elif isinstance(e, requests.exceptions.ConnectionError):
                    e = NetworkError(f"Connection error: {e}")
                elif isinstance(e, requests.exceptions.RequestException):
                    e = RequestFailedError(f"Request failed: {e}")
                
                if not self._retry_helper.should_retry(attempt, e):
                    break
                
                if attempt < self._retry_helper.max_attempts - 1:
                    delay = self._retry_helper.get_delay(attempt)
                    self._retry_helper.sync_sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception
    
    def fetch(self, url: str, **kwargs) -> HTTPResponse:
        """GET request (fetch semantic method)"""
        return self.request('GET', url, **kwargs)
    
    def send(self, url: str, data: Any = None, **kwargs) -> HTTPResponse:
        """POST request (send semantic method)"""
        return self.request('POST', url, data=data, **kwargs)
    
    def update(self, url: str, data: Any = None, **kwargs) -> HTTPResponse:
        """PUT request (update semantic method)"""
        return self.request('PUT', url, data=data, **kwargs)
    
    def modify(self, url: str, data: Any = None, **kwargs) -> HTTPResponse:
        """PATCH request (modify semantic method)"""
        return self.request('PATCH', url, data=data, **kwargs)
    
    def remove(self, url: str, **kwargs) -> HTTPResponse:
        """DELETE request (remove semantic method)"""
        return self.request('DELETE', url, **kwargs)
    
    def info(self, url: str, **kwargs) -> HTTPResponse:
        """HEAD request (info semantic method)"""
        return self.request('HEAD', url, **kwargs)
    
    def probe(self, url: str, **kwargs) -> HTTPResponse:
        """OPTIONS request (probe semantic method)"""
        return self.request('OPTIONS', url, **kwargs)
    
    # Asynchronous methods
    async def arequest(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                      params: Optional[Dict[str, Any]] = None, data: Any = None,
                      json_data: Optional[Dict[str, Any]] = None, timeout: Optional[Union[int, float]] = None,
                      raise_for_status: bool = True, **kwargs) -> HTTPResponse:
        """Make HTTP request (async)"""
        
        url = self._prepare_url(url)
        headers = format_headers(headers) if headers else {}
        timeout = validate_timeout(timeout) if timeout is not None else self.timeout
        
        # Handle JSON data
        if json_data is not None:
            if data is not None:
                raise ValidationError("Cannot specify both 'data' and 'json_data'")
            data = json_data  # aiohttp handles JSON serialization
            kwargs['json'] = data
            data = None
        else:
            # Prepare data and headers for non-JSON data
            data, headers = self._prepare_request_data(data, headers)
        
        session = await self._get_async_session()
        
        # Retry logic
        last_exception = None
        for attempt in range(self._retry_helper.max_attempts):
            try:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=timeout,
                    allow_redirects=self.allow_redirects,
                    **kwargs
                ) as response:
                    http_response = HTTPResponse(response, is_async=True)
                    # Pre-load content for error handling
                    await http_response.acontent()
                    self._handle_response_errors(http_response, raise_for_status)
                    return http_response
                    
            except Exception as e:
                last_exception = e
                
                # Convert aiohttp exceptions to our exceptions
                if isinstance(e, (aiohttp.ServerTimeoutError, asyncio.TimeoutError)):
                    e = TimeoutError(f"Request timed out: {e}")
                elif isinstance(e, aiohttp.ClientConnectionError):
                    e = NetworkError(f"Connection error: {e}")
                elif isinstance(e, aiohttp.ClientError):
                    e = RequestFailedError(f"Request failed: {e}")
                
                if not self._retry_helper.should_retry(attempt, e):
                    break
                
                if attempt < self._retry_helper.max_attempts - 1:
                    delay = self._retry_helper.get_delay(attempt)
                    await self._retry_helper.async_sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception
    
    async def afetch(self, url: str, **kwargs) -> HTTPResponse:
        """GET request (async fetch semantic method)"""
        return await self.arequest('GET', url, **kwargs)
    
    async def asend(self, url: str, data: Any = None, **kwargs) -> HTTPResponse:
        """POST request (async send semantic method)"""
        return await self.arequest('POST', url, data=data, **kwargs)
    
    async def aupdate(self, url: str, data: Any = None, **kwargs) -> HTTPResponse:
        """PUT request (async update semantic method)"""
        return await self.arequest('PUT', url, data=data, **kwargs)
    
    async def amodify(self, url: str, data: Any = None, **kwargs) -> HTTPResponse:
        """PATCH request (async modify semantic method)"""
        return await self.arequest('PATCH', url, data=data, **kwargs)
    
    async def aremove(self, url: str, **kwargs) -> HTTPResponse:
        """DELETE request (async remove semantic method)"""
        return await self.arequest('DELETE', url, **kwargs)
    
    async def ainfo(self, url: str, **kwargs) -> HTTPResponse:
        """HEAD request (async info semantic method)"""
        return await self.arequest('HEAD', url, **kwargs)
    
    async def aprobe(self, url: str, **kwargs) -> HTTPResponse:
        """OPTIONS request (async probe semantic method)"""
        return await self.arequest('OPTIONS', url, **kwargs)
    
    # File upload methods
    def upload_file(self, url: str, file_path: str, field_name: str = 'file',
                   additional_data: Optional[Dict] = None, **kwargs) -> HTTPResponse:
        """Upload file using multipart/form-data"""
        with open(file_path, 'rb') as f:
            files = {field_name: f}
            return self.send(url, data=additional_data, files=files, **kwargs)
    
    async def aupload_file(self, url: str, file_path: str, field_name: str = 'file',
                          additional_data: Optional[Dict] = None, **kwargs) -> HTTPResponse:
        """Upload file using multipart/form-data (async)"""
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field(field_name, f, filename=file_path.split('/')[-1])
            
            if additional_data:
                for key, value in additional_data.items():
                    data.add_field(key, str(value))
            
            return await self.asend(url, data=data, **kwargs)
    
    # Download methods
    def download_file(self, url: str, file_path: str, chunk_size: int = 8192,
                     progress_callback: Optional[callable] = None, **kwargs) -> int:
        """Download file with progress tracking"""
        response = self.fetch(url, stream=True, **kwargs)
        
        total_size = 0
        downloaded = 0
        
        # Get content length if available
        content_length = response.headers.get('Content-Length')
        if content_length:
            total_size = int(content_length)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        return downloaded
    
    async def adownload_file(self, url: str, file_path: str, chunk_size: int = 8192,
                            progress_callback: Optional[callable] = None, **kwargs) -> int:
        """Download file with progress tracking (async)"""
        response = await self.afetch(url, **kwargs)
        
        total_size = 0
        downloaded = 0
        
        # Get content length if available
        content_length = response.headers.get('Content-Length')
        if content_length:
            total_size = int(content_length)
        
        with open(file_path, 'wb') as f:
            async for chunk in response.aiter_content(chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        if asyncio.iscoroutinefunction(progress_callback):
                            await progress_callback(downloaded, total_size)
                        else:
                            progress_callback(downloaded, total_size)
        
        return downloaded
    
    # Session management
    def close(self):
        """Close the HTTP session"""
        if self._session:
            self._session.close()
            self._session = None
    
    async def aclose(self):
        """Close the HTTP session (async)"""
        if self._async_session:
            await self._async_session.close()
            self._async_session = None
    
    # Context managers
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()


class HTTPClientBuilder:
    """Builder pattern for HTTP client configuration"""
    
    def __init__(self):
        self._config = {}
    
    def base_url(self, url: str):
        """Set base URL"""
        self._config['base_url'] = url
        return self
    
    def timeout(self, timeout: Union[int, float, tuple]):
        """Set timeout"""
        self._config['timeout'] = timeout
        return self
    
    def headers(self, headers: Dict[str, str]):
        """Set default headers"""
        self._config['headers'] = headers
        return self
    
    def verify_ssl(self, verify: bool = True):
        """Set SSL verification"""
        self._config['verify_ssl'] = verify
        return self
    
    def proxy(self, proxy_url: str):
        """Set proxy"""
        self._config['proxy'] = proxy_url
        return self
    
    def max_redirects(self, max_redirects: int):
        """Set maximum redirects"""
        self._config['max_redirects'] = max_redirects
        return self
    
    def cookies(self, cookies: Dict[str, str]):
        """Set cookies"""
        self._config['cookies'] = cookies
        return self
    
    def auth_bearer(self, token: str):
        """Add Bearer token authentication"""
        headers = self._config.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        self._config['headers'] = headers
        return self
    
    def auth_basic(self, username: str, password: str):
        """Add Basic authentication"""
        import base64
        credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
        headers = self._config.get('headers', {})
        headers['Authorization'] = f'Basic {credentials}'
        self._config['headers'] = headers
        return self
    
    def build(self) -> HTTPClient:
        """Build HTTP client with configuration"""
        return HTTPClient(**self._config)


# Convenience functions
def create_http_client(**kwargs) -> HTTPClient:
    """Create HTTP client with configuration"""
    return HTTPClient(**kwargs)


def builder() -> HTTPClientBuilder:
    """Create HTTP client builder"""
    return HTTPClientBuilder()