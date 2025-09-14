"""
Subscriber (user) model for xwolfapi
"""

from typing import Dict, Any, Optional
from ..constants import OnlineState, Gender, Language, Relationship, LookingFor


class Subscriber:
    """Represents a subscriber (user) in WOLF"""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize subscriber from raw data"""
        self.id = data.get('id')
        self.nickname = data.get('nickname', '')
        self.status = data.get('status', '')
        self.reputation = data.get('reputation', '0.0')
        self.icon = data.get('icon', {})
        self.online_state = data.get('onlineState', OnlineState.OFFLINE)
        self.device_type = data.get('deviceType', 0)
        self.privileges = data.get('privileges', 0)
        
        # Extended profile information
        extended = data.get('extended', {})
        self.extended = SubscriberExtended(extended)
        
        # Calculate percentage for reputation
        try:
            rep_parts = str(self.reputation).split('.')
            if len(rep_parts) >= 2:
                self.percentage = int(rep_parts[1]) if rep_parts[1] else 0
            else:
                self.percentage = 0
        except (ValueError, IndexError):
            self.percentage = 0
    
    @property
    def is_online(self) -> bool:
        """Check if subscriber is online"""
        return self.online_state == OnlineState.ONLINE
    
    @property
    def level(self) -> int:
        """Get the user's level (integer part of reputation)"""
        try:
            return int(float(self.reputation))
        except (ValueError, TypeError):
            return 0
    
    def __str__(self) -> str:
        return f"Subscriber(id={self.id}, nickname='{self.nickname}', level={self.level})"
    
    def __repr__(self) -> str:
        return self.__str__()


class SubscriberExtended:
    """Extended subscriber profile information"""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize extended profile from raw data"""
        self.about = data.get('about', '')
        self.date_of_birth = data.get('dateOfBirth')
        self.gender = data.get('gender', Gender.NOT_SPECIFIED)
        self.language = data.get('language', Language.ENGLISH)
        self.looking_for = data.get('lookingFor', LookingFor.NOT_SPECIFIED)
        self.name = data.get('name', '')
        self.relationship = data.get('relationship', Relationship.NOT_SPECIFIED)
        self.urls = data.get('urls', [])
    
    def __str__(self) -> str:
        return f"SubscriberExtended(name='{self.name}', gender={self.gender}, language={self.language})"
    
    def __repr__(self) -> str:
        return self.__str__()