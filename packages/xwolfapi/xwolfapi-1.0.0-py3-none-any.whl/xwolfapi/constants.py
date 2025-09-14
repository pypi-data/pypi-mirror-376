"""
Constants used throughout the xwolfapi library.
Converted from wolf.js constants.
"""

from enum import IntEnum


class OnlineState(IntEnum):
    """Online state constants"""
    OFFLINE = 0
    ONLINE = 1
    AWAY = 2
    BUSY = 3
    INVISIBLE = 5


class LoginType(IntEnum):
    """Login type constants"""
    EMAIL = 0
    API_KEY = 1


class MessageType(IntEnum):
    """Message type constants"""
    TEXT = 1
    IMAGE = 2
    VOICE = 3
    VIDEO = 4


class ContextType(IntEnum):
    """Context type constants"""
    CHANNEL = 1
    PRIVATE = 2


class Gender(IntEnum):
    """Gender constants"""
    NOT_SPECIFIED = 0
    MALE = 1
    FEMALE = 2
    NON_BINARY = 3


class Language(IntEnum):
    """Language constants"""
    ENGLISH = 1
    SPANISH = 2
    FRENCH = 3
    GERMAN = 4
    ITALIAN = 5
    PORTUGUESE = 6
    RUSSIAN = 7
    ARABIC = 8
    CHINESE = 9
    JAPANESE = 10


class Relationship(IntEnum):
    """Relationship status constants"""
    NOT_SPECIFIED = 0
    SINGLE = 1
    TAKEN = 2
    MARRIED = 3
    COMPLICATED = 4


class LookingFor(IntEnum):
    """Looking for constants (can be combined with bitwise OR)"""
    NOT_SPECIFIED = 0
    FRIENDSHIP = 1
    RELATIONSHIP = 2
    CHAT = 4
    ADVICE = 8


class Command:
    """WOLF protocol command constants"""
    # Authentication
    SECURITY_LOGIN = "security login"
    SECURITY_LOGOUT = "security logout"
    
    # Messages
    MESSAGE_SEND = "message send"
    MESSAGE_UPDATE = "message update"
    MESSAGE_DELETE = "message delete"
    
    # Channels
    CHANNEL_LIST = "channel list"
    CHANNEL_JOIN = "channel join"
    CHANNEL_LEAVE = "channel leave"
    CHANNEL_MESSAGE = "channel message"
    
    # Subscribers
    SUBSCRIBER_PROFILE = "subscriber profile"
    SUBSCRIBER_PROFILE_UPDATE = "subscriber profile update"
    SUBSCRIBER_SETTINGS_UPDATE = "subscriber settings update"
    
    # Private messages
    PRIVATE_MESSAGE = "private message"
    
    # Welcome/Ready
    WELCOME = "welcome"
    
    # Presence
    PRESENCE_UPDATE = "presence update"


class Privilege(IntEnum):
    """User privilege levels"""
    REGULAR = 0
    ADMIN = 100
    MOD = 50
    VIP = 25


class DeviceType(IntEnum):
    """Device type constants"""
    UNKNOWN = 0
    MOBILE = 1
    DESKTOP = 2
    WEB = 3


class IconSize(IntEnum):
    """Icon size constants"""
    SMALL = 25
    MEDIUM = 50
    LARGE = 100
    XLARGE = 200


class LogLevel(IntEnum):
    """Log level constants"""
    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3