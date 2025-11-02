# Contributing to ToolboxAI Solutions

Thank you for your interest in contributing to ToolboxAI! This document provides guidelines and standards for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please be respectful and professional in all interactions.

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:
- Python 3.11+
- Node.js 22+
- Docker & Docker Compose
- Git configured with your GitHub account

### Initial Setup

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ToolboxAI-Solutions.git
   cd ToolboxAI-Solutions
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/GrayGhostDev/ToolboxAI-Solutions.git
   ```

4. **Set up development environment**:
   ```bash
   # Python setup
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend setup
   cd apps/dashboard
   npm install --legacy-peer-deps
   cd ../..
   
   # Start services
   make docker-dev
   ```

5. **Verify setup**:
   - Dashboard: http://localhost:5179
   - API: http://localhost:8009
   - API Docs: http://localhost:8009/docs

---

## Project Structure

After the October 2025 reorganization, the project follows this structure:

```
ToolBoxAI-Solutions/
├── apps/
│   ├── backend/              # FastAPI application
│   │   ├── api/             # API routes
│   │   ├── core/            # Core functionality
│   │   ├── middleware/      # Request middleware
│   │   ├── models/          # Data models
│   │   ├── routers/         # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   └── dashboard/           # React frontend
├── core/                    # AI agents & orchestration
├── database/                # Database layer
├── infrastructure/          # Docker & deployment
│   └── docker/
│       ├── compose/         # Docker Compose files
│       └── Dockerfile.*     # Container definitions
├── docs/                    # Documentation
│   ├── guides/              # Developer guides
│   ├── setup/               # Setup instructions
│   └── INDEX.md            # Documentation index
├── tests/                   # Test suites
└── config/                  # Configuration files
```

**Important**: Always place files in their proper location:
- Backend code → `apps/backend/`
- Frontend code → `apps/dashboard/`
- Tests → `tests/`
- Documentation → `docs/`
- Docker files → `infrastructure/docker/`

See [CLEANUP_SUMMARY_2025.md](../../CLEANUP_SUMMARY_2025.md) for details on the reorganization.

---

## Development Workflow

### Branching Strategy

We use a feature-branch workflow:

1. **Main branches**:
   - `main` - Production-ready code
   - `develop` - Integration branch (if applicable)

2. **Feature branches**:
   - Format: `feature/descriptive-name`
   - Example: `feature/add-course-analytics`

3. **Bug fix branches**:
   - Format: `fix/descriptive-name`
   - Example: `fix/authentication-timeout`

4. **Chore branches**:
   - Format: `chore/descriptive-name`
   - Example: `chore/update-dependencies`

### Workflow Steps

1. **Sync with upstream**:
   ```bash
   git checkout main
   git fetch upstream
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes** following coding standards

4. **Test your changes**:
   ```bash
   # Run tests
   make test
   
   # Run linters
   make lint
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add descriptive commit message"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request** on GitHub

---

## Coding Standards

### General Principles

- Follow [2025 Implementation Standards](../../guides/2025-IMPLEMENTATION-STANDARDS.md)
- Write clean, readable, maintainable code
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Comment complex logic, not obvious code
- Avoid premature optimization

### Python Standards (Backend)

**Style Guide**: PEP 8 + Black formatting

```python
# Good example
from typing import Optional, List
from pydantic import BaseModel

class CourseSchema(BaseModel):
    """Schema for course data validation."""
    
    id: Optional[int] = None
    title: str
    description: str
    tags: List[str] = []
    
    class Config:
        orm_mode = True

async def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Course]:
    """
    Retrieve paginated list of courses.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum records to return
        
    Returns:
        List of Course objects
    """
    return await db.query(Course).offset(skip).limit(limit).all()
```

**Key Points**:
- Use type hints for all function parameters and returns
- Use `async/await` for I/O operations
- Follow Black formatting (line length: 88)
- Use Pydantic for data validation
- Document all public APIs with docstrings

**Tools**:
```bash
# Format code
black apps/backend/

# Sort imports
isort apps/backend/

# Type checking
mypy apps/backend/

# Linting
ruff check apps/backend/
```

### TypeScript/React Standards (Frontend)

**Style Guide**: ESLint + Prettier

```typescript
// Good example
import React, { useState, useEffect } from 'react';
import { Course } from '@/types/database';
import { fetchCourses } from '@/services/api';

interface CourseListProps {
  userId: string;
  onCourseSelect?: (course: Course) => void;
}

