# ToolBoxAI API Documentation

## Overview

The ToolBoxAI API provides comprehensive functionality for educational content generation, Roblox integration, AI-powered learning experiences, and platform management. This documentation covers all 39 API endpoint modules with detailed specifications, examples, and integration guides.

## Documentation Structure

- **[API Reference](./api-reference.md)** - Complete endpoint documentation
- **[OpenAPI Specification](./openapi-spec.yaml)** - Machine-readable API spec
- **[Postman Collection](./toolboxai-postman.json)** - Testing collection
- **[Authentication Guide](./authentication.md)** - Auth flows and security
- **[WebSocket Guide](./websocket.md)** - Real-time communication
- **[Quick Start](./quick-start.md)** - Getting started examples
- **[Error Reference](./error-codes.md)** - Error codes and handling
- **[Rate Limiting](./rate-limiting.md)** - Usage limits and policies

## API Categories

### 🔐 Authentication & User Management
- **Authentication** (`/api/v1/auth`) - Login, logout, token refresh
- **User Management** (`/api/v1/users`) - User CRUD operations
- **Enhanced User Management** (`/api/v1/user-management`) - Advanced user features
- **Password Management** (`/api/v1/password`) - Password reset and security

### 📚 Educational Content
- **Educational Content** (`/api/v1/educational-content`) - Content management
- **Enhanced Content** (`/api/v1/content`) - AI-powered content generation
- **Lessons** (`/api/v1/lessons`) - Lesson planning and delivery
- **Assessments** (`/api/v1/assessments`) - Quiz and test management

### 🎮 Roblox Integration
- **Roblox Core** (`/api/v1/roblox`) - Basic Roblox integration
- **Roblox AI** (`/api/v1/roblox-ai`) - AI-powered Roblox features
- **Roblox Integration** (`/api/v1/roblox`) - OAuth2, Open Cloud, Rojo
- **Enhanced Roblox** (`/api/v1/roblox-integration`) - Advanced features
- **Roblox Environment** (`/api/v1/roblox-environment`) - 3D environment generation
- **Roblox Agents** (`/api/v1/roblox-agents`) - Specialized AI agents

### 🤖 AI & Agent Systems
- **AI Agent Orchestration** (`/api/v1/ai-agents`) - Multi-agent coordination
- **AI Chat** (`/api/v1/ai-chat`) - Conversational AI
- **Agent Swarm** (`/api/v1/agent-swarm`) - Swarm intelligence
- **Orchestrator** (`/api/v1/orchestrator`) - Agent workflow management
- **Database Swarm** (`/api/v1/database-swarm`) - Database AI agents
- **Prompt Templates** (`/api/v1/prompt-templates`) - AI prompt management

### 📊 Analytics & Reporting
- **Analytics** (`/api/v1/analytics`) - Basic analytics
- **Advanced Analytics** (`/api/v1/analytics-reporting`) - Real-time dashboards
- **Reports** (`/api/v1/reports`) - Report generation
- **Progress Tracking** (`/api/v1/progress`) - Student progress

### 🏫 Organization Management
- **Schools** (`/api/v1/schools`) - School and district management
- **Classes** (`/api/v1/classes`) - Classroom management
- **Admin** (`/api/v1/admin`) - Administrative functions

### 💬 Communication & Real-time
- **Messages** (`/api/v1/messages`) - Messaging system
- **Pusher Auth** (`/api/v1/pusher`) - Real-time authentication
- **WebSockets** (`/ws/*`) - Real-time communication

### 🎯 System Features
- **Gamification** (`/api/v1/gamification`) - Achievements and rewards
- **Compliance** (`/api/v1/compliance`) - Privacy and compliance
- **Privacy** (`/api/v1/privacy`) - Data privacy controls
- **Dashboard** (`/api/v1/dashboard`) - Dashboard configuration

### 🔧 Integration & Utilities
- **API Keys** (`/api/v1/api-keys`) - API key management
- **Mobile** (`/api/v1/mobile`) - Mobile app integration
- **Integration** (`/api/v1/integration`) - Third-party integrations
- **Design Files** (`/api/v1/design-files`) - Asset management
- **Validation** (`/api/v1/validation`) - Data validation

### 💳 Payment Processing
- **Stripe Checkout** (`/api/v1/stripe/checkout`) - Payment processing
- **Stripe Webhooks** (`/api/v1/payments/stripe`) - Payment events

## Base URL

- **Production**: `https://api.toolboxai.com`
- **Staging**: `https://staging-api.toolboxai.com`
- **Development**: `http://localhost:8009`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

```bash
Authorization: Bearer <jwt_token>
```

See [Authentication Guide](./authentication.md) for detailed information.

## Rate Limiting

- **Standard**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user
- **Premium**: 10,000 requests per minute per user

See [Rate Limiting Guide](./rate-limiting.md) for details.

## Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "metadata": {
    "timestamp": "2025-01-21T10:00:00Z",
    "request_id": "req_123456",
    "version": "1.0.0"
  }
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes and detailed error information:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "metadata": {
    "timestamp": "2025-01-21T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

## Getting Started

1. **Obtain API credentials** from the dashboard
2. **Authenticate** using the login endpoint
3. **Make your first request** to test connectivity
4. **Explore the documentation** for specific endpoints

See [Quick Start Guide](./quick-start.md) for step-by-step instructions.

## Support

- **Documentation**: This comprehensive guide
- **API Status**: Check system status at `/health`
- **Rate Limits**: Monitor usage in response headers
- **Community**: Join our developer community

---

**Last Updated**: January 21, 2025
**API Version**: v1.0.0
**Documentation Version**: 2.0.0