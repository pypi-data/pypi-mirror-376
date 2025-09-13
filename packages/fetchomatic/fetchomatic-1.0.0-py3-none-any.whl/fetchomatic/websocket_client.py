"""
SmartFetch WebSocket Client
Handles WebSocket communication with sync and async support
"""

import json
import asyncio
import threading
import time
from typing import Any, Dict, Optional, Union, Callable, List
from urllib.parse import urlparse
from queue import Queue, Empty
import websockets
from websockets.exceptions import WebSocketException, ConnectionClosed
from .exceptions import (
    NetworkError, TimeoutError, ValidationError, ConnectionError,
    RequestFailedError
)
from .utils import validate_timeout, format_headers


class WebSocketMessage:
    """Wrapper for WebSocket messages"""
    
    def __init__(self, data: Union[str, bytes], message_type: str = 'text',
                 timestamp: float = None):
        self._data = data
        self._message_type = message_type
        self._timestamp = timestamp or time.time()
        self._json = None
    
    @property
    def data(self) -> Union[str, bytes]:
        """Get raw message data"""
        return self._data
    
    @property
    def message_type(self) -> str:
        """Get message type (text/binary)"""
        return self._message_type
    
    @property
    def timestamp(self) -> float:
        """Get message timestamp"""
        return self._timestamp
    
    @property
    def is_text(self) -> bool:
        """Check if message is text"""
        return self._message_type == 'text'
    
    @property
    def is_binary(self) -> bool:
        """Check if message is binary"""
        return self._message_type == 'binary'
    
    @property
    def size(self) -> int:
        """Get message size in bytes"""
        if isinstance(self._data, str):
            return len(self._data.encode('utf-8'))
        return len(self._data)
    
    def text(self) -> str:
        """Get message as text"""
        if isinstance(self._data, bytes):
            return self._data.decode('utf-8')
        return self._data
    
    def bytes(self) -> bytes:
        """Get message as bytes"""
        if isinstance(self._data, str):
            return self._data.encode('utf-8')
        return self._data
    
    def json(self) -> Any:
        """Parse message as JSON"""
        if self._json is None:
            try:
                text = self.text()
                self._json = json.loads(text)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ValidationError(f"Failed to parse JSON: {e}")
        return self._json
    
    def __str__(self) -> str:
        preview = self.text()[:50]
        if len(self.text()) > 50:
            preview += "..."
        return f"WebSocketMessage(type={self._message_type}, size={self.size}, data='{preview}')"


