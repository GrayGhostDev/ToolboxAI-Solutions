# JWT Security Deployment Guide

## Overview

The ToolboxAI JWT security system provides comprehensive protection against common JWT vulnerabilities including:

- ✅ Weak secret detection and prevention
- ✅ Automatic secure secret generation
- ✅ Secret validation and strength checking
- ✅ Secret rotation capabilities
- ✅ Production security enforcement
- ✅ Development convenience features

## Quick Start

### 1. Generate Secure JWT Secret

```bash
# Generate a secure 64-character secret
python apps/backend/core/security/jwt_cli.py generate --length 64 --instructions

# Or use the convenience function
python -c "from apps.backend.core.security.jwt import generate_secure_jwt_secret; print(generate_secure_jwt_secret())"
```

### 2. Set Environment Variable

```bash
# For production
export JWT_SECRET_KEY="your-generated-secure-secret-here"

# Or add to your .env file
echo "JWT_SECRET_KEY=your-generated-secure-secret-here" >> .env
```

### 3. Verify Security

```bash
# Test the system
python apps/backend/core/security/jwt_cli.py test

# Check current status
python apps/backend/core/security/jwt_cli.py status
```

## Production Deployment

### Environment Variables

Set these environment variables in your production environment:

```bash
# Required: Secure JWT secret (minimum 32 characters)
JWT_SECRET_KEY=your-cryptographically-secure-secret-here

# Environment identifier (enables production security checks)
ENV_NAME=production

# Optional: Master key for local secret encryption
MASTER_KEY=your-master-encryption-key
```

### Security Features

The system automatically validates JWT secrets with:
- Length check (minimum 32 characters)
- Entropy validation (high randomness requirement)
- Pattern detection (rejects common weak patterns)
- Character diversity requirements

For complete deployment instructions, monitoring, troubleshooting, and security best practices, see the full documentation.
