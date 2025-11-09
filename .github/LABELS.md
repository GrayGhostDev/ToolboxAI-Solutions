# GitHub Labels Guide

This document describes the standardized label system for the ToolboxAI Solutions repository.

## Label Categories

### Type Labels
Labels that describe the type of work being done.

| Label | Description | When to Use |
|-------|-------------|-------------|
| `type: bug` | Something isn't working correctly | Fixing broken functionality |
| `type: feature` | New feature or request | Adding new capabilities |
| `type: enhancement` | Improvement to existing feature | Improving existing functionality |
| `type: documentation` | Documentation improvements or additions | Docs changes |
| `type: refactor` | Code refactoring without changing functionality | Code cleanup and restructuring |
| `type: test` | Testing related changes | Adding or fixing tests |
| `type: ci/cd` | CI/CD pipeline and automation changes | Workflow and pipeline updates |

### Priority Labels
Labels that indicate the urgency and importance.

| Label | Description | Response Time |
|-------|-------------|---------------|
| `priority: critical` | Critical priority - immediate attention required | Within 24 hours |
| `priority: high` | High priority - should be addressed soon | Within 1 week |
| `priority: medium` | Medium priority - normal timeline | Within 1 month |
| `priority: low` | Low priority - when time permits | When capacity allows |

### Status Labels
Labels that track the current state of work.

| Label | Description | When to Apply |
|-------|-------------|---------------|
| `status: ready` | Ready to be worked on | Issue is fully defined and ready |
| `status: in-progress` | Currently being worked on | Active development |
| `status: blocked` | Blocked by dependencies or other issues | Cannot proceed without resolution |
| `status: on-hold` | Paused pending decision or resources | Temporarily paused |
| `status: needs-review` | Needs code review or approval | PR ready for review |

### Area Labels
Labels that identify the affected area of the codebase.

| Label | Description | Scope |
|-------|-------------|-------|
| `area: frontend` | Frontend/UI related changes | React, UI components, styling |
| `area: backend` | Backend/API related changes | FastAPI, services, business logic |
| `area: database` | Database schema or queries | PostgreSQL, migrations, queries |
| `area: infrastructure` | Infrastructure and deployment | Docker, CI/CD, cloud services |
| `area: security` | Security related changes | Auth, encryption, vulnerabilities |
| `area: performance` | Performance improvements | Optimization, caching, speed |

### Effort Labels
Labels that estimate the amount of work required.

| Label | Description | Estimated Time |
|-------|-------------|----------------|
| `effort: small` | Small effort - less than 1 day | < 8 hours |
| `effort: medium` | Medium effort - 1-3 days | 1-3 days |
| `effort: large` | Large effort - more than 3 days | > 3 days |

### Special Labels
Labels for specific purposes.

| Label | Description | Usage |
|-------|-------------|-------|
| `good first issue` | Good for newcomers | Issues suitable for new contributors |
| `help wanted` | Extra attention is needed | Community help requested |
| `dependencies` | Dependency updates | Dependabot PRs |
| `security` | Security vulnerability or fix | CVEs and security patches |
| `breaking-change` | Breaking change requiring migration | API/schema changes |
| `needs-triage` | Needs initial triage and classification | New issues pending review |
| `duplicate` | Duplicate issue or PR | Mark duplicates |
| `wontfix` | Will not be worked on | Rejected issues |
| `invalid` | Invalid issue or request | Not applicable |
| `tech-debt` | Technical debt that needs addressing | Code quality improvements |
| `question` | Further information is requested | Questions from users |
| `automation` | Automated PR or issue | Bot-created items |

### Technology Labels
Labels for specific technologies.

| Label | Description |
|-------|-------------|
| `github_actions` | GitHub Actions workflow updates |
| `python` | Python code changes |
| `javascript` | JavaScript/TypeScript code changes |
| `docker` | Docker related changes |

## Usage Guidelines

### For Issue Creators

When creating a new issue, please apply:
1. **One type label** (required)
2. **One priority label** (recommended)
3. **One or more area labels** (recommended)
4. **One effort label** (optional, can be added during triage)

**Example:**
```
type: bug
priority: high
area: backend
area: database
```

### For Pull Request Creators

When creating a PR, please apply:
1. **One type label** (required)
2. **One or more area labels** (required)
3. **Technology labels** as applicable
4. **Special labels** if applicable (breaking-change, security, etc.)

**Example:**
```
type: feature
area: frontend
javascript
```

### For Maintainers

**Triage Process:**
1. New issues get `needs-triage` automatically (via automation)
2. Review and add appropriate labels
3. Remove `needs-triage` once classified
4. Add `status: ready` when ready for development

**During Development:**
1. Add `status: in-progress` when work starts
2. Update to `status: blocked` if blocked
3. Change to `status: needs-review` when PR is ready
4. Remove status labels when merged/closed

**Priority Assignment:**
- `priority: critical` - Security issues, production outages
- `priority: high` - User-impacting bugs, key features
- `priority: medium` - Standard features and enhancements
- `priority: low` - Nice-to-haves, minor improvements

## Automation

### Dependabot PRs
Automatically labeled with:
- `dependencies`
- Technology label (`python`, `javascript`, `github_actions`, `docker`)
- `automation`

### GitHub Actions
The Dependabot auto-merge workflow uses labels to:
- Identify patch and minor updates
- Auto-approve and merge safe updates
- Require manual review for major versions

## Label Sync

Labels are version-controlled in `.github/labels.json` and can be synced using:

```bash
# Export current labels
gh label list --json name,description,color > .github/labels.json

# Import/sync labels
cat .github/labels.json | jq -r '.[] | "\(.name)|\(.color)|\(.description)"' | \
  while IFS='|' read name color desc; do
    gh label create "$name" --color "$color" --description "$desc" || \
    gh label edit "$name" --color "$color" --description "$desc"
  done
```

## Best Practices

### DO:
✅ Use consistent labeling across issues and PRs
✅ Update labels as status changes
✅ Combine multiple labels for better classification
✅ Use technology labels to help filter
✅ Apply `breaking-change` for API changes

### DON'T:
❌ Use multiple type labels on one issue
❌ Skip priority labels on bugs
❌ Forget to update status during work
❌ Create custom labels without discussion
❌ Remove automation labels manually

## Examples

### Bug Report
```
Labels:
- type: bug
- priority: high
- area: backend
- area: security
- python
```

### Feature Request
```
Labels:
- type: feature
- priority: medium
- area: frontend
- effort: large
- javascript
```

### Dependency Update
```
Labels:
- dependencies
- automation
- github_actions
```

### Documentation
```
Labels:
- type: documentation
- priority: low
- effort: small
```

## Questions?

If you're unsure which labels to use, ask in the issue comments or tag a maintainer. The triage team will help classify your issue appropriately.

---

**Last Updated:** 2025-11-09  
**Maintained By:** Repository Maintainers