class WebSocketClient:
    """WebSocket client with sync and async support"""
    
    def __init__(self, timeout: Union[int, float] = 30.0,
                 ping_interval: float = 20.0, ping_timeout: float = 10.0,
                 close_timeout: float = 10.0, max_size: Optional[int] = None,
                 headers: Optional[Dict[str, str]] = None,
                 subprotocols: Optional[List[str]] = None):
        self.timeout = validate_timeout(timeout)
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.close_timeout = close_timeout
        self.max_size = max_size
        self.headers = format_headers(headers) if headers else {}
        self.subprotocols = subprotocols
        
        # Connection state
        self._websocket = None
        self._connected = False
        self._url = None
        
        # Message handling
        self._message_queue = Queue()
        self._message_handlers = []
        self._error_handlers = []
        
        # Threading for sync operations
        self._receiver_thread = None
        self._running = False
    
    def _validate_websocket_url(self, url: str) -> str:
        """Validate and normalize WebSocket URL"""
        if not url.startswith(('ws://', 'wss://')):
            # Try to convert from HTTP
            if url.startswith('http://'):
                url = url.replace('http://', 'ws://', 1)
            elif url.startswith('https://'):
                url = url.replace('https://', 'wss://', 1)
            else:
                # Default to secure WebSocket
                url = f'wss://{url}'
        
        parsed = urlparse(url)
        if not parsed.hostname:
            raise ValidationError("WebSocket URL must contain hostname")
        
        return url
    
    def _prepare_message(self, data: Any) -> Union[str, bytes]:
        """Prepare message data for sending"""
        if data is None:
            return ""
        
        if isinstance(data, (str, bytes)):
            return data
        elif isinstance(data, dict):
            return json.dumps(data)
        else:
            return str(data)
    
    # Synchronous methods (using threading with asyncio)
    def _run_async_in_thread(self, coro):
        """Run async coroutine in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def connect(self, url: str) -> bool:
        """Connect to WebSocket server (sync)"""
        self._url = self._validate_websocket_url(url)
        
        def _connect():
            return self._run_async_in_thread(self._async_connect())
        
        return _connect()
    
    def disconnect(self):
        """Disconnect from WebSocket server (sync)"""
        def _disconnect():
            return self._run_async_in_thread(self._async_disconnect())
        
        _disconnect()
    
    def send_message(self, data: Any) -> bool:
        """Send message to WebSocket server (sync)"""
        if not self._connected:
            raise ConnectionError("Not connected to WebSocket server")
        
        def _send():
            return self._run_async_in_thread(self._async_send_message(data))
        
        return _send()
    
    def receive_message(self, timeout: Optional[float] = None) -> Optional[WebSocketMessage]:
        """Receive message from WebSocket server (sync)"""
        timeout = timeout or self.timeout
        
        try:
            # Try to get message from queue
            data = self._message_queue.get(timeout=timeout)
            if isinstance(data, Exception):
                raise data
            return data
        except Empty:
            raise TimeoutError(f"No message received within {timeout} seconds")
    
    def send_and_receive(self, data: Any, timeout: Optional[float] = None) -> WebSocketMessage:
        """Send message and wait for response (sync)"""
        self.send_message(data)
        return self.receive_message(timeout)
    
    # Asynchronous methods
    async def aconnect(self, url: str) -> bool:
        """Connect to WebSocket server (async)"""
        self._url = self._validate_websocket_url(url)
        return await self._async_connect()
    
    async def _async_connect(self) -> bool:
        """Internal async connect method"""
        try:
            connect_kwargs = {
                'ping_interval': self.ping_interval,
                'ping_timeout': self.ping_timeout,
                'close_timeout': self.close_timeout
            }
            
            if self.max_size:
                connect_kwargs['max_size'] = self.max_size
            
            if self.headers:
                connect_kwargs['extra_headers'] = self.headers
            
            if self.subprotocols:
                connect_kwargs['subprotocols'] = self.subprotocols
            
            self._websocket = await websockets.connect(self._url, **connect_kwargs)
            self._connected = True
            
            # Start message receiver for sync operations
            if not self._receiver_thread or not self._receiver_thread.is_alive():
                self._running = True
                self._receiver_thread = threading.Thread(target=self._message_receiver_loop)
                self._receiver_thread.daemon = True
                self._receiver_thread.start()
            
            return True
        
        except Exception as e:
            self._connected = False
            if isinstance(e, WebSocketException):
                raise ConnectionError(f"WebSocket connection failed: {e}")
            raise NetworkError(f"Connection error: {e}")
    
    async def adisconnect(self):
        """Disconnect from WebSocket server (async)"""
        await self._async_disconnect()
    
    async def _async_disconnect(self):
        """Internal async disconnect method"""
        self._running = False
        self._connected = False
        
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass  # Ignore errors during close
            finally:
                self._websocket = None
        
        if self._receiver_thread and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=1.0)
    
    async def asend_message(self, data: Any) -> bool:
        """Send message to WebSocket server (async)"""
        return await self._async_send_message(data)
    
    async def _async_send_message(self, data: Any) -> bool:
        """Internal async send message method"""
        if not self._connected or not self._websocket:
            raise ConnectionError("Not connected to WebSocket server")
        
        try:
            message = self._prepare_message(data)
            await self._websocket.send(message)
            return True
        
        except ConnectionClosed as e:
            self._connected = False
            raise ConnectionError(f"WebSocket connection closed: {e}")
        except Exception as e:
            raise NetworkError(f"Failed to send message: {e}")
    
    async def areceive_message(self, timeout: Optional[float] = None) -> WebSocketMessage:
        """Receive message from WebSocket server (async)"""
        if not self._connected or not self._websocket:
            raise ConnectionError("Not connected to WebSocket server")
        
        timeout = timeout or self.timeout
        
        try:
            message = await asyncio.wait_for(
                self._websocket.recv(), 
                timeout=timeout
            )
            
            message_type = 'binary' if isinstance(message, bytes) else 'text'
            return WebSocketMessage(message, message_type)
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"No message received within {timeout} seconds")
        except ConnectionClosed as e:
            self._connected = False
            raise ConnectionError(f"WebSocket connection closed: {e}")
        except Exception as e:
            raise NetworkError(f"Failed to receive message: {e}")
    
    async def asend_and_receive(self, data: Any, timeout: Optional[float] = None) -> WebSocketMessage:
        """Send message and wait for response (async)"""
        await self.asend_message(data)
        return await self.areceive_message(timeout)
    
    # Message receiver loop for sync operations
    def _message_receiver_loop(self):
        """Background thread to receive messages for sync operations"""
        async def _receiver():
            while self._running and self._connected and self._websocket:
                try:
                    message = await self._websocket.recv()
                    message_type = 'binary' if isinstance(message, bytes) else 'text'
                    ws_message = WebSocketMessage(message, message_type)
                    
                    # Put message in queue for sync receive_message calls
                    self._message_queue.put(ws_message)
                    
                    # Call registered handlers
                    for handler in self._message_handlers:
                        try:
                            handler(ws_message)
                        except Exception as e:
                            self._handle_error(e)
                
                except ConnectionClosed:
                    self._connected = False
                    break
                except Exception as e:
                    self._message_queue.put(e)
                    self._handle_error(e)
                    break
        
        # Run the async receiver in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_receiver())
        finally:
            loop.close()
    
    def _handle_error(self, error: Exception):
        """Handle errors and call error handlers"""
        for handler in self._error_handlers:
            try:
                handler(error)
            except Exception:
                pass  # Don't let error handlers raise exceptions
    
    # Event handlers
    def add_message_handler(self, handler: Callable[[WebSocketMessage], None]):
        """Add message handler callback"""
        self._message_handlers.append(handler)
    
    def remove_message_handler(self, handler: Callable[[WebSocketMessage], None]):
        """Remove message handler callback"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
    
    def add_error_handler(self, handler: Callable[[Exception], None]):
        """Add error handler callback"""
        self._error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[[Exception], None]):
        """Remove error handler callback"""
        if handler in self._error_handlers:
            self._error_handlers.remove(handler)
    
    # Semantic methods
    def send(self, url: str, data: Any = None) -> WebSocketMessage:
        """Send data to WebSocket (semantic method)"""
        if not self._connected:
            self.connect(url)
        return self.send_and_receive(data)
    
    def fetch(self, url: str, data: Any = None) -> WebSocketMessage:
        """Alias for send (WebSocket is bidirectional)"""
        return self.send(url, data)
    
    async def asend(self, url: str, data: Any = None) -> WebSocketMessage:
        """Send data to WebSocket (async semantic method)"""
        if not self._connected:
            await self.aconnect(url)
        return await self.asend_and_receive(data)
    
    async def afetch(self, url: str, data: Any = None) -> WebSocketMessage:
        """Alias for asend (WebSocket is bidirectional) (async)"""
        return await self.asend(url, data)
    
    # Utility methods
    def ping(self, data: bytes = b'') -> bool:
        """Send ping frame (sync)"""
        if not self._connected:
            raise ConnectionError("Not connected to WebSocket server")
        
        def _ping():
            return self._run_async_in_thread(self._websocket.ping(data))
        
        try:
            _ping()
            return True
        except Exception:
            return False
    
    async def aping(self, data: bytes = b'') -> bool:
        """Send ping frame (async)"""
        if not self._connected or not self._websocket:
            raise ConnectionError("Not connected to WebSocket server")
        
        try:
            await self._websocket.ping(data)
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._connected and self._websocket is not None
    
    @property
    def url(self) -> Optional[str]:
        """Get connected URL"""
        return self._url
    
    # Context managers
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connected:
            self.disconnect()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._connected:
            await self.adisconnect()


