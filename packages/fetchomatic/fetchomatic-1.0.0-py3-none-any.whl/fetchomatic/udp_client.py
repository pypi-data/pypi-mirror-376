"""
SmartFetch UDP Client
Handles UDP communication with sync and async support with middleware, retries, and logging
"""

import socket
import asyncio
import time
import json
from typing import Any, Dict, Optional, Union, Tuple, List, Callable
from urllib.parse import urlparse
import logging

# ------------------------
# Exceptions
# ------------------------
class SmartFetchError(Exception):
    pass

class NetworkError(SmartFetchError):
    pass

class TimeoutError(SmartFetchError):
    pass

class ValidationError(SmartFetchError):
    pass

class RequestFailedError(SmartFetchError):
    pass

# ------------------------
# Utils
# ------------------------
class RetryHelper:
    def __init__(self, max_attempts: int = 3, base_delay: float = 0.5):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        return attempt < self.max_attempts - 1
    
    def get_delay(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)
    
    def sync_sleep(self, delay: float):
        time.sleep(delay)
    
    async def async_sleep(self, delay: float):
        await asyncio.sleep(delay)

def validate_timeout(timeout: Union[int, float]) -> float:
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValidationError("Timeout must be a positive number")
    return float(timeout)

# ------------------------
# UDP Response Wrapper
# ------------------------
class UDPResponse:
    """Wrapper for UDP responses"""
    
    def __init__(self, data: bytes, address: Tuple[str, int], 
                 response_time: float = 0.0):
        self._data = data
        self._address = address
        self._response_time = response_time
        self._text = None
        self._json = None
    
    @property
    def data(self) -> bytes:
        return self._data
    
    @property
    def address(self) -> Tuple[str, int]:
        return self._address
    
    @property
    def host(self) -> str:
        return self._address[0]
    
    @property
    def port(self) -> int:
        return self._address[1]
    
    @property
    def size(self) -> int:
        return len(self._data)
    
    @property
    def response_time(self) -> float:
        return self._response_time
    
    def text(self, encoding: str = 'utf-8') -> str:
        if self._text is None:
            try:
                self._text = self._data.decode(encoding)
            except UnicodeDecodeError as e:
                raise ValidationError(f"Failed to decode response as {encoding}: {e}")
        return self._text
    
    def json(self) -> Any:
        if self._json is None:
            try:
                text = self.text()
                self._json = json.loads(text)
            except (json.JSONDecodeError, ValidationError) as e:
                raise ValidationError(f"Failed to parse JSON: {e}")
        return self._json
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __str__(self) -> str:
        return f"UDPResponse(size={self.size}, from={self.host}:{self.port})"

