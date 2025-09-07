"""
Secrets Management Module

Secure handling of sensitive configuration:
- Environment variable loading with validation
- Secrets rotation support
- Encryption at rest for local secrets
- Integration with external secret stores (AWS Secrets Manager, HashiCorp Vault)
"""

import base64
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretProvider(Enum):
    """Supported secret providers"""

    ENVIRONMENT = "environment"
    LOCAL_FILE = "local_file"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    HASHICORP_VAULT = "hashicorp_vault"
    AZURE_KEY_VAULT = "azure_key_vault"


@dataclass
class SecretConfig:
    """Configuration for a secret"""

    name: str
    provider: SecretProvider
    required: bool = True
    default_value: Optional[str] = None
    rotation_days: Optional[int] = None
    validators: List[callable] = None
    description: str = ""


class SecretValidationError(Exception):
    """Secret validation error"""

    pass


class SecretsManager:
    """Centralized secrets management"""

    def __init__(
        self,
        config_file: Optional[Path] = None,
        master_key: Optional[str] = None,
        auto_rotate: bool = False,
    ):
        self.config_file = config_file or Path("secrets_config.json")
        self.master_key = master_key or os.getenv("MASTER_KEY")
        self.auto_rotate = auto_rotate

        # Initialize encryption
        self.cipher_suite = self._init_encryption()

        # Secret storage
        self.secrets: Dict[str, Any] = {}
        self.secret_configs: Dict[str, SecretConfig] = {}
        self.last_rotation: Dict[str, datetime] = {}

        # Load configuration
        self._load_config()

        # Load secrets
        self._load_secrets()

    def _init_encryption(self) -> Optional[Fernet]:
        """Initialize encryption for local secrets"""
        if not self.master_key:
            logger.warning(
                "No master key provided, local secrets will not be encrypted"
            )
            return None

        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"toolboxai-salt",  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)

    def _load_config(self):
        """Load secret configurations"""
        # Default configurations
        default_configs = [
            SecretConfig(
                name="OPENAI_API_KEY",
                provider=SecretProvider.ENVIRONMENT,
                required=True,
                description="OpenAI API key for AI services",
                validators=[self._validate_api_key],
            ),
            SecretConfig(
                name="DATABASE_URL",
                provider=SecretProvider.ENVIRONMENT,
                required=True,
                description="PostgreSQL database connection string",
                validators=[self._validate_database_url],
            ),
            SecretConfig(
                name="REDIS_URL",
                provider=SecretProvider.ENVIRONMENT,
                required=False,
                default_value="redis://localhost:6379",
                description="Redis connection string",
            ),
            SecretConfig(
                name="JWT_SECRET_KEY",
                provider=SecretProvider.ENVIRONMENT,
                required=True,
                rotation_days=90,
                description="JWT signing key",
                validators=[self._validate_jwt_key],
            ),
            SecretConfig(
                name="SCHOOLOGY_KEY",
                provider=SecretProvider.ENVIRONMENT,
                required=False,
                description="Schoology API key",
            ),
            SecretConfig(
                name="SCHOOLOGY_SECRET",
                provider=SecretProvider.ENVIRONMENT,
                required=False,
                description="Schoology API secret",
            ),
            SecretConfig(
                name="CANVAS_TOKEN",
                provider=SecretProvider.ENVIRONMENT,
                required=False,
                description="Canvas LMS API token",
            ),
        ]

        # Load custom config if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    custom_configs = json.load(f)
                    for config_data in custom_configs:
                        config = SecretConfig(
                            name=config_data["name"],
                            provider=SecretProvider(
                                config_data.get("provider", "environment")
                            ),
                            required=config_data.get("required", True),
                            default_value=config_data.get("default_value"),
                            rotation_days=config_data.get("rotation_days"),
                            description=config_data.get("description", ""),
                        )
                        self.secret_configs[config.name] = config
            except Exception as e:
                logger.error(f"Failed to load custom config: {e}")

        # Add default configs
        for config in default_configs:
            if config.name not in self.secret_configs:
                self.secret_configs[config.name] = config

    def _load_secrets(self):
        """Load secrets from configured providers"""
        errors = []

        for name, config in self.secret_configs.items():
            try:
                value = self._load_secret(config)

                # Validate secret
                if value is not None and config.validators:
                    for validator in config.validators:
                        validator(value)

                self.secrets[name] = value

                # Track rotation
                if config.rotation_days:
                    self.last_rotation[name] = datetime.now()

            except Exception as e:
                if config.required:
                    errors.append(f"Failed to load required secret {name}: {e}")
                else:
                    logger.warning(f"Failed to load optional secret {name}: {e}")
                    self.secrets[name] = config.default_value

        if errors:
            raise SecretValidationError(f"Secret loading failed: {'; '.join(errors)}")

    def _load_secret(self, config: SecretConfig) -> Optional[str]:
        """Load a single secret from its provider"""
        if config.provider == SecretProvider.ENVIRONMENT:
            return os.getenv(config.name, config.default_value)

        elif config.provider == SecretProvider.LOCAL_FILE:
            return self._load_local_secret(config.name)

        elif config.provider == SecretProvider.AWS_SECRETS_MANAGER:
            return self._load_aws_secret(config.name)

        elif config.provider == SecretProvider.HASHICORP_VAULT:
            return self._load_vault_secret(config.name)

        elif config.provider == SecretProvider.AZURE_KEY_VAULT:
            return self._load_azure_secret(config.name)

        return config.default_value

    def _load_local_secret(self, name: str) -> Optional[str]:
        """Load secret from local encrypted file"""
        secret_file = Path(f".secrets/{name}")
        if not secret_file.exists():
            return None

        with open(secret_file, "rb") as f:
            encrypted_data = f.read()

        if self.cipher_suite:
            return self.cipher_suite.decrypt(encrypted_data).decode()
        else:
            return encrypted_data.decode()

    def _load_aws_secret(self, name: str) -> Optional[str]:
        """Load secret from AWS Secrets Manager"""
        try:
            import boto3

            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=name)
            return response["SecretString"]
        except ImportError:
            logger.warning("boto3 not installed, cannot use AWS Secrets Manager")
            return None
        except Exception as e:
            logger.error(f"Failed to load AWS secret {name}: {e}")
            return None

    def _load_vault_secret(self, name: str) -> Optional[str]:
        """Load secret from HashiCorp Vault"""
        try:
            import hvac

            client = hvac.Client(
                url=os.getenv("VAULT_URL", "http://localhost:8200"),
                token=os.getenv("VAULT_TOKEN"),
            )
            response = client.secrets.kv.v2.read_secret_version(path=name)
            return response["data"]["data"].get("value")
        except ImportError:
            logger.warning("hvac not installed, cannot use HashiCorp Vault")
            return None
        except Exception as e:
            logger.error(f"Failed to load Vault secret {name}: {e}")
            return None

    def _load_azure_secret(self, name: str) -> Optional[str]:
        """Load secret from Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            vault_url = os.getenv("AZURE_VAULT_URL")
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            secret = client.get_secret(name)
            return secret.value
        except ImportError:
            logger.warning("azure-keyvault-secrets not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to load Azure secret {name}: {e}")
            return None

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value"""
        # Check if rotation is needed
        if self.auto_rotate and name in self.last_rotation:
            config = self.secret_configs.get(name)
            if config and config.rotation_days:
                days_since_rotation = (datetime.now() - self.last_rotation[name]).days
                if days_since_rotation >= config.rotation_days:
                    logger.warning(
                        f"Secret {name} needs rotation (last rotated {days_since_rotation} days ago)"
                    )

        return self.secrets.get(name, default)

    def get_required(self, name: str) -> str:
        """Get a required secret value"""
        value = self.get(name)
        if value is None:
            raise SecretValidationError(f"Required secret {name} not found")
        return value

    def set(self, name: str, value: str, persist: bool = False):
        """Set a secret value (runtime only unless persist=True)"""
        # Validate if validators exist
        config = self.secret_configs.get(name)
        if config and config.validators:
            for validator in config.validators:
                validator(value)

        self.secrets[name] = value

        if persist and config and config.provider == SecretProvider.LOCAL_FILE:
            self._save_local_secret(name, value)

    def _save_local_secret(self, name: str, value: str):
        """Save secret to local encrypted file"""
        secret_dir = Path(".secrets")
        secret_dir.mkdir(exist_ok=True)

        secret_file = secret_dir / name

        if self.cipher_suite:
            encrypted_data = self.cipher_suite.encrypt(value.encode())
            with open(secret_file, "wb") as f:
                f.write(encrypted_data)
        else:
            with open(secret_file, "w") as f:
                f.write(value)

        # Set restrictive permissions
        os.chmod(secret_file, 0o600)

    def rotate_secret(self, name: str, new_value: str):
        """Rotate a secret"""
        old_value = self.secrets.get(name)

        # Update secret
        self.set(name, new_value, persist=True)

        # Track rotation
        self.last_rotation[name] = datetime.now()

        # Log rotation (without exposing values)
        logger.info(f"Secret {name} rotated successfully")

        return old_value

    def check_rotation_needed(self) -> List[str]:
        """Check which secrets need rotation"""
        needs_rotation = []

        for name, config in self.secret_configs.items():
            if config.rotation_days:
                if name not in self.last_rotation:
                    needs_rotation.append(name)
                else:
                    days_since = (datetime.now() - self.last_rotation[name]).days
                    if days_since >= config.rotation_days:
                        needs_rotation.append(name)

        return needs_rotation

    # Validators
    @staticmethod
    def _validate_api_key(value: str):
        """Validate API key format"""
        if not value or len(value) < 20:
            raise SecretValidationError("Invalid API key format")

        # Check for common test keys
        test_keys = ["test", "demo", "example", "12345"]
        if any(test in value.lower() for test in test_keys):
            logger.warning("API key appears to be a test key")

    @staticmethod
    def _validate_database_url(value: str):
        """Validate database URL format"""
        if not value:
            raise SecretValidationError("Database URL is required")

        # Basic format check
        if not value.startswith(
            ("postgresql://", "postgres://", "mysql://", "sqlite://")
        ):
            raise SecretValidationError("Invalid database URL format")

        # Check for default passwords
        if "password" in value or "admin" in value or "12345" in value:
            logger.warning("Database URL may contain weak credentials")

    @staticmethod
    def _validate_jwt_key(value: str):
        """Validate JWT secret key"""
        if not value or len(value) < 32:
            raise SecretValidationError("JWT secret key must be at least 32 characters")

        # Check entropy
        if len(set(value)) < 10:
            raise SecretValidationError("JWT secret key has low entropy")

    def get_status(self) -> Dict[str, Any]:
        """Get secrets manager status"""
        return {
            "total_secrets": len(self.secrets),
            "configured_secrets": len(self.secret_configs),
            "providers_used": list(
                set(c.provider.value for c in self.secret_configs.values())
            ),
            "rotation_needed": self.check_rotation_needed(),
            "encryption_enabled": self.cipher_suite is not None,
        }

    def export_config(self, output_file: Path):
        """Export secret configuration (without values)"""
        config_data = []
        for name, config in self.secret_configs.items():
            config_data.append(
                {
                    "name": name,
                    "provider": config.provider.value,
                    "required": config.required,
                    "rotation_days": config.rotation_days,
                    "description": config.description,
                    "has_value": name in self.secrets,
                }
            )

        with open(output_file, "w") as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Exported configuration to {output_file}")


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def init_secrets_manager(
    config_file: Optional[Path] = None,
    master_key: Optional[str] = None,
    auto_rotate: bool = False,
) -> SecretsManager:
    """Initialize global secrets manager"""
    global _secrets_manager
    _secrets_manager = SecretsManager(config_file, master_key, auto_rotate)
    return _secrets_manager


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret from global manager"""
    if not _secrets_manager:
        # Fallback to environment variables
        return os.getenv(name, default)
    return _secrets_manager.get(name, default)


def get_required_secret(name: str) -> str:
    """Get required secret from global manager"""
    if not _secrets_manager:
        value = os.getenv(name)
        if not value:
            raise SecretValidationError(f"Required secret {name} not found")
        return value
    return _secrets_manager.get_required(name)
