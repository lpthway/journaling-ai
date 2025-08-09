# backend/app/core/input_validation.py
"""
Input validation and sanitization utilities for security.
"""

import re
import html
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    # Dangerous patterns that could indicate injection attempts
    DANGEROUS_PATTERNS = [
        r'<script[\s\S]*?</script>',  # Script tags
        r'javascript:',               # JavaScript URLs
        r'vbscript:',                # VBScript URLs
        r'on\w+\s*=',                # Event handlers
        r'expression\s*\(',          # CSS expressions
        r'<iframe[\s\S]*?</iframe>', # iframes
        r'<object[\s\S]*?</object>', # objects
        r'<embed[\s\S]*?</embed>',   # embeds
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\'\s*(OR|AND)\s*\')',
        r'(\'\s*=\s*\')',
        r'(;\s*(DROP|DELETE|INSERT|UPDATE))',
        r'(--|\#|\/\*)',
    ]
    
    @classmethod
    def sanitize_html(cls, text: str, allowed_tags: List[str] = None) -> str:
        """
        Sanitize HTML content to prevent XSS.
        
        Args:
            text: Input text to sanitize
            allowed_tags: List of allowed HTML tags (default: safe subset)
            
        Returns:
            str: Sanitized text
        """
        if not text or not isinstance(text, str):
            return ""
            
        # Default safe tags for journal entries
        if allowed_tags is None:
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 's', 'ul', 'ol', 'li',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre'
            ]
        
        # Basic HTML escape for security
        escaped = html.escape(text)
        
        # Allow only specific safe tags by converting back
        if allowed_tags:
            for tag in allowed_tags:
                # Convert escaped safe tags back to HTML
                escaped = escaped.replace(f'&lt;{tag}&gt;', f'<{tag}>')
                escaped = escaped.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
        
        # Remove any remaining dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            escaped = re.sub(pattern, '', escaped, flags=re.IGNORECASE)
            
        return escaped
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email format with security considerations.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid email format
        """
        if not email or not isinstance(email, str):
            return False
            
        # Length check
        if len(email) > 254:  # RFC 5321 limit
            return False
            
        # Basic format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
            
        # Check for dangerous patterns
        if cls._contains_dangerous_patterns(email):
            return False
            
        return True
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """
        Validate username format and security.
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if valid username
        """
        if not username or not isinstance(username, str):
            return False
            
        # Length and character validation
        if not (3 <= len(username) <= 50):
            return False
            
        # Only allow alphanumeric, underscore, hyphen, period
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            return False
            
        # Check for dangerous patterns
        if cls._contains_dangerous_patterns(username):
            return False
            
        # Prevent admin-like usernames
        admin_patterns = ['admin', 'root', 'system', 'test', 'api', 'support']
        if username.lower() in admin_patterns:
            return False
            
        return True
    
    @classmethod
    def sanitize_search_query(cls, query: str) -> str:
        """
        Sanitize search queries to prevent injection attacks.
        
        Args:
            query: Search query to sanitize
            
        Returns:
            str: Sanitized query
        """
        if not query or not isinstance(query, str):
            return ""
            
        # Limit length
        if len(query) > 500:
            query = query[:500]
            
        # Remove dangerous SQL patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            query = re.sub(pattern, '', query, flags=re.IGNORECASE)
            
        # Remove dangerous HTML/JS patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            query = re.sub(pattern, '', query, flags=re.IGNORECASE)
            
        # Clean up whitespace
        query = ' '.join(query.split())
        
        return query
    
    @classmethod
    def validate_url(cls, url: str, allowed_schemes: List[str] = None) -> bool:
        """
        Validate URL format and scheme.
        
        Args:
            url: URL to validate
            allowed_schemes: List of allowed schemes (default: http, https)
            
        Returns:
            bool: True if valid and safe URL
        """
        if not url or not isinstance(url, str):
            return False
            
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
            
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in allowed_schemes:
                return False
                
            # Check for dangerous patterns
            if cls._contains_dangerous_patterns(url):
                return False
                
            # Basic format validation
            if not parsed.netloc:
                return False
                
            return True
            
        except Exception:
            return False
    
    @classmethod
    def sanitize_json_input(cls, json_data: Any, max_depth: int = 10) -> Any:
        """
        Sanitize JSON input recursively.
        
        Args:
            json_data: JSON data to sanitize
            max_depth: Maximum nesting depth allowed
            
        Returns:
            Any: Sanitized JSON data
        """
        return cls._sanitize_recursive(json_data, 0, max_depth)
    
    @classmethod
    def validate_file_upload(cls, filename: str, allowed_extensions: List[str] = None) -> bool:
        """
        Validate file upload security.
        
        Args:
            filename: Name of uploaded file
            allowed_extensions: List of allowed file extensions
            
        Returns:
            bool: True if file is safe to upload
        """
        if not filename or not isinstance(filename, str):
            return False
            
        if allowed_extensions is None:
            allowed_extensions = ['.txt', '.md', '.json', '.pdf']
            
        # Check extension
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in allowed_extensions:
            return False
            
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
            
        # Check for dangerous patterns
        if cls._contains_dangerous_patterns(filename):
            return False
            
        return True
    
    @classmethod
    def _contains_dangerous_patterns(cls, text: str) -> bool:
        """Check if text contains dangerous patterns."""
        text_lower = text.lower()
        
        for pattern in cls.DANGEROUS_PATTERNS + cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
                
        return False
    
    @classmethod
    def _sanitize_recursive(cls, data: Any, depth: int, max_depth: int) -> Any:
        """Recursively sanitize nested data structures."""
        if depth > max_depth:
            return None
            
        if isinstance(data, dict):
            return {
                cls._sanitize_key(k): cls._sanitize_recursive(v, depth + 1, max_depth)
                for k, v in data.items()
                if cls._sanitize_key(k) is not None
            }
        elif isinstance(data, list):
            return [
                cls._sanitize_recursive(item, depth + 1, max_depth)
                for item in data[:100]  # Limit array size
            ]
        elif isinstance(data, str):
            return cls.sanitize_html(data[:10000])  # Limit string length
        else:
            return data
    
    @classmethod
    def _sanitize_key(cls, key: Any) -> Optional[str]:
        """Sanitize dictionary keys."""
        if not isinstance(key, str):
            return None
            
        if len(key) > 100:  # Reasonable key length limit
            return None
            
        if cls._contains_dangerous_patterns(key):
            return None
            
        return key


# Global validator instance
input_validator = InputValidator()