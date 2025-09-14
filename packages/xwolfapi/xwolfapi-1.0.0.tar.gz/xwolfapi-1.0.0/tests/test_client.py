"""
Test WOLF client for xwolfapi
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from xwolfapi.client.wolf import WOLF
from xwolfapi.constants import OnlineState, LoginType
from xwolfapi.exceptions import WOLFAPIError
from xwolfapi.models.subscriber import Subscriber


class TestWOLFClient:
    def test_client_creation(self):
        """Test WOLF client creation"""
        client = WOLF()
        
        assert client.config is not None
        assert client.config['keyword'] == 'bot'
        assert client.config['framework']['language'] == 'en'
        assert client.connected is False
        assert client.current_subscriber is None
    
    def test_config_loading(self):
        """Test configuration loading"""
        # Test with non-existent config file
        client = WOLF(config_path="nonexistent.yaml")
        assert client.config['keyword'] == 'bot'  # Should use defaults
    
    def test_event_handling(self):
        """Test event registration and emission"""
        client = WOLF()
        
        # Test sync handler
        test_called = []
        def sync_handler(data):
            test_called.append(data)
        
        client.on('test_event', sync_handler)
        client.emit('test_event', "test_data")
        
        assert test_called == ["test_data"]
    
    @pytest.mark.asyncio
    async def test_login_validation(self):
        """Test login parameter validation"""
        client = WOLF()
        
        # Test without email for email login
        with pytest.raises(WOLFAPIError, match="Email is required"):
            await client.login(login_type=LoginType.EMAIL)
        
        # Test without API key for API login
        with pytest.raises(WOLFAPIError, match="API key is required"):
            await client.login(login_type=LoginType.API_KEY)
    
    @pytest.mark.asyncio
    async def test_login_process(self):
        """Test login process with mocked websocket"""
        client = WOLF()
        
        # Mock websocket
        client.websocket.connect = AsyncMock(return_value=True)
        client.websocket.send_command = AsyncMock(return_value={
            'success': True,
            'body': {
                'subscriber': {
                    'id': 12345,
                    'nickname': 'TestBot'
                }
            }
        })
        
        # Test successful login
        result = await client.login("test@example.com", "password")
        
        assert result is True
        assert client.connected is True
        assert client.current_subscriber is not None
        assert client.current_subscriber.id == 12345
    
    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout process"""
        client = WOLF()
        client.connected = True
        client.current_subscriber = Subscriber({'id': 12345, 'nickname': 'Test'})
        
        # Mock websocket
        client.websocket.send_command = AsyncMock()
        client.websocket.disconnect = AsyncMock()
        
        result = await client.logout()
        
        assert result is True
        assert client.connected is False
        assert client.current_subscriber is None
    
    @pytest.mark.asyncio
    async def test_set_online_state(self):
        """Test setting online state"""
        client = WOLF()
        client.connected = True
        
        # Mock websocket
        client.websocket.send_command = AsyncMock(return_value={'success': True})
        
        result = await client.set_online_state(OnlineState.AWAY)
        assert result is True
        
        # Test when not connected
        client.connected = False
        result = await client.set_online_state(OnlineState.ONLINE)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_profile(self):
        """Test profile update"""
        client = WOLF()
        client.connected = True
        client.current_subscriber = Subscriber({
            'id': 12345,
            'nickname': 'OldNick',
            'status': 'Old status'
        })
        
        # Mock websocket
        client.websocket.send_command = AsyncMock(return_value={'success': True})
        
        result = await client.update_profile(nickname="NewNick", status="New status")
        assert result is True
        
        # Verify the call was made with correct data
        args, kwargs = client.websocket.send_command.call_args
        update_data = args[1]
        assert update_data['nickname'] == 'NewNick'
        assert update_data['status'] == 'New status'
    
    async def test_message_handling(self):
        """Test message handling"""
        client = WOLF()
        
        # Mock command handler
        client.command_handler.handle_command = AsyncMock()
        
        # Test channel message
        channel_message_data = {
            'id': 'msg123',
            'body': '!test command',
            'targetChannelId': 67890,
            'sourceSubscriberId': 12345
        }
        
        message_emitted = []
        def message_handler(message):
            message_emitted.append(message)
        
        client.on('channelMessage', message_handler)
        client._handle_message(channel_message_data)
        
        # Give async tasks time to complete
        import asyncio
        await asyncio.sleep(0.1)
        
        assert len(message_emitted) == 1
        assert message_emitted[0].body == '!test command'
        assert message_emitted[0].is_command is True
    
    def test_subscriber_update_handling(self):
        """Test subscriber update handling"""
        client = WOLF()
        client.current_subscriber = Subscriber({'id': 12345, 'nickname': 'Test'})
        
        # Test update for current subscriber
        update_data = {
            'id': 12345,
            'nickname': 'UpdatedNick',
            'status': 'Updated status'
        }
        
        client._handle_subscriber_update(update_data)
        
        assert client.current_subscriber.nickname == 'UpdatedNick'
        assert client.current_subscriber.status == 'Updated status'