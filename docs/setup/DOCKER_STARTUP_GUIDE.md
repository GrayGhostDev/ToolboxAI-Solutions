# ToolBoxAI Docker Startup Guide

## 🚨 Current Status

The automated Docker startup is experiencing delays. This is likely because:
1. Docker Desktop is not running
2. Docker Desktop is starting up
3. Docker is processing other operations

## ✅ Manual Startup Steps

### Step 1: Verify Docker Desktop is Running

**On macOS:**
1. Open "Docker Desktop" from Applications
2. Wait for the Docker icon in the menu bar to show "Docker Desktop is running"
3. Verify with: `docker ps` in terminal (should show container list, even if empty)

### Step 2: Start the Application

Once Docker is confirmed running, execute:

```bash
cd /Users/grayghostdataconsultants/GrayGhostDataConsultants/Development/ActiveProjects/Development/Cursor/Customers/ToolboxAI-Solutions

# Option A: Use the automated script
./start-application.sh

# Option B: Start services manually
docker compose -f docker-compose.core.yml up -d
```

### Step 3: Monitor Startup Progress

```bash
# Watch all service logs
docker compose -f docker-compose.core.yml logs -f

# Or check specific services
docker compose -f docker-compose.core.yml logs -f backend
docker compose -f docker-compose.core.yml logs -f dashboard
```

### Step 4: Verify Services are Running

```bash
# Check container status
docker compose -f docker-compose.core.yml ps

# Should show:
# - toolboxai-postgres (healthy)
# - toolboxai-redis (healthy)
# - toolboxai-backend (running)
# - toolboxai-dashboard (running)
```

### Step 5: Access the Application

Once all services are running:

- **Dashboard**: http://localhost:5179
- **Backend API**: http://localhost:8009
- **API Documentation**: http://localhost:8009/docs
- **Health Check**: http://localhost:8009/health

## 🔧 Troubleshooting

### If Docker won't start:
```bash
# Check Docker status
docker info

# Restart Docker Desktop (macOS)
# 1. Quit Docker Desktop
# 2. Reopen Docker Desktop
# 3. Wait for it to fully start
```

### If containers fail to build:
```bash
# Clean rebuild
docker compose -f docker-compose.core.yml down -v
docker system prune -f
docker compose -f docker-compose.core.yml build --no-cache
docker compose -f docker-compose.core.yml up -d
```

### If backend fails to start:
```bash
# Check logs
docker logs toolboxai-backend

# Common issues:
# - Database not ready: Wait 10 seconds, restart backend
# - Migration errors: Check DATABASE_URL in .env
# - Port conflict: Check if port 8009 is in use
```

### If dashboard fails to start:
```bash
# Check logs
docker logs toolboxai-dashboard

# Common issues:
# - npm install failing: Rebuild with --no-cache
# - Port conflict: Check if port 5179 is in use
# - Backend not ready: Ensure backend is running first
```

## 📊 What's Configured

Your application is set up with:

✅ **Database**: PostgreSQL 15 (Port 5432)
✅ **Cache**: Redis 7 (Port 6379)
✅ **Backend**: FastAPI with all APIs (Port 8009)
✅ **Dashboard**: React 19 + Mantine (Port 5179)

✅ **Integrations Active**:
- Pusher (Real-time): `${PUSHER_KEY}` on cluster `us2`
- OpenAI API: Configured for AI features
- Anthropic Claude: Available for advanced AI
- Roblox OAuth: Client ID `2214511122270781418`
- Clerk Auth: Available with your keys
- Stripe Payments: Configured
- Supabase: Connected to `jlesbkscprldariqcbvt.supabase.co`

✅ **Feature Flags Enabled**:
- Pusher Real-time Communication
- 3D Features
- Roblox Integration
- Gamification
- Analytics
- COPPA/FERPA/GDPR Compliance

## 🎯 Next Steps After Startup

1. **Verify Backend Health**:
   ```bash
   curl http://localhost:8009/health
   ```

2. **Test Pusher Connection**:
   - Open Dashboard at http://localhost:5179
   - Check browser console for Pusher connection messages

3. **Test Roblox Integration**:
   - Navigate to Roblox section in Dashboard
   - Verify OAuth flow works

4. **Check Database**:
   ```bash
   docker exec -it toolboxai-postgres psql -U eduplatform -d educational_platform_dev
   ```

5. **Monitor Real-time Events**:
   ```bash
   docker logs -f toolboxai-backend | grep -i pusher
   ```

## 📝 Service Dependencies

```
PostgreSQL ──┐
             ├──> Backend API ──> Dashboard
Redis ───────┘                      │
                                    └──> User Browser
```

## 🔄 Quick Commands Reference

```bash
# Start everything
./start-application.sh

# Stop everything
docker compose -f docker-compose.core.yml down

# Restart backend only
docker compose -f docker-compose.core.yml restart backend

# Restart dashboard only
docker compose -f docker-compose.core.yml restart dashboard

# View all logs
docker compose -f docker-compose.core.yml logs -f

# View backend logs only
docker compose -f docker-compose.core.yml logs -f backend

# Check status
docker compose -f docker-compose.core.yml ps

# Rebuild everything
docker compose -f docker-compose.core.yml build --no-cache
docker compose -f docker-compose.core.yml up -d
```

## 🎉 Expected Result

When everything is running successfully, you should see:

```
✅ ToolBoxAI Application Started Successfully!
===========================================

Access Points:
  📊 Dashboard:        http://localhost:5179
  🔌 Backend API:      http://localhost:8009
  📖 API Docs:         http://localhost:8009/docs
  ❤️  Health Check:     http://localhost:8009/health

Service Status:
  🗄️  PostgreSQL:       Port 5432
  🔴 Redis:            Port 6379
  🐍 Backend:          Port 8009
  ⚛️  Dashboard:        Port 5179

Configuration Active:
  🔄 Pusher:           Enabled (us2)
  🤖 OpenAI:           Configured
  🎮 Roblox:           Integrated
  🔐 Clerk:            Available
  💳 Stripe:           Configured
  🗃️  Supabase:         Connected
```

---

**Ready to start?** Simply run: `./start-application.sh`

