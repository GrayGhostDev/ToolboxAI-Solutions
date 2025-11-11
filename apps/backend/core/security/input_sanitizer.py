"""
Input Sanitization and Error Handling Security Module

Provides secure utilities for:
1. Sanitizing user input before logging (prevents log injection)
2. Creating safe error responses (prevents stack trace exposure)
3. Validating and cleaning untrusted data

Usage:
    from apps.backend.core.security.input_sanitizer import (
        sanitize_for_logging,
        get_safe_error_response
    )
    
    # Sanitize before logging
    logger.warning(f"Invalid input: {sanitize_for_logging(user_input)}")
    
    # Safe error response
    return jsonify(get_safe_error_response(e)), 500
"""

import re
import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def sanitize_for_logging(user_input: Any, max_length: int = 200) -> str:
    """
    Sanitize user input to prevent log injection attacks.
    
    Removes or escapes characters that could be used to inject
    malicious log entries (newlines, carriage returns, control characters).
    
    Args:
        user_input: Potentially unsafe user input (any type)
        max_length: Maximum length of output (prevents log flooding)
        
    Returns:
        Sanitized string safe for logging
        
    Example:
        >>> sanitize_for_logging("user\\ndata\\rwith\\ninjection")
        'user data with injection'
        >>> sanitize_for_logging("x" * 300)
        'xxx...xxx...'  # Truncated to max_length
    """
    if user_input is None:
        return "None"
    
    # Convert to string if not already
    if not isinstance(user_input, str):
        try:
            user_input = str(user_input)
        except Exception:
            return "<unable to convert to string>"
    
    # Remove newlines, carriage returns (prevents log injection)
    sanitized = user_input.replace('\n', ' ').replace('\r', ' ')
    
    # Remove all control characters (0x00-0x1F and 0x7F)
    sanitized = re.sub(r'[\x00-\x1F\x7F]', '', sanitized)
    
    # Remove or escape ANSI escape sequences (could manipulate terminal/logs)
    sanitized = re.sub(r'\x1b\[[0-9;]*m', '', sanitized)
    
    # Limit length to prevent log flooding/DoS
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def get_safe_error_response(
    error: Exception,
    include_type: bool = False,
    custom_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a safe error response that doesn't expose stack traces or
    sensitive information to external users.
    
    Logs the actual error internally while returning a generic message
    to the user to prevent information disclosure.
    
    Args:
        error: The exception that occurred
        include_type: Whether to include the error type in response
        custom_message: Optional custom error message (if appropriate)
        
    Returns:
        Dictionary with safe error information for API response
        
    Example:
        >>> try:
        ...     raise ValueError("Database connection string invalid")
        ... except Exception as e:
        ...     response = get_safe_error_response(e)
        >>> response
        {'success': False, 'error': 'Invalid input provided'}
    """
    # Log the actual error for debugging (server-side only)
    logger.error(f"Error occurred: {type(error).__name__}: {str(error)}", exc_info=True)
    
    # Map specific error types to user-friendly messages
    # These messages are safe to expose and don't reveal system details
    error_messages = {
        "ValueError": "Invalid input provided",
        "KeyError": "Required field missing",
        "FileNotFoundError": "Resource not found",
        "PermissionError": "Permission denied",
        "TimeoutError": "Request timed out",
        "ConnectionError": "Service temporarily unavailable",
        "AttributeError": "Invalid operation",
        "TypeError": "Invalid data type",
        "IndexError": "Invalid index or range",
        "ZeroDivisionError": "Invalid calculation",
        "RuntimeError": "Operation failed",
        "NotImplementedError": "Feature not available",
        "IOError": "Input/output error",
        "OSError": "System error occurred",
    }
    
    # Use custom message if provided, otherwise use generic mapping
    if custom_message:
        generic_message = custom_message
    else:
        generic_message = error_messages.get(
            type(error).__name__,
            "An error occurred while processing your request"
        )
    
    response = {
        "success": False,
        "error": generic_message
    }
    
    # Optionally include error type (but never the message or stack trace)
    if include_type:
        response["error_type"] = type(error).__name__
    
    return response


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.
    
    Args:
        filename: User-provided filename
        max_length: Maximum allowed filename length
        
    Returns:
        Safe filename
        
    Example:
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
        >>> sanitize_filename("file<>name?.txt")
        'filename.txt'
    """
    import os
    
    # Get basename to prevent path traversal
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    # Keep only: alphanumeric, dash, underscore, period
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Remove leading dots (hidden files on Unix)
    filename = filename.lstrip('.')
    
    # Ensure not empty
    if not filename:
        filename = "unnamed_file"
    
    # Limit length
    if len(filename) > max_length:
        # Try to preserve extension
        name, ext = os.path.splitext(filename)
        if ext:
            filename = name[:max_length - len(ext)] + ext
        else:
            filename = filename[:max_length]
    
    return filename


def sanitize_path(path: str, base_dir: str) -> str:
    """
    Sanitize a file path to prevent path traversal attacks.
    
    Ensures the resolved path stays within the base directory.
    
    Args:
        path: User-provided path
        base_dir: Base directory that path must stay within
        
    Returns:
        Safe absolute path
        
    Raises:
        ValueError: If path attempts to escape base_dir
        
    Example:
        >>> sanitize_path("uploads/file.txt", "/var/www/uploads")
        '/var/www/uploads/file.txt'
        >>> sanitize_path("../../../etc/passwd", "/var/www/uploads")
        ValueError: Path traversal attempt detected
    """
    import os
    
    # Resolve to absolute paths
    base_dir = os.path.abspath(base_dir)
    target_path = os.path.abspath(os.path.join(base_dir, path))
    
    # Check if target path is within base directory
    if not target_path.startswith(base_dir):
        raise ValueError("Path traversal attempt detected")
    
    return target_path


def validate_content_type(content_type: str, allowed_types: list) -> bool:
    """
    Validate that a content type is in the allowed list.
    
    Args:
        content_type: The content type to validate
        allowed_types: List of allowed content types
        
    Returns:
        True if allowed, False otherwise
        
    Example:
        >>> validate_content_type("image/png", ["image/png", "image/jpeg"])
        True
        >>> validate_content_type("application/x-executable", ["image/png"])
        False
    """
    # Extract base type (ignore parameters like charset)
    base_type = content_type.split(';')[0].strip().lower()
    allowed_types = [t.lower() for t in allowed_types]
    
    return base_type in allowed_types