export const CourseList: React.FC<CourseListProps> = ({ 
  userId, 
  onCourseSelect 
}) => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const data = await fetchCourses(userId);
        setCourses(data);
      } catch (error) {
        console.error('Failed to load courses:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCourses();
  }, [userId]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="course-list">
      {courses.map(course => (
        <CourseCard 
          key={course.id} 
          course={course}
          onClick={() => onCourseSelect?.(course)}
        />
      ))}
    </div>
  );
};
```

**Key Points**:
- Use TypeScript for all new code
- Use functional components with hooks
- Proper prop typing with interfaces
- Use Mantine UI components (not Material-UI)
- Follow React best practices (memo, useCallback, etc.)

**Tools**:
```bash
# Lint and fix
npm run lint:fix

# Type check
npm run type-check

# Format
npm run format
```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

**Examples**:
```bash
feat(courses): add course analytics dashboard
fix(auth): resolve JWT token expiration issue
docs(api): update authentication endpoint documentation
chore(deps): update dependencies to latest versions
```

---

## Testing Guidelines

### Test Coverage Goals

- **Overall**: 80% coverage target
- **Current**: ~40% (we're working on it!)
- **Critical paths**: 100% coverage required

### Writing Tests

**Backend (pytest)**:
```python
# tests/test_courses.py
import pytest
from httpx import AsyncClient
from apps.backend.main import app

@pytest.mark.asyncio
async def test_get_courses():
    """Test retrieving course list."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/courses")
        
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_create_course(auth_headers):
    """Test course creation with authentication."""
    course_data = {
        "title": "Test Course",
        "description": "Test Description"
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/courses",
            json=course_data,
            headers=auth_headers
        )
        
    assert response.status_code == 201
    assert response.json()["title"] == "Test Course"
```

**Frontend (Vitest + React Testing Library)**:
```typescript
// tests/CourseList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { CourseList } from '@/components/CourseList';
import { vi } from 'vitest';

vi.mock('@/services/api', () => ({
  fetchCourses: vi.fn(() => Promise.resolve([
    { id: 1, title: 'Test Course', description: 'Test' }
  ]))
}));

describe('CourseList', () => {
  it('renders course list', async () => {
    render(<CourseList userId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Course')).toBeInTheDocument();
    });
  });
});
```

### Running Tests

```bash
# All tests
make test

# Backend only
pytest

# Frontend only
npm -w apps/dashboard test

# With coverage
pytest --cov=apps/backend --cov-report=html
npm -w apps/dashboard run test:coverage
```

---

## Documentation Standards

### When to Document

- All public APIs and functions
- Complex algorithms or business logic
- Setup and configuration steps
- Architecture decisions
- Breaking changes

### Documentation Types

1. **Code Documentation**:
   - Docstrings for Python functions/classes
   - JSDoc for TypeScript functions
   - Inline comments for complex logic

2. **User Documentation**:
   - Setup guides in `docs/setup/`
   - Feature guides in `docs/guides/`
   - Update `docs/INDEX.md` when adding new docs

3. **API Documentation**:
   - Update `openapi.yaml` for API changes
   - FastAPI auto-generates from docstrings

### Documentation Format

Use Markdown with clear structure:

```markdown
# Title

> Brief description

## Section 1

Content here...

### Subsection

More specific content...

## Examples

\```python
# Code example
def example():
    pass
\```
```

---

## Pull Request Process

### Before Submitting

1. ✅ Code follows style guidelines
2. ✅ All tests pass
3. ✅ New tests added for new features
4. ✅ Documentation updated
5. ✅ Commits follow convention
6. ✅ Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Review Process

1. **Automated checks** must pass:
   - Linting (Black, ESLint)
   - Type checking (MyPy, TypeScript)
   - Tests (pytest, Vitest)
   - Security scanning

2. **Code review** by maintainer:
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Architecture fit

3. **Approval and merge**:
   - At least 1 approval required
   - Squash and merge preferred
   - Delete branch after merge

---

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What should happen

**Screenshots**
If applicable

**Environment**
- OS: [e.g., macOS]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

**Additional context**
Any other information
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of what you want

**Describe alternatives you've considered**
Other solutions considered

**Additional context**
Mockups, examples, etc.
```

---

## Additional Resources

- [Documentation Index](../../INDEX.md) - Complete documentation guide
- [2025 Implementation Standards](../../guides/2025-IMPLEMENTATION-STANDARDS.md) - Detailed coding standards
- [Collaboration Guide](../../guides/COLLABORATION.md) - Team workflows
- [Quick Start Guide](../../setup/QUICK_START_GUIDE.md) - Setup instructions
- [TODO.md](../../TODO.md) - Current priorities and known issues

---

## Questions?

- Check [docs/INDEX.md](../../INDEX.md) for documentation
- Review [TODO.md](../../TODO.md) for known issues
- Open a GitHub issue with label `question`
- Review existing issues and PRs

---

**Thank you for contributing to ToolboxAI!** 🎉

Your contributions help make education better for everyone.
