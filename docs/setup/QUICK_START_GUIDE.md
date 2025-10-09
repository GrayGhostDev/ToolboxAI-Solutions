# Ensure postgres is running
docker compose -f docker-compose.complete.yml ps postgres

# Restart postgres
docker compose -f docker-compose.complete.yml restart postgres

# Wait a few seconds, then try again
sleep 5
```

---

## 📊 Health Checks

### Quick Health Check
```bash
# Check all endpoints
curl http://localhost:8009/health
curl http://localhost:5179
curl http://localhost:9090/-/healthy
```

### Detailed Service Check
```bash
# Backend API
curl http://localhost:8009/health | jq

# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq
```

---

## 🔐 Security Notes

### For Development:
- ✅ Default credentials are fine
- ✅ Use localhost URLs
- ✅ CORS is permissive

### For Production:
- ⚠️ Change all default passwords
- ⚠️ Use strong JWT secret (32+ characters)
- ⚠️ Configure proper CORS origins
- ⚠️ Enable HTTPS with SSL certificates
- ⚠️ Use a secrets manager (Vault, AWS Secrets Manager)
- ⚠️ Enable rate limiting
- ⚠️ Configure Sentry for error tracking

---

## 📚 Next Steps

After getting the application running:

1. **Review the Complete Application Review**: `APPLICATION_REVIEW_2025.md`
2. **Set up TeamCity CI/CD**: See `infrastructure/teamcity/README.md`
3. **Configure monitoring**: See `DEPLOYMENT_GUIDE.md`
4. **Run tests**: `docker compose exec backend pytest`
5. **Explore API**: http://localhost:8009/docs

---

## 🆘 Getting Help

- **Documentation**: See `/docs` folder
- **API Reference**: http://localhost:8009/docs
- **Issues**: Check logs with `docker compose logs`
- **Review Guide**: `APPLICATION_REVIEW_2025.md`

---

## 🎯 Development Workflow

### Making Changes to Backend
```bash
# Backend auto-reloads with uvicorn --reload
# Just edit files in apps/backend/ and save

# Run tests
docker compose exec backend pytest tests/

# Check code quality
docker compose exec backend black apps/backend/
docker compose exec backend mypy apps/backend/
```

### Making Changes to Dashboard
```bash
# Dashboard auto-reloads with Vite HMR
# Just edit files in apps/dashboard/src/ and save

# Run tests
docker compose exec dashboard npm test

# Build for production
docker compose exec dashboard npm run build
```

---

## ✅ Verification Checklist

After starting the application, verify:

- [ ] All containers are running (8 services)
- [ ] Dashboard loads at http://localhost:5179
- [ ] API docs accessible at http://localhost:8009/docs
- [ ] Health check returns 200: `curl http://localhost:8009/health`
- [ ] No errors in logs: `docker compose logs`
- [ ] Database is accessible
- [ ] Redis is responding
- [ ] Prometheus is collecting metrics
- [ ] Grafana is accessible

---

**Ready to go! 🎉**

Start the application now:
```bash
./validate-env.sh && docker compose -f docker-compose.complete.yml up -d
```
# 🚀 ToolBoxAI Quick Start Guide

**Last Updated**: October 6, 2025  
**Status**: Ready for Deployment

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ Docker Desktop installed and running
- ✅ Docker Compose v2.0+
- ✅ At least 8GB RAM available
- ✅ 10GB free disk space
- ✅ Ports available: 5179, 8009, 5432, 6379, 9090, 3001

---

## ⚡ Quick Start (3 Steps)

### Step 1: Configure Environment Variables

```bash
# Copy the .env.example to .env
cp .env.example .env

# Edit .env and fill in your API keys
nano .env  # or use your preferred editor
```

**Required Variables to Fill In:**
```bash
# Pusher (Get from https://dashboard.pusher.com)
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret

# OpenAI (Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key

# JWT Secret (Generate a random string)
JWT_SECRET_KEY=your-secure-random-key
```

### Step 2: Validate Configuration

```bash
# Run the validation script
./validate-env.sh
```

This will check that all required environment variables are set.

### Step 3: Start the Application

```bash
# Start all services
docker compose -f docker-compose.complete.yml up -d

# Watch the logs
docker compose -f docker-compose.complete.yml logs -f
```

---

## 🌐 Access the Application

Once all services are running (takes ~2-3 minutes):

- **Dashboard**: http://localhost:5179
- **API Documentation**: http://localhost:8009/docs
- **API Health Check**: http://localhost:8009/health
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

---

## 🔧 Common Commands

### Check Service Status
```bash
docker compose -f docker-compose.complete.yml ps
```

### View Logs
```bash
# All services
docker compose -f docker-compose.complete.yml logs -f

# Specific service
docker compose -f docker-compose.complete.yml logs -f backend
docker compose -f docker-compose.complete.yml logs -f dashboard
```

### Stop Services
```bash
docker compose -f docker-compose.complete.yml down
```

### Restart a Service
```bash
docker compose -f docker-compose.complete.yml restart backend
```

### Run Database Migrations
```bash
docker compose -f docker-compose.complete.yml exec backend \
  python -m alembic upgrade head
```

### Access Database
```bash
docker compose -f docker-compose.complete.yml exec postgres \
  psql -U eduplatform -d educational_platform_dev
```

---

## 🐛 Troubleshooting

### Dashboard not loading?
```bash
# Check if dashboard is running
docker compose -f docker-compose.complete.yml ps dashboard

# Check logs for errors
docker compose -f docker-compose.complete.yml logs dashboard

# Restart dashboard
docker compose -f docker-compose.complete.yml restart dashboard
```

### API returning 500 errors?
```bash
# Check backend logs
docker compose -f docker-compose.complete.yml logs backend

# Check database connection
docker compose -f docker-compose.complete.yml exec backend \
  python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); print('Connected!' if engine.connect() else 'Failed')"
```

### Port already in use?
```bash
# Find what's using the port (e.g., 8009)
lsof -i :8009

# Kill the process
kill -9 <PID>
```

### Database connection refused?
```bash

