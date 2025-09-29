# Docker Secrets Templates

## ⚠️ CRITICAL SECURITY WARNING

**NEVER commit actual secrets to Git!** This directory contains templates only.

## Quick Setup

1. Copy this directory to `../secrets/`:
   ```bash
   cp -r secrets.example/ secrets/
   cd secrets/
   ```

2. Generate secure passwords:
   ```bash
   # Database password
   openssl rand -base64 32 | tr -d "=+/" | cut -c1-32 > db_password
   
   # Redis password  
   openssl rand -base64 32 | tr -d "=+/" | cut -c1-32 > redis_password
   ```

3. Verify the secrets directory is ignored by Git:
   ```bash
   git status secrets/  # Should show "nothing to commit"
   ```

## Security Requirements

- **Minimum 32 characters** for all passwords
- **Mixed case, numbers, special characters** required
- **Unique passwords** for each service
- **Regular rotation** (quarterly recommended)

## Production Deployment

For production environments, use proper secret management:

- **AWS**: AWS Secrets Manager or Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Google Secret Manager
- **Kubernetes**: Kubernetes Secrets with encryption at rest
- **Docker Swarm**: Docker Secrets

## Emergency Response

If secrets are accidentally committed:

1. **Immediately rotate all affected passwords**
2. **Remove from Git history**: `git filter-branch` or BFG Repo-Cleaner
3. **Force push** to remote repositories
4. **Audit access logs** for potential unauthorized usage
5. **Update all deployment configurations**

## File Structure

```
secrets/
├── README.md              # This file (safe to commit)
├── db_password            # PostgreSQL password (NEVER COMMIT)
├── redis_password         # Redis password (NEVER COMMIT)  
├── jwt_secret             # JWT signing key (NEVER COMMIT)
├── openai_api_key         # OpenAI API key (NEVER COMMIT)
└── anthropic_api_key      # Anthropic API key (NEVER COMMIT)
```

## Validation Commands

```bash
# Check password strength (example for db_password)
echo "Password length: $(wc -c < db_password)"
echo "Contains uppercase: $(grep -c '[A-Z]' db_password)"
echo "Contains lowercase: $(grep -c '[a-z]' db_password)"  
echo "Contains numbers: $(grep -c '[0-9]' db_password)"
echo "Contains special chars: $(grep -c '[^A-Za-z0-9]' db_password)"
```

## Integration Points

These secrets are used by:
- `docker-compose.*.yml` files
- Kubernetes deployments in `../kubernetes/`
- Terraform modules in `../terraform/`
- Monitoring stack in `../monitoring/`

Always use environment variables or Docker secrets, never hardcode!
