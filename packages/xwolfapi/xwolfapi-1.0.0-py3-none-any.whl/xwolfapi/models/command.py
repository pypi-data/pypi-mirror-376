"""
Command model for xwolfapi
"""

from typing import Dict, Any, Callable, Optional, Union
import re
import asyncio


class Command:
    """Represents a command that can be executed"""
    
    def __init__(self, pattern: str, handlers: Dict[str, Callable], subcommands: Optional[list] = None):
        """
        Initialize a command
        
        Args:
            pattern: The command pattern to match
            handlers: Dictionary with 'both', 'channel', or 'private' handlers
            subcommands: List of subcommands
        """
        self.pattern = pattern
        self.handlers = handlers or {}
        self.subcommands = subcommands or []
        self._compile_pattern()
    
    def _compile_pattern(self):
        """Compile the pattern for matching"""
        # Convert simple patterns to regex
        if self.pattern.startswith("!"):
            # Convert !command to regex
            escaped = re.escape(self.pattern[1:])
            self.regex = re.compile(f"^!{escaped}(\\s|$)", re.IGNORECASE)
        else:
            # Use as direct string match
            self.regex = re.compile(re.escape(self.pattern), re.IGNORECASE)
    
    def matches(self, text: str) -> bool:
        """Check if text matches this command"""
        return bool(self.regex.search(text))
    
    def extract_args(self, text: str) -> list:
        """Extract arguments from command text"""
        match = self.regex.search(text)
        if match:
            # Return everything after the command
            remaining = text[match.end():].strip()
            return remaining.split() if remaining else []
        return []
    
    async def execute(self, context: 'CommandContext') -> Any:
        """Execute the command with given context"""
        handler = None
        
        # Choose appropriate handler
        if context.is_channel and 'channel' in self.handlers:
            handler = self.handlers['channel']
        elif context.is_private and 'private' in self.handlers:
            handler = self.handlers['private']
        elif 'both' in self.handlers:
            handler = self.handlers['both']
        
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(context)
            else:
                return handler(context)
        
        return None


class CommandContext:
    """Context for command execution"""
    
    def __init__(self, client, message, command: Command, args: list):
        """
        Initialize command context
        
        Args:
            client: The WOLF client instance
            message: The message that triggered the command
            command: The command being executed
            args: Command arguments
        """
        self.client = client
        self.message = message
        self.command = command
        self.args = args
        self.source_subscriber_id = getattr(message, 'source_subscriber_id', None)
        self.target_channel_id = getattr(message, 'target_channel_id', None)
        self.is_channel = hasattr(message, 'target_channel_id') and message.target_channel_id
        self.is_private = not self.is_channel
        self.is_command = True
    
    async def reply(self, text: str, **kwargs) -> Any:
        """Reply to the command"""
        if hasattr(self.message, 'reply'):
            return await self.message.reply(text, **kwargs)
        elif self.is_channel and self.target_channel_id:
            return await self.client.messaging.send_channel_message(
                self.target_channel_id, text, **kwargs
            )
        elif self.is_private and self.source_subscriber_id:
            return await self.client.messaging.send_private_message(
                self.source_subscriber_id, text, **kwargs
            )
        return None
    
    def get_phrase(self, phrase_key: str, **replacements) -> str:
        """Get a phrase with replacements"""
        if hasattr(self.client, 'phrase'):
            return self.client.phrase.get(phrase_key, **replacements)
        return phrase_key