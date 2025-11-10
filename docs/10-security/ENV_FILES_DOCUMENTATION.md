# Environment Files Documentation

## Overview
This document describes the purpose of each `.env` file in the ToolBoxAI-Solutions project.

## Root Directory Environment Files

### `.env` (Active Configuration)
- **Purpose**: Main environment configuration for the entire project
- **Status**: Active - Used by backend services and scripts
- **Contains**: Database connections, API keys, service URLs
- **Security**: Never commit - ignored by git

### `.env.example`
- **Purpose**: Template showing all required environment variables
- **Status**: Safe to commit - contains no real credentials
- **Usage**: Copy to `.env` and fill in actual values

### `.env.local`
- **Purpose**: Local development overrides
- **Status**: Developer-specific - ignored by git
- **Usage**: Override specific variables for local testing

### `.env.local.example`
- **Purpose**: Template for local development overrides
- **Status**: Safe to commit

### `.env.production`
- **Purpose**: Production environment configuration template
- **Status**: May contain references but not actual secrets
- **Usage**: Used in deployment processes

### `.env.supabase.local.example`
- **Purpose**: Template for Supabase-specific local configuration
- **Status**: Safe to commit

## Dashboard App (`/apps/dashboard/`)

### `.env.local`
- **Purpose**: Dashboard-specific environment variables
- **Status**: Development overrides - ignored by git
- **Contains**: Frontend API endpoints, feature flags

### `.env.example`
- **Purpose**: Dashboard environment template
- **Status**: Safe to commit

## Docker Compose (`/infrastructure/docker/compose/`)

### `.env`
- **Purpose**: Docker-specific environment configuration
- **Status**: Active - used by docker-compose
- **Contains**: Container configs, network settings, credentials

### `.env.example`
- **Purpose**: Docker environment template
- **Status**: Safe to commit

### `.env.secret`
- **Purpose**: Sensitive docker secrets (passwords, tokens)
- **Status**: Highly sensitive - must be ignored
- **Security**: Contains actual production secrets

## Best Practices

1. **Never commit actual credentials**
   - Only `.example` files should be committed
   - Use environment-specific files for actual values

2. **Use .env hierarchy**
   - `.env` = Base configuration
   - `.env.local` = Local overrides
   - `.env.production` = Production-specific

3. **Document all variables**
   - Keep `.example` files up to date
   - Add comments explaining each variable

4. **Use secrets management**
   - For production, use Docker secrets or vault
   - Never store production secrets in `.env` files in git

## Security Notes

- All `.env*` files (except `.example`) are in `.gitignore`
- Backup `.env` files should be stored securely outside git
- Rotate credentials regularly
- Use different credentials for each environment

---

*Last Updated: 2025-11-09*
*Part of ToolBoxAI-Solutions Security Documentation*