# Convenience functions
def create_websocket_client(**kwargs) -> WebSocketClient:
    """Create WebSocket client with configuration"""
    return WebSocketClient(**kwargs)


def send_websocket(url: str, data: Any = None, **kwargs) -> WebSocketMessage:
    """Send WebSocket message (convenience function)"""
    client = WebSocketClient(**kwargs)
    return client.send(url, data)


async def asend_websocket(url: str, data: Any = None, **kwargs) -> WebSocketMessage:
    """Send WebSocket message (async convenience function)"""
    client = WebSocketClient(**kwargs)
    return await client.asend(url, data)


class WebSocketServer:
    """Simple WebSocket server for testing"""
    
    def __init__(self, host: str = 'localhost', port: int = 0):
        self.host = host
        self.port = port
        self._server = None
        self._clients = set()
    
    async def handle_client(self, websocket, path):
        """Handle client connection"""
        self._clients.add(websocket)
        try:
            async for message in websocket:
                # Echo message back to sender
                await websocket.send(f"Echo: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
    
    async def start(self, handler=None):
        """Start WebSocket server"""
        handler = handler or self.handle_client
        
        self._server = await websockets.serve(
            handler, 
            self.host, 
            self.port
        )
        
        # Update port if it was 0 (auto-assigned)
        if self.port == 0:
            self.port = self._server.sockets[0].getsockname()[1]
        
        print(f"WebSocket server started on ws://{self.host}:{self.port}")
        return self._server
    
    async def stop(self):
        """Stop WebSocket server"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        if self._clients:
            await asyncio.gather(
                *[client.send(message) for client in self._clients],
                return_exceptions=True
            )


def create_websocket_server(host: str = 'localhost', port: int = 0) -> WebSocketServer:
    """Create WebSocket server"""
    return WebSocketServer(host, port)