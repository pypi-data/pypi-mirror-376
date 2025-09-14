"""
Utility helper for xwolfapi
"""

import re
from typing import Dict, Any, Union


class Utility:
    """Utility functions for xwolfapi"""
    
    def __init__(self, wolf_client):
        """Initialize utility helper"""
        self.wolf_client = wolf_client
        self.string = StringUtility()
    

class StringUtility:
    """String utility functions"""
    
    def replace(self, text: str, replacements: Dict[str, Any]) -> str:
        """
        Replace placeholders in text with values
        
        Args:
            text: Text with placeholders
            replacements: Dictionary of placeholder-value pairs
            
        Returns:
            Text with placeholders replaced
        """
        if not isinstance(text, str) or not replacements:
            return text
        
        result = text
        for key, value in replacements.items():
            # Replace both {key} and {key} formats
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not isinstance(text, str):
            return text
        
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in text)
    
    def strip_html(self, text: str) -> str:
        """Strip HTML tags from text"""
        if not isinstance(text, str):
            return text
        
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def truncate(self, text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to maximum length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated
            
        Returns:
            Truncated text
        """
        if not isinstance(text, str) or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    def clean_whitespace(self, text: str) -> str:
        """Clean excessive whitespace from text"""
        if not isinstance(text, str):
            return text
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()
    
    def is_url(self, text: str) -> bool:
        """Check if text is a valid URL"""
        if not isinstance(text, str):
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(text))
    
    def extract_urls(self, text: str) -> list:
        """Extract URLs from text"""
        if not isinstance(text, str):
            return []
        
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            re.IGNORECASE
        )
        
        return url_pattern.findall(text)
    
    def capitalize_words(self, text: str) -> str:
        """Capitalize each word in text"""
        if not isinstance(text, str):
            return text
        
        return ' '.join(word.capitalize() for word in text.split())
    
    def to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        if not isinstance(text, str):
            return text
        
        # Insert underscores before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        # Insert underscores before uppercase letters that follow lowercase letters
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def to_camel_case(self, text: str) -> str:
        """Convert text to camelCase"""
        if not isinstance(text, str):
            return text
        
        components = text.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    def to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        if not isinstance(text, str):
            return text
        
        return ''.join(x.capitalize() for x in text.split('_'))