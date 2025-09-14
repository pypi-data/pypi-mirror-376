"""
Channel helper for xwolfapi
"""

from typing import List, Optional, Dict, Any
from ..constants import Command
from ..models.channel import Channel, ChannelMember
from ..exceptions import WOLFAPIError


class ChannelHelper:
    """Helper for channel-related operations"""
    
    def __init__(self, wolf_client):
        """Initialize channel helper"""
        self.wolf_client = wolf_client
        self._channel_cache: Dict[int, Channel] = {}
    
    async def get_by_id(self, channel_id: int) -> Optional[Channel]:
        """
        Get channel by ID
        
        Args:
            channel_id: Channel ID to fetch
            
        Returns:
            Channel object if found
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        # Check cache first
        if channel_id in self._channel_cache:
            return self._channel_cache[channel_id]
        
        response = await self.wolf_client.websocket.send_command(
            'channel profile',
            {'id': channel_id}
        )
        
        if response and response.get('success'):
            channel_data = response.get('body', {})
            channel = Channel(channel_data)
            channel.set_client(self.wolf_client)
            self._channel_cache[channel_id] = channel
            return channel
        
        return None
    
    async def get_by_name(self, channel_name: str) -> Optional[Channel]:
        """
        Get channel by name
        
        Args:
            channel_name: Channel name to search for
            
        Returns:
            Channel object if found
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'channel search',
            {'query': channel_name}
        )
        
        if response and response.get('success'):
            channels = response.get('body', [])
            for channel_data in channels:
                if channel_data.get('name', '').lower() == channel_name.lower():
                    channel = Channel(channel_data)
                    channel.set_client(self.wolf_client)
                    self._channel_cache[channel.id] = channel
                    return channel
        
        return None
    
    async def join_by_id(self, channel_id: int, password: Optional[str] = None) -> bool:
        """
        Join channel by ID
        
        Args:
            channel_id: Channel ID to join
            password: Channel password if required
            
        Returns:
            True if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        join_data = {'id': channel_id}
        if password:
            join_data['password'] = password
        
        response = await self.wolf_client.websocket.send_command(
            Command.CHANNEL_JOIN, join_data
        )
        
        return response and response.get('success', False)
    
    async def join_by_name(self, channel_name: str, password: Optional[str] = None) -> bool:
        """
        Join channel by name
        
        Args:
            channel_name: Channel name to join
            password: Channel password if required
            
        Returns:
            True if successful
        """
        channel = await self.get_by_name(channel_name)
        if channel:
            return await self.join_by_id(channel.id, password)
        return False
    
    async def leave_by_id(self, channel_id: int) -> bool:
        """
        Leave channel by ID
        
        Args:
            channel_id: Channel ID to leave
            
        Returns:
            True if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            Command.CHANNEL_LEAVE,
            {'id': channel_id}
        )
        
        # Remove from cache
        self._channel_cache.pop(channel_id, None)
        
        return response and response.get('success', False)
    
    async def get_members(self, channel_id: int) -> List[ChannelMember]:
        """
        Get channel members
        
        Args:
            channel_id: Channel ID
            
        Returns:
            List of channel members
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'channel member list',
            {'id': channel_id}
        )
        
        if response and response.get('success'):
            members_data = response.get('body', [])
            return [ChannelMember(member) for member in members_data]
        
        return []
    
    async def search(self, query: str, limit: int = 25) -> List[Channel]:
        """
        Search for channels
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of channels matching query
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'channel search',
            {'query': query, 'limit': limit}
        )
        
        if response and response.get('success'):
            channels_data = response.get('body', [])
            channels = []
            for channel_data in channels_data:
                channel = Channel(channel_data)
                channel.set_client(self.wolf_client)
                channels.append(channel)
                # Cache the channel
                self._channel_cache[channel.id] = channel
            return channels
        
        return []
    
    def _clear_cache(self):
        """Clear channel cache"""
        self._channel_cache.clear()