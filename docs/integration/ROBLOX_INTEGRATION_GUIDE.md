# Roblox Studio Integration Guide

## Overview

This guide covers the complete integration between ToolboxAI Educational Platform and Roblox Studio, enabling AI-powered educational content generation directly within Roblox environments.

## Rojo Server Configuration

**ToolboxAI-Solutions uses Rojo server at `localhost:34872`**

The Rojo server is configured to run on localhost port 34872 for all ToolboxAI-Solutions projects. This is the default port for Roblox Studio integration.

## Architecture Components

### 1. Backend Services
- **OAuth2 Authentication Service** (`apps/backend/services/roblox_auth.py`)
  - Implements Roblox OAuth2 with PKCE flow (2025 standards)
  - Secure token management with refresh capabilities

- **Open Cloud API Client** (`apps/backend/services/open_cloud_client.py`)
  - Complete Open Cloud API v2 implementation
  - Asset management, DataStore operations, messaging service

- **Rojo Manager** (`apps/backend/services/rojo_manager.py`)
  - Enhanced Rojo 7.5.1 integration
  - Multi-project support with automatic port allocation

- **Conversation Flow Manager** (`apps/backend/core/prompts/enhanced_conversation_flow.py`)
  - 8-stage conversation system with LCEL chains
  - AI-guided content generation

### 2. API Endpoints
- **Authentication**
  - `POST /api/v1/roblox/auth/initiate` - Start OAuth2 flow
  - `GET /api/v1/roblox/auth/callback` - OAuth2 callback
  - `POST /api/v1/roblox/auth/refresh` - Refresh access token
  - `POST /api/v1/roblox/auth/revoke` - Revoke tokens

- **Conversation Flow**
  - `POST /api/v1/roblox/conversation/start` - Begin 8-stage process
  - `POST /api/v1/roblox/conversation/input` - Process user input
  - `POST /api/v1/roblox/conversation/advance` - Move to next stage
  - `POST /api/v1/roblox/conversation/generate` - Generate environment

- **Rojo Management**
  - `GET /api/v1/roblox/rojo/check` - Check Rojo installation
  - `GET /api/v1/roblox/rojo/projects` - List projects
  - `POST /api/v1/roblox/rojo/project/{id}/start` - Start sync
  - `POST /api/v1/roblox/rojo/project/{id}/stop` - Stop sync
  - `POST /api/v1/roblox/rojo/project/{id}/build` - Build project

- **Open Cloud Operations**
  - `POST /api/v1/roblox/assets/upload` - Upload assets
  - `POST /api/v1/roblox/datastore/set` - Set DataStore entry
  - `GET /api/v1/roblox/datastore/get` - Get DataStore entry
  - `POST /api/v1/roblox/messaging/publish` - Publish messages

### 3. Dashboard Components
- **RobloxConversationFlow** (`apps/dashboard/src/components/roblox/RobloxConversationFlow.tsx`)
  - Interactive 8-stage UI with real-time updates
  - Progress tracking and stage visualization

- **RobloxStudioConnector** (`apps/dashboard/src/components/roblox/RobloxStudioConnector.tsx`)
  - Rojo connection management
  - OAuth2 flow initiation

- **EnvironmentPreview** (`apps/dashboard/src/components/roblox/EnvironmentPreview.tsx`)
  - 3D preview of generated environment
  - Interactive editing capabilities

### 4. Roblox Studio Plugin
- **AIContentGenerator2025** (`roblox/plugins/AIContentGenerator2025.lua`)
  - OAuth2 authentication
  - Conversation flow UI
  - Environment building tools
  - Real-time sync with backend

## Setup Instructions

### Prerequisites
1. **Roblox Studio** (latest version)
2. **Rojo Extension** (7.5.1 or later)
3. **Node.js** (v18+) and **Python** (3.11+)
4. **PostgreSQL** and **Redis** running
5. **Pusher account** for real-time features

### Backend Setup

