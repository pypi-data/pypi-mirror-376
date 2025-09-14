"""
Command handler for xwolfapi
"""

import logging
from typing import List, Dict, Any
from ..models.command import Command, CommandContext
from ..exceptions import WOLFAPIError


class CommandHandler:
    """Handles command registration and execution"""
    
    def __init__(self, wolf_client):
        """Initialize command handler"""
        self.wolf_client = wolf_client
        self.commands: List[Command] = []
        self.logger = logging.getLogger('xwolfapi.commands')
    
    def register(self, commands: List[Command]):
        """
        Register commands
        
        Args:
            commands: List of Command objects to register
        """
        if isinstance(commands, Command):
            commands = [commands]
        
        for command in commands:
            self.commands.append(command)
            self.logger.debug(f"Registered command: {command.pattern}")
    
    def unregister(self, pattern: str):
        """
        Unregister command by pattern
        
        Args:
            pattern: Command pattern to unregister
        """
        self.commands = [cmd for cmd in self.commands if cmd.pattern != pattern]
        self.logger.debug(f"Unregistered command: {pattern}")
    
    async def handle_command(self, message) -> bool:
        """
        Handle incoming command message
        
        Args:
            message: Message object that might be a command
            
        Returns:
            True if command was handled
        """
        if not message.body.startswith('!'):
            return False
        
        # Check command ignoring rules
        ignore_config = self.wolf_client.config['framework']['command']['ignore']
        
        # Skip if sender is self and self commands are ignored
        if (ignore_config.get('self', True) and 
            self.wolf_client.current_subscriber and 
            message.source_subscriber_id == self.wolf_client.current_subscriber.id):
            return False
        
        # Find matching command
        for command in self.commands:
            if command.matches(message.body):
                try:
                    args = command.extract_args(message.body)
                    context = CommandContext(self.wolf_client, message, command, args)
                    
                    # Execute command
                    await command.execute(context)
                    
                    # Check for subcommands
                    if command.subcommands and args:
                        await self._handle_subcommands(command.subcommands, context, args)
                    
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Error executing command {command.pattern}: {e}")
                    # Optionally send error message to user
                    if hasattr(message, 'reply'):
                        try:
                            await message.reply(f"Command error: {str(e)}")
                        except:
                            pass
        
        return False
    
    async def _handle_subcommands(self, subcommands: List[Command], 
                                parent_context: CommandContext, args: List[str]):
        """
        Handle subcommands
        
        Args:
            subcommands: List of subcommands
            parent_context: Parent command context
            args: Arguments from parent command
        """
        if not args:
            return
        
        subcommand_text = ' '.join(args)
        
        for subcommand in subcommands:
            if subcommand.matches(subcommand_text):
                try:
                    sub_args = subcommand.extract_args(subcommand_text)
                    context = CommandContext(
                        self.wolf_client, 
                        parent_context.message, 
                        subcommand, 
                        sub_args
                    )
                    
                    await subcommand.execute(context)
                    return
                    
                except Exception as e:
                    self.logger.error(f"Error executing subcommand {subcommand.pattern}: {e}")
    
    def get_commands(self) -> List[Command]:
        """Get list of registered commands"""
        return self.commands.copy()
    
    def clear_commands(self):
        """Clear all registered commands"""
        self.commands.clear()
        self.logger.debug("Cleared all commands")