# TeamCity Cloud Quick Setup Guide

## 🚀 Immediate Actions in TeamCity UI

### Step 1: Login
- **URL**: https://grayghost-toolboxai.teamcity.com
- **Username**: GrayGhostDev
- **Password**: [Your password]

### Step 2: Complete Project Setup

#### If ToolBoxAISolutions project exists:
1. Click on **ToolBoxAISolutions** project
2. Go to **Project Settings** (gear icon)
3. Click **Versioned Settings** in left menu
4. Enable **Synchronization enabled**
5. Select **use settings from VCS**
6. Format: **Kotlin**
7. Click **Apply**

#### If project doesn't exist:
1. Click **+ New Project**
2. Select **From a repository URL**
3. Repository URL: `https://github.com/GrayGhostDev/ToolboxAI-Solutions.git`
4. Select branch: `chore/remove-render-worker-2025-09-20`
5. Click **Proceed**
6. TeamCity will detect `.teamcity/settings.kts`
7. Click **Import settings from Kotlin DSL**

### Step 3: Configure Credentials

1. Go to **Administration** → **Projects** → **ToolBoxAISolutions**
2. Click **Connections**
3. Add new connection:
   - Type: **Docker Registry**
   - Display name: **TeamCity Cloud Registry**
   - Docker registry URL: `build-cloud.docker.com:443`
   - Username: `thegrayghost23`
   - Password: [Your Docker Hub password]
   - Test connection and save

### Step 4: Add Environment Variables

1. Still in Project Settings
2. Click **Parameters**
3. Add these parameters:

| Parameter | Value |
|-----------|-------|
| env.OPENAI_API_KEY | [Your OpenAI key] |
| env.ANTHROPIC_API_KEY | [Your Anthropic key] |
| env.PUSHER_APP_ID | [Your Pusher App ID] |
| env.PUSHER_KEY | [Your Pusher Key] |
| env.PUSHER_SECRET | [Your Pusher Secret] |
| env.PUSHER_CLUSTER | us2 |

### Step 5: Verify Build Configurations

You should see these 6 build configurations:
- ✅ **Dashboard (React + Vite)**
- ✅ **Backend (FastAPI)**
- ✅ **MCP Server**
- ✅ **Agent Coordinator**
- ✅ **Integration Tests**
- ✅ **Deploy to Production**

### Step 6: Run First Build

1. Click on **Dashboard (React + Vite)**
2. Click **Run** button
3. Select branch: `chore/remove-render-worker-2025-09-20`
4. Click **Run Build**

## 📊 Monitor Build Progress

### Build View URLs:
- **All Builds**: https://grayghost-toolboxai.teamcity.com/buildConfiguration/ToolBoxAISolutions_DashboardBuild
- **Build Queue**: https://grayghost-toolboxai.teamcity.com/queue.html
- **Build Log**: Click on running build to see real-time logs

### Expected Build Steps:
1. ✅ Checkout from GitHub
2. ✅ Setup Node.js
3. ✅ Install Dependencies
4. ✅ TypeScript Check (parallel)
5. ✅ Lint Check (parallel)
6. ✅ Unit Tests (parallel)
7. ✅ Build Production
8. ✅ Build Docker Image
9. ✅ Push to Registry

## 🔍 Troubleshooting

### If builds don't appear:
1. Check **Administration** → **Projects** → **ToolBoxAISolutions** → **Versioned Settings**
2. Click **Load project settings from VCS**
3. Check for errors in the settings

### If build fails:
1. Check build log for specific errors
2. Common issues:
   - Missing credentials → Add in Project Parameters
   - Agent not available → Check Cloud Agents status
   - Docker registry auth → Verify connection settings

### Cloud Agent Status:
- Go to **Agents** → **Cloud**
- Should see: `linux-amd64` agent available
- If offline, check cloud configuration

## 🎯 Success Indicators

✅ **Project Created**: ToolBoxAISolutions appears in projects list
✅ **Settings Synced**: 6 build configurations visible
✅ **Agent Connected**: Cloud agent shows as available
✅ **Build Running**: Dashboard build starts and progresses
✅ **Docker Push**: Images appear in registry

## 📱 Pusher Integration

Once builds are running, you'll receive real-time notifications:
- Channel: `dashboard-builds`
- Events: `build-status`

## 🔗 Quick Links

- **Project Overview**: https://grayghost-toolboxai.teamcity.com/project/ToolBoxAISolutions
- **Build Chain**: https://grayghost-toolboxai.teamcity.com/chainResults/ToolBoxAISolutions
- **Docker Registry**: https://build-cloud.docker.com (login as thegrayghost23)
- **GitHub Repo**: https://github.com/GrayGhostDev/ToolboxAI-Solutions

## ⚡ Next Actions After First Build

1. **Trigger Backend Build**: Test Python/FastAPI pipeline
2. **Run Integration Tests**: Validate full stack
3. **Setup Build Triggers**: Configure automatic builds on push
4. **Configure Notifications**: Add Slack/Email alerts
5. **Setup Deployment**: Configure production deployment

---

**Need Help?**
- TeamCity Docs: https://www.jetbrains.com/help/teamcity/
- Cloud Docs: https://www.jetbrains.com/help/teamcity/teamcity-cloud.html