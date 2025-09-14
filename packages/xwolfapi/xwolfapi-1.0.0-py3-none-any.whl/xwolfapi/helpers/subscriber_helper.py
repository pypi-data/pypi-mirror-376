"""
Subscriber helper for xwolfapi
"""

from typing import Optional, Dict, Any, List
from ..models.subscriber import Subscriber
from ..exceptions import WOLFAPIError


class SubscriberHelper:
    """Helper for subscriber-related operations"""
    
    def __init__(self, wolf_client):
        """Initialize subscriber helper"""
        self.wolf_client = wolf_client
        self._subscriber_cache: Dict[int, Subscriber] = {}
    
    async def get_by_id(self, subscriber_id: int) -> Optional[Subscriber]:
        """
        Get subscriber by ID
        
        Args:
            subscriber_id: Subscriber ID to fetch
            
        Returns:
            Subscriber object if found
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        # Check cache first
        if subscriber_id in self._subscriber_cache:
            return self._subscriber_cache[subscriber_id]
        
        response = await self.wolf_client.websocket.send_command(
            'subscriber profile',
            {'id': subscriber_id}
        )
        
        if response and response.get('success'):
            subscriber_data = response.get('body', {})
            subscriber = Subscriber(subscriber_data)
            self._subscriber_cache[subscriber_id] = subscriber
            return subscriber
        
        return None
    
    async def get_by_nickname(self, nickname: str) -> Optional[Subscriber]:
        """
        Get subscriber by nickname
        
        Args:
            nickname: Nickname to search for
            
        Returns:
            Subscriber object if found
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'subscriber search',
            {'query': nickname}
        )
        
        if response and response.get('success'):
            subscribers = response.get('body', [])
            for subscriber_data in subscribers:
                if subscriber_data.get('nickname', '').lower() == nickname.lower():
                    subscriber = Subscriber(subscriber_data)
                    self._subscriber_cache[subscriber.id] = subscriber
                    return subscriber
        
        return None
    
    async def search(self, query: str, limit: int = 25) -> List[Subscriber]:
        """
        Search for subscribers
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of subscribers matching query
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'subscriber search',
            {'query': query, 'limit': limit}
        )
        
        if response and response.get('success'):
            subscribers_data = response.get('body', [])
            subscribers = []
            for subscriber_data in subscribers_data:
                subscriber = Subscriber(subscriber_data)
                subscribers.append(subscriber)
                # Cache the subscriber
                self._subscriber_cache[subscriber.id] = subscriber
            return subscribers
        
        return []
    
    async def get_contacts(self) -> List[Subscriber]:
        """
        Get user's contacts
        
        Returns:
            List of contacts
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'contact list',
            {}
        )
        
        if response and response.get('success'):
            contacts_data = response.get('body', [])
            contacts = []
            for contact_data in contacts_data:
                subscriber = Subscriber(contact_data)
                contacts.append(subscriber)
                # Cache the subscriber
                self._subscriber_cache[subscriber.id] = subscriber
            return contacts
        
        return []
    
    async def add_contact(self, subscriber_id: int) -> bool:
        """
        Add subscriber to contacts
        
        Args:
            subscriber_id: ID of subscriber to add
            
        Returns:
            True if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'contact add',
            {'id': subscriber_id}
        )
        
        return response and response.get('success', False)
    
    async def remove_contact(self, subscriber_id: int) -> bool:
        """
        Remove subscriber from contacts
        
        Args:
            subscriber_id: ID of subscriber to remove
            
        Returns:
            True if successful
        """
        if not self.wolf_client.connected:
            raise WOLFAPIError("Not connected to WOLF")
        
        response = await self.wolf_client.websocket.send_command(
            'contact remove',
            {'id': subscriber_id}
        )
        
        return response and response.get('success', False)
    
    def _clear_cache(self):
        """Clear subscriber cache"""
        self._subscriber_cache.clear()