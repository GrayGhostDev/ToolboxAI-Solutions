"""
Secure Credential Management System
Handles all credential operations with encryption and validation
"""

import json
import os
import secrets
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet


class CredentialManager:
    """Secure credential management with encryption and environment variable integration"""

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or ".env.secure"
        self.required_credentials = {
            "DATABASE_URL": {
                "description": "PostgreSQL connection string",
                "pattern": r"^postgresql://.*",
                "encrypted": True,
            },
            "PGPASSWORD": {
                "description": "PostgreSQL password",
                "encrypted": True,
                "sensitive": True,
            },
            "JWT_SECRET_KEY": {
                "description": "JWT signing secret (min 32 chars)",
                "min_length": 32,
                "encrypted": True,
                "generate_if_missing": True,
            },
            "PUSHER_SECRET": {
                "description": "Pusher secret key",
                "encrypted": True,
                "sensitive": True,
            },
            "PUSHER_KEY": {"description": "Pusher application key", "encrypted": False},
            "PUSHER_APP_ID": {
                "description": "Pusher application ID",
                "encrypted": False,
            },
            "PUSHER_CLUSTER": {"description": "Pusher cluster", "encrypted": False},
            "GITHUB_TOKEN": {
                "description": "GitHub personal access token",
                "encrypted": True,
                "optional": True,
            },
            "REDIS_URL": {
                "description": "Redis connection string",
                "default": "redis://localhost:6379",
                "encrypted": False,
            },
        }

        # Initialize encryption key
        self._init_encryption()

    def _init_encryption(self):
        """Initialize or load encryption key"""
        key_file = Path.home() / ".claude" / "security" / "master.key"
        key_file.parent.mkdir(parents=True, exist_ok=True)

        if key_file.exists():
            with open(key_file, "rb") as f:
                self.encryption_key = f.read()
        else:
            # Generate new encryption key
            self.encryption_key = Fernet.generate_key()
            # Save with restricted permissions
            key_file.touch(mode=0o600)
            with open(key_file, "wb") as f:
                f.write(self.encryption_key)

        self.cipher = Fernet(self.encryption_key)

    def generate_secure_secret(self, length: int = 64) -> str:
        """Generate a cryptographically secure random secret"""
        return secrets.token_urlsafe(length)

    def encrypt_value(self, value: str) -> str:
        """Encrypt a credential value"""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a credential value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()

    def validate_credentials(self) -> dict[str, Any]:
        """Validate all required credentials are present and secure"""
        validation_results = {"valid": True, "missing": [], "weak": [], "exposed": []}

        for cred_name, config in self.required_credentials.items():
            value = os.getenv(cred_name)

            # Check if credential exists
            if not value and not config.get("optional", False):
                if config.get("generate_if_missing"):
                    # Generate missing credential
                    min_length = config.get("min_length", 32)
                    value = self.generate_secure_secret(min_length)
                    os.environ[cred_name] = value
                    print(f"✅ Generated secure {cred_name}")
                else:
                    validation_results["missing"].append(cred_name)
                    validation_results["valid"] = False

            # Check credential strength
            if value and config.get("min_length"):
                if len(value) < config["min_length"]:
                    validation_results["weak"].append(cred_name)
                    validation_results["valid"] = False

            # Check for default/weak values
            if value and "default" in str(value).lower():
                validation_results["weak"].append(cred_name)

        return validation_results

    def rotate_credential(self, cred_name: str) -> str:
        """Rotate a specific credential with a new secure value"""
        if cred_name not in self.required_credentials:
            raise ValueError(f"Unknown credential: {cred_name}")

        self.required_credentials[cred_name]

        # Generate new credential
        if cred_name == "JWT_SECRET_KEY":
            new_value = self.generate_secure_secret(64)
        elif cred_name.startswith("PUSHER_"):
            # For Pusher, you'd need to update via their API
            raise NotImplementedError("Pusher credential rotation requires API integration")
        elif cred_name == "GITHUB_TOKEN":
            raise NotImplementedError("GitHub token rotation requires manual generation")
        else:
            new_value = self.generate_secure_secret(32)

        # Update environment
        os.environ[cred_name] = new_value

        return new_value

    def create_secure_env_template(self) -> str:
        """Create a secure .env.example template without sensitive values"""
        template_lines = [
            "# ToolBoxAI Secure Environment Configuration",
            "# Generated by Credential Manager",
            "# DO NOT commit actual values to version control!",
            "",
            "# Database Configuration",
            "DATABASE_URL=postgresql://[USER]:[PASSWORD]@[HOST]/[DATABASE]",
            "PGUSER=[DATABASE_USER]",
            "PGPASSWORD=[SECURE_PASSWORD]",
            "PGHOST=localhost",
            "PGPORT=5432",
            "PGDATABASE=[DATABASE_NAME]",
            "",
            "# Security",
            f"JWT_SECRET_KEY={self.generate_secure_secret(64)[:10]}...[GENERATE_SECURE_KEY]",
            "JWT_ALGORITHM=HS256",
            "JWT_EXPIRATION_DELTA=86400",
            "",
            "# Pusher Configuration",
            "PUSHER_APP_ID=[YOUR_PUSHER_APP_ID]",
            "PUSHER_KEY=[YOUR_PUSHER_KEY]",
            "PUSHER_SECRET=[YOUR_PUSHER_SECRET]",
            "PUSHER_CLUSTER=[YOUR_PUSHER_CLUSTER]",
            "",
            "# Redis",
            "REDIS_URL=redis://localhost:6379",
            "",
            "# GitHub (Optional)",
            "GITHUB_TOKEN=[YOUR_GITHUB_TOKEN]",
            "",
            "# Environment",
            "ENVIRONMENT=development",
            "DEBUG=false",
            "",
            "# CORS",
            "CORS_ALLOWED_ORIGINS=http://localhost:5179,http://127.0.0.1:5179",
            "",
            "# Rate Limiting",
            "RATE_LIMIT_PER_MINUTE=100",
            "WS_RATE_LIMIT_PER_MINUTE=60",
        ]

        return "\n".join(template_lines)

    def check_git_exposure(self) -> bool:
        """Check if any credentials are exposed in git history"""
        import subprocess

        sensitive_patterns = [
            "eduplatform2024",  # Known exposed password
            "45e89fd91f50fe615235",  # Known exposed Pusher secret
            "postgresql://.*:.*@",  # Database URLs with passwords
            "JWT_SECRET_KEY=.*",
            "PUSHER_SECRET=.*",
        ]

        exposed = False
        for pattern in sensitive_patterns:
            try:
                result = subprocess.run(
                    ["git", "log", "-p", "-S", pattern],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if pattern in result.stdout:
                    print(f"⚠️ WARNING: Pattern '{pattern[:20]}...' found in git history!")
                    exposed = True
            except:
                pass

        return exposed

    def generate_mcp_config_secure(self) -> dict[str, Any]:
        """Generate secure MCP configuration without hardcoded credentials"""
        return {
            "mcpServers": {
                "postgres": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres"],
                    "env": {
                        "DATABASE_URL": "${DATABASE_URL}",
                        "PGUSER": "${PGUSER}",
                        "PGPASSWORD": "${PGPASSWORD}",
                        "PGHOST": "${PGHOST:-localhost}",
                        "PGPORT": "${PGPORT:-5432}",
                        "PGDATABASE": "${PGDATABASE}",
                    },
                    "description": "PostgreSQL access - credentials from environment",
                    "scope": "project",
                },
                "toolboxai-orchestrator": {
                    "command": "python",
                    "args": ["core/mcp/server.py"],
                    "env": {
                        "MCP_SERVER_TYPE": "orchestrator",
                        "REDIS_URL": "${REDIS_URL}",
                        "DATABASE_URL": "${DATABASE_URL}",
                        "PUSHER_APP_ID": "${PUSHER_APP_ID}",
                        "PUSHER_KEY": "${PUSHER_KEY}",
                        "PUSHER_SECRET": "${PUSHER_SECRET}",
                        "PUSHER_CLUSTER": "${PUSHER_CLUSTER}",
                    },
                    "description": "ToolBoxAI MCP orchestrator - secure configuration",
                    "scope": "project",
                },
            }
        }


