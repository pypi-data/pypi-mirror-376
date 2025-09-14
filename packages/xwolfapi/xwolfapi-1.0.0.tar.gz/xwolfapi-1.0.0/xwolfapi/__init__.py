"""
xwolfapi - Python API for WOLF (Palringo) Chat Platform

This is a Python conversion of the wolf.js JavaScript library.
"""

from .client.wolf import WOLF
from .models.command import Command
from .constants import (
    OnlineState, LoginType, MessageType, ContextType, Gender, 
    Language, Relationship, LookingFor, Command as CommandConstants
)

__version__ = "1.0.0"
__author__ = "Converted from wolf.js by dawalters1"
__license__ = "MIT"

__all__ = [
    "WOLF",
    "Command",
    "OnlineState",
    "LoginType",
    "MessageType",
    "ContextType",
    "Gender",
    "Language",
    "Relationship",
    "LookingFor",
]