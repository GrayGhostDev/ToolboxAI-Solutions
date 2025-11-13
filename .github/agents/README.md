# GitHub Copilot Agents - Quick Reference

**Last Updated**: November 13, 2025  
**Location**: `.github/agents/`  
**Documentation**: See `.github/instructions.md` and `CLAUDE.md`

---

## Available Agents

### 1. Issue Resolution Agent
**File**: `my-agent.agent.md`

**Purpose**: Automatically analyze, fix, and resolve repository issues

**Triggers**:
- Issue comments containing keywords: `bug`, `fix`, `resolve`, `error`
- PR labels: `bug`, `fix`, `enhancement`
- Direct invocation: `@copilot resolve this issue`

**Capabilities**:
- Issue analysis and root cause identification
- Bug fix implementation
- Test creation and validation
- Documentation updates
- Conventional commit messages
- PR creation and management

**Best for**:
- Bug fixes
- Issue resolution
- Code improvements
- PR reviews

---

### 2. Backend Development Specialist
**File**: `backend-specialist.agent.md`

**Purpose**: Expert in FastAPI, Python, PostgreSQL, Redis, Celery, LangChain

**Triggers**:
- File paths: `apps/backend/**/*.py`
- PR labels: `backend`, `api`, `database`, `celery`
- Keywords: `fastapi`, `sqlalchemy`, `celery`, `langchain`, `pytest`

**Capabilities**:
- FastAPI endpoint creation with async/await
- SQLAlchemy models and migrations
- Celery task development
- LangChain v1.0 agent implementation
- Pydantic v2 validation
- pytest test writing
- BasedPyright type checking

**Best for**:
- Creating new API endpoints
- Database schema changes
- Background task implementation
- AI agent development
- Backend testing

**Example**:
```
@copilot using backend-specialist create an async FastAPI endpoint
for uploading student assignments with file validation
```

---

### 3. Frontend Development Specialist
**File**: `frontend-specialist.agent.md`

**Purpose**: Expert in React 19, TypeScript, Vite, Mantine UI, Redux

**Triggers**:
- File paths: `apps/dashboard/**/*.{tsx,ts,jsx,js,css}`
- PR labels: `frontend`, `ui`, `dashboard`, `react`
- Keywords: `react`, `mantine`, `typescript`, `redux`, `clerk`, `pusher`

**Capabilities**:
- React 19 functional components
- Mantine UI v8 integration (NOT Material-UI)
- TypeScript strict mode
- Redux Toolkit + RTK Query
- Clerk authentication
- Pusher real-time features
- Vitest + Playwright testing

**Best for**:
- Creating UI components
- State management
- API integration
- Authentication flows
- Real-time features

**Example**:
```
@copilot using frontend-specialist create a Mantine Card component
for displaying student progress with TypeScript interfaces
```

---

### 4. AI Agent Development Specialist
**File**: `ai-agent-specialist.agent.md`

**Purpose**: Expert in LangChain v1.0, LangGraph, OpenAI GPT-4, multi-agent systems

**Triggers**:
- File paths: `apps/backend/agents/**/*.py`
- PR labels: `ai`, `agents`, `langchain`, `llm`
- Keywords: `langchain`, `langgraph`, `openai`, `gpt`, `agent`, `llm`

**Capabilities**:
- LangChain v1.0 agent development (NOT v0.x)
- LangGraph workflow orchestration
- Custom tool creation
- Prompt engineering
- Vector store integration (Supabase pgvector)
- LangSmith tracing and debugging
- Token optimization

**Best for**:
- Creating new AI agents
- Designing agent workflows
- Building custom tools for agents
- Optimizing prompts
- Debugging agent behavior

**Example**:
```
@copilot using ai-agent-specialist create a LangGraph workflow
for multi-agent content review with feedback loop
```

---

### 5. DevOps & Infrastructure Specialist
**File**: `devops-specialist.agent.md`

**Purpose**: Expert in Docker, TeamCity, Render, Vercel, Supabase deployment

**Triggers**:
- File paths: `infrastructure/**/*`, `.github/workflows/**/*`, `*.Dockerfile`, `docker-compose*.yml`
- PR labels: `infrastructure`, `deployment`, `docker`, `ci-cd`
- Keywords: `docker`, `teamcity`, `render`, `vercel`, `deployment`

**Capabilities**:
- Docker Compose configuration
- Dockerfile optimization (multi-stage builds)
- TeamCity Cloud pipeline setup
- Render deployment configuration
- Vercel configuration
- Monitoring stack (Prometheus, Grafana, Jaeger)
- Database migrations
- Security scanning

**Best for**:
- Deployment issues
- Docker optimization
- CI/CD pipeline configuration
- Monitoring setup
- Infrastructure changes

**Example**:
```
@copilot using devops-specialist optimize the backend Dockerfile
for faster builds using multi-stage builds
```

---

### 6. Documentation Specialist
**File**: `documentation-specialist.agent.md`

**Purpose**: Expert in technical documentation, API specs, user guides

