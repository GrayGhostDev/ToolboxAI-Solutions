# Developer Onboarding Guide

Welcome to the ToolboxAI Roblox Environment project! This guide will help you get started with development.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or 3.12
- Node.js 22+ (use `.nvmrc` file)
- PostgreSQL 14+
- Redis 6+
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ToolBoxAI-Solutions
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up Node environment**
   ```bash
   nvm use  # Uses Node version from .nvmrc
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Key environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `REDIS_URL`: Redis connection string
   - `JWT_SECRET_KEY`: Secret for JWT tokens (auto-generated in dev)
   - `OPENAI_API_KEY`: For AI features
   - `PUSHER_*`: For realtime features (replaces WebSocket)
     - `PUSHER_APP_ID`: Pusher application ID
     - `PUSHER_KEY`: Pusher application key
     - `PUSHER_SECRET`: Pusher application secret
     - `PUSHER_CLUSTER`: Pusher cluster (usually 'us2')
   - `STRIPE_*`: For payment processing

## 🏗️ Project Structure

```
ToolBoxAI-Solutions/
├── apps/
│   ├── backend/          # FastAPI server (port 8008)
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core utilities
│   │   ├── models/      # Data models
│   │   └── services/    # Business logic
│   └── dashboard/       # React frontend (port 5179)
│       └── src/         # React source code
├── core/                # Shared core components
│   ├── agents/          # AI agents
│   ├── mcp/            # Model Context Protocol
│   └── sparc/          # SPARC framework
├── database/           # Database models & migrations
├── roblox/             # Roblox scripts & plugins
├── tests/              # Test suites
└── docs/               # Documentation
```

## 🔧 Development Workflow

### Starting Services

1. **Start database and Redis**
   ```bash
   # PostgreSQL
   brew services start postgresql@14  # macOS
   # Or use Docker:
   docker-compose up -d postgres redis
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Start backend server**
   ```bash
   make backend
   # Or manually:
   cd apps/backend
   uvicorn main:app --host 127.0.0.1 --port 8008 --reload
   ```

4. **Start frontend dashboard**
   ```bash
   make dashboard
   # Or manually:
   cd apps/dashboard
   npm run dev
   ```

5. **Access the application**
   - Dashboard: http://localhost:5179
   - API docs: http://localhost:8008/docs
   - Health check: http://localhost:8008/health

### Authentication

The system includes test accounts for development:

| Username | Password | Role |
|----------|----------|------|
| admin | changeme123! | Admin |
| john_teacher | changeme123! | Teacher |
| sarah_student | changeme123! | Student |
| mary_parent | changeme123! | Parent |

**Security Features:**
- JWT tokens with 15-minute expiry
- Refresh tokens in HttpOnly cookies
- OAuth 3.0 compliant token rotation
- Cross-tab authentication sync

### Running Tests

```bash
# All tests
make test

# Python tests only
pytest tests/unit/

# Frontend tests
npm -w apps/dashboard test

# With coverage
pytest --cov=apps.backend tests/unit/
npm -w apps/dashboard run test:coverage
```

### Code Quality

```bash
# Linting
make lint

# Type checking
basedpyright .
npm -w apps/dashboard run typecheck

# Format code
black apps/backend
npm -w apps/dashboard run format
```

## 🔌 Key Features

### 1. Realtime Updates (Pusher)
- Configure Pusher credentials in `.env`
- Channels: `dashboard-updates`, `content-generation`, `agent-status`
- ~~WebSocket fallback available at `/ws/*`~~ **DEPRECATED**: Use Pusher Channels instead

### 2. AI Content Generation
- Endpoint: `POST /api/v1/agents/generate`
- Supports educational content, quizzes, Roblox scripts
- SPARC framework for structured reasoning

### 3. Stripe Integration
- Webhook endpoint: `POST /api/v1/stripe/webhooks`
- Enable with `ENABLE_STRIPE_WEBHOOKS=true`
- Signature validation included

### 4. Roblox Integration
- Content deployment: `POST /api/v1/roblox/deploy/{content_id}`
- Environment sync via Pusher Channels (migrated from WebSocket)
- Rojo integration for live sync

## 🐛 Debugging

### Common Issues

1. **Import errors**
   - Ensure virtual environment is activated
   - Use absolute imports: `from apps.backend.module import ...`

2. **Database connection**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in `.env`

3. **Frontend not connecting**
   - Check CORS settings in backend
   - Verify API_BASE_URL in frontend `.env.local`

4. **Tests failing**
   - Run with verbose output: `pytest -v`
   - Check test database is accessible
   - Some tests require environment flags (see CLAUDE.md)

### Logging

- Backend logs: JSON format to stdout
- Frontend: Browser console
- Test logs: `tests/logs/`

### Development Tools

- **FastAPI Interactive Docs**: http://localhost:8008/docs
- **Redux DevTools**: Install browser extension
- **React DevTools**: Install browser extension
- **Pusher Debug Console**: Set `Pusher.logToConsole = true`

## 📚 Additional Resources

### Documentation
- [CLAUDE.md](./CLAUDE.md) - AI assistant context
- [ROOT_DIRECTORY_ORGANIZATION.md](./ROOT_DIRECTORY_ORGANIZATION.md) - Detailed structure
- [ROBLOX_API_GUIDE.md](../ROBLOX_API_GUIDE.md) - Roblox integration
- [TODO.md](../TODO.md) - Current project status

### Runbooks
- [Local Development](./runbooks/local-dev.md)
- [Deployment](./runbooks/deployment.md)
- [Incident Response](./runbooks/incident-response.md)

### API Documentation
- OpenAPI spec: `/docs/03-api/openapi-spec.json`
- Postman collection: Available on request

## 🤝 Contributing

1. Create feature branch from `main`
2. Follow existing code patterns
3. Add tests for new features
4. Ensure all tests pass
5. Update documentation
6. Submit PR with clear description

### Commit Messages
Follow conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `test:` Test improvements
- `refactor:` Code refactoring

## 📞 Support

- GitHub Issues: Report bugs and request features
- Slack: #toolboxai-dev channel
- Email: dev@toolboxai.com

## 🎯 Next Steps

1. Review the [TODO.md](../TODO.md) for current priorities
2. Pick a task from the backlog
3. Join the daily standup
4. Reach out if you need help!

Welcome aboard! 🚀