1. **Environment Variables**
   Create `.env` file in project root:
   ```bash
   # Roblox OAuth2
   ROBLOX_CLIENT_ID=your-client-id
   ROBLOX_CLIENT_SECRET=your-client-secret

   # Open Cloud API
   ROBLOX_API_KEY=your-api-key
   ROBLOX_UNIVERSE_ID=your-universe-id

   # Pusher
   PUSHER_APP_ID=your-app-id
   PUSHER_KEY=your-key
   PUSHER_SECRET=your-secret
   PUSHER_CLUSTER=your-cluster

   # Database
   DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev
   REDIS_URL=redis://localhost:6379

   # OpenAI
   OPENAI_API_KEY=your-openai-key
   ```

2. **Install Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start Backend**
   ```bash
   uvicorn apps.backend.main:app --host 127.0.0.1 --port 8008 --reload
   ```

### Dashboard Setup

1. **Environment Variables**
   Create `apps/dashboard/.env.local`:
   ```bash
   VITE_API_BASE_URL=http://127.0.0.1:8008
   VITE_PUSHER_KEY=your-pusher-key
   VITE_PUSHER_CLUSTER=your-cluster
   VITE_PUSHER_AUTH_ENDPOINT=/api/v1/pusher/auth
   ```

2. **Install Dependencies**
   ```bash
   cd apps/dashboard
   npm install
   ```

3. **Start Dashboard**
   ```bash
   npm run dev
   ```

### Roblox Studio Setup

