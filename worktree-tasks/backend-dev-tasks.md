# Backend Development Worktree Tasks
**Branch**: development
**Ports**: Backend(8011), Dashboard(5182), MCP(9879), Coordinator(8890)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` before writing ANY code!

**Requirements**:
- ✅ Python 3.12 with type hints
- ✅ FastAPI async endpoints
- ✅ Pydantic v2 models with ConfigDict
- ✅ SQLAlchemy 2.0 async patterns
- ✅ Auto-accept enabled for corrections
- ❌ NO sync-only code or Pydantic v1 patterns

## Primary Objectives
1. **API Development**
   - Build RESTful API endpoints
   - Implement GraphQL schema
   - Add API versioning

2. **Database Optimization**
   - Optimize query performance
   - Add database indexes
   - Implement caching layer

3. **Microservices Architecture**
   - Design service communication
   - Implement message queues
   - Add service discovery

## Current Tasks
- [ ] Review existing API endpoints in `core/api/`
- [ ] Analyze database performance bottlenecks
- [ ] Design new API endpoints for dashboard metrics
- [ ] Implement rate limiting and authentication
- [ ] Add Redis caching for frequent queries
- [ ] Create API documentation with OpenAPI/Swagger
- [ ] Write integration tests
- [ ] Setup API monitoring and logging

## File Locations
- API Routes: `ToolboxAI-Solutions/core/api/routes/`
- Controllers: `ToolboxAI-Solutions/core/api/controllers/`
- Models: `ToolboxAI-Solutions/database/models/`
- Middleware: `ToolboxAI-Solutions/core/middleware/`
- Config: `ToolboxAI-Solutions/config/api.json`

## Technical Stack
- Node.js + Express/Fastify
- PostgreSQL + Redis
- GraphQL (Apollo Server)
- WebSocket (Socket.io)
- Message Queue (Bull/RabbitMQ)

## Commands
```bash
cd ToolboxAI-Solutions
npm run start:backend  # Start backend on port 8011
npm run test:api       # Run API tests
npm run db:migrate     # Run database migrations
npm run db:seed        # Seed test data
npm run docs:api       # Generate API documentation
```
