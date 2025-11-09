# Contributing to ToolboxAI Solutions

Thank you for your interest in contributing to ToolboxAI Solutions! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Using Labels](#using-labels)
- [Pull Request Process](#pull-request-process)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please be respectful and professional in all interactions.

## Getting Started

1. **Fork the repository** - Click the 'Fork' button in the top right
2. **Clone your fork** - `git clone https://github.com/YOUR_USERNAME/ToolboxAI-Solutions.git`
3. **Create a branch** - `git checkout -b feature/your-feature-name`
4. **Make your changes** - Follow our coding standards
5. **Test your changes** - Ensure all tests pass
6. **Commit your changes** - Use conventional commit messages
7. **Push to your fork** - `git push origin feature/your-feature-name`
8. **Create a Pull Request** - Submit your changes for review

## How to Contribute

### Reporting Bugs

When reporting bugs, please use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots if applicable

**Required Labels:**
- `type: bug`
- `needs-triage` (added automatically)
- Suggested priority level
- Affected area(s)

### Requesting Features

When requesting features, please use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- Problem description
- Proposed solution
- Alternative solutions considered
- Additional context

**Required Labels:**
- `type: feature`
- `needs-triage` (added automatically)
- Suggested priority level
- Affected area(s)

### Fixing Issues

1. Browse [open issues](https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues)
2. Look for `good first issue` or `help wanted` labels
3. Comment on the issue to claim it
4. Wait for assignment before starting work
5. Follow the development process

## Using Labels

We use a comprehensive labeling system to organize issues and PRs. Please familiarize yourself with our [Label Guide](.github/LABELS.md).

### Label Categories

#### Type Labels (Required)
- `type: bug` - Bug fixes
- `type: feature` - New features
- `type: enhancement` - Improvements
- `type: documentation` - Documentation changes
- `type: refactor` - Code refactoring
- `type: test` - Testing changes
- `type: ci/cd` - CI/CD updates

#### Priority Labels (Recommended)
- `priority: critical` - Immediate attention
- `priority: high` - Address soon
- `priority: medium` - Normal timeline
- `priority: low` - When time permits

#### Area Labels (Recommended)
- `area: frontend` - UI/React changes
- `area: backend` - API/FastAPI changes
- `area: database` - Database changes
- `area: infrastructure` - DevOps/deployment
- `area: security` - Security fixes
- `area: performance` - Performance improvements

#### Status Labels (Maintainer Use)
- `status: ready` - Ready to work
- `status: in-progress` - Being worked on
- `status: blocked` - Blocked by dependencies
- `status: needs-review` - Needs review

#### Effort Labels (Optional)
- `effort: small` - < 1 day
- `effort: medium` - 1-3 days
- `effort: large` - > 3 days

### Applying Labels

**For Issues:**
```
type: bug
priority: high
area: backend
area: database
```

**For Pull Requests:**
```
type: feature
area: frontend
javascript
```

See the complete [Label Guide](.github/LABELS.md) for detailed usage instructions.

## Pull Request Process

### Before Creating a PR

1. **Update your branch** with the latest main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Run tests** - Ensure all tests pass:
   ```bash
   # Backend tests
   cd apps/backend && pytest
   
   # Frontend tests
   cd apps/dashboard && npm test
   ```

3. **Run linters** - Fix any linting errors:
   ```bash
   # Python
   black apps/backend
   mypy apps/backend
   
   # JavaScript
   cd apps/dashboard && npm run lint
   ```

### Creating a PR

1. **Use a descriptive title**:
   ```
   feat(backend): add user authentication endpoint
   fix(frontend): resolve dashboard loading issue
   docs(readme): update installation instructions
   ```

2. **Fill out the PR template** completely
3. **Add appropriate labels** (type, area, technology)
4. **Link related issues** using keywords:
   - `Fixes #123`
   - `Closes #456`
   - `Relates to #789`

5. **Request reviewers** if you know who should review

### PR Requirements

✅ **Required:**
- All tests pass
- No linting errors
- Documentation updated (if applicable)
- Commit messages follow conventional commits
- PR description is complete
- Appropriate labels applied

✅ **Recommended:**
- Add/update tests for new features
- Include screenshots for UI changes
- Update CHANGELOG.md for significant changes
- Add migration guide for breaking changes

### PR Review Process

1. **Automated checks** run on all PRs
2. **Code review** by maintainers
3. **Address feedback** promptly
4. **Maintainer approval** required
5. **Merge** after approval and passing checks

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+

### Backend Setup

```bash
cd apps/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd apps/dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [MyPy](http://mypy-lang.org/) for type checking
- Maximum line length: 100 characters
- Use type hints for all functions

**Example:**
```python
def calculate_total(items: list[dict], tax_rate: float = 0.0) -> float:
    """Calculate total price including tax.
    
    Args:
        items: List of item dictionaries with 'price' key
        tax_rate: Tax rate as decimal (default 0.0)
        
    Returns:
        Total price including tax
    """
    subtotal = sum(item["price"] for item in items)
    return subtotal * (1 + tax_rate)
```

### JavaScript/TypeScript

- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use [ESLint](https://eslint.org/) and [Prettier](https://prettier.io/)
- Prefer TypeScript for new code
- Use functional components with hooks
- Maximum line length: 100 characters

**Example:**
```typescript
interface User {
  id: string;
  name: string;
  email: string;
}

const fetchUser = async (userId: string): Promise<User> => {
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  return response.json();
};
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructuring
- `test` - Testing
- `chore` - Maintenance

**Examples:**
```
feat(auth): add JWT token refresh endpoint

Implements automatic token refresh to improve user experience.
Users will no longer need to re-login when tokens expire.

Closes #123
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps/backend --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_success
```

### Frontend Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test UserProfile.test.tsx

# Run in watch mode
npm test -- --watch
```

### E2E Tests

```bash
# Run Playwright tests
cd apps/dashboard
npm run test:e2e

# Run in headed mode
npm run test:e2e:headed

# Run specific test
npm run test:e2e -- login.spec.ts
```

## Documentation

### Code Documentation

- **Python:** Use docstrings (Google style)
- **JavaScript:** Use JSDoc comments
- Document all public APIs
- Include examples for complex functions

### Repository Documentation

Documentation files should be placed in the `docs/` directory:

```
docs/
├── api/              # API documentation
├── architecture/     # Architecture docs
├── deployment/       # Deployment guides
├── development/      # Development guides
└── user-guides/      # User documentation
```

**No documentation should be in the root directory** except README.md.

### Updating Documentation

When making changes that affect documentation:

1. Update relevant `.md` files
2. Update OpenAPI spec if API changed
3. Update inline code documentation
4. Add migration guide if breaking change
5. Update CHANGELOG.md

## Questions?

- Check existing [issues](https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues)
- Review [documentation](docs/)
- Ask in issue comments
- Tag maintainers with `@GrayGhostDev`

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to ToolboxAI Solutions!** 🚀
