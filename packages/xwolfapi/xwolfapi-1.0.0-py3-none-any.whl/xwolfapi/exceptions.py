"""
Exceptions for xwolfapi
"""


class WOLFAPIError(Exception):
    """Base exception for WOLF API errors"""
    
    def __init__(self, message: str, data: dict = None):
        super().__init__(message)
        self.message = message
        self.data = data or {}
    
    def __str__(self):
        return f"WOLFAPIError: {self.message}"
    
    def __repr__(self):
        return f"WOLFAPIError(message='{self.message}', data={self.data})"


class ConnectionError(WOLFAPIError):
    """WebSocket connection error"""
    pass


class AuthenticationError(WOLFAPIError):
    """Authentication failed error"""
    pass


class ValidationError(WOLFAPIError):
    """Input validation error"""
    pass


class PermissionError(WOLFAPIError):
    """Permission denied error"""
    pass