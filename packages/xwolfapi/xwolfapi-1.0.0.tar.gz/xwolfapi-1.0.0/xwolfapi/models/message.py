"""
Message model for xwolfapi
"""

from typing import Optional, Dict, Any
from datetime import datetime


class Message:
    """Represents a message in WOLF"""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize message from raw data"""
        self.id = data.get('id')
        self.body = data.get('body', '')
        self.source_subscriber_id = data.get('sourceSubscriberId')
        self.target_channel_id = data.get('targetChannelId')
        self.timestamp = data.get('timestamp')
        self.is_deleted = data.get('isDeleted', False)
        self.is_edited = data.get('isEdited', False)
        self.metadata = data.get('metadata', {})
        self.type = data.get('type', 1)  # Default to text
        self._client = None
        self.is_command = False
    
    def set_client(self, client):
        """Set the client reference"""
        self._client = client
    
    @property
    def is_channel_message(self) -> bool:
        """Check if this is a channel message"""
        return bool(self.target_channel_id)
    
    @property
    def is_private_message(self) -> bool:
        """Check if this is a private message"""
        return not self.is_channel_message
    
    async def reply(self, text: str, **kwargs) -> Optional['Message']:
        """Reply to this message"""
        if not self._client:
            return None
            
        if self.is_channel_message:
            return await self._client.messaging.send_channel_message(
                self.target_channel_id, text, **kwargs
            )
        elif self.source_subscriber_id:
            return await self._client.messaging.send_private_message(
                self.source_subscriber_id, text, **kwargs
            )
        return None
    
    async def delete(self) -> bool:
        """Delete this message"""
        if not self._client or not self.id:
            return False
        return await self._client.messaging.delete_message(self.id)
    
    async def edit(self, new_body: str) -> bool:
        """Edit this message"""
        if not self._client or not self.id:
            return False
        return await self._client.messaging.edit_message(self.id, new_body)
    
    def __str__(self) -> str:
        return f"Message(id={self.id}, body='{self.body[:50]}...', from={self.source_subscriber_id})"
    
    def __repr__(self) -> str:
        return self.__str__()