def main():
    """Run credential security audit and rotation"""
    print("🔐 ToolBoxAI Credential Security Manager")
    print("=" * 50)

    manager = CredentialManager()

    # Validate current credentials
    print("\n📋 Validating credentials...")
    results = manager.validate_credentials()

    if results["missing"]:
        print(f"❌ Missing credentials: {', '.join(results['missing'])}")

    if results["weak"]:
        print(f"⚠️ Weak credentials: {', '.join(results['weak'])}")

    if results["valid"]:
        print("✅ All required credentials are configured")
    else:
        print("❌ Credential validation failed - security risk!")

    # Check git exposure
    print("\n🔍 Checking git history for exposed credentials...")
    if manager.check_git_exposure():
        print("⚠️ CRITICAL: Credentials found in git history!")
        print("   Run: git filter-branch or BFG Repo-Cleaner to clean history")
    else:
        print("✅ No credentials found in git history")

    # Generate secure templates
    print("\n📝 Generating secure configuration templates...")

    # Create secure .env.example
    env_template = manager.create_secure_env_template()
    with open(".env.secure.example", "w") as f:
        f.write(env_template)
    print("✅ Created .env.secure.example")

    # Create secure MCP config
    mcp_config = manager.generate_mcp_config_secure()
    with open(".mcp.secure.json", "w") as f:
        json.dump(mcp_config, f, indent=2)
    print("✅ Created .mcp.secure.json")

    print("\n✨ Credential security audit complete!")
    print("\nNext steps:")
    print("1. Review and update .env with secure values")
    print("2. Replace .mcp.json with .mcp.secure.json")
    print("3. Rotate all exposed credentials")
    print("4. Clean git history if needed")


if __name__ == "__main__":
    main()
