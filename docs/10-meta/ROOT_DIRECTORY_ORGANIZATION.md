---
title: Root Directory Organization
description: Overview of the organized root directory structure
version: 2.0.0
last_updated: 2025-09-14
---

# 📁 Root Directory Organization

## Overview

This document outlines the organization of the ToolboxAI Solutions root directory after cleanup and reorganization.

## 🏗️ Essential Root Directory Files

### Core Configuration Files
- `README.md` - Main project README
- `package.json` - Node.js package configuration
- `package-lock.json` - Node.js dependency lock file
- `pyproject.toml` - Python project configuration
- `requirements.txt` - Python dependencies
- `pytest.ini` - Pytest configuration
- `Makefile` - Build automation
- `ToolBoxAI-Solutions.code-workspace` - VS Code workspace

### Environment Files
- `.env` - Main environment configuration
- `.env.example` - Environment template
- `.env.production` - Production environment
- `.env.staging` - Staging environment
- `.env.sentry.example` - Sentry configuration template
- `.env.temp` - Temporary environment

### Git and IDE Configuration
- `.gitignore` - Git ignore rules
- `.nvmrc` - Node.js version specification
- `.python-version` - Python version specification
- `.dockerignore` - Docker ignore rules

## 📂 Organized Directory Structure

### Application Directories
- `apps/` - Application code (backend, dashboard)
- `core/` - Core system components and AI agents
- `database/` - Database models and migrations
- `src/` - Shared source code
- `roblox/` - Roblox integration code

### Documentation
- `docs/` - Comprehensive documentation (organized in subfolders)

### Infrastructure
- `infrastructure/` - Docker, Kubernetes, Terraform configurations
- `config/` - Configuration files and settings

### Development Tools
- `scripts/` - Automation scripts and utilities
- `tests/` - Test suites and test data
- `examples/` - Code examples and demos
- `tooling/` - Development tools configuration

### Data and Storage
- `data/` - Data processing components
- `logs/` - Application and system logs
- `backups/` - Backup files and archives

### Third-Party Integrations
- `github/` - GitHub integration code
- `Stripe/` - Stripe payment integration
- `packages/` - Shared packages and utilities

### Settings and Utilities
- `toolboxai_settings/` - Application settings
- `toolboxai_utils/` - Utility functions
- `test-reports/` - Test execution reports

## 🗑️ Files Moved or Removed

### Documentation Files Moved to `docs/`
- `CLAUDE.md` → `docs/09-meta/CLAUDE.md`
- `COMMAND_PALETTE_FIX_GLOBAL.md` → `docs/09-meta/fixes/`
- `COMMUNICATION.md` → `docs/09-meta/COMMUNICATION.md`
- `fix_python_extension.md` → `docs/09-meta/fixes/`
- `KEYBINDING_FIX_SUMMARY.md` → `docs/09-meta/summaries/`
- `test_fixes_summary.md` → `docs/10-reports/test-reports/`
- `TEST_IMPROVEMENTS_REPORT.md` → `docs/10-reports/test-reports/`
- `test_keybindings.md` → `docs/10-reports/test-reports/`
- `TOML_FIX_SUMMARY.md` → `docs/09-meta/summaries/`

### Test Results Moved to `docs/10-reports/test-reports/`
- `Test Results - All_Tests.html`
- `test_results_unit_latest.txt`
- `test_results_unit.txt`
- `test_results.json`
- `test_results.log`
- `test_results.txt`
- `unit_test_results.txt`

### Log Files Moved to `logs/`
- `complete_test_results.log`
- `final_test_run.log`
- `full_test_run.log`
- `swarm.log`

### Configuration Files Moved to `config/tools/`
- `basedpyright_baseline.json`
- `pyrightconfig.json`

### Test Scripts Moved to `tests/`
- `test_comprehensive_fixes.py`

### Fixes Moved to `docs/09-meta/fixes/`
- `fixes/` directory and contents

### Server Binary Moved to `scripts/`
- `server` → `scripts/server`

### Files Removed
- `WARP.md` (symlink to CLAUDE.md)
- `htmlcov/` (test coverage artifacts)
- `test-results/` (duplicate test results)
- `venv_clean/` (cleanup virtual environment)
- `ToolboxAI-Roblox-Environment/` (duplicate environment)

## 🎯 Benefits of This Organization

### 1. **Clean Root Directory**
- Only essential files remain in root
- Clear separation of concerns
- Easy to identify core project files

### 2. **Logical Grouping**
- Related files are grouped together
- Documentation is centralized
- Test artifacts are organized

### 3. **Improved Navigation**
- Clear directory structure
- Easy to find specific file types
- Reduced clutter in root directory

### 4. **Better Maintenance**
- Easier to clean up temporary files
- Clear organization for new contributors
- Simplified CI/CD processes

## 📋 Root Directory Best Practices

### Essential Files Only
- Core configuration files
- Main README and documentation
- Environment configuration
- Build and dependency files

### Organized Subdirectories
- Application code in `apps/` and `core/`
- Documentation in `docs/`
- Configuration in `config/`
- Scripts in `scripts/`
- Tests in `tests/`

### Temporary Files
- Log files in `logs/`
- Test reports in `test-reports/`
- Backup files in `backups/`

## 🔄 Maintenance Guidelines

### Regular Cleanup
1. Move temporary files to appropriate directories
2. Archive old test results and logs
3. Remove unnecessary symlinks and duplicates
4. Update documentation when moving files

### New File Placement
1. Configuration files → `config/`
2. Documentation → `docs/` (appropriate subfolder)
3. Scripts → `scripts/`
4. Test files → `tests/`
5. Log files → `logs/`

### File Naming
1. Use descriptive names
2. Follow project conventions
3. Include version numbers when appropriate
4. Use consistent file extensions

---

*Last Updated: 2025-09-14*
*Version: 2.0.0*
*Compliance: COPPA, FERPA, GDPR, SOC 2 Type 2*
