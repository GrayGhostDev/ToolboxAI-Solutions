"""
JWT Secret Generator

Provides cryptographically secure JWT secret generation, validation,
and rotation capabilities for the ToolboxAI authentication system.
"""

import os
import secrets
import string
import hashlib
import hmac
import logging
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class JWTSecretGenerator:
    """Secure JWT secret generator and manager"""
    
    # Security constants
    MIN_SECRET_LENGTH = 32
    RECOMMENDED_SECRET_LENGTH = 64
    ENTROPY_THRESHOLD = 3.0  # bits per character
    WEAK_PATTERNS = [
        'password', 'secret', 'key', 'token', '12345', 'admin',
        'test', 'demo', 'dev', 'prod', 'staging', 'change-in-production',
        'your-secret-key', 'default', 'example'
    ]
    
    def __init__(self):
        self.secret_file = Path('.secrets/jwt_secret_history.enc')
        self.secret_file.parent.mkdir(exist_ok=True)
    
    @staticmethod
    def generate_secure_secret(length: int = None) -> str:
        """
        Generate a cryptographically secure JWT secret
        
        Args:
            length: Length of secret (default: 64)
            
        Returns:
            Secure random secret string
        """
        if length is None:
            length = JWTSecretGenerator.RECOMMENDED_SECRET_LENGTH
        
        if length < JWTSecretGenerator.MIN_SECRET_LENGTH:
            raise ValueError(f"Secret length must be at least {JWTSecretGenerator.MIN_SECRET_LENGTH} characters")
        
        # Use a mix of secure random methods for maximum entropy
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
        # Generate using cryptographically secure random
        secret = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure we have good character distribution
        while not JWTSecretGenerator._has_sufficient_entropy(secret):
            secret = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return secret
    
    @staticmethod
    def generate_hex_secret(length: int = None) -> str:
        """
        Generate a hexadecimal JWT secret
        
        Args:
            length: Number of hex characters (default: 64)
            
        Returns:
            Secure random hex string
        """
        if length is None:
            length = JWTSecretGenerator.RECOMMENDED_SECRET_LENGTH
            
        if length < JWTSecretGenerator.MIN_SECRET_LENGTH:
            raise ValueError(f"Secret length must be at least {JWTSecretGenerator.MIN_SECRET_LENGTH} characters")
            
        # Generate secure random hex
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def generate_base64_secret(byte_length: int = None) -> str:
        """
        Generate a base64 encoded JWT secret
        
        Args:
            byte_length: Number of random bytes (default: 48)
            
        Returns:
            Secure base64 encoded string
        """
        if byte_length is None:
            byte_length = 48  # Results in 64 character base64 string
            
        if byte_length < 24:  # 24 bytes = 32 base64 characters
            raise ValueError("Byte length must be at least 24")
            
        # Generate secure random bytes and encode
        random_bytes = secrets.token_bytes(byte_length)
        return base64.urlsafe_b64encode(random_bytes).decode('ascii')
    
    @classmethod
    def validate_secret(cls, secret: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate JWT secret strength and security
        
        Args:
            secret: Secret to validate
            
        Returns:
            Tuple of (is_valid, validation_report)
        """
        report = {
            'length_ok': False,
            'entropy_ok': False,
            'no_weak_patterns': False,
            'character_diversity': 0,
            'entropy_score': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        # Check minimum length
        if len(secret) < cls.MIN_SECRET_LENGTH:
            report['issues'].append(f"Secret too short (minimum {cls.MIN_SECRET_LENGTH} characters)")
            report['recommendations'].append(f"Use at least {cls.MIN_SECRET_LENGTH} characters")
        else:
            report['length_ok'] = True
        
        # Check for weak patterns
        secret_lower = secret.lower()
        found_patterns = [pattern for pattern in cls.WEAK_PATTERNS if pattern in secret_lower]
        if found_patterns:
            report['issues'].append(f"Contains weak patterns: {', '.join(found_patterns)}")
            report['recommendations'].append("Avoid common words and predictable patterns")
        else:
            report['no_weak_patterns'] = True
        
        # Calculate entropy
        entropy_score = cls._calculate_entropy(secret)
        report['entropy_score'] = entropy_score
        
        if entropy_score < cls.ENTROPY_THRESHOLD:
            report['issues'].append(f"Low entropy ({entropy_score:.2f} bits/char, minimum {cls.ENTROPY_THRESHOLD})")
            report['recommendations'].append("Use more diverse characters")
        else:
            report['entropy_ok'] = True
        
        # Check character diversity
        unique_chars = len(set(secret))
        report['character_diversity'] = unique_chars
        
        if unique_chars < 10:
            report['issues'].append(f"Low character diversity ({unique_chars} unique characters)")
            report['recommendations'].append("Use a wider variety of characters")
        
        # Overall validation
        is_valid = all([
            report['length_ok'],
            report['entropy_ok'],
            report['no_weak_patterns'],
            unique_chars >= 10
        ])
        
        return is_valid, report
    
    @staticmethod
    def _calculate_entropy(text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        
        for count in char_counts.values():
            probability = count / text_len
            entropy -= probability * (math.log2(probability) if probability > 0 else 0)
        
        return entropy
    
    @staticmethod
    def _has_sufficient_entropy(secret: str) -> bool:
        """Check if secret has sufficient entropy"""
        entropy = JWTSecretGenerator._calculate_entropy(secret)
        unique_chars = len(set(secret))
        
        return entropy >= JWTSecretGenerator.ENTROPY_THRESHOLD and unique_chars >= 10
    
    def store_secret_securely(self, secret: str, description: str = "") -> str:
        """
        Store JWT secret securely with encryption and metadata
        
        Args:
            secret: Secret to store
            description: Optional description
            
        Returns:
            Secret ID for retrieval
        """
        # Validate secret first
        is_valid, report = self.validate_secret(secret)
        if not is_valid:
            raise ValueError(f"Invalid secret: {', '.join(report['issues'])}")
        
        # Generate secret ID
        secret_id = secrets.token_hex(16)
        
        # Create metadata
        metadata = {
            'id': secret_id,
            'created_at': datetime.utcnow().isoformat(),
            'description': description,
            'entropy_score': report['entropy_score'],
            'character_diversity': report['character_diversity'],
            'hash': hashlib.sha256(secret.encode()).hexdigest()[:16]  # For verification
        }
        
        # Encrypt and store
        self._store_encrypted_secret(secret_id, secret, metadata)
        
        logger.info(f"JWT secret stored securely with ID: {secret_id}")
        return secret_id
    
    def _store_encrypted_secret(self, secret_id: str, secret: str, metadata: dict):
        """Store encrypted secret to file"""
        # This is a simplified encryption - in production use proper key management
        master_key = os.getenv('MASTER_KEY', 'default-master-key-change-me')
        
        # Derive encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'toolboxai-jwt-salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        
        from cryptography.fernet import Fernet
        cipher_suite = Fernet(key)
        
        # Encrypt secret
        encrypted_secret = cipher_suite.encrypt(secret.encode())
        
        # Store to file
        storage_data = {
            'metadata': metadata,
            'encrypted_secret': base64.b64encode(encrypted_secret).decode()
        }
        
        # Append to history file
        import json
        if self.secret_file.exists():
            with open(self.secret_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(storage_data)
        
        with open(self.secret_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Set secure file permissions
        os.chmod(self.secret_file, 0o600)
    
    def generate_and_store_secret(self, description: str = "Auto-generated JWT secret") -> Tuple[str, str]:
        """
        Generate and securely store a new JWT secret
        
        Args:
            description: Description for the secret
            
        Returns:
            Tuple of (secret, secret_id)
        """
        secret = self.generate_secure_secret()
        secret_id = self.store_secret_securely(secret, description)
        
        return secret, secret_id
    
    def rotate_secret(self, current_secret_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Rotate JWT secret with secure generation and storage
        
        Args:
            current_secret_id: ID of current secret (for audit trail)
            
        Returns:
            Tuple of (new_secret, new_secret_id)
        """
        description = f"Rotated from {current_secret_id}" if current_secret_id else "Secret rotation"
        
        new_secret, new_secret_id = self.generate_and_store_secret(description)
        
        logger.info(f"JWT secret rotated: {current_secret_id} -> {new_secret_id}")
        
        return new_secret, new_secret_id
    
    @staticmethod
    def create_environment_instructions(secret: str, secret_id: str) -> str:
        """
        Create instructions for setting environment variable
        
        Args:
            secret: Generated secret
            secret_id: Secret identifier
            
        Returns:
            Instructions string
        """
        instructions = f"""
JWT Secret Configuration Instructions
====================================

A secure JWT secret has been generated for your application.

Secret ID: {secret_id}
Generated at: {datetime.utcnow().isoformat()}Z

IMPORTANT: Add the following to your environment variables:

For Development (.env file):
JWT_SECRET_KEY={secret}

For Production (secure environment variable):
export JWT_SECRET_KEY="{secret}"

For Docker:
environment:
  - JWT_SECRET_KEY={secret}

SECURITY NOTES:
1. Never commit this secret to version control
2. Use different secrets for different environments
3. Rotate secrets regularly (recommended: every 90 days)
4. Monitor for unauthorized access to this secret
5. Ensure all instances use the same secret for token validation

The old hardcoded secret will be rejected when this new secret is active.
"""
        return instructions

# Convenience function for quick secret generation
def generate_secure_jwt_secret(length: int = None) -> str:
    """
    Generate a secure JWT secret
    
    Args:
        length: Length of secret (default: 64)
        
    Returns:
        Cryptographically secure secret
    """
    return JWTSecretGenerator.generate_secure_secret(length)

# Main execution for CLI usage
if __name__ == "__main__":
    import sys
    
    generator = JWTSecretGenerator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        # Generate new secret
        secret, secret_id = generator.generate_and_store_secret()
        print(generator.create_environment_instructions(secret, secret_id))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "validate":
        if len(sys.argv) < 3:
            print("Usage: python jwt_secret_generator.py validate <secret>")
            sys.exit(1)
            
        secret = sys.argv[2]
        is_valid, report = generator.validate_secret(secret)
        
        print(f"Secret validation: {'VALID' if is_valid else 'INVALID'}")
        print(f"Length: {len(secret)} characters")
        print(f"Entropy: {report['entropy_score']:.2f} bits/char")
        print(f"Character diversity: {report['character_diversity']} unique characters")
        
        if report['issues']:
            print("\nIssues:")
            for issue in report['issues']:
                print(f"  - {issue}")
                
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
                
    else:
        print("Usage:")
        print("  python jwt_secret_generator.py generate")
        print("  python jwt_secret_generator.py validate <secret>")
