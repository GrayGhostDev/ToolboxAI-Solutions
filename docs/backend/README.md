# ToolboxAI Backend

## Overview

The ToolboxAI Backend is a comprehensive FastAPI-based microservice architecture designed for educational content generation and management. The system features a modular monolith with router-based organization, real-time communication capabilities, and extensive AI agent integration.

## Quick Start

### Development Setup
```bash
# Navigate to backend directory
cd apps/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Start database services
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --host 127.0.0.1 --port 8009 --reload
```

### Health Check
```bash
# Verify system is running
curl http://localhost:8009/health

# Check detailed status
curl http://localhost:8009/health/verbose
```

## Architecture

### Key Components
- **FastAPI Application**: Main HTTP server with async support
- **Router System**: Modular endpoint organization
- **Service Layer**: Business logic implementation
- **Agent System**: AI-powered task automation
- **Security Layer**: JWT authentication, CORS, rate limiting
- **Monitoring**: Sentry integration, structured logging
- **Real-time**: Pusher Channels for WebSocket replacement

### Technology Stack
- **Framework**: FastAPI 0.104.1 with Pydantic v2
- **Database**: PostgreSQL with async SQLAlchemy
- **Cache**: Redis for sessions and rate limiting
- **AI Integration**: OpenAI API with LangChain
- **Real-time**: Pusher Channels
- **Monitoring**: Sentry, structured logging
- **Security**: JWT, circuit breakers, rate limiting

## Project Structure

```
apps/backend/
├── main.py                 # FastAPI application entry point
├── core/                   # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── logging.py         # Logging system
│   ├── monitoring.py      # Sentry and metrics
│   ├── circuit_breaker.py # Fault tolerance
│   ├── rate_limiter.py    # Rate limiting
│   └── security/          # Security components
├── api/                   # API layer
│   ├── v1/endpoints/      # Router modules
│   ├── middleware/        # Custom middleware
│   └── webhooks/          # Webhook handlers
├── services/              # Business logic
│   ├── agent_service.py   # AI agent coordination
│   ├── pusher_realtime.py # Real-time communication
│   └── analytics.py       # Analytics processing
├── agents/                # AI agent system
│   ├── agent.py          # Base agent implementation
│   └── content_agent.py  # Content generation
├── models/                # Data models
└── tests/                 # Test suite
```

## Documentation

### 📚 Complete Documentation Suite

#### Core Documentation
- **[🏗️ Architecture Overview](ARCHITECTURE.md)** - System architecture, components, and data flow
- **[🔄 Migration Guide](MIGRATION.md)** - Step-by-step migration procedures and rollback
- **[👨‍💻 Developer Guide](DEVELOPER_GUIDE.md)** - Development workflow, coding standards, and best practices
- **[⚙️ Configuration Guide](CONFIGURATION.md)** - Environment variables, security, and performance tuning
- **[🐛 Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues, debugging, and error resolution

#### Quick References
| Topic | Link | Description |
|-------|------|-------------|
| API Development | [Creating Endpoints](DEVELOPER_GUIDE.md#creating-endpoints) | How to create new API endpoints |
| Service Development | [Service Development](DEVELOPER_GUIDE.md#service-development) | Building business logic services |
| Testing | [Testing Guidelines](DEVELOPER_GUIDE.md#testing-guidelines) | Unit and integration testing |
| Configuration | [Environment Variables](CONFIGURATION.md#environment-variables) | Complete config reference |
| Performance | [Performance Tuning](CONFIGURATION.md#performance-tuning) | Optimization guidelines |
| Security | [Security Configuration](CONFIGURATION.md#security-configuration) | Authentication and authorization |
| Debugging | [Debug Techniques](TROUBLESHOOTING.md#debug-techniques) | Debugging and monitoring |
| Deployment | [Deployment Updates](MIGRATION.md#deployment-updates) | Production deployment |

## Key Features

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Admin, Teacher, Student roles
- **CORS Protection**: Configurable cross-origin security
- **Rate Limiting**: Request throttling and DDoS protection
- **Circuit Breakers**: Fault tolerance and cascade failure prevention

### 🤖 AI Agent System
- **Multi-agent Architecture**: Specialized agents for different tasks
- **Content Generation**: Educational content creation
- **Task Queue Management**: Efficient task distribution
- **Real-time Updates**: Live progress tracking via Pusher
- **Performance Monitoring**: Agent health and metrics tracking

### ⚡ Real-time Communication
- **Pusher Channels**: Modern WebSocket alternative
- **Private Channels**: Secure user-specific communication
- **Event Broadcasting**: System-wide notifications
- **Legacy WebSocket Support**: Backward compatibility

### 📊 Monitoring & Observability
- **Structured Logging**: JSON logs with correlation IDs
- **Sentry Integration**: Error tracking and performance monitoring
- **Health Checks**: Comprehensive system health monitoring
- **Metrics Collection**: Performance and usage analytics

### 🚀 Performance & Scalability
- **Async Operations**: Non-blocking I/O throughout
- **Connection Pooling**: Database and Redis optimization
- **Caching Strategy**: Multi-level caching implementation
- **Resource Management**: Efficient resource utilization

## Development Workflow

### Creating New Features
1. **Plan**: Define requirements and acceptance criteria
2. **Implement**: Follow TDD approach and coding standards
3. **Test**: Write comprehensive unit and integration tests
4. **Review**: Code review and quality checks
5. **Deploy**: Staged deployment with monitoring

### Code Standards
- **Python**: Black formatting, type hints, docstrings
- **API Design**: RESTful patterns, consistent responses
- **Testing**: >80% coverage, unit and integration tests
- **Documentation**: Inline docs and architecture updates

### Testing Strategy
```bash
# Unit tests
pytest apps/backend/tests/unit/ -v

# Integration tests
pytest apps/backend/tests/integration/ -v

# Coverage report
pytest --cov=apps/backend apps/backend/tests/

# Load testing
locust -f scripts/load_test.py --host=http://localhost:8009
```

## Environment Configuration

### Required Environment Variables
```bash
# Core Application
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-super-secret-key

# AI Services
OPENAI_API_KEY=sk-your-openai-key

# Real-time Communication
PUSHER_APP_ID=123456
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### Development vs Production
- **Development**: Debug enabled, verbose logging, permissive CORS
- **Production**: Security hardened, performance optimized, strict monitoring

## Troubleshooting

### Common Issues
1. **Server won't start**: Check port conflicts and dependencies
2. **Database errors**: Verify connection and run migrations
3. **Authentication issues**: Check JWT configuration and tokens
4. **Performance problems**: Monitor connection pools and query performance

### Debug Commands
```bash
# Health check
curl http://localhost:8009/health

# Service status
curl http://localhost:8009/circuit-breakers/status
curl http://localhost:8009/agents/health

# Logs analysis
tail -f logs/app.log | grep ERROR
```

## Support

### Getting Help
1. **Documentation**: Check the comprehensive docs above
2. **Health Checks**: Use built-in diagnostic endpoints
3. **Logs**: Review structured logs for error details
4. **Monitoring**: Check Sentry for error tracking

### Contributing
1. **Read the guides**: Start with [Developer Guide](DEVELOPER_GUIDE.md)
2. **Follow standards**: Use established patterns and conventions
3. **Test thoroughly**: Ensure comprehensive test coverage
4. **Document changes**: Update relevant documentation

---

**Note**: This backend system is designed for scalability, maintainability, and developer productivity. The comprehensive documentation ensures smooth development and operations across all environments.