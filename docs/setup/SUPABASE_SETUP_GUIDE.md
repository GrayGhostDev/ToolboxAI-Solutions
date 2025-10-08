# Supabase Integration Setup Guide

## Overview

This guide walks you through integrating Supabase Cloud as your database provider for ToolboxAI.

## Prerequisites

1. **Docker Desktop** - Must be running
2. **Supabase Account** - Sign up at https://supabase.com
3. **Project Created** - Create a new project in Supabase Dashboard

## Step 1: Get Your Supabase Credentials

1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **Project Settings** (gear icon in sidebar)
4. Click on **API** section:
   - Copy your **Project URL** (looks like: `https://xxxxxxxxxxxxx.supabase.co`)
   - Copy your **anon/public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)
   - Copy your **service_role key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)
5. Click on **Database** section:
   - Copy your **Connection String** (URI format)
   - Use **Transaction** or **Session** mode (recommended for compatibility)

## Step 2: Update Your .env File

Replace the placeholder values in `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-actual-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-anon-key...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-service-role-key...
SUPABASE_JWT_SECRET=your-jwt-secret-from-api-settings

# Database Connection
DATABASE_URL=postgresql://postgres.your-project:[YOUR-PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres

# Frontend (same values)
VITE_SUPABASE_URL=https://your-actual-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-anon-key...
```

**⚠️ IMPORTANT:** Keep your `service_role` key secret! Never commit it to version control.

## Step 3: Initialize Your Database Schema (Optional)

If you need to create tables, you can either:

### Option A: Using Supabase Dashboard (Recommended)

1. Go to **SQL Editor** in Supabase Dashboard
2. Create your tables:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Example: Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add your other tables here...
```

### Option B: Using Alembic Migrations

If you have existing Alembic migrations:

```bash
# Run from your local machine (not inside Docker)
cd apps/backend
alembic upgrade head
```

## Step 4: Start All Services

### Using the Automated Script (Recommended)

```bash
./start-supabase-services.sh
```

This script will:
- ✅ Check Docker is running
- ✅ Verify .env configuration
- ✅ Create Docker network
- ✅ Stop conflicting services (local PostgreSQL)
- ✅ Start all services in the correct order
- ✅ Test all endpoints
- ✅ Display service URLs

### Manual Startup

If you prefer manual control:

```bash
# Create network
docker network create toolboxai-network

# Stop any existing containers
docker compose -f docker-compose.complete.yml down

# Start services in order
docker compose -f docker-compose.complete.yml up -d redis
sleep 15
docker compose -f docker-compose.complete.yml up -d backend
sleep 20
docker compose -f docker-compose.complete.yml up -d dashboard mcp-server coordinator
docker compose -f docker-compose.complete.yml up -d prometheus grafana
```

## Step 5: Verify Everything is Running

### Check Service Status

```bash
docker compose -f docker-compose.complete.yml ps
```

Expected output - all services should show "Up":
```
NAME                    STATUS
toolboxai-redis         Up (healthy)
toolboxai-backend       Up (healthy)
toolboxai-dashboard     Up
toolboxai-mcp           Up
toolboxai-coordinator   Up
toolboxai-prometheus    Up
toolboxai-grafana       Up
```

### Test Endpoints

```bash
# Test Redis
docker exec toolboxai-redis redis-cli ping
# Expected: PONG

# Test Backend API
curl http://localhost:8009/health
# Expected: {"status":"healthy",...}

# Test Dashboard (in browser)
open http://localhost:5179
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:5179 | Main application UI |
| **Backend API** | http://localhost:8009 | REST API endpoints |
| **API Docs** | http://localhost:8009/docs | Swagger/OpenAPI UI |
| **Health Check** | http://localhost:8009/health | Service health status |
| **MCP Server** | http://localhost:8010 | Model Context Protocol |
| **Coordinator** | http://localhost:8888 | Agent coordination |
| **Prometheus** | http://localhost:9090 | Metrics monitoring |
| **Grafana** | http://localhost:3001 | Dashboards (admin/admin) |
| **Supabase** | https://supabase.com/dashboard | Database management |

## Troubleshooting

### Services Won't Start

1. **Check Docker is running:**
   ```bash
   docker info
   ```

2. **Check for port conflicts:**
   ```bash
   lsof -i :5432 -i :6380 -i :8009 -i :5179
   ```

3. **View service logs:**
   ```bash
   docker compose -f docker-compose.complete.yml logs backend
   docker compose -f docker-compose.complete.yml logs dashboard
   ```

### Backend Can't Connect to Supabase

1. **Verify credentials in .env:**
   ```bash
   grep SUPABASE .env
   ```

2. **Test connection from terminal:**
   ```bash
   # Install psql if needed: brew install postgresql
   psql "your-database-url-from-env"
   ```

3. **Check Supabase project status:**
   - Go to Supabase Dashboard
   - Ensure project is active (not paused)

### Dashboard Shows Blank Page

1. **Dashboard takes time to compile (30-60 seconds on first start)**
2. **Check dashboard logs:**
   ```bash
   docker compose -f docker-compose.complete.yml logs dashboard -f
   ```
3. **Wait for message:** `ready in XXX ms`
4. **Refresh browser:** http://localhost:5179

### Port 5432 Already in Use

You have local PostgreSQL running. Since we're using Supabase, stop it:

```bash
# Homebrew PostgreSQL
brew services stop postgresql
brew services stop postgresql@16

# Or find and kill the process
lsof -i :5432
kill -9 <PID>
```

## Useful Commands

```bash
# View all logs
docker compose -f docker-compose.complete.yml logs -f

# View specific service logs
docker compose -f docker-compose.complete.yml logs -f backend

# Restart a service
docker compose -f docker-compose.complete.yml restart backend

# Stop all services
docker compose -f docker-compose.complete.yml down

# Stop and remove volumes
docker compose -f docker-compose.complete.yml down -v

# Rebuild a service
docker compose -f docker-compose.complete.yml build backend
docker compose -f docker-compose.complete.yml up -d backend

# Check service status
docker compose -f docker-compose.complete.yml ps

# Execute command in container
docker exec -it toolboxai-backend bash
docker exec -it toolboxai-redis redis-cli
```

## Benefits of Supabase Integration

✅ **No Local PostgreSQL Management** - Cloud-hosted, automatically backed up
✅ **Built-in Authentication** - Row Level Security (RLS) and JWT support  
✅ **Real-time Subscriptions** - Live data updates via websockets
✅ **Storage & CDN** - File uploads with automatic CDN distribution
✅ **Edge Functions** - Serverless functions at the edge
✅ **Visual Database Editor** - Easy table management via Supabase Studio
✅ **Automatic Backups** - Point-in-time recovery included
✅ **Scalability** - Automatically scales with your needs

## Next Steps

1. ✅ Configure your Supabase credentials
2. ✅ Start all services
3. 📝 Create your database schema in Supabase Dashboard
4. 🔐 Set up authentication rules (Row Level Security)
5. 🚀 Start building your application!

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

If you encounter issues:
1. Check the logs: `docker compose -f docker-compose.complete.yml logs -f`
2. Review this guide's Troubleshooting section
3. Check Supabase project status in Dashboard
4. Verify all environment variables are set correctly

