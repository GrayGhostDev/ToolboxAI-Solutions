# ToolBoxAI API Documentation - Complete Summary

## 📚 Documentation Generated

This directory contains comprehensive API documentation for the ToolBoxAI Educational Platform, covering all 39 endpoint modules and their functionality.

## 📁 Generated Files

### Core Documentation
- **[README.md](./README.md)** - Main overview and navigation
- **[api-reference.md](./api-reference.md)** - Complete endpoint documentation (39 modules)
- **[authentication.md](./authentication.md)** - JWT auth, roles, and security
- **[quick-start.md](./quick-start.md)** - Step-by-step getting started guide

### Technical Specifications
- **[openapi-spec.yaml](./openapi-spec.yaml)** - OpenAPI 3.0 specification
- **[toolboxai-postman.json](./toolboxai-postman.json)** - Postman collection for testing
- **[websocket.md](./websocket.md)** - Real-time WebSocket communication guide

### Reference Guides
- **[error-codes.md](./error-codes.md)** - Comprehensive error handling reference
- **[rate-limiting.md](./rate-limiting.md)** - Rate limits, policies, and optimization

## 🚀 API Overview

### Platform Capabilities
The ToolBoxAI API provides:
- **🤖 AI-Powered Content Generation** - Educational content creation using SPARC framework
- **🎮 Advanced Roblox Integration** - OAuth2, Open Cloud APIs, environment generation
- **📊 Real-time Analytics** - Learning progress tracking and dashboard analytics
- **🎯 Role-Based Access Control** - Admin, Teacher, Student, Parent roles
- **🔄 Live Communication** - WebSockets and Pusher Channels for real-time updates
- **🎨 Gamification System** - Achievements, leaderboards, and rewards
- **🏫 Multi-School Management** - Classroom and district administration
- **💳 Payment Integration** - Stripe-powered subscription processing

### Base URLs
- **Development**: `http://localhost:8009`
- **Staging**: `https://staging-api.toolboxai.com`
- **Production**: `https://api.toolboxai.com`

## 📋 Complete Endpoint Inventory

### 🔐 Authentication & User Management (4 modules)
1. **Authentication** (`/api/v1/auth`) - Login, logout, token refresh
2. **User Management** (`/api/v1/users`) - Basic user operations
3. **Enhanced User Management** (`/api/v1/user-management`) - Advanced user features
4. **Password Management** (`/api/v1/password`) - Password reset and security

### 📚 Educational Content (4 modules)
5. **Educational Content** (`/api/v1/educational-content`) - Content management
6. **Enhanced Content** (`/api/v1/content`) - AI-powered content generation
7. **Lessons** (`/api/v1/lessons`) - Lesson planning and delivery
8. **Assessments** (`/api/v1/assessments`) - Quiz and test management

### 🎮 Roblox Integration (6 modules)
9. **Roblox Core** (`/api/v1/roblox`) - Basic Roblox integration
10. **Roblox AI** (`/api/v1/roblox-ai`) - AI-powered Roblox features
11. **Roblox Integration** (`/api/v1/roblox`) - OAuth2, Open Cloud, Rojo
12. **Enhanced Roblox** (`/api/v1/roblox-integration`) - Advanced features
13. **Roblox Environment** (`/api/v1/roblox-environment`) - 3D environment generation
14. **Roblox Agents** (`/api/v1/roblox-agents`) - Specialized AI agents

### 🤖 AI & Agent Systems (6 modules)
15. **AI Agent Orchestration** (`/api/v1/ai-agents`) - Multi-agent coordination
16. **AI Chat** (`/api/v1/ai-chat`) - Conversational AI assistant
17. **Agent Swarm** (`/api/v1/agent-swarm`) - Swarm intelligence
18. **Orchestrator** (`/api/v1/orchestrator`) - Agent workflow management
19. **Database Swarm** (`/api/v1/database-swarm`) - Database AI agents
20. **Prompt Templates** (`/api/v1/prompt-templates`) - AI prompt management

