"""
Main WOLF client for xwolfapi
"""

import asyncio
import json
import logging
import os
import yaml
from typing import Dict, Any, Optional, Callable, Union
from ..constants import OnlineState, LoginType, Command
from ..models.message import Message
from ..models.subscriber import Subscriber
from ..models.channel import Channel
from ..helpers.websocket import WebSocketClient
from ..helpers.messaging import MessagingHelper
from ..helpers.channel_helper import ChannelHelper
from ..helpers.subscriber_helper import SubscriberHelper
from ..helpers.command_handler import CommandHandler
from ..helpers.phrase_helper import PhraseHelper
from ..helpers.utility import Utility
from ..exceptions import WOLFAPIError


class WOLF:
    """Main WOLF client class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize WOLF client
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.current_subscriber: Optional[Subscriber] = None
        self.connected = False
        self._event_handlers: Dict[str, list] = {}
        
        # Initialize components
        self.websocket = WebSocketClient(self)
        self.messaging = MessagingHelper(self)
        self.channel = ChannelHelper(self)
        self.subscriber = SubscriberHelper(self)
        self.command_handler = CommandHandler(self)
        self.phrase = PhraseHelper(self)
        self.utility = Utility(self)
        
        # Setup logging
        self._setup_logging()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or defaults"""
        default_config = {
            'keyword': 'bot',
            'framework': {
                'developer': '',
                'language': 'en',
                'login': {
                    'email': '',
                    'password': '',
                    'onlineState': OnlineState.ONLINE,
                    'type': LoginType.EMAIL,
                    'apiKey': None
                },
                'command': {
                    'ignore': {
                        'official': True,
                        'unofficial': True,
                        'self': True
                    }
                },
                'message': {
                    'ignore': {
                        'self': True
                    }
                },
                'subscriptions': {
                    'messages': {
                        'channel': {
                            'enabled': True,
                            'tipping': True
                        },
                        'private': {
                            'enabled': True,
                            'tipping': False
                        }
                    }
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                
                # Merge with defaults
                default_config.update(file_config)
            except Exception as e:
                logging.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('xwolfapi')
    
    def on(self, event: str, handler: Callable):
        """Register an event handler"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def emit(self, event: str, *args, **kwargs):
        """Emit an event to registered handlers"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(*args, **kwargs))
                    else:
                        handler(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event}: {e}")
    
    async def login(self, email: Optional[str] = None, password: Optional[str] = None, 
                   api_key: Optional[str] = None, online_state: int = OnlineState.ONLINE,
                   login_type: int = LoginType.EMAIL) -> bool:
        """
        Login to WOLF
        
        Args:
            email: Email address (optional, uses config if not provided)
            password: Password (optional, uses config if not provided)
            api_key: API key for API login (optional)
            online_state: Online state to set
            login_type: Login type (email or API key)
            
        Returns:
            bool: True if login successful
        """
        if self.connected and self.current_subscriber:
            return True
        
        # Use provided credentials or fall back to config
        login_config = self.config['framework']['login']
        email = email or login_config.get('email')
        password = password or login_config.get('password')
        api_key = api_key or login_config.get('apiKey')
        online_state = online_state or login_config.get('onlineState', OnlineState.ONLINE)
        login_type = login_type or login_config.get('type', LoginType.EMAIL)
        
        if not email and login_type == LoginType.EMAIL:
            raise WOLFAPIError("Email is required for email login")
        
        if not api_key and login_type == LoginType.API_KEY:
            raise WOLFAPIError("API key is required for API key login")
        
        # Connect websocket and login
        success = await self.websocket.connect()
        if success:
            success = await self._perform_login(email, password, api_key, online_state, login_type)
        
        return success
    
    async def _perform_login(self, email: str, password: str, api_key: Optional[str],
                           online_state: int, login_type: int) -> bool:
        """Perform the actual login process"""
        login_data = {
            'onlineState': online_state,
            'type': login_type
        }
        
        if login_type == LoginType.EMAIL:
            login_data.update({
                'email': email,
                'password': password
            })
        else:
            login_data['apiKey'] = api_key
        
        response = await self.websocket.send_command(Command.SECURITY_LOGIN, login_data)
        
        if response and response.get('success'):
            self.connected = True
            # Store current subscriber info
            body = response.get('body', {})
            if 'subscriber' in body:
                self.current_subscriber = Subscriber(body['subscriber'])
            
            self.emit('ready')
            self.logger.info("Successfully logged in to WOLF")
            return True
        else:
            error_msg = response.get('body', {}).get('message', 'Login failed') if response else 'Connection failed'
            self.logger.error(f"Login failed: {error_msg}")
            return False
    
    async def logout(self, disconnect: bool = True) -> bool:
        """
        Logout from WOLF
        
        Args:
            disconnect: Whether to disconnect websocket
            
        Returns:
            bool: True if logout successful
        """
        if self.connected:
            await self.websocket.send_command(Command.SECURITY_LOGOUT, {})
        
        if disconnect:
            await self.websocket.disconnect()
        
        self.connected = False
        self.current_subscriber = None
        self.emit('disconnect')
        return True
    
    async def set_online_state(self, online_state: int) -> bool:
        """
        Set online state
        
        Args:
            online_state: New online state
            
        Returns:
            bool: True if successful
        """
        if not self.connected:
            return False
        
        response = await self.websocket.send_command(
            Command.SUBSCRIBER_SETTINGS_UPDATE,
            {'state': {'state': online_state}}
        )
        
        return response and response.get('success', False)
    
    async def update_profile(self, **kwargs) -> bool:
        """
        Update user profile
        
        Args:
            **kwargs: Profile fields to update
            
        Returns:
            bool: True if successful
        """
        if not self.connected or not self.current_subscriber:
            return False
        
        # Build update data
        update_data = {
            'nickname': kwargs.get('nickname', self.current_subscriber.nickname),
            'status': kwargs.get('status', self.current_subscriber.status),
            'extended': {}
        }
        
        # Handle extended fields
        extended_fields = ['about', 'gender', 'language', 'lookingFor', 'name', 'relationship', 'urls']
        for field in extended_fields:
            if field in kwargs:
                update_data['extended'][field] = kwargs[field]
        
        response = await self.websocket.send_command(Command.SUBSCRIBER_PROFILE_UPDATE, update_data)
        return response and response.get('success', False)
    
    def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming message"""
        message = Message(data)
        message.set_client(self)
        
        # Check if it's a command
        if message.body.startswith('!'):
            message.is_command = True
            asyncio.create_task(self.command_handler.handle_command(message))
        
        # Emit appropriate event
        if message.is_channel_message:
            self.emit('channelMessage', message)
        else:
            self.emit('privateMessage', message)
    
    def _handle_welcome(self, data: Dict[str, Any]):
        """Handle welcome message"""
        self.emit('welcome', data)
    
    def _handle_subscriber_update(self, data: Dict[str, Any]):
        """Handle subscriber update"""
        if self.current_subscriber and data.get('id') == self.current_subscriber.id:
            # Update current subscriber
            self.current_subscriber = Subscriber(data)
        
        self.emit('subscriberUpdate', Subscriber(data))
    
    async def run_forever(self):
        """Run the client forever (blocking)"""
        if not self.connected:
            await self.login()
        
        try:
            await self.websocket.run_forever()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            await self.logout()
    
    def __str__(self) -> str:
        status = "connected" if self.connected else "disconnected"
        user = f" as {self.current_subscriber.nickname}" if self.current_subscriber else ""
        return f"WOLF(status={status}{user})"
    
    def __repr__(self) -> str:
        return self.__str__()