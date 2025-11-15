"""
Test module to validate CodeRabbit AI integration.

⚠️ WARNING: FOR TESTING PURPOSES ONLY ⚠️
This file contains INTENTIONAL SECURITY VULNERABILITIES and should NEVER be used in production.
DO NOT import or execute this code outside of CodeRabbit validation testing.

This file intentionally has several issues that CodeRabbit should detect:
1. No test coverage (new file)
2. Potential security issues
3. Missing error handling
4. No input validation
5. Synchronous code (should be async)

Expected CodeRabbit feedback:
- Request test cases
- Flag security concerns
- Suggest async/await patterns
- Recommend input validation
- Estimate coverage impact
"""

import os
import sys
from typing import Any

# Safety guard: Prevent accidental execution
if os.getenv("CODERABBIT_VALIDATION_MODE") != "true":
    raise RuntimeError(
        "⚠️ SECURITY: This file contains intentional vulnerabilities for testing only. "
        "Set CODERABBIT_VALIDATION_MODE=true to bypass this check."
    )


# Additional guard: Prevent imports in production
if "pytest" not in sys.modules and os.getenv("CODERABBIT_VALIDATION_MODE") != "true":
    raise ImportError(
        "This module can only be imported during testing with CODERABBIT_VALIDATION_MODE=true"
    )


def authenticate_user(username: str, password: str) -> dict[str, Any]:
    """
    Authenticate user with username and password.

    ⚠️ INTENTIONAL ISSUES FOR CODERABBIT TO DETECT:
    - No input validation
    - Hardcoded credentials (security risk)
    - Synchronous (should be async)
    - No error handling
    - No password hashing
    - SQL injection vulnerable
    """
    # SECURITY ISSUE: Hardcoded credentials
    if username == "admin" and password == "password123":
        return {"authenticated": True, "user_id": 1, "role": "admin"}

    # SECURITY ISSUE: SQL injection vulnerable - demonstrating bad practice
    # This query is intentionally vulnerable and serves as an example for CodeRabbit
    vulnerable_query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # In real code, this would be executed against a database (NEVER DO THIS!)
    _ = vulnerable_query  # Acknowledge the variable is used for demonstration

    # Missing: Actual database call, error handling, password hashing
    return {"authenticated": False}


def get_user_data(user_id: int) -> dict[str, Any]:
    """
    Retrieve user data by ID.

    ⚠️ INTENTIONAL ISSUES:
    - No input validation (user_id could be negative, None, etc.)
    - No error handling
    - Synchronous (should be async with database)
    - No authorization check
    - Returns potentially sensitive data
    """
    # ISSUE: No validation - what if user_id is negative or None?
    user_data = {
        "id": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "abc123",  # SECURITY: Shouldn't return password hash
        "ssn": "123-45-6789",  # SECURITY: PII exposure
        "credit_card": "4111111111111111",  # SECURITY: PCI violation
    }

    return user_data


def process_payment(amount: float, card_number: str) -> bool:
    """
    Process payment with credit card.

    ⚠️ INTENTIONAL ISSUES:
    - No input validation
    - Logs sensitive data
    - No error handling
    - Missing PCI compliance
    - Synchronous payment processing
    """
    # SECURITY: Logging sensitive payment data
    print(f"Processing payment of ${amount} with card {card_number}")

    # ISSUE: No validation - negative amounts, invalid card numbers
    if amount > 0:
        return True

    return False


class UserSession:
    """
    Manage user sessions.

    ⚠️ INTENTIONAL ISSUES:
    - Session fixation vulnerability
    - No session timeout
    - Predictable session IDs
    - No CSRF protection
    """

    def __init__(self, user_id: int):
        # SECURITY: Predictable session ID
        self.session_id = f"session_{user_id}"
        self.user_id = user_id
        self.created_at = None  # ISSUE: No timestamp

    def is_valid(self) -> bool:
        """Check if session is valid."""
        # ISSUE: Always returns True (no expiration check)
        return True

    def get_data(self) -> dict[str, Any]:
        """Get session data."""
        # SECURITY: Exposes session ID
        return {"session_id": self.session_id, "user_id": self.user_id}


# ISSUE: No tests for any of these functions
# ISSUE: No async/await patterns
# ISSUE: No Pydantic models for validation
# ISSUE: No proper authentication (should use Clerk)
# ISSUE: No database integration (should use SQLAlchemy)