### 📊 Analytics & Reporting (4 modules)
21. **Analytics** (`/api/v1/analytics`) - Basic analytics and metrics
22. **Advanced Analytics** (`/api/v1/analytics-reporting`) - Real-time dashboards
23. **Reports** (`/api/v1/reports`) - Custom report generation
24. **Progress Tracking** (`/api/v1/progress`) - Student progress monitoring

### 🏫 Organization Management (3 modules)
25. **Schools** (`/api/v1/schools`) - School and district management
26. **Classes** (`/api/v1/classes`) - Classroom management
27. **Admin** (`/api/v1/admin`) - Administrative functions

### 💬 Communication & Real-time (2 modules)
28. **Messages** (`/api/v1/messages`) - Messaging system
29. **Pusher Auth** (`/api/v1/pusher`) - Real-time authentication

### 🎯 System Features (4 modules)
30. **Gamification** (`/api/v1/gamification`) - Achievements and rewards
31. **Compliance** (`/api/v1/compliance`) - Privacy and compliance tools
32. **Privacy** (`/api/v1/privacy`) - Data privacy controls
33. **Dashboard** (`/api/v1/dashboard`) - Dashboard configuration

### 🔧 Integration & Utilities (4 modules)
34. **API Keys** (`/api/v1/api-keys`) - API key management
35. **Mobile** (`/api/v1/mobile`) - Mobile app integration
36. **Integration** (`/api/v1/integration`) - Third-party integrations
37. **Design Files** (`/api/v1/design-files`) - Asset management
38. **Validation** (`/api/v1/validation`) - Data validation services

### 💳 Payment Processing (2 modules)
39. **Stripe Checkout** (`/api/v1/stripe/checkout`) - Payment processing
40. **Stripe Webhooks** (`/api/v1/payments/stripe`) - Payment event handling

## 🔑 Authentication System

### Demo Accounts
```json
{
  "admin": {
    "email": "admin@toolboxai.com",
    "password": "Admin123!",
    "role": "admin"
  },
  "teacher": {
    "email": "jane.smith@school.edu",
    "password": "Teacher123!",
    "role": "teacher"
  },
  "student": {
    "email": "alex.johnson@student.edu",
    "password": "Student123!",
    "role": "student"
  }
}
```

### JWT Token Usage
All authenticated endpoints require:
```bash
Authorization: Bearer <jwt_token>
```

### Role-Based Permissions
- **Admin**: Full system access (10,000 requests/minute)
- **Teacher**: Content creation, class management (5,000 requests/minute)
- **Student**: Content viewing, progress tracking (1,000 requests/minute)

## 🚦 Rate Limiting

### General Limits
- **Unauthenticated**: 100 requests/minute per IP
- **Content Generation**: 50 requests/hour (Teacher/Admin)
- **WebSocket Connections**: 10 concurrent per user
- **API Authentication**: 10 attempts/minute per IP

### Headers
```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4987
X-RateLimit-Reset: 1642771200
X-RateLimit-Type: user
X-RateLimit-Scope: teacher
```

## 🌐 Real-time Communication

### WebSocket Endpoints
- **Content Generation**: `ws://localhost:8009/ws/content/{session_id}`
- **Roblox Environment**: `ws://localhost:8009/ws/roblox`
- **Agent Communication**: `ws://localhost:8009/ws/agent/{agent_id}`
- **Test Echo**: `ws://localhost:8009/ws/native`

### Pusher Channels
- **Dashboard Updates**: `private-dashboard-updates`
- **Content Generation**: `private-content-generation`
- **Agent Status**: `private-agent-status`
- **Public Announcements**: `public`

## 📝 Quick Start Examples

### 1. Basic Authentication & API Call
```bash
# Login
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane.smith@school.edu","password":"Teacher123!"}'

# Use token for API calls
curl -X GET http://localhost:8009/api/v1/classes \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Generate Educational Content
```bash
curl -X POST http://localhost:8009/api/v1/content/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Science",
    "grade_level": "6-8",
    "content_type": "interactive_lesson",
    "learning_objectives": ["Understand the solar system"],
    "environment_theme": "space_station",
    "difficulty": "medium"
  }'
