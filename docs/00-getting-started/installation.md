# Installation and Setup Guide

This comprehensive guide covers installation and setup for all user types, from end-users accessing the web platform to developers setting up local development environments.

## Table of Contents

- [End-User Setup](#end-user-setup) (Teachers, Students, Administrators)
- [Developer Setup](#developer-setup) (Local development environment)
- [System Requirements](#system-requirements)
- [Network Configuration](#network-configuration)
- [Troubleshooting](#troubleshooting)

## End-User Setup

### Prerequisites

#### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux Ubuntu 18.04+
- **Browser**: Chrome 90+, Firefox 85+, Safari 14+, or Edge 90+
- **RAM**: 4GB minimum, 8GB recommended
- **Internet**: Broadband connection (5+ Mbps download, 1+ Mbps upload)
- **Storage**: 500MB free space for Roblox client

#### Roblox Requirements
- **Roblox Account**: Free account at [roblox.com](https://roblox.com)
- **Roblox Client**: Desktop application (auto-downloaded on first use)
- **Age Verification**: May be required for certain features

### Step 1: Account Setup

#### 1.1 Create ToolBoxAI Account
1. Visit the ToolBoxAI platform URL provided by your organization
2. Click "Sign Up" or "Get Started"
3. Choose your role (Teacher, Student, Administrator)
4. Fill out the registration form:
   ```
   - Full Name
   - Email Address
   - Role/Position
   - Organization/School
   - Grade Level (if student) or Subject Area (if teacher)
   ```
5. Verify your email address
6. Complete initial profile setup

#### 1.2 Link Roblox Account
1. In your ToolBoxAI dashboard, go to "Account Settings"
2. Click "Connect Roblox Account"
3. Sign in to Roblox when prompted
4. Authorize ToolBoxAI to access your Roblox account
5. Verify the connection is successful

### Step 2: Browser Configuration

#### 2.1 Enable Required Features
Ensure your browser has these features enabled:
- **JavaScript**: Required for platform functionality
- **Cookies**: Needed for authentication and preferences
- **Local Storage**: Used for offline features and caching
- **WebSocket Support**: Required for real-time features

#### 2.2 Browser Extensions
**Recommended**: No special extensions required
**Compatible**: Most educational browser extensions work fine
**Incompatible**: Ad blockers may interfere with Roblox integration

#### 2.3 Security Settings
- Allow pop-ups from your ToolBoxAI domain
- Add ToolBoxAI and Roblox domains to trusted sites
- Ensure clipboard access is allowed (for sharing codes)

### Step 3: Roblox Client Setup

#### 3.1 Install Roblox
1. Visit [roblox.com](https://roblox.com)
2. Download and install the Roblox client
3. Sign in to your Roblox account
4. Test the installation by joining any public game

#### 3.2 Configure Roblox Settings
1. Open Roblox settings (gear icon)
2. **Privacy Settings**:
   - Set appropriate privacy level for your organization
   - Enable voice chat if permitted and desired
   - Configure friend requests and messaging
3. **Graphics Settings**:
   - Set to "Auto" for optimal performance
   - Adjust if experiencing lag or performance issues
4. **Audio Settings**:
   - Test microphone and speakers
   - Set appropriate volume levels

### Step 4: Network Configuration (School IT)

#### 4.1 Firewall Configuration
Allow outbound connections to these domains:
```
# ToolBoxAI Platform
*.toolboxai.com
api.toolboxai.com
platform.toolboxai.com

# Roblox Integration
*.roblox.com
*.rbxcdn.com
*.robloxcdn.com

# Real-time Features
pusher.com
*.pusher.com

# CDN and Assets
cloudfront.net
amazonaws.com
```

#### 4.2 Port Requirements
```
# Standard Web Traffic
Port 80 (HTTP)
Port 443 (HTTPS)

# Roblox Client
Port 53640 (UDP) - Roblox client communication
Ports 49152-65535 (TCP/UDP) - Dynamic port range

# WebSocket Connections
Port 443 (WSS) - Secure WebSocket
```

#### 4.3 Content Filtering
- Whitelist Roblox educational content categories
- Allow ToolBoxAI domain and subdomains
- Configure any content filtering to permit educational gaming

## Developer Setup

### Prerequisites

#### Required Software
- **Node.js**: Version 18+ (LTS recommended)
- **Python**: Version 3.11+
- **Git**: Latest version
- **PostgreSQL**: Version 14+
- **Redis**: Version 7+

#### Development Tools (Recommended)
- **VS Code** or **Cursor**: With Python and TypeScript extensions
- **Docker**: For containerized development
- **Postman**: For API testing
- **Roblox Studio**: For Roblox development

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/toolboxai/solutions.git
cd toolboxai-solutions

# Check current branch
git status
# Should show: On branch main
```

### Step 2: Python Environment Setup

#### 2.1 Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Verify activation
which python  # Should point to venv/bin/python
```

#### 2.2 Install Python Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI installed successfully')"
```

### Step 3: Node.js Environment Setup

#### 3.1 Install Node Dependencies
```bash
# Install root dependencies
npm install

# Install dashboard dependencies
cd apps/dashboard
npm install
cd ../..
```

#### 3.2 Verify Node Setup
```bash
# Check Node version
node --version  # Should be 18+

# Check npm version
npm --version

# Test TypeScript compilation
cd apps/dashboard
npm run typecheck
cd ../..
```

### Step 4: Database Setup

#### 4.1 PostgreSQL Installation

**On macOS (using Homebrew)**:
```bash
brew install postgresql
brew services start postgresql
createdb toolboxai_dev
```

**On Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb toolboxai_dev
```

**On Windows**:
1. Download PostgreSQL installer from [postgresql.org](https://postgresql.org)
2. Run installer and follow setup wizard
3. Use pgAdmin or command line to create database

#### 4.2 Redis Installation

**On macOS (using Homebrew)**:
```bash
brew install redis
brew services start redis
```

**On Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**On Windows**:
1. Download Redis from [redis.io](https://redis.io)
2. Extract and run `redis-server.exe`

### Step 5: Environment Configuration

#### 5.1 Create Environment Files

**Backend Configuration** (`.env`):
```bash
# Copy example environment file
cp .env.example .env

# Edit with your specific values
nano .env
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://username:password@localhost/toolboxai_dev
REDIS_URL=redis://localhost:6379

# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Pusher (for real-time features)
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=us2

# JWT Configuration
JWT_SECRET_KEY=your_very_secure_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
```

**Frontend Configuration** (`apps/dashboard/.env.local`):
```bash
# Create frontend environment file
cd apps/dashboard
cp .env.example .env.local

# Edit with your values
nano .env.local
```

Required frontend variables:
```bash
VITE_API_BASE_URL=http://127.0.0.1:8009
VITE_WS_URL=http://127.0.0.1:8009
VITE_ENABLE_WEBSOCKET=true
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
```

### Step 6: Database Migration

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run database migrations
cd apps/backend
alembic upgrade head

# Verify migration
alembic current
cd ../..
```

### Step 7: Start Development Servers

#### 7.1 Start Backend Server
```bash
# In terminal 1
source venv/bin/activate
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8009 --reload
```

#### 7.2 Start Frontend Server
```bash
# In terminal 2
cd apps/dashboard
npm run dev
```

#### 7.3 Verify Setup
1. **Backend**: Visit [http://localhost:8009/docs](http://localhost:8009/docs) for API documentation
2. **Frontend**: Visit [http://localhost:5179](http://localhost:5179) for dashboard
3. **Health Check**: Visit [http://localhost:8009/health](http://localhost:8009/health)

### Step 8: IDE Configuration

#### 8.1 VS Code Setup
1. **Install Extensions**:
   - Python
   - TypeScript and JavaScript
   - Prettier
   - ESLint
   - GitLens

2. **Configure Python Interpreter**:
   - Open Command Palette (Cmd/Ctrl + Shift + P)
   - Type "Python: Select Interpreter"
   - Choose `./venv/bin/python`

3. **Workspace Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## Docker Development Setup (Alternative)

### Prerequisites
- **Docker**: Latest version
- **Docker Compose**: V2+

### Quick Start with Docker
```bash
# Clone repository
git clone https://github.com/toolboxai/solutions.git
cd toolboxai-solutions

# Create environment files
cp .env.example .env
cd apps/dashboard && cp .env.example .env.local && cd ../..

# Start all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Check service status
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps
```

### Docker Services
- **PostgreSQL**: Port 5434
- **Redis**: Port 6381
- **Backend**: Port 8009
- **Frontend**: Port 5179

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core 2.0 GHz
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Network**: Broadband internet connection

### Recommended Requirements
- **CPU**: Quad-core 2.5 GHz or better
- **RAM**: 8GB or more
- **Storage**: 5GB free space (including Roblox)
- **Network**: High-speed broadband (10+ Mbps)

### Platform Support
- **Web Browsers**: Chrome 90+, Firefox 85+, Safari 14+, Edge 90+
- **Operating Systems**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Mobile**: iOS 13+ (Safari), Android 8+ (Chrome)

## Network Configuration

### For School IT Administrators

#### Firewall Rules
```bash
# Allow HTTPS traffic to ToolBoxAI
allow out port 443 to *.toolboxai.com

# Allow Roblox client communication
allow out port 53640 UDP to *.roblox.com
allow out ports 49152-65535 TCP/UDP to *.roblox.com

# Allow WebSocket connections
allow out port 443 WSS to *.toolboxai.com
```

#### Proxy Configuration
If using a proxy server, configure these domains for direct connection:
- `*.toolboxai.com`
- `*.roblox.com`
- `*.rbxcdn.com`

#### Content Filtering
Whitelist these categories in your content filter:
- Educational gaming platforms
- Programming and development tools
- Educational content management systems

## Troubleshooting

### Common Installation Issues

#### Python Issues
**Problem**: `python3: command not found`
**Solution**:
```bash
# On macOS
brew install python3

# On Ubuntu
sudo apt install python3 python3-pip

# On Windows
# Download Python from python.org
```

**Problem**: Virtual environment activation fails
**Solution**:
```bash
# Ensure you're in the right directory
pwd  # Should show your project directory

# Try explicit path
source ./venv/bin/activate

# On Windows
.\venv\Scripts\activate
```

#### Database Connection Issues
**Problem**: `FATAL: database "toolboxai_dev" does not exist`
**Solution**:
```bash
# Create database
createdb toolboxai_dev

# Or using psql
psql -c "CREATE DATABASE toolboxai_dev;"
```

**Problem**: PostgreSQL connection refused
**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Start PostgreSQL if needed
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS
```

#### Node.js Issues
**Problem**: `npm ERR! peer dep missing`
**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem**: TypeScript compilation errors
**Solution**:
```bash
# Check TypeScript version
npx tsc --version

# Reinstall TypeScript
npm install -D typescript@latest

# Clear TypeScript cache
rm -rf node_modules/.cache
```

#### Network and Firewall Issues
**Problem**: Cannot connect to Roblox from school network
**Solution**:
1. Contact IT administrator
2. Request whitelisting of Roblox domains
3. Test connection with our diagnostic tool
4. Consider using mobile hotspot temporarily

**Problem**: WebSocket connections fail
**Solution**:
1. Check browser console for specific errors
2. Verify firewall allows WebSocket connections
3. Test with different browser
4. Contact support with error details

### Performance Issues
**Problem**: Slow page loading or Roblox lag
**Solution**:
1. Check internet connection speed
2. Close unnecessary browser tabs
3. Restart Roblox client
4. Clear browser cache and cookies
5. Update graphics drivers

### Getting Additional Help

#### Documentation Resources
- [Developer Documentation](../07-development/README.md)
- [API Documentation](../03-api/README.md)
- [Troubleshooting Guide](../08-troubleshooting/README.md)

#### Support Channels
- **Email**: support@toolboxai.com
- **Chat**: Available in platform during business hours
- **Forum**: community.toolboxai.com
- **Status Page**: status.toolboxai.com

#### Before Contacting Support
Please gather this information:
1. Operating system and version
2. Browser type and version
3. Error messages (full text or screenshots)
4. Steps to reproduce the issue
5. Network environment (school, home, public Wi-Fi)

---

**Installation Guide Version**: 2.0.0
**Last Updated**: January 2025
**Compatibility**: All supported platforms and browsers

*For the most up-to-date installation instructions, always refer to the online documentation at docs.toolboxai.com*