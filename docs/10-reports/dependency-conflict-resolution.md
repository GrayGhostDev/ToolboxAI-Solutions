# Dependency Conflict Resolution Guide

## Overview

This document provides comprehensive solutions for resolving the aiofiles version conflict and other dependency issues in the ToolBoxAI-Solutions project's Docker containers.

## Problem Description

### Original Issue
```
ERROR: Cannot install aiofiles==23.2.1 and aiofiles==24.1.0 because these package versions have conflicting dependencies.
```

### Root Cause Analysis

The conflict occurred due to:

1. **Cached Docker Layers**: Old Docker build layers contained aiofiles 23.2.1
2. **Transitive Dependencies**: Some packages in the dependency tree were requesting different aiofiles versions
3. **Inconsistent Requirements**: Multiple requirements files or cached pip installations

### Investigation Results

After thorough analysis:
- ✅ **Main requirements.txt**: Contains only `aiofiles==24.1.0` (line 47)
- ✅ **Current venv**: Has correct aiofiles 24.1.0 installed
- ✅ **No duplicate entries**: No conflicting versions in requirements.txt
- ✅ **No transitive conflicts**: LangChain and other packages don't force aiofiles 23.2.1

## Solution Implementation

### 1. Immediate Fix

#### Clear Docker Cache
```bash
# Remove all cached layers and images
docker system prune -af
docker builder prune -af
docker images -q ghcr.io/toolboxai-solutions/* | xargs -r docker rmi -f
```

#### Enhanced Dockerfile
The updated `infrastructure/docker/backend.Dockerfile` includes:

- **Cache Purging**: `pip cache purge` before installation
- **Force Reinstall**: `--force-reinstall` flag for all packages
- **Version Verification**: Explicit check for aiofiles 24.1.0
- **Multi-stage Build**: Separate builder stage for dependencies

#### Key Improvements:
```dockerfile
# Clear pip cache and upgrade pip first
RUN pip cache purge && \
    pip install --no-cache-dir --upgrade pip setuptools wheel

# Install with conflict resolution
RUN pip install --no-cache-dir --user --force-reinstall -r requirements.txt

# Verify aiofiles version
RUN python3 -c "import aiofiles; assert aiofiles.__version__ == '24.1.0'"
```

### 2. Preventive Measures

#### Dependency Lock File
Generated `requirements.lock` with exact versions and hashes:
```bash
pip-compile --generate-hashes --output-file=requirements.lock requirements.txt
```

#### Enhanced .dockerignore
Prevents local virtual environments from contaminating builds:
```
venv/
venv_clean/
env/
ENV/
```

#### Dependency Audit Script
`scripts/dependency-audit.sh` provides automated checking:
- Security vulnerability scanning
- Version conflict detection
- Outdated package identification
- Docker build readiness verification

### 3. Automated Resolution

#### Docker Dependency Fix Script
`scripts/docker-dependency-fix.sh` provides complete automation:

1. **Backup Creation**: Saves current state
2. **Environment Cleaning**: Removes cached Docker layers
3. **Requirements Analysis**: Checks for conflicts
4. **Clean Build**: Generates conflict-free Dockerfile
5. **Testing**: Verifies successful build

## Usage Instructions

### Quick Fix
```bash
# Run the automated fix
./scripts/docker-dependency-fix.sh

# Or manual steps:
docker builder prune -af
docker build -f infrastructure/docker/backend.Dockerfile . --no-cache
```

### Comprehensive Audit
```bash
# Run full dependency analysis
./scripts/dependency-audit.sh

# Check specific package
source venv/bin/activate
pip show aiofiles
pipdeptree | grep -A5 -B5 aiofiles
```

### Build Verification
```bash
# Test Docker build
docker build -f infrastructure/docker/backend.Dockerfile . --tag toolboxai-backend-test

# Verify dependencies in container
docker run --rm toolboxai-backend-test python3 -c "
import aiofiles
import fastapi
import langchain
print(f'aiofiles: {aiofiles.__version__}')
print(f'fastapi: {fastapi.__version__}')
print(f'langchain: {langchain.__version__}')
"
```

## Dependency Management Best Practices

