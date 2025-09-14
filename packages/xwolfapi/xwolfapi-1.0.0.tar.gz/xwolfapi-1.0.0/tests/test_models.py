"""
Test models for xwolfapi
"""

import pytest
from unittest.mock import Mock, AsyncMock
from xwolfapi.models.message import Message
from xwolfapi.models.subscriber import Subscriber
from xwolfapi.models.channel import Channel, ChannelMember
from xwolfapi.models.command import Command, CommandContext
from xwolfapi.constants import OnlineState, Gender, Language


class TestMessage:
    def test_message_creation(self):
        """Test message creation from data"""
        data = {
            'id': 'msg123',
            'body': 'Hello world',
            'sourceSubscriberId': 12345,
            'targetChannelId': 67890,
            'timestamp': 1234567890,
            'type': 1
        }
        
        message = Message(data)
        assert message.id == 'msg123'
        assert message.body == 'Hello world'
        assert message.source_subscriber_id == 12345
        assert message.target_channel_id == 67890
        assert message.is_channel_message is True
        assert message.is_private_message is False
    
    def test_private_message(self):
        """Test private message detection"""
        data = {
            'id': 'msg123',
            'body': 'Private message',
            'sourceSubscriberId': 12345,
            'timestamp': 1234567890
        }
        
        message = Message(data)
        assert message.is_channel_message is False
        assert message.is_private_message is True
    
    @pytest.mark.asyncio
    async def test_message_reply(self):
        """Test message reply functionality"""
        data = {
            'id': 'msg123',
            'body': 'Hello',
            'sourceSubscriberId': 12345,
            'targetChannelId': 67890
        }
        
        message = Message(data)
        
        # Mock client with messaging helper
        mock_client = Mock()
        mock_client.messaging = Mock()
        mock_client.messaging.send_channel_message = AsyncMock(return_value=Mock())
        
        message.set_client(mock_client)
        
        # Test reply
        await message.reply("Hello back!")
        
        mock_client.messaging.send_channel_message.assert_called_once_with(
            67890, "Hello back!"
        )


class TestSubscriber:
    def test_subscriber_creation(self):
        """Test subscriber creation from data"""
        data = {
            'id': 12345,
            'nickname': 'TestUser',
            'status': 'Hello world',
            'reputation': '5.75',
            'onlineState': OnlineState.ONLINE,
            'extended': {
                'name': 'Test User',
                'about': 'Test description',
                'gender': Gender.MALE,
                'language': Language.ENGLISH
            }
        }
        
        subscriber = Subscriber(data)
        assert subscriber.id == 12345
        assert subscriber.nickname == 'TestUser'
        assert subscriber.level == 5
        assert subscriber.percentage == 75
        assert subscriber.is_online is True
        assert subscriber.extended.name == 'Test User'
        assert subscriber.extended.gender == Gender.MALE
    
    def test_reputation_parsing(self):
        """Test reputation parsing edge cases"""
        # Normal case
        subscriber1 = Subscriber({'reputation': '10.25'})
        assert subscriber1.level == 10
        assert subscriber1.percentage == 25
        
        # No decimal
        subscriber2 = Subscriber({'reputation': '7'})
        assert subscriber2.level == 7
        assert subscriber2.percentage == 0
        
        # Invalid reputation
        subscriber3 = Subscriber({'reputation': 'invalid'})
        assert subscriber3.level == 0
        assert subscriber3.percentage == 0


class TestChannel:
    def test_channel_creation(self):
        """Test channel creation from data"""
        data = {
            'id': 67890,
            'name': 'Test Channel',
            'description': 'A test channel',
            'ownerId': 12345,
            'memberCount': 50,
            'isOfficial': False,
            'isDiscoverable': True,
            'passwordProtected': False
        }
        
        channel = Channel(data)
        assert channel.id == 67890
        assert channel.name == 'Test Channel'
        assert channel.member_count == 50
        assert channel.is_public is True
        assert channel.is_password_protected is False
    
    @pytest.mark.asyncio
    async def test_channel_send_message(self):
        """Test channel send message functionality"""
        data = {'id': 67890, 'name': 'Test Channel'}
        channel = Channel(data)
        
        # Mock client
        mock_client = Mock()
        mock_client.messaging = Mock()
        mock_client.messaging.send_channel_message = AsyncMock(return_value=Mock())
        
        channel.set_client(mock_client)
        
        # Test send message
        await channel.send_message("Hello channel!")
        
        mock_client.messaging.send_channel_message.assert_called_once_with(
            67890, "Hello channel!"
        )


class TestCommand:
    def test_command_creation(self):
        """Test command creation and pattern matching"""
        def test_handler(context):
            return "Response"
        
        command = Command("!test", {"both": test_handler})
        
        assert command.pattern == "!test"
        assert command.matches("!test") is True
        assert command.matches("!test arg1 arg2") is True
        assert command.matches("!other") is False
        assert command.matches("test") is False
    
    def test_command_args_extraction(self):
        """Test command argument extraction"""
        def test_handler(context):
            return "Response"
        
        command = Command("!test", {"both": test_handler})
        
        args = command.extract_args("!test arg1 arg2 arg3")
        assert args == ["arg1", "arg2", "arg3"]
        
        args = command.extract_args("!test")
        assert args == []
    
    @pytest.mark.asyncio
    async def test_command_execution_async(self):
        """Test async command execution"""
        async def async_handler(context):
            return "Async response"
        
        command = Command("!test", {"both": async_handler})
        
        # Mock context
        context = Mock()
        context.is_channel = True
        context.is_private = False
        
        result = await command.execute(context)
        assert result == "Async response"
    
    @pytest.mark.asyncio
    async def test_command_execution_sync(self):
        """Test sync command execution"""
        def sync_handler(context):
            return "Sync response"
        
        command = Command("!test", {"both": sync_handler})
        
        # Mock context
        context = Mock()
        context.is_channel = True
        context.is_private = False
        
        result = await command.execute(context)
        assert result == "Sync response"


class TestChannelMember:
    def test_channel_member_creation(self):
        """Test channel member creation"""
        data = {
            'subscriberId': 12345,
            'nickname': 'TestUser',
            'privileges': 100,
            'reputation': '5.25'
        }
        
        member = ChannelMember(data)
        assert member.subscriber_id == 12345
        assert member.nickname == 'TestUser'
        assert member.privileges == 100
        assert member.is_admin is True
        assert member.is_mod is True