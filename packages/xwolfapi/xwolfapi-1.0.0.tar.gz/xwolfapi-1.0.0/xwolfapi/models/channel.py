"""
Channel model for xwolfapi
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .message import Message


class Channel:
    """Represents a channel in WOLF"""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize channel from raw data"""
        self.id = data.get('id')
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.owner_id = data.get('ownerId')
        self.reputation = data.get('reputation', 0)
        self.member_count = data.get('memberCount', 0)
        self.icon = data.get('icon', {})
        self.category_ids = data.get('categoryIds', [])
        self.is_official = data.get('isOfficial', False)
        self.is_discoverable = data.get('isDiscoverable', True)
        self.is_password_protected = data.get('passwordProtected', False)
        self.language = data.get('language', 1)  # Default to English
        self.members = []
        self._client = None
    
    def set_client(self, client):
        """Set the client reference"""
        self._client = client
    
    @property
    def is_public(self) -> bool:
        """Check if channel is public"""
        return self.is_discoverable and not self.is_password_protected
    
    async def send_message(self, text: str, **kwargs) -> Optional['Message']:
        """Send a message to this channel"""
        if not self._client:
            return None
        return await self._client.messaging.send_channel_message(self.id, text, **kwargs)
    
    async def join(self, password: Optional[str] = None) -> bool:
        """Join this channel"""
        if not self._client:
            return False
        return await self._client.channel.join_by_id(self.id, password)
    
    async def leave(self) -> bool:
        """Leave this channel"""
        if not self._client:
            return False
        return await self._client.channel.leave_by_id(self.id)
    
    async def get_members(self) -> List['ChannelMember']:
        """Get channel members"""
        if not self._client:
            return []
        return await self._client.channel.get_members(self.id)
    
    def __str__(self) -> str:
        return f"Channel(id={self.id}, name='{self.name}', members={self.member_count})"
    
    def __repr__(self) -> str:
        return self.__str__()


class ChannelMember:
    """Represents a member of a channel"""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize channel member from raw data"""
        self.subscriber_id = data.get('subscriberId')
        self.nickname = data.get('nickname', '')
        self.privileges = data.get('privileges', 0)
        self.capabilities = data.get('capabilities', 0)
        self.joined_at = data.get('joinedAt')
        self.reputation = data.get('reputation', '0.0')
        self.icon = data.get('icon', {})
    
    @property
    def is_admin(self) -> bool:
        """Check if member is an admin"""
        return self.privileges >= 100
    
    @property
    def is_mod(self) -> bool:
        """Check if member is a moderator"""
        return self.privileges >= 50
    
    def __str__(self) -> str:
        return f"ChannelMember(id={self.subscriber_id}, nickname='{self.nickname}', privileges={self.privileges})"
    
    def __repr__(self) -> str:
        return self.__str__()