**Triggers**:
- File paths: `docs/**/*.md`, `*.md`, `openapi.{yaml,json}`
- PR labels: `documentation`, `docs`
- Keywords: `documentation`, `docs`, `readme`, `guide`

**Capabilities**:
- Technical documentation writing
- OpenAPI/Swagger spec creation
- User guide creation (role-specific)
- Code example documentation
- Troubleshooting guides
- Documentation structure maintenance
- Link validation

**Best for**:
- Writing documentation
- Updating API specifications
- Creating user guides
- Fixing broken links
- Organizing documentation

**Example**:
```
@copilot using documentation-specialist create a user guide for
educators on creating and managing quiz content
```

---

## How to Use Agents

### In Code Comments

```python
# @copilot using backend-specialist
# Create an async FastAPI endpoint for bulk quiz import
# with CSV parsing and validation
```

```typescript
// @copilot using frontend-specialist
// Create a Mantine form for editing user profiles
// with validation and error handling
```

### In Pull Requests

```markdown
@copilot using frontend-specialist review this PR and check:
- Proper TypeScript types
- Mantine UI best practices
- Accessibility compliance (WCAG 2.1 AA)
```

### In Issues

```markdown
@copilot using ai-agent-specialist

We need a new agent for analyzing student writing. Requirements:
1. Use GPT-4 for analysis
2. Provide personalized feedback
3. Store results in database
4. Send notifications via Pusher
```

### In GitHub CLI

```bash
# Get suggestions
gh copilot suggest "using backend-specialist create Celery task for email sending"

# Generate code
gh copilot generate "using frontend-specialist create User interface"
```

---

## Agent Selection Guide

| Task | Agent |
|------|-------|
| FastAPI endpoint | Backend Development Specialist |
| React component | Frontend Development Specialist |
| LangChain agent | AI Agent Development Specialist |
| Docker configuration | DevOps & Infrastructure Specialist |
| Writing docs | Documentation Specialist |
| Bug fixes | Issue Resolution Agent |
| Code review | Issue Resolution Agent |
| Database migration | Backend Development Specialist |
| UI state management | Frontend Development Specialist |
| Agent workflow | AI Agent Development Specialist |
| CI/CD pipeline | DevOps & Infrastructure Specialist |
| API documentation | Documentation Specialist |

---

## Best Practices

### 1. Be Specific
```
❌ Bad: "@copilot create a user endpoint"
✅ Good: "@copilot using backend-specialist create an async FastAPI 
         endpoint for user creation with email validation and 
         Clerk authentication"
```

### 2. Provide Context
```
❌ Bad: "@copilot fix the form"
✅ Good: "@copilot using frontend-specialist fix the UserProfile 
         form validation - email field should use Mantine's 
         TextInput with email validator"
```

### 3. Mention Constraints
```
❌ Bad: "@copilot create a new agent"
✅ Good: "@copilot using ai-agent-specialist create a content 
         generation agent using LangChain v1.0 with GPT-4, 
         following the BaseAgent pattern in apps/backend/agents/base.py"
```

### 4. Reference Standards
```
✅ "@copilot using backend-specialist - ensure you use BasedPyright 
    for type checking, NOT mypy"

✅ "@copilot using frontend-specialist - use Mantine UI v8 components, 
    NOT Material-UI"
```

### 5. Test Output
- Always review generated code
- Run tests before committing
- Verify security implications
- Check for compliance with standards

---

## Agent Limitations

1. **Knowledge Cutoff**: Agents have training data up to their cutoff date
2. **Review Required**: Always review generated code for security
3. **Testing Essential**: Test thoroughly before merging to production
4. **Standards Compliance**: Verify code follows repository standards
5. **Complex Tasks**: Break down into smaller, manageable steps

---

## Getting Help

### For Agent Issues
1. Check agent file in `.github/agents/`
2. Review `.github/instructions.md`
3. Check `CLAUDE.md` for agent triggers
4. Create issue with label `copilot-agent`

### For New Agent Requests
1. Identify the domain/specialty needed
2. Create issue with label `copilot-agent-request`
3. Describe the agent's purpose and capabilities
4. Specify trigger conditions

---

## File Locations

```
.github/
├── agents/
│   ├── my-agent.agent.md                    # Issue Resolution
│   ├── backend-specialist.agent.md          # Backend Development
│   ├── frontend-specialist.agent.md         # Frontend Development
│   ├── ai-agent-specialist.agent.md         # AI/ML Development
│   ├── devops-specialist.agent.md           # Infrastructure/DevOps
│   └── documentation-specialist.agent.md    # Documentation
├── instructions.md                          # Main Copilot instructions
└── copilot-autofix.yml                      # Autofix configuration
```

---

## Related Documentation

- **Main Instructions**: `.github/instructions.md`
- **Claude Guide**: `CLAUDE.md`
- **Contributing Guide**: `.github/CONTRIBUTING.md`
- **Agent Development**: `docs/04-implementation/agent-system/`

---

**Last Updated**: November 13, 2025  
**Maintained by**: ToolBoxAI Development Team
