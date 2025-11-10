# GitHub Projects Integration

This document describes the GitHub Projects setup for ToolBoxAI-Solutions.

## Overview

GitHub Projects provides powerful project management capabilities integrated with issues and pull requests. This repository uses GitHub Projects (v2) for:

- **Sprint planning and tracking**
- **Feature development coordination**
- **Bug triage and resolution**
- **Security issue management**
- **Infrastructure and DevOps tasks**
- **Documentation planning**

## Quick Start

### Initial Setup

```bash
# Create projects
./scripts/github-projects/setup-projects.sh

# Get project number
gh project list --owner GrayGhostDev

# Add issues and PRs
./scripts/github-projects/create-project-items.sh <project-number>

# Configure automation
./scripts/github-projects/configure-project-automation.sh <project-number>
```

## Resources

- Scripts: `scripts/github-projects/README.md`
- Workflow: `.github/workflows/project-automation.yml`
- Templates: `.github/PROJECT_TEMPLATES/`

---

**Last Updated:** 2025-11-10  
**Maintained by:** ToolBoxAI Development Team
