# ToolBoxAI Educational Platform

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-339933?style=flat-square&logo=node.js&logoColor=white)
![React](https://img.shields.io/badge/React-19.1.0-61DAFB?style=flat-square&logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9.2-3178C6?style=flat-square&logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-25.x-2496ED?style=flat-square&logo=docker&logoColor=white)

> **AI-Powered Educational Platform with Roblox Integration**
> Educational content generation and learning management system with real-time features

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 22+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

```bash
# Clone repository
git clone https://github.com/ToolBoxAI-Solutions/toolboxai.git
cd toolboxai

# Python backend setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup (use Docker on external drives)
cd apps/dashboard
npm install --no-bin-links --legacy-peer-deps  # For external drives
cd ../..

# Start services
make docker-dev  # Recommended: Start all services with Docker
# OR
make dev        # Start backend and frontend natively
```

### Access Points
- **Dashboard**: http://localhost:5179
- **API**: http://localhost:8009
- **API Docs**: http://localhost:8009/docs

## 🏗️ Architecture

### Project Structure
```
ToolBoxAI-Solutions/
├── apps/
│   ├── backend/         # FastAPI server (350+ endpoints)
│   └── dashboard/       # React 19 frontend
├── core/               # AI agents & orchestration
│   ├── agents/         # Content generation agents
│   ├── mcp/           # Model Context Protocol
│   └── sparc/         # SPARC reasoning framework
├── database/          # PostgreSQL models & migrations
├── roblox/           # Roblox integration
├── infrastructure/   # Docker & deployment configs
└── tests/           # Test suites
```

### Tech Stack

#### Backend
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL + Redis
- **Authentication**: JWT with RBAC
- **Real-time**: Pusher Channels (migrating from WebSocket)
- **Task Queue**: Celery 5.4
- **AI**: OpenAI GPT-4 integration

#### Frontend
- **Framework**: React 19.1.0 + TypeScript 5.9.2
- **Build Tool**: Vite 6.0.1
- **UI Library**: Mantine v8 (migrated from Material-UI)
- **State Management**: Redux Toolkit
- **Real-time**: Pusher.js

#### Infrastructure
- **Containerization**: Docker with security hardening
- **Orchestration**: Docker Compose / Kubernetes ready
- **CI/CD**: GitHub Actions (23 workflows)
- **Monitoring**: Prometheus + Grafana (ready to deploy)

## 📚 Core Features

### Educational Platform
- AI-powered content generation
- Multi-role support (Admin, Teacher, Student, Parent)
- Interactive lessons and assessments
- Progress tracking and analytics
- Gamification with badges and leaderboards

### Roblox Integration
- Content synchronization with Roblox games
- Asset deployment and management
- Real-time game state updates
- Custom plugin for Roblox Studio

### AI Capabilities
- SPARC reasoning framework
- 8+ specialized AI agents
- Content generation pipeline
- Automated grading and feedback

## 🔧 Development Commands

### Common Tasks
```bash
# Testing
make test                    # Run all tests
pytest                       # Python tests
npm -w apps/dashboard test   # Frontend tests

# Linting & Formatting
make lint                    # Run all linters
black apps/backend          # Format Python
npm -w apps/dashboard run lint:fix  # Fix JS/TS

# Docker Services
make docker-dev             # Start development stack
make docker-monitoring      # Start monitoring stack
make celery-up             # Start Celery workers
make urls                  # Show all service URLs
```

### Database
```bash
# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Access
make db-shell              # PostgreSQL CLI
make redis-cli            # Redis CLI
```

## 🚨 Known Issues & Status

### Current Limitations
- **Test Coverage**: ~40% (target: 80%)
- **Pusher Integration**: Backend complete, frontend 60% done
- **Multi-tenancy**: 70% complete (middleware pending)
- **Error Handling**: 1,439 generic exceptions need fixing

### External Drive Development
- Native binaries (esbuild, Rollup) fail with error -88
- Use Docker or `vite.config.js` instead of `.ts`
- Install with `npm install --no-bin-links --legacy-peer-deps`

### Production Readiness
- ✅ Backend infrastructure complete
- ✅ Security hardening implemented
- ⚠️ Testing coverage needs improvement
- ⚠️ Monitoring not yet deployed
- ⚠️ Documentation needs updates

## 🔐 Security

- JWT authentication with RS256
- Role-based access control (RBAC)
- PII encryption with AES-256-GCM
- GDPR compliance features
- Docker security hardening
- Secret management via environment variables

### Required Environment Variables for Local Scripts

The dashboard startup scripts require these runtime variables:

- VITE_PUSHER_KEY
- VITE_CLERK_PUBLISHABLE_KEY

Export them before running:

```bash
export VITE_PUSHER_KEY={{your_key}}
export VITE_CLERK_PUBLISHABLE_KEY={{your_key}}
```

See SECURITY.md for placeholder conventions and details.

## 📖 Documentation

- [API Documentation](http://localhost:8009/docs) - Interactive Swagger UI
- [Architecture Guide](docs/03-architecture/system-design.md)
- [Development Guide](CLAUDE.md) - AI assistant instructions
- [Deployment Guide](docs/deployment/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

Proprietary - All rights reserved

## 🆘 Support

For issues or questions:
- Check [TODO.md](TODO.md) for known issues
- Review [CLAUDE.md](CLAUDE.md) for development patterns
- Open GitHub issue for bugs

---

**Current Branch**: `chore/remove-render-worker-2025-09-20`
**Version**: Pre-production (70% complete)
**Last Updated**: October 2025