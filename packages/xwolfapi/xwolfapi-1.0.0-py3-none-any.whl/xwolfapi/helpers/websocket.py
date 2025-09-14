"""
WebSocket client for xwolfapi
"""

import asyncio
import json
import logging
import websocket
import threading
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from ..exceptions import ConnectionError, WOLFAPIError


class WebSocketClient:
    """WebSocket client for WOLF protocol"""
    
    def __init__(self, wolf_client):
        """Initialize WebSocket client"""
        self.wolf_client = wolf_client
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.url = "wss://v3.palapi.com"
        self.logger = logging.getLogger('xwolfapi.websocket')
        self._message_queue = None  # Will be initialized when loop is available
        self._response_handlers: Dict[str, asyncio.Future] = {}
        self._message_id_counter = 0
        self._running = False
        self._loop = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        
    async def connect(self) -> bool:
        """Connect to WOLF WebSocket"""
        try:
            # Store the current event loop
            self._loop = asyncio.get_event_loop()
            
            # Initialize message queue with current loop
            self._message_queue = asyncio.Queue()
            
            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in separate thread
            self._ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self._ws_thread.start()
            
            # Wait for connection
            await asyncio.sleep(1)
            return self.connected
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"WebSocket connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self._running = False
        if self.ws:
            self.ws.close()
        self.connected = False
        
        # Clean up executor
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
    
    def _on_open(self, ws):
        """Handle WebSocket open"""
        self.connected = True
        self._running = True
        self.logger.info("WebSocket connected")
        
        # Start message processing in the main event loop
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._process_messages(), self._loop)
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            # Add message to queue for async processing using the main event loop
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._queue_message(message), self._loop)
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _queue_message(self, message: str):
        """Add message to processing queue"""
        if self._message_queue:
            await self._message_queue.put(message)
    
    async def _process_messages(self):
        """Process messages from queue"""
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: str):
        """Handle parsed message"""
        try:
            data = json.loads(message)
            
            # Check if this is a response to a command we sent
            if 'id' in data and data['id'] in self._response_handlers:
                future = self._response_handlers.pop(data['id'])
                if not future.done():
                    future.set_result(data)
                return
            
            # Handle different message types
            command = data.get('command', '')
            body = data.get('body', {})
            
            if command == 'message send':
                self.wolf_client._handle_message(body)
            elif command == 'welcome':
                self.wolf_client._handle_welcome(body)
            elif command == 'subscriber update':
                self.wolf_client._handle_subscriber_update(body)
            else:
                self.logger.debug(f"Unhandled command: {command}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        self.logger.error(f"WebSocket error: {error}")
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False
        self._running = False
        
        # Schedule the disconnect event in the main loop
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self.wolf_client.emit, 'disconnect')
        else:
            self.wolf_client.emit('disconnect')
    
    async def send_command(self, command: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command and wait for response"""
        if not self.connected or not self.ws:
            raise ConnectionError("WebSocket not connected")
        
        message_id = str(self._message_id_counter)
        self._message_id_counter += 1
        
        message = {
            'id': message_id,
            'command': command,
            'body': body
        }
        
        # Create future for response
        future = asyncio.Future()
        self._response_handlers[message_id] = future
        
        try:
            # Send message
            self.ws.send(json.dumps(message))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
            
        except asyncio.TimeoutError:
            # Clean up handler
            self._response_handlers.pop(message_id, None)
            raise WOLFAPIError(f"Command {command} timed out")
        except Exception as e:
            # Clean up handler
            self._response_handlers.pop(message_id, None)
            raise WOLFAPIError(f"Failed to send command {command}: {e}")
    
    def send_message(self, message: Dict[str, Any]):
        """Send message without waiting for response"""
        if not self.connected or not self.ws:
            return False
        
        try:
            self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def run_forever(self):
        """Run WebSocket forever"""
        while self._running:
            await asyncio.sleep(1)