1. **Install Rojo**
   - Install Rojo extension from VS Code marketplace
   - Or download from [GitHub Releases](https://github.com/rojo-rbx/rojo/releases)

2. **Install Plugin**
   - Open Roblox Studio
   - Navigate to Plugins → Manage Plugins
   - Click "Install from File"
   - Select `roblox/plugins/AIContentGenerator2025.lua`

3. **Configure Plugin**
   - Open plugin from Plugins toolbar
   - Click "Settings"
   - Enter backend URL: `http://127.0.0.1:8008`
   - Authenticate with OAuth2

## Usage Workflow

### 1. Authentication
1. Open Roblox Studio plugin
2. Click "Connect to ToolboxAI"
3. Browser opens for OAuth2 authorization
4. Grant permissions
5. Return to Studio - connection established

### 2. Content Generation Flow

#### Stage 1: Greeting & Introduction
- Plugin presents welcome message
- User selects educational level

#### Stage 2: Discovery Questions
- AI asks about learning objectives
- User describes desired outcomes

#### Stage 3: Requirements Gathering
- Specific content requirements
- Age group and complexity

#### Stage 4: Personalization
- Teaching style preferences
- Cultural considerations

#### Stage 5: Content Design
- AI proposes environment structure
- User reviews and adjusts

#### Stage 6: Uniqueness Enhancement
- Add special features
- Interactive elements

#### Stage 7: Validation
- Review complete specification
- Confirm generation

#### Stage 8: Generation & Review
- Environment builds in Studio
- Real-time progress via Pusher
- Final adjustments available

### 3. Environment Management

#### Connecting to Rojo Server (ToolboxAI-Solutions at localhost:34872)

1. **Start Rojo Server**
   ```bash
   # The server runs on localhost:34872 for ToolboxAI-Solutions
   rojo serve generated_projects/[project_id]/default.project.json --port 34872
   ```

2. **Connect from Roblox Studio**
   ```lua
   -- In Roblox Studio command bar
   local HttpService = game:GetService("HttpService")
   local ROJO_SERVER = "http://localhost:34872"  -- ToolboxAI-Solutions Rojo server
   local response = HttpService:GetAsync(ROJO_SERVER .. "/")
   print("Connected to ToolboxAI-Solutions Rojo server:", response)
   ```

3. **Using Rojo Plugin**
   - Open Roblox Studio
   - Click on Rojo plugin icon
   - Enter server address: `localhost:34872`
   - Click "Connect"
   - You should see "Connected to ToolboxAI-Solutions project"

#### Manual Asset Upload
```python
# Using Python client
from apps.backend.services.open_cloud_client import OpenCloudAPIClient

client = OpenCloudAPIClient()
await client.create_asset(
    asset=AssetDescription(
        assetType="Model",
        displayName="Educational Model",
        description="Generated by AI"
    ),
    file_content=model_bytes
)
```

## Real-time Features

### Pusher Channels
- `roblox-conversation-{session_id}` - Conversation updates
- `roblox-generation-{session_id}` - Generation progress
- `roblox-sync-{project_id}` - Rojo sync status

### Event Types
```typescript
// Conversation Events
interface ConversationEvent {
  type: 'stage_changed' | 'input_processed' | 'generation_started';
  data: {
    stage: string;
    progress: number;
    message: string;
  };
}

// Generation Events
interface GenerationEvent {
  type: 'asset_created' | 'script_generated' | 'environment_built';
  data: {
    assetId: string;
    assetType: string;
    status: 'success' | 'error';
  };
}
```

## API Examples

### Starting Conversation
```typescript
const response = await fetch('http://127.0.0.1:8008/api/v1/roblox/conversation/start', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    initial_message: 'I want to create a math learning environment'
  })
});

const { session_id, pusher_channel } = await response.json();

// Subscribe to updates
const channel = pusher.subscribe(pusher_channel);
channel.bind('stage_changed', (data) => {
  console.log('New stage:', data.stage);
});
```

### Generating Environment
```typescript
const response = await fetch(`http://127.0.0.1:8008/api/v1/roblox/conversation/generate?session_id=${sessionId}`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const { project_id, rojo_port, files_generated } = await response.json();
console.log(`Generated ${files_generated} files, Rojo on port ${rojo_port}`);
```

## Testing

### Unit Tests
```bash
# Backend tests
pytest tests/unit/roblox/

# Dashboard tests
cd apps/dashboard
npm test
```

### Integration Tests
```bash
# With environment flags
RUN_ROJO_TESTS=1 pytest tests/integration/test_roblox_flow.py
```

### E2E Tests
```bash
# Full flow test
python tests/e2e/test_roblox_generation.py
```

## Troubleshooting

### Common Issues

#### OAuth2 Connection Failed
- Check `ROBLOX_CLIENT_ID` and `ROBLOX_CLIENT_SECRET`
- Verify redirect URI matches configuration
- Check Roblox app permissions

#### Rojo Sync Not Working
- Ensure Rojo is installed: `rojo --version`
- Check port availability: `lsof -i :34872`
- Verify project path exists

#### Generation Fails
- Check OpenAI API key is valid
- Verify database connections
- Review logs: `tail -f logs/generation.log`

#### Pusher Not Connecting
- Verify Pusher credentials
- Check CORS configuration
- Test with Pusher debug console

### Debug Mode
Enable detailed logging:
```python
# In apps/backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks
```bash
# Check all services
curl http://127.0.0.1:8008/health

# Check Rojo
curl http://127.0.0.1:8008/api/v1/roblox/rojo/check

# Check Pusher
curl http://127.0.0.1:8008/api/v1/pusher/status
```

## Security Considerations

1. **OAuth2 Security**
   - PKCE flow prevents authorization code interception
   - Tokens stored encrypted in database
   - Automatic token refresh before expiry

2. **API Security**
   - Rate limiting on all endpoints
   - JWT authentication required
   - CORS restricted to allowed origins

3. **Data Protection**
   - User data encrypted at rest
   - SSL/TLS for all communications
   - Regular security audits

## Performance Optimization

1. **Caching Strategy**
   - Redis caching for frequent queries
   - Asset CDN for generated content
   - Conversation state in memory

2. **Async Operations**
   - All I/O operations async
   - Background tasks for generation
   - Concurrent asset uploads

3. **Resource Management**
   - Connection pooling for database
   - Rojo process lifecycle management
   - Automatic cleanup of old projects

## Monitoring

### Metrics to Track
- OAuth2 success rate
- Conversation completion rate
- Generation time per stage
- Rojo sync reliability
- Asset upload success rate

### Logging
- Structured JSON logging
- Correlation IDs for request tracking
- Error aggregation with Sentry

## Future Enhancements

1. **Planned Features**
   - Multi-user collaboration
   - Version control for environments
   - Template library
   - AI learning from user feedback

2. **Integration Expansions**
   - Unity support
   - Minecraft Education Edition
   - VR/AR platforms

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review error messages in dashboard console
3. Consult API documentation at `/docs`
4. Contact support with correlation ID

## Version History

- **v2.0.0** (2025-09) - Complete Roblox integration with 8-stage flow
- **v1.5.0** (2025-08) - Pusher migration from Socket.IO
- **v1.0.0** (2025-07) - Initial release

---

*Last Updated: September 2025*
*Documentation Version: 2.0.0*