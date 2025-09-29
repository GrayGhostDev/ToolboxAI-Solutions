# Roblox Rojo Integration Guide

## 🎯 Complete Integration Chain: Dashboard → Backend → Database → Roblox → Frontend → Database → Backend

This guide explains how to set up the complete communication flow from the dashboard user to Roblox Studio using Rojo API for natural language environment creation.

## 🏗️ Architecture Overview

```
Dashboard User → Frontend → Backend API → Rojo API → Roblox Studio
     ↓              ↓           ↓           ↓           ↓
   Natural      React UI    FastAPI    Rojo Server   Roblox
  Language      Component   Endpoints   Integration   Environment
     ↓              ↓           ↓           ↓           ↓
  Description → Service → Database → Project → Generated
     ↓              ↓           ↓           ↓           ↓
   Preview      Validation   Storage    Structure    World
```

## 🔧 Prerequisites

### 1. Roblox Studio Setup
- Install [Roblox Studio](https://create.roblox.com/landing)
- Install [Rojo Plugin](https://rojo.space/docs/installation/)
- Start Roblox Studio with Rojo plugin enabled

### 2. Rojo Installation
```bash
# Install Rojo CLI
npm install -g @rojo/cli

# Verify installation
rojo --version
```

### 3. Backend Dependencies
```bash
# Install required Python packages
pip install aiohttp aiofiles
```

## ⚙️ Configuration

### Backend Configuration

Create environment variables in your backend:

```bash
# Rojo API Configuration
ROJO_ENABLED=true
ROJO_HOST=localhost
ROJO_PORT=34872
ROJO_TIMEOUT=30

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/toolboxai
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=127.0.0.1
API_PORT=8008

# Pusher Configuration (for real-time updates)
PUSHER_ENABLED=true
PUSHER_APP_ID=your_app_id
PUSHER_KEY=your_key
PUSHER_SECRET=your_secret
PUSHER_CLUSTER=us2
```

### Frontend Configuration

Create environment variables in your frontend:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8008

# Pusher Configuration
VITE_PUSHER_KEY=your_key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=http://localhost:8008/pusher/auth

# WebSocket Configuration
VITE_ENABLE_WEBSOCKET=true
```

## 🚀 Setup Instructions

### 1. Start Roblox Studio
1. Open Roblox Studio
2. Create a new place or open existing place
3. Ensure Rojo plugin is installed and active
4. Note the Rojo server port (default: 34872)

### 2. Start Backend Server
```bash
cd apps/backend
python -m uvicorn main:app --host 127.0.0.1 --port 8008 --reload
```

### 3. Start Frontend Dashboard
```bash
cd apps/dashboard
npm install
npm run dev
```

### 4. Verify Rojo Connection
```bash
# Test Rojo API connection
curl http://localhost:34872/api/rojo
```

## 🎮 Usage Flow

### 1. Dashboard User Experience
1. Navigate to `/roblox/create-environment`
2. Fill in environment details:
   - Name: "Math Adventure World"
   - Grade Level: "3-5"
   - Subject: "Mathematics"
   - Description: "Create a math classroom with interactive whiteboards, student desks, and a cozy reading corner with books about numbers and shapes."

### 2. Natural Language Processing
The system parses the description and identifies:
- **Terrain**: Natural features (mountains, forests, water)
- **Buildings**: Structures (classrooms, labs, libraries)
- **Objects**: Furniture and equipment (desks, computers, boards)
- **Lighting**: Ambient conditions (bright, dark, moonlight)
- **Effects**: Environmental effects (rain, snow, fog)

### 3. Rojo Project Generation
The backend creates a Rojo project structure:
```json
{
  "name": "Math Adventure World",
  "tree": {
    "$className": "DataModel",
    "Workspace": {
      "$className": "Workspace",
      "Environment": {
        "$className": "Folder",
        "Buildings": {
          "$className": "Folder",
          "Classroom": {
            "$className": "Model"
          }
        },
        "Objects": {
          "$className": "Folder",
          "Desks": {
            "$className": "Model"
          },
          "Whiteboards": {
            "$className": "Model"
          }
        }
      }
    }
  }
}
```

### 4. Roblox Studio Integration
- Rojo builds the project
- Syncs to Roblox Studio
- Creates the environment in real-time
- Provides Rojo URL for ongoing sync

## 🔌 API Endpoints

### Environment Creation
```http
POST /api/v1/roblox/environment/create
Content-Type: application/json

{
  "name": "Math Adventure World",
  "description": "Create a math classroom with interactive whiteboards...",
  "grade_level": "3-5",
  "subject": "math",
  "max_players": 20
}
```

### Check Rojo Connection
```http
POST /api/v1/roblox/environment/rojo/check
```

### Get Environment Status
```http
GET /api/v1/roblox/environment/status/{environment_name}
```

### List User Environments
```http
GET /api/v1/roblox/environment/list
```

## 🧪 Testing the Integration

### 1. Test Rojo Connection
```bash
# Check if Rojo is running
curl -X POST http://localhost:8008/api/v1/roblox/environment/rojo/check
```

### 2. Test Environment Creation
```bash
curl -X POST http://localhost:8008/api/v1/roblox/environment/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Environment",
    "description": "A simple classroom with desks and a whiteboard",
    "grade_level": "3-5",
    "subject": "math"
  }'
```

### 3. Test Frontend Integration
1. Navigate to `http://localhost:5179/roblox/create-environment`
2. Fill in the form
3. Click "Create Environment"
4. Check Roblox Studio for the generated environment

## 🔄 Real-time Updates

The system uses WebSocket/Pusher for real-time updates:

### Connection Status
- Real-time Rojo connection status
- Environment creation progress
- Error notifications

### Environment Updates
- Live environment status
- Player count updates
- Modification notifications

## 🛠️ Troubleshooting

### Common Issues

#### 1. Rojo Not Connected
**Error**: "Rojo is not running or not accessible"

**Solution**:
- Ensure Roblox Studio is open
- Check Rojo plugin is installed and active
- Verify Rojo server is running on port 34872
- Test connection: `curl http://localhost:34872/api/rojo`

#### 2. Environment Creation Fails
**Error**: "Environment creation failed"

**Solution**:
- Check backend logs for detailed error messages
- Verify Rojo project structure is valid
- Ensure sufficient disk space for temporary files
- Check file permissions

#### 3. Frontend Connection Issues
**Error**: "Failed to create environment"

**Solution**:
- Verify backend server is running on port 8008
- Check CORS configuration
- Verify authentication token is valid
- Check network connectivity

### Debug Mode

Enable debug logging:

```bash
# Backend
export DEBUG=true
export LOG_LEVEL=DEBUG

# Frontend
export VITE_DEBUG_MODE=true
```

## 📊 Monitoring

### Backend Metrics
- Environment creation success rate
- Rojo connection status
- API response times
- Error rates

### Frontend Metrics
- User interaction tracking
- Environment creation attempts
- Success/failure rates
- User satisfaction

## 🔒 Security

### Authentication
- JWT token-based authentication
- Role-based access control (teachers/admins only)
- Session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

## 🚀 Production Deployment

### Environment Variables
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
ROJO_HOST=your-production-host
ROJO_PORT=34872
DATABASE_URL=your-production-database
REDIS_URL=your-production-redis
```

### Scaling Considerations
- Load balancing for multiple Rojo instances
- Database connection pooling
- Redis clustering for session management
- CDN for static assets

## 📈 Future Enhancements

### Planned Features
1. **AI-Powered Parsing**: Advanced NLP for better environment understanding
2. **Template System**: Pre-built environment templates
3. **Collaborative Editing**: Multiple users editing the same environment
4. **Version Control**: Environment versioning and rollback
5. **Asset Library**: Shared asset repository
6. **Performance Optimization**: Faster environment generation
7. **Mobile Support**: Mobile app for environment management

### Integration Opportunities
- **LMS Integration**: Connect with Canvas, Schoology, Google Classroom
- **Assessment Tools**: Built-in quiz and assessment features
- **Analytics**: Detailed usage and learning analytics
- **Parent Portal**: Parent access to student environments

## 📝 Summary

The Roblox Rojo integration provides a complete end-to-end solution for creating educational environments from natural language descriptions. The system:

✅ **Connects Dashboard to Roblox Studio** via Rojo API
✅ **Processes Natural Language** into structured components
✅ **Generates Rojo Projects** automatically
✅ **Creates Environments** in real-time
✅ **Provides Real-time Updates** via WebSocket
✅ **Handles Errors Gracefully** with proper error handling
✅ **Supports Multiple Users** with authentication
✅ **Scales for Production** with proper configuration

The integration is now ready for use! Simply configure your environment variables and start creating educational Roblox environments from natural language descriptions.

---

**Next Steps**:
1. Configure your environment variables
2. Start Roblox Studio with Rojo
3. Test the integration
4. Begin creating educational environments!
