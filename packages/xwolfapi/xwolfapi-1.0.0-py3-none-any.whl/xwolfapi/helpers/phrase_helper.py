"""
Phrase helper for xwolfapi
"""

import json
import os
import logging
from typing import Dict, Any, Optional


class PhraseHelper:
    """Helper for managing phrases and translations"""
    
    def __init__(self, wolf_client):
        """Initialize phrase helper"""
        self.wolf_client = wolf_client
        self.phrases: Dict[str, Dict[str, str]] = {}
        self.logger = logging.getLogger('xwolfapi.phrases')
        self._load_default_phrases()
    
    def _load_default_phrases(self):
        """Load default phrases"""
        # Load phrases for the configured language
        language = self.wolf_client.config['framework']['language']
        keyword = self.wolf_client.config['keyword']
        
        # Default English phrases
        default_phrases = {
            f"{keyword}_command_{keyword}": f"!{keyword}",
            f"{keyword}_command_help": "help",
            f"{keyword}_help_message": f"Welcome to the {keyword} bot\\n\\n!{keyword} help - To display this message\\n!{keyword} me - Display basic information about your profile",
            f"{keyword}_command_me": "me",
            f"{keyword}_subscriber_message": "Nickname: {nickname} (ID: {id})\\nStatus Message: {status}\\nLevel: {level} ({percentage}% completed)"
        }
        
        self.phrases[language] = default_phrases
        
        # Try to load from phrases directory
        phrases_dir = os.path.join(os.getcwd(), 'phrases')
        if os.path.exists(phrases_dir):
            self._load_phrases_from_directory(phrases_dir)
    
    def _load_phrases_from_directory(self, phrases_dir: str):
        """Load phrases from directory"""
        try:
            for filename in os.listdir(phrases_dir):
                if filename.endswith('.json'):
                    language_code = filename[:-5]  # Remove .json
                    filepath = os.path.join(phrases_dir, filename)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        phrases_data = json.load(f)
                    
                    # Convert list format to dict format
                    if isinstance(phrases_data, list):
                        phrases_dict = {}
                        for phrase in phrases_data:
                            if 'name' in phrase and 'value' in phrase:
                                phrases_dict[phrase['name']] = phrase['value']
                        self.phrases[language_code] = phrases_dict
                    elif isinstance(phrases_data, dict):
                        self.phrases[language_code] = phrases_data
                        
        except Exception as e:
            self.logger.warning(f"Failed to load phrases from {phrases_dir}: {e}")
    
    def get(self, phrase_key: str, language: Optional[str] = None, **replacements) -> str:
        """
        Get phrase with optional replacements
        
        Args:
            phrase_key: Key of the phrase to get
            language: Language code (uses default if not provided)
            **replacements: Replacement values for placeholders
            
        Returns:
            Formatted phrase or the key if not found
        """
        if language is None:
            language = self.wolf_client.config['framework']['language']
        
        # Get phrase from appropriate language
        phrase = self.phrases.get(language, {}).get(phrase_key)
        
        # Fall back to English if not found
        if phrase is None and language != 'en':
            phrase = self.phrases.get('en', {}).get(phrase_key)
        
        # Fall back to the key itself if still not found
        if phrase is None:
            phrase = phrase_key
        
        # Apply replacements
        if replacements:
            try:
                # Replace placeholders in format {placeholder}
                for key, value in replacements.items():
                    placeholder = f"{{{key}}}"
                    phrase = phrase.replace(placeholder, str(value))
            except Exception:
                pass  # Return phrase without replacements if formatting fails
        
        return phrase
    
    def get_by_language_and_name(self, language: str, phrase_key: str, **replacements) -> str:
        """
        Get phrase by specific language and name
        
        Args:
            language: Language code
            phrase_key: Key of the phrase to get
            **replacements: Replacement values for placeholders
            
        Returns:
            Formatted phrase
        """
        return self.get(phrase_key, language, **replacements)
    
    def set(self, phrase_key: str, value: str, language: Optional[str] = None):
        """
        Set a phrase value
        
        Args:
            phrase_key: Key of the phrase
            value: Phrase value
            language: Language code (uses default if not provided)
        """
        if language is None:
            language = self.wolf_client.config['framework']['language']
        
        if language not in self.phrases:
            self.phrases[language] = {}
        
        self.phrases[language][phrase_key] = value
    
    def add_phrases(self, phrases_dict: Dict[str, str], language: Optional[str] = None):
        """
        Add multiple phrases
        
        Args:
            phrases_dict: Dictionary of phrase key-value pairs
            language: Language code (uses default if not provided)
        """
        if language is None:
            language = self.wolf_client.config['framework']['language']
        
        if language not in self.phrases:
            self.phrases[language] = {}
        
        self.phrases[language].update(phrases_dict)
    
    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return list(self.phrases.keys())
    
    def get_all_phrases(self, language: Optional[str] = None) -> Dict[str, str]:
        """
        Get all phrases for a language
        
        Args:
            language: Language code (uses default if not provided)
            
        Returns:
            Dictionary of all phrases
        """
        if language is None:
            language = self.wolf_client.config['framework']['language']
        
        return self.phrases.get(language, {}).copy()