"""
Secure Test Data Generator for ToolBoxAI

Provides secure generation of test credentials and user data without hardcoded values.
Ensures production safety while maintaining development functionality.
"""

import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class TestUser:
    """Secure test user data structure"""
    id: str
    username: str
    email: str
    password_hash: str
    role: str
    created_at: datetime
    is_active: bool = True


class SecureTestDataGenerator:
    """Generates secure test data for development and testing"""

    def __init__(self, seed: Optional[str] = None):
        """
        Initialize with optional seed for reproducible test data

        Args:
            seed: Optional seed for deterministic generation (testing only)
        """
        self.seed = seed
        self._deterministic_counter = 0

    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        if self.seed:
            # Deterministic for testing - use counter + seed
            self._deterministic_counter += 1
            chars = string.ascii_letters + string.digits + "!@#$%"
            # Create deterministic but varied password
            password_seed = f"{self.seed}_{self._deterministic_counter}"
            password = ''.join(chars[hash(f"{password_seed}_{i}") % len(chars)] for i in range(length))
            # Ensure it has required complexity
            if not any(c.isupper() for c in password):
                password = password[0].upper() + password[1:]
            if not any(c in "!@#$%" for c in password):
                password = password[:-1] + "!"
            return password
        else:
            # Truly random for production-like testing
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            return ''.join(secrets.choice(chars) for _ in range(length))

    def generate_user_id(self) -> str:
        """Generate a unique user ID"""
        if self.seed:
            # Deterministic for testing
            self._deterministic_counter += 1
            return f"user-{hash(f'{self.seed}_{self._deterministic_counter}') % 100000:05d}"
        else:
            return str(uuid.uuid4())

    def generate_username(self, role: str, index: int = 0) -> str:
        """Generate username based on role"""
        if self.seed:
            # Deterministic usernames for testing
            base_names = {
                "admin": ["admin.user", "system.admin", "super.admin"],
                "teacher": ["jane.smith", "john.doe", "alice.brown", "bob.wilson"],
                "student": ["alex.johnson", "sam.davis", "taylor.kim", "jordan.lee"]
            }
            names = base_names.get(role, ["test.user"])
            return names[index % len(names)]
        else:
            # Random usernames for production-like testing
            first_names = ["admin", "user", "test"] if role == "admin" else [
                secrets.choice(["alex", "sam", "taylor", "jordan", "casey", "robin", "drew"])
            ]
            last_names = ["user", "test", secrets.choice(["smith", "doe", "brown", "wilson", "davis", "kim", "lee"])]
            return f"{secrets.choice(first_names)}.{secrets.choice(last_names)}"

    def generate_email(self, username: str, domain: str = "toolboxai-test.local") -> str:
        """Generate email address"""
        # Use test domain to prevent accidental production use
        return f"{username}@{domain}"

    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return pwd_context.hash(password)

    def generate_test_user(self, role: str, index: int = 0) -> TestUser:
        """Generate a complete test user"""
        user_id = self.generate_user_id()
        username = self.generate_username(role, index)
        email = self.generate_email(username)
        password = self.generate_password()
        password_hash = self.hash_password(password)

        return TestUser(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )

    def generate_test_users(self, counts: Optional[Dict[str, int]] = None) -> Dict[str, List[TestUser]]:
        """
        Generate a set of test users by role

        Args:
            counts: Dictionary of role -> count. Defaults to {"admin": 1, "teacher": 2, "student": 3}
        """
        if counts is None:
            counts = {"admin": 1, "teacher": 2, "student": 3}

        users = {}
        for role, count in counts.items():
            users[role] = [self.generate_test_user(role, i) for i in range(count)]

        return users

    def get_test_credentials(self) -> List[Dict[str, str]]:
        """
        Get test credentials for authentication testing

        Returns:
            List of credential dictionaries with username, password, and role
            Note: Passwords are NOT hashed in this return for testing purposes
        """
        users = self.generate_test_users()
        credentials = []

        for role, user_list in users.items():
            for i, user in enumerate(user_list):
                # Generate fresh password for credentials (unhashed)
                password = self.generate_password()
                credentials.append({
                    "username": user.username,
                    "email": user.email,
                    "password": password,
                    "password_hash": self.hash_password(password),
                    "role": role,
                    "id": user.id
                })

        return credentials


def get_secure_test_data(seed: Optional[str] = None) -> Dict[str, Any]:
    """
    Get secure test data for development/testing

    Args:
        seed: Optional seed for deterministic testing

    Returns:
        Dictionary containing test users and credentials
    """
    generator = SecureTestDataGenerator(seed)

    # Generate users
    users = generator.generate_test_users()

    # Generate credentials (with unhashed passwords for testing)
    credentials = generator.get_test_credentials()

    # Create lookup dictionaries for easy access
    users_by_username = {}
    users_by_email = {}

    for role, user_list in users.items():
        for user in user_list:
            users_by_username[user.username] = user
            users_by_email[user.email] = user

    return {
        "users": users,
        "users_by_username": users_by_username,
        "users_by_email": users_by_email,
        "credentials": credentials,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed
    }


# Development helper functions
def get_development_credentials() -> List[Dict[str, str]]:
    """Get development credentials (deterministic for consistency)"""
    return get_secure_test_data(seed="development_2025")["credentials"]


def get_testing_credentials() -> List[Dict[str, str]]:
    """Get testing credentials (deterministic for test consistency)"""
    return get_secure_test_data(seed="testing_2025")["credentials"]


def get_production_test_credentials() -> List[Dict[str, str]]:
    """Get production-safe test credentials (truly random)"""
    return get_secure_test_data(seed=None)["credentials"]