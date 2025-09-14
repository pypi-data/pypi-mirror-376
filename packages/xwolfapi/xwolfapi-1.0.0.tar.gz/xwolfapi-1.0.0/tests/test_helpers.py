"""
Test helper modules for xwolfapi
"""

import pytest
from unittest.mock import Mock, AsyncMock
from xwolfapi.helpers.messaging import MessagingHelper
from xwolfapi.helpers.channel_helper import ChannelHelper
from xwolfapi.helpers.subscriber_helper import SubscriberHelper
from xwolfapi.helpers.command_handler import CommandHandler
from xwolfapi.helpers.phrase_helper import PhraseHelper
from xwolfapi.helpers.utility import Utility, StringUtility
from xwolfapi.models.command import Command
from xwolfapi.models.message import Message
from xwolfapi.exceptions import WOLFAPIError


class TestMessagingHelper:
    @pytest.mark.asyncio
    async def test_send_channel_message(self):
        """Test sending channel message"""
        mock_client = Mock()
        mock_client.connected = True
        mock_client.websocket = Mock()
        mock_client.websocket.send_command = AsyncMock(return_value={
            'success': True,
            'body': {'id': 'msg123', 'body': 'Hello'}
        })
        
        helper = MessagingHelper(mock_client)
        result = await helper.send_channel_message(12345, "Hello channel!")
        
        assert result is not None
        assert isinstance(result, Message)
        mock_client.websocket.send_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_private_message(self):
        """Test sending private message"""
        mock_client = Mock()
        mock_client.connected = True
        mock_client.websocket = Mock()
        mock_client.websocket.send_command = AsyncMock(return_value={
            'success': True,
            'body': {'id': 'msg123', 'body': 'Hello'}
        })
        
        helper = MessagingHelper(mock_client)
        result = await helper.send_private_message(67890, "Hello user!")
        
        assert result is not None
        assert isinstance(result, Message)


class TestChannelHelper:
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting channel by ID"""
        mock_client = Mock()
        mock_client.connected = True
        mock_client.websocket = Mock()
        mock_client.websocket.send_command = AsyncMock(return_value={
            'success': True,
            'body': {'id': 12345, 'name': 'Test Channel'}
        })
        
        helper = ChannelHelper(mock_client)
        result = await helper.get_by_id(12345)
        
        assert result is not None
        assert result.id == 12345
        assert result.name == 'Test Channel'
        
        # Test cache
        result2 = await helper.get_by_id(12345)
        assert result2 is result  # Should be cached
    
    @pytest.mark.asyncio
    async def test_join_by_id(self):
        """Test joining channel by ID"""
        mock_client = Mock()
        mock_client.connected = True
        mock_client.websocket = Mock()
        mock_client.websocket.send_command = AsyncMock(return_value={'success': True})
        
        helper = ChannelHelper(mock_client)
        result = await helper.join_by_id(12345)
        
        assert result is True
        mock_client.websocket.send_command.assert_called_once()


class TestSubscriberHelper:
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting subscriber by ID"""
        mock_client = Mock()
        mock_client.connected = True
        mock_client.websocket = Mock()
        mock_client.websocket.send_command = AsyncMock(return_value={
            'success': True,
            'body': {'id': 12345, 'nickname': 'TestUser'}
        })
        
        helper = SubscriberHelper(mock_client)
        result = await helper.get_by_id(12345)
        
        assert result is not None
        assert result.id == 12345
        assert result.nickname == 'TestUser'


class TestCommandHandler:
    @pytest.mark.asyncio
    async def test_command_registration(self):
        """Test command registration"""
        mock_client = Mock()
        mock_client.config = {
            'framework': {
                'command': {
                    'ignore': {'self': True}
                }
            }
        }
        mock_client.current_subscriber = None
        
        handler = CommandHandler(mock_client)
        
        def test_handler(context):
            return "Test response"
        
        command = Command("!test", {"both": test_handler})
        handler.register([command])
        
        assert len(handler.commands) == 1
        assert handler.commands[0].pattern == "!test"
    
    @pytest.mark.asyncio
    async def test_handle_command(self):
        """Test command handling"""
        mock_client = Mock()
        mock_client.config = {
            'framework': {
                'command': {
                    'ignore': {'self': False}
                }
            }
        }
        mock_client.current_subscriber = None
        
        handler = CommandHandler(mock_client)
        
        # Register a test command
        executed = []
        def test_handler(context):
            executed.append(context.args)
        
        command = Command("!test", {"both": test_handler})
        handler.register([command])
        
        # Create mock message
        mock_message = Mock()
        mock_message.body = "!test arg1 arg2"
        mock_message.source_subscriber_id = 12345
        mock_message.reply = AsyncMock()
        
        result = await handler.handle_command(mock_message)
        
        assert result is True
        assert executed == [["arg1", "arg2"]]


class TestPhraseHelper:
    def test_phrase_management(self):
        """Test phrase management"""
        mock_client = Mock()
        mock_client.config = {
            'framework': {'language': 'en'},
            'keyword': 'test'
        }
        
        helper = PhraseHelper(mock_client)
        
        # Test setting and getting phrases
        helper.set("test_phrase", "Hello {name}!")
        result = helper.get("test_phrase", name="World")
        
        assert result == "Hello World!"
    
    def test_phrase_fallback(self):
        """Test phrase fallback behavior"""
        mock_client = Mock()
        mock_client.config = {
            'framework': {'language': 'es'},
            'keyword': 'test'
        }
        
        helper = PhraseHelper(mock_client)
        
        # Set English phrase
        helper.set("test_phrase", "Hello", language="en")
        
        # Try to get in Spanish (should fallback to English)
        result = helper.get("test_phrase", language="es")
        assert result == "Hello"
        
        # Try to get non-existent phrase (should return key)
        result = helper.get("nonexistent_phrase")
        assert result == "nonexistent_phrase"


class TestStringUtility:
    def test_replace(self):
        """Test string replacement"""
        utility = StringUtility()
        
        result = utility.replace("Hello {name}, you are {age} years old", {
            'name': 'John',
            'age': 25
        })
        
        assert result == "Hello John, you are 25 years old"
    
    def test_url_detection(self):
        """Test URL detection"""
        utility = StringUtility()
        
        assert utility.is_url("https://example.com") is True
        assert utility.is_url("http://test.org") is True
        assert utility.is_url("not a url") is False
        assert utility.is_url("") is False
    
    def test_case_conversion(self):
        """Test case conversion utilities"""
        utility = StringUtility()
        
        assert utility.to_snake_case("CamelCase") == "camel_case"
        assert utility.to_snake_case("PascalCase") == "pascal_case"
        assert utility.to_camel_case("snake_case") == "snakeCase"
        assert utility.to_pascal_case("snake_case") == "SnakeCase"
    
    def test_text_utilities(self):
        """Test text utility functions"""
        utility = StringUtility()
        
        # Test truncate
        assert utility.truncate("Long text here", 8) == "Long ..."
        assert utility.truncate("Short", 10) == "Short"
        
        # Test clean whitespace
        assert utility.clean_whitespace("  multiple   spaces  ") == "multiple spaces"
        
        # Test capitalize words
        assert utility.capitalize_words("hello world") == "Hello World"