"""
Messaging helper for xwolfapi
"""

from typing import Optional, Dict, Any
from ..constants import Command, MessageType
from ..models.message import Message
from ..exceptions import WOLFAPIError


class MessagingHelper:
    """Helper for message-related operations"""
    
    def __init__(self, wolf_client):
        """Initialize messaging helper"""
        self.wolf_client = wolf_client
    
    async def send_channel_message(self, channel_id: int, text: str, 
                                 message_type: int = MessageType.TEXT,
                                 **kwargs) -> Optional[Message]:
        """
        Send a message to a channel
        
        Args:
            channel_id: Target channel ID
            text: Message text
            message_type: Type of message
            **kwargs: Additional message parameters
            
        Returns:
            Message object if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        message_data = {
            'targetChannelId': channel_id,
            'body': text,
            'type': message_type,
            **kwargs
        }
        
        response = await self.wolf_client.websocket.send_command(
            Command.MESSAGE_SEND, message_data
        )
        
        if response and response.get('success'):
            message = Message(response.get('body', {}))
            message.set_client(self.wolf_client)
            return message
        return None
    
    async def send_private_message(self, subscriber_id: int, text: str,
                                 message_type: int = MessageType.TEXT,
                                 **kwargs) -> Optional[Message]:
        """
        Send a private message to a subscriber
        
        Args:
            subscriber_id: Target subscriber ID
            text: Message text
            message_type: Type of message
            **kwargs: Additional message parameters
            
        Returns:
            Message object if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        message_data = {
            'targetSubscriberId': subscriber_id,
            'body': text,
            'type': message_type,
            **kwargs
        }
        
        response = await self.wolf_client.websocket.send_command(
            Command.MESSAGE_SEND, message_data
        )
        
        if response and response.get('success'):
            message = Message(response.get('body', {}))
            message.set_client(self.wolf_client)
            return message
        return None
    
    async def edit_message(self, message_id: str, new_body: str) -> bool:
        """
        Edit a message
        
        Args:
            message_id: ID of message to edit
            new_body: New message body
            
        Returns:
            True if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            Command.MESSAGE_UPDATE,
            {'id': message_id, 'body': new_body}
        )
        
        return response and response.get('success', False)
    
    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message
        
        Args:
            message_id: ID of message to delete
            
        Returns:
            True if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            Command.MESSAGE_DELETE,
            {'id': message_id}
        )
        
        return response and response.get('success', False)