### 1. Version Pinning Strategy
```python
# requirements.txt patterns
fastapi==0.116.1        # Exact version for stability
pytest>=8.0,<9.0       # Major version constraint
langchain~=0.3.0       # Compatible release
```

### 2. Lock File Management
```bash
# Generate lock file
pip-compile --generate-hashes requirements.txt

# Update specific package
pip-compile --upgrade-package aiofiles requirements.txt

# Sync environment with lock file
pip-sync requirements.lock
```

### 3. Docker Best Practices
```dockerfile
# Use specific Python version
FROM python:3.12-slim

# Clear caches
RUN pip cache purge

# Use --no-cache-dir
RUN pip install --no-cache-dir -r requirements.txt

# Verify critical packages
RUN python3 -c "import package; print(package.__version__)"
```

### 4. Continuous Integration
```yaml
# .github/workflows/dependency-check.yml
- name: Check dependencies
  run: |
    pip install safety pip-audit
    safety check
    pip-audit
```

## Troubleshooting Guide

### Common Issues

#### 1. "No module named 'aiofiles'"
```bash
# Solution: Reinstall in clean environment
pip uninstall aiofiles -y
pip install aiofiles==24.1.0
```

#### 2. Docker Build Timeout
```bash
# Solution: Use multi-stage build and optimize layers
# See enhanced Dockerfile for implementation
```

#### 3. Pip Dependency Resolver Conflict
```bash
# Solution: Use --force-reinstall
pip install --force-reinstall -r requirements.txt
```

#### 4. Cached Dependencies
```bash
# Solution: Clear all caches
pip cache purge
docker builder prune -af
rm -rf ~/.cache/pip
```

### Debug Commands

```bash
# Check dependency tree
pipdeptree --packages aiofiles

# Show package info
pip show aiofiles

# List installed packages
pip list | grep aiofiles

# Check for conflicts
pip check

# Dry run installation
pip install --dry-run --report /tmp/report.json -r requirements.txt
```

## Monitoring and Maintenance

### Weekly Tasks
```bash
# Run dependency audit
./scripts/dependency-audit.sh

# Check for security issues
safety check

# Update outdated packages (carefully)
pip list --outdated
```

### Monthly Tasks
```bash
# Full environment refresh
python3 -m venv venv_new
source venv_new/bin/activate
pip install -r requirements.txt
# Test thoroughly before switching

# Update lock file
pip-compile --upgrade requirements.txt
```

### Before Deployment
```bash
# Test Docker build
docker build --no-cache -f infrastructure/docker/backend.Dockerfile .

# Run security scan
docker run --rm -v $(pwd):/app clair-scanner:latest
```

## Emergency Recovery

If dependency conflicts persist:

### 1. Nuclear Option
```bash
# Complete environment reset
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
```

### 2. Docker Reset
```bash
# Complete Docker reset
docker system prune -af --volumes
docker builder prune -af
# Rebuild from scratch
```

### 3. Requirements Rebuild
```bash
# Start with minimal requirements
mv requirements.txt requirements.txt.backup
echo "fastapi==0.116.1" > requirements.txt
echo "uvicorn[standard]==0.35.0" >> requirements.txt
# Add packages incrementally
```

## Automation and Monitoring

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: dependency-check
        name: Check dependencies
        entry: ./scripts/dependency-audit.sh
        language: system
        pass_filenames: false
```

### GitHub Actions
```yaml
# .github/workflows/dependency-check.yml
name: Dependency Check
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Security audit
        run: |
          pip install safety
          safety check
      - name: Dependency check
        run: ./scripts/dependency-audit.sh
```

## Related Documentation

- [Docker Deployment Guide](../04-implementation/development-setup/comprehensive-development-setup.md)
- [Development Environment Setup](../01-overview/getting-started/getting-started.md)
- [Security Best Practices](../02-architecture/security-architecture.md)

## Contact and Support

For dependency-related issues:
1. Run `./scripts/dependency-audit.sh` for automated analysis
2. Check this guide for common solutions
3. Review Docker build logs for specific error messages
4. Create detailed issue report with environment information

---

*Last Updated: 2025-09-19*
*Tested with: Python 3.12, Docker 24.0+*