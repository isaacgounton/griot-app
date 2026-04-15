"""
Enhanced input validation utilities with comprehensive security checks.

This module provides robust validation patterns to prevent path traversal attacks,
validate file operations, and ensure secure input handling across the application.
"""
import os
import re
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from urllib.parse import urlparse
from loguru import logger

class SecurityValidationError(ValueError):
    """Custom exception for security validation failures."""
    pass

class InputValidator:
    """Comprehensive input validation with security-focused checks."""
    
    # Security patterns to detect potential attacks
    SUSPICIOUS_PATTERNS = [
        r'\.\./',           # Path traversal
        r'\.\.\\',          # Windows path traversal
        r'/etc/passwd',     # System file access
        r'/proc/',          # Process information
        r'<script',         # XSS attempts
        r'javascript:',     # JavaScript injection
        r'shell_exec',      # Command injection
        r'eval\(',          # Code evaluation
        r'union.*select',   # SQL injection
        r'\.sql$',          # SQL files
        r'\.exe$',          # Executable files
        r'\.bat$',          # Batch files
        r'\.sh$',           # Shell scripts
        r'\.py$',           # Python scripts (in file uploads)
        r'\.php$',          # PHP scripts
        r'\.jsp$',          # JSP scripts
    ]
    
    # Valid file extensions for different media types
    VALID_EXTENSIONS = {
        "image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".svg"},
        "video": {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"},
        "audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma", ".opus"},
        "document": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"},
        "archive": {".zip", ".rar", ".7z", ".tar", ".gz"}
    }
    
    def __init__(self, base_storage_path: Optional[str] = None):
        """
        Initialize validator with optional base storage path.
        
        Args:
            base_storage_path: Base directory for file operations (for path validation)
        """
        self.base_storage_path = Path(base_storage_path).resolve() if base_storage_path else None
        
    def validate_media_id(self, media_id: str) -> Tuple[str, str]:
        """
        Validate and parse a media ID to prevent path traversal attacks.
        
        Args:
            media_id: Media ID to validate (format: "type_filename")
            
        Returns:
            Tuple of (media_type, filename)
            
        Raises:
            SecurityValidationError: If media_id is invalid or contains security risks
        """
        if not media_id or not isinstance(media_id, str):
            raise SecurityValidationError("Media ID must be a non-empty string")
            
        if "_" not in media_id:
            raise SecurityValidationError("Invalid media ID format - missing type separator")
            
        # Split only on first underscore to allow underscores in filenames
        parts = media_id.split("_", 1)
        if len(parts) != 2:
            raise SecurityValidationError("Invalid media ID format")
            
        media_type, filename = parts
        
        # Validate media type
        valid_types = ["image", "video", "audio", "tmp", "document", "archive"]
        if media_type not in valid_types:
            raise SecurityValidationError(f"Invalid media type: {media_type}")
            
        # Validate filename for security risks
        self._validate_filename_security(filename)
        
        return media_type, filename
        
    def _validate_filename_security(self, filename: str):
        """
        Validate filename for security risks.
        
        Args:
            filename: Filename to validate
            
        Raises:
            SecurityValidationError: If filename contains security risks
        """
        if not filename or len(filename) > 255:
            raise SecurityValidationError("Invalid filename length")
            
        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            raise SecurityValidationError("Filename contains path traversal attempt")
            
        # Check for null bytes and control characters
        if "\x00" in filename or any(ord(c) < 32 for c in filename if c not in ['\t']):
            raise SecurityValidationError("Filename contains invalid characters")
            
        # Check against suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                raise SecurityValidationError(f"Filename matches suspicious pattern: {pattern}")
                
        # Additional security checks
        if filename.startswith('.') and len(filename) > 1:
            # Allow some common hidden files but be restrictive
            allowed_hidden = {'.gitignore', '.htaccess', '.env.example'}
            if filename not in allowed_hidden:
                logger.warning(f"Hidden file detected: {filename}")
                
    def validate_file_extension(self, filename: str, expected_type: str) -> bool:
        """
        Validate file extension against expected media type.
        
        Args:
            filename: Filename to check
            expected_type: Expected media type (image, video, audio, etc.)
            
        Returns:
            True if extension is valid for the type
            
        Raises:
            SecurityValidationError: If extension is invalid or suspicious
        """
        if not filename:
            raise SecurityValidationError("Filename cannot be empty")
            
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if not extension:
            raise SecurityValidationError("File must have an extension")
            
        valid_extensions = self.VALID_EXTENSIONS.get(expected_type, set())
        if extension not in valid_extensions:
            raise SecurityValidationError(
                f"Invalid extension '{extension}' for type '{expected_type}'. "
                f"Valid extensions: {', '.join(valid_extensions)}"
            )
            
        return True
        
    def get_safe_file_path(self, media_id: str, base_path: Optional[str] = None) -> Path:
        """
        Get a safe file path for the given media ID after validation.
        
        Args:
            media_id: Media ID to get path for
            base_path: Optional base path (uses instance base_path if not provided)
            
        Returns:
            Safe Path object
            
        Raises:
            SecurityValidationError: If path validation fails
        """
        media_type, filename = self.validate_media_id(media_id)
        
        # Use provided base path or instance base path
        storage_base = Path(base_path).resolve() if base_path else self.base_storage_path
        if not storage_base:
            raise SecurityValidationError("No base storage path configured")
            
        # Construct the full path
        file_path = storage_base / media_type / filename
        
        # Resolve the path and check it's within the storage directory
        resolved_path = file_path.resolve()
        
        # Ensure the path is within the allowed storage directory
        try:
            resolved_path.relative_to(storage_base)
        except ValueError:
            raise SecurityValidationError("Path traversal attempt detected")
            
        return resolved_path
        
    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """
        Validate URL format and security.
        
        Args:
            url: URL to validate
            allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])
            
        Returns:
            True if URL is valid
            
        Raises:
            SecurityValidationError: If URL is invalid or suspicious
        """
        if not url or not isinstance(url, str):
            raise SecurityValidationError("URL must be a non-empty string")
            
        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                raise SecurityValidationError(f"URL matches suspicious pattern: {pattern}")
                
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise SecurityValidationError(f"Invalid URL format: {e}")
            
        # Validate scheme
        allowed_schemes = allowed_schemes or ['http', 'https']
        if parsed.scheme not in allowed_schemes:
            raise SecurityValidationError(f"Invalid URL scheme. Allowed: {allowed_schemes}")
            
        # Validate that netloc exists
        if not parsed.netloc:
            raise SecurityValidationError("URL must have a valid domain")
            
        # Check for private/local addresses (basic check)
        if any(local in parsed.netloc.lower() for local in ['localhost', '127.0.0.1', '192.168.', '10.', '172.']):
            logger.warning(f"Private/local URL detected: {url}")
            
        return True
        
    def sanitize_text_input(self, text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input for safe processing.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
            
        Raises:
            SecurityValidationError: If text contains security risks
        """
        if not isinstance(text, str):
            raise SecurityValidationError("Input must be a string")
            
        if len(text) > max_length:
            raise SecurityValidationError(f"Text too long. Maximum length: {max_length}")
            
        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in text: {pattern}")
                
        # Remove null bytes and control characters (except common whitespace)
        sanitized = ''.join(c for c in text if ord(c) >= 32 or c in ['\t', '\n', '\r'])
        
        return sanitized.strip()
        
    def validate_numeric_range(self, value: float, min_val: float, max_val: float, name: str) -> float:
        """
        Validate numeric value is within acceptable range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Parameter name for error messages
            
        Returns:
            Validated value
            
        Raises:
            SecurityValidationError: If value is out of range
        """
        if not isinstance(value, (int, float)):
            raise SecurityValidationError(f"{name} must be a number")
            
        if value < min_val or value > max_val:
            raise SecurityValidationError(f"{name} must be between {min_val} and {max_val}")
            
        return float(value)
        
    def validate_file_size(self, file_path: str, max_size_mb: int = 100) -> bool:
        """
        Validate file size is within limits.
        
        Args:
            file_path: Path to file to check
            max_size_mb: Maximum size in MB
            
        Returns:
            True if file size is acceptable
            
        Raises:
            SecurityValidationError: If file is too large
        """
        if not os.path.exists(file_path):
            raise SecurityValidationError("File does not exist")
            
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise SecurityValidationError(f"File too large. Maximum size: {max_size_mb}MB")
            
        return True

# Global validator instance
input_validator = InputValidator()

# Convenience functions for easy access
def validate_media_id(media_id: str) -> Tuple[str, str]:
    """Validate media ID format and security."""
    return input_validator.validate_media_id(media_id)

def validate_url(url: str) -> bool:
    """Validate URL format and security."""
    return input_validator.validate_url(url)

def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize text input for safe processing."""
    return input_validator.sanitize_text_input(text, max_length)

def validate_file_extension(filename: str, expected_type: str) -> bool:
    """Validate file extension against expected type."""
    return input_validator.validate_file_extension(filename, expected_type)

def get_safe_file_path(media_id: str, base_path: Optional[str] = None) -> Path:
    """Get safe file path after validation."""
    return input_validator.get_safe_file_path(media_id, base_path)