```

### 3. Real-time Progress Monitoring
```javascript
const ws = new WebSocket('ws://localhost:8009/ws/content/gen_abc123');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'Bearer YOUR_JWT_TOKEN'
  }));
};
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'progress_update') {
    console.log(`Progress: ${message.data.progress_percent}%`);
  }
};
```

## 🛠️ Development Tools

### Postman Collection
Import `toolboxai-postman.json` with these environment variables:
- `base_url`: `http://localhost:8009`
- `user_email`: `jane.smith@school.edu`
- `user_password`: `Teacher123!`

### OpenAPI Integration
Use `openapi-spec.yaml` for:
- Code generation (SDKs)
- API documentation tools
- Mock server setup
- Contract testing

## ⚠️ Error Handling

### Common Error Codes
- **401 AUTHENTICATION_REQUIRED**: Missing or invalid JWT token
- **403 INSUFFICIENT_PERMISSIONS**: User role lacks required permissions
- **429 RATE_LIMIT_EXCEEDED**: Request rate limit exceeded
- **400 VALIDATION_ERROR**: Invalid request parameters
- **500 INTERNAL_SERVER_ERROR**: Unexpected server error

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": { "specific": "error information" }
  },
  "metadata": {
    "timestamp": "2025-01-21T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

## 🔧 Integration Patterns

### 1. Content Creation Workflow
Login → Create/Select Class → Generate Content → Monitor Progress → Deploy to Roblox

### 2. Student Progress Monitoring
Authenticate → Get Classes → Fetch Analytics → Track Real-time Updates

### 3. Multi-Agent Content Generation
Start Generation → Monitor Agent Status → Coordinate Dependencies → Collect Results

## 📊 Special Features

### AI Content Generation
- **SPARC Framework Integration**: Structured reasoning for educational content
- **5-Stage Pipeline**: Analysis → Generation → Validation → Personalization → Deployment
- **Real-time Progress**: WebSocket updates throughout generation process

### Roblox Integration
- **OAuth2 Flow**: Secure Roblox account linking
- **Open Cloud APIs**: Direct Roblox platform integration
- **3D Environment Generation**: Automated Roblox world creation
- **Script Generation**: Lua code generation for interactive experiences

### Advanced Analytics
- **Real-time Dashboards**: Live student progress and engagement metrics
- **Predictive Analytics**: Learning outcome predictions
- **Multi-dimensional Reports**: Custom report generation with various filters

## 🎯 Production Considerations

### Security
- HTTPS required in production
- JWT token rotation recommended
- Rate limit monitoring essential
- Input validation on all endpoints

### Performance
- Implement response caching
- Use batch endpoints when available
- Monitor rate limit headers
- Implement request queuing for high-volume operations

### Monitoring
- Track API response times
- Monitor error rates by endpoint
- Set up alerts for rate limit approaching
- Log authentication failures

## 📞 Support & Resources

### Documentation Links
- [Complete API Reference](./api-reference.md)
- [Authentication Guide](./authentication.md)
- [WebSocket Documentation](./websocket.md)
- [Error Code Reference](./error-codes.md)
- [Rate Limiting Guide](./rate-limiting.md)

### Support Channels
- **API Support**: api-support@toolboxai.com
- **Documentation Issues**: Create issue in repository
- **Feature Requests**: Contact product team
- **Emergency Support**: Check `/health` endpoint first

### Additional Resources
- API Status: Check `/health` endpoint
- Rate Limit Monitoring: Response headers
- WebSocket Testing: Use `/ws/native` for connectivity tests
- Postman Collection: Pre-configured requests and environments

---

## 🎉 Getting Started

1. **Choose your environment** (development recommended for testing)
2. **Review the [Quick Start Guide](./quick-start.md)** for step-by-step instructions
3. **Import the [Postman Collection](./toolboxai-postman.json)** for easy testing
4. **Explore the [API Reference](./api-reference.md)** for detailed endpoint documentation
5. **Set up [WebSocket connections](./websocket.md)** for real-time features

**Ready to build amazing educational experiences with AI and Roblox? Let's get started! 🚀**

---

*This documentation was generated on January 21, 2025, covering all 39 API endpoint modules in the ToolBoxAI Educational Platform.*