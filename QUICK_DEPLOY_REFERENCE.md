# 🚀 ToolBoxAI - Quick Deployment Reference

## Environment Variables Required

### Supabase
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_DATABASE_URL=postgresql://...
```

### Sentry
```bash
# Frontend
VITE_SENTRY_DSN=https://xxx@o123456.ingest.sentry.io/xxx

# Backend
SENTRY_DSN_BACKEND=https://yyy@o123456.ingest.sentry.io/yyy

# CLI
SENTRY_AUTH_TOKEN=sntrys_...
SENTRY_ORG=toolboxai
```

### Vercel
```bash
VERCEL_TOKEN=your_token
VERCEL_ORG_ID=team_xxx
VERCEL_PROJECT_ID=prj_xxx
```

### Render
```bash
RENDER_API_KEY=rnd_xxx
RENDER_SERVICE_ID=srv-xxx
```

---

## Quick Commands

### Deploy All Services
```bash
npm run deploy:all
```

### Deploy Frontend Only
```bash
cd apps/dashboard
vercel --prod
```

### Deploy Backend Only
```bash
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys
```

### Health Check
```bash
./scripts/health-check.sh
```

### Docker Commands
```bash
# Production build
npm run docker:build:prod

# Start services
npm run docker:up:prod

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

---

## URLs

- **Frontend**: https://toolboxai.vercel.app
- **Backend**: https://toolboxai-backend.onrender.com
- **Health**: https://toolboxai-backend.onrender.com/health
- **Sentry**: https://sentry.io/organizations/toolboxai/
- **Render**: https://dashboard.render.com/
- **Vercel**: https://vercel.com/dashboard
- **Supabase**: https://supabase.com/dashboard/

---

## Files Reference

### Configuration
- `apps/dashboard/vercel.json` - Vercel config
- `render.yaml` - Render services config
- `.env.production` - Production environment
- `infrastructure/docker/compose/docker-compose.prod.yml` - Docker production

### Monitoring
- `apps/dashboard/src/config/sentry.ts` - Frontend Sentry
- `apps/backend/config/sentry.py` - Backend Sentry

### Deployment
- `.teamcity/deployment.kts` - CI/CD pipeline
- `scripts/health-check.sh` - Health verification

### Documentation
- `DEPLOYMENT_GUIDE.md` - Full deployment guide
- `DOCKER_VERCEL_RENDER_IMPLEMENTATION.md` - Implementation summary

---

## Troubleshooting

### Backend Issues
```bash
# View logs
render logs toolboxai-backend --tail 100

# Check health
curl https://toolboxai-backend.onrender.com/health
```

### Frontend Issues
```bash
# View deployment logs
vercel logs

# Check browser console
# Open DevTools > Console & Network tabs
```

### Database Issues
```bash
# Test connection
psql $SUPABASE_DATABASE_URL -c "SELECT 1;"

# Check Supabase dashboard
open https://supabase.com/dashboard/
```

---

## Emergency Rollback

### Vercel
```bash
vercel ls
vercel rollback [deployment-url]
```

### Render
```bash
# Via dashboard or API
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys/[deploy-id]/rollback"
```

---

## Support

- **Docs**: `/docs/`
- **Issues**: GitHub Issues
- **Slack**: #deployments
- **Sentry**: Check for errors first

---

**Last Updated**: November 2, 2025