# ------------------------
# UDP Client
# ------------------------
class UDPClient:
    """UDP client with sync and async support, middleware, and logging"""
    
    def __init__(self, timeout: Union[int, float] = 10.0, 
                 buffer_size: int = 8192, bind_port: Optional[int] = None,
                 enable_broadcast: bool = False, retries: int = 3):
        self.timeout = validate_timeout(timeout)
        self.buffer_size = buffer_size
        self.bind_port = bind_port
        self.enable_broadcast = enable_broadcast
        self.retries = retries
        self._retry_helper = RetryHelper(max_attempts=retries)
        
        # Socket instances
        self._socket = None
        self._async_transport = None
        self._async_protocol = None
        
        # Middleware lists
        self.request_middlewares: List[Callable[[Dict], None]] = []
        self.response_middlewares: List[Callable[[UDPResponse], None]] = []
        
        # Logging
        self.logger = logging.getLogger("SmartFetch.UDP")
        self.logger.setLevel(logging.INFO)
    
    # ------------------------
    # Middleware hooks
    # ------------------------
    def add_request_middleware(self, func: Callable[[Dict], None]):
        self.request_middlewares.append(func)
    
    def add_response_middleware(self, func: Callable[[UDPResponse], None]):
        self.response_middlewares.append(func)
    
    def _apply_request_middlewares(self, request_data: Dict):
        for mw in self.request_middlewares:
            mw(request_data)
    
    def _apply_response_middlewares(self, response: UDPResponse):
        for mw in self.response_middlewares:
            mw(response)
    
    # ------------------------
    # Socket helpers
    # ------------------------
    def _parse_udp_url(self, url: str) -> Tuple[str, int]:
        if not url.startswith('udp://'):
            raise ValidationError("UDP URL must start with 'udp://'")
        parsed = urlparse(url)
        if not parsed.hostname:
            raise ValidationError("UDP URL must contain hostname")
        if not parsed.port:
            raise ValidationError("UDP URL must contain port")
        return parsed.hostname, parsed.port
    
    def _create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(self.timeout)
            if self.enable_broadcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            if self.bind_port:
                sock.bind(('', self.bind_port))
            return sock
        except Exception as e:
            sock.close()
            raise NetworkError(f"Failed to create UDP socket: {e}")
    
    def _prepare_data(self, data: Any) -> bytes:
        if data is None:
            return b''
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode('utf-8')
        elif isinstance(data, dict):
            return json.dumps(data).encode('utf-8')
        else:
            return str(data).encode('utf-8')
    
    # ------------------------
    # Synchronous methods
    # ------------------------
    def send_and_receive(self, url: str, data: Any = None) -> UDPResponse:
        host, port = self._parse_udp_url(url)
        data = self._prepare_data(data)
        self._apply_request_middlewares({"url": url, "data": data})
        last_exception = None
        for attempt in range(self._retry_helper.max_attempts):
            sock = None
            try:
                sock = self._create_socket()
                start_time = time.time()
                sent_bytes = sock.sendto(data, (host, port))
                if sent_bytes != len(data):
                    raise NetworkError(f"Only sent {sent_bytes}/{len(data)} bytes")
                response_data, addr = sock.recvfrom(self.buffer_size)
                response_time = time.time() - start_time
                response = UDPResponse(response_data, addr, response_time)
                self._apply_response_middlewares(response)
                return response
            except Exception as e:
                last_exception = e
                if not self._retry_helper.should_retry(attempt, e):
                    break
                if attempt < self._retry_helper.max_attempts - 1:
                    delay = self._retry_helper.get_delay(attempt)
                    self._retry_helper.sync_sleep(delay)
            finally:
                if sock:
                    sock.close()
        raise last_exception
    
    def send_only(self, url: str, data: Any = None) -> int:
        host, port = self._parse_udp_url(url)
        data = self._prepare_data(data)
        self._apply_request_middlewares({"url": url, "data": data})
        sock = None
        try:
            sock = self._create_socket()
            sent_bytes = sock.sendto(data, (host, port))
            return sent_bytes
        finally:
            if sock:
                sock.close()
    
    # Semantic methods
    def send(self, url: str, data: Any = None) -> UDPResponse:
        return self.send_and_receive(url, data)
    
    def fetch(self, url: str, data: Any = None) -> UDPResponse:
        return self.send_and_receive(url, data)
    
    def probe(self, url: str, data: Any = b'ping') -> UDPResponse:
        return self.send_and_receive(url, data)
    
    # ------------------------
    # Asynchronous methods
    # ------------------------
    class _AsyncUDPProtocol(asyncio.DatagramProtocol):
        def __init__(self, future: asyncio.Future):
            self.future = future
            self.start_time = time.time()
        def datagram_received(self, data: bytes, addr: Tuple[str, int]):
            if not self.future.done():
                response_time = time.time() - self.start_time
                self.future.set_result(UDPResponse(data, addr, response_time))
        def error_received(self, exc: Exception):
            if not self.future.done():
                self.future.set_exception(exc)
        def connection_lost(self, exc: Optional[Exception]):
            if not self.future.done() and exc:
                self.future.set_exception(exc)
    
    async def asend_and_receive(self, url: str, data: Any = None) -> UDPResponse:
        host, port = self._parse_udp_url(url)
        data = self._prepare_data(data)
        self._apply_request_middlewares({"url": url, "data": data})
        last_exception = None
        for attempt in range(self._retry_helper.max_attempts):
            transport = None
            try:
                loop = asyncio.get_event_loop()
                future = loop.create_future()
                local_addr = ('', self.bind_port) if self.bind_port else None
                transport, protocol = await loop.create_datagram_endpoint(
                    lambda: self._AsyncUDPProtocol(future),
                    local_addr=local_addr
                )
                transport.sendto(data, (host, port))
                response = await asyncio.wait_for(future, timeout=self.timeout)
                self._apply_response_middlewares(response)
                return response
            except Exception as e:
                last_exception = e
                if not self._retry_helper.should_retry(attempt, e):
                    break
                if attempt < self._retry_helper.max_attempts - 1:
                    delay = self._retry_helper.get_delay(attempt)
                    await self._retry_helper.async_sleep(delay)
            finally:
                if transport:
                    transport.close()
        raise last_exception
    
    async def asend(self, url: str, data: Any = None) -> UDPResponse:
        return await self.asend_and_receive(url, data)
    
    async def afetch(self, url: str, data: Any = None) -> UDPResponse:
        return await self.asend_and_receive(url, data)
    
    async def asend_only(self, url: str, data: Any = None) -> int:
        host, port = self._parse_udp_url(url)
        data = self._prepare_data(data)
        self._apply_request_middlewares({"url": url, "data": data})
        loop = asyncio.get_event_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(host, port)
        )
        transport.sendto(data)
        transport.close()
        return len(data)
