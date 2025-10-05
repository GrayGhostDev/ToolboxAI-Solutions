# Roblox Dashboard - Production Deployment Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Build Process](#build-process)
4. [Deployment Options](#deployment-options)
5. [Docker Deployment](#docker-deployment)
6. [Performance Optimization](#performance-optimization)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Logging](#monitoring--logging)
9. [Rollback Procedures](#rollback-procedures)
10. [Troubleshooting](#troubleshooting)

---

## ✅ Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (`npm test`)
- [ ] TypeScript compilation successful (`npm run typecheck`)
- [ ] ESLint passes with 0 warnings (`npm run lint`)
- [ ] Code coverage > 80%
- [ ] Production build succeeds (`npm run build`)

### Security
- [ ] No secrets in code (check with grep)
- [ ] Environment variables properly configured
- [ ] API endpoints use HTTPS
- [ ] CORS configured correctly
- [ ] Content Security Policy (CSP) headers set
- [ ] Dependencies scanned for vulnerabilities

### Performance
- [ ] Bundle size < 500KB (initial load)
- [ ] Lighthouse score > 90
- [ ] Images optimized (WebP format)
- [ ] Code splitting implemented
- [ ] Lazy loading for routes

### Accessibility
- [ ] WCAG 2.1 AA compliance verified
- [ ] Keyboard navigation tested
- [ ] Screen reader compatible
- [ ] Color contrast ratios meet standards

---

## 🔧 Environment Setup

### Required Environment Variables

Create a `.env.production` file:

```bash
# API Configuration
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_API_TIMEOUT=30000

# Feature Flags
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_CLERK_AUTH=false
VITE_ENABLE_3D_FEATURES=true

# Pusher Configuration
VITE_PUSHER_KEY=your-production-pusher-key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/api/pusher/auth

# Analytics (Optional)
VITE_GA_TRACKING_ID=UA-XXXXXXXXX-X
VITE_SENTRY_DSN=https://xxx@sentry.io/xxx

# Build Configuration
VITE_BUILD_TIMESTAMP=$(date +%s)
VITE_VERSION=1.0.0
```

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379

# JWT
JWT_SECRET_KEY=generate-a-secure-random-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Pusher
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=us2

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Debug
DEBUG=false
LOG_LEVEL=info
```

---

## 🏗️ Build Process

### 1. Install Dependencies

```bash
# Navigate to dashboard
cd apps/dashboard

# Install with production flag
npm ci --production=false

# For external drives (if needed)
npm install --no-bin-links --legacy-peer-deps
```

### 2. Run Quality Checks

```bash
# Type checking
npm run typecheck

# Linting
npm run lint

# Tests
npm test

# Build validation
npm run build:validate
```

### 3. Production Build

```bash
# Create optimized production build
npm run build:production

# Analyze bundle size
npm run analyze:bundle

# Preview production build locally
npm run preview:production
```

### 4. Build Output

The build process creates:

```
dist/
├── index.html              # Entry point
├── assets/
│   ├── index-[hash].js    # Main bundle
│   ├── vendor-[hash].js   # Third-party code
│   ├── styles-[hash].css  # Compiled styles
│   └── *.woff2            # Fonts
├── images/                 # Optimized images
└── manifest.json          # PWA manifest
```

---

## 🚀 Deployment Options

### Option 1: Static Hosting (Vercel/Netlify)

#### Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to production
vercel --prod

# Environment variables via dashboard or CLI
vercel env add VITE_API_BASE_URL production
```

**vercel.json**:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

#### Netlify Deployment

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod

# Or use netlify.toml
```

**netlify.toml**:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

### Option 2: AWS S3 + CloudFront

```bash
# Build for production
npm run build

# Sync to S3
aws s3 sync dist/ s3://your-bucket-name/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Option 3: Docker Container

See [Docker Deployment](#docker-deployment) section below.

---

## 🐳 Docker Deployment

### Production Dockerfile

Create `apps/dashboard/Dockerfile.production`:

```dockerfile
# Multi-stage build for optimized production image
FROM node:22-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production=false

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

Create `apps/dashboard/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; connect-src 'self' https: wss:;" always;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss;

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (if backend on same server)
    location /api/ {
        proxy_pass http://backend:8009;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Build and Run Docker Image

```bash
# Build image
docker build -f apps/dashboard/Dockerfile.production \
  -t roblox-dashboard:latest .

# Run container
docker run -d \
  --name roblox-dashboard \
  -p 80:80 \
  --restart unless-stopped \
  roblox-dashboard:latest

# View logs
docker logs -f roblox-dashboard
```

### Docker Compose (Full Stack)

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./apps/dashboard
      dockerfile: Dockerfile.production
    ports:
      - "80:80"
      - "443:443"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    networks:
      - app-network

  backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
    ports:
      - "8009:8009"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    restart: unless-stopped
    networks:
      - app-network
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=roblox_dashboard
      - POSTGRES_USER=roblox
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres-data:
```

---

## ⚡ Performance Optimization

### Bundle Size Optimization

```bash
# Analyze bundle
npm run analyze:bundle

# Check specific imports
npx vite-bundle-visualizer
```

### Code Splitting

```typescript
// Route-based code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));

// Component-based splitting for heavy 3D components
const RobloxCharacterAvatar = lazy(() =>
  import('./components/roblox/RobloxCharacterAvatar')
);
```

### Image Optimization

```bash
# Convert images to WebP
for file in *.png; do
  cwebp -q 80 "$file" -o "${file%.png}.webp"
done

# Optimize SVGs
svgo --multipass *.svg
```

### Caching Strategy

```javascript
// Service Worker caching
// public/sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('roblox-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/assets/index.js',
        '/assets/styles.css'
      ]);
    })
  );
});
```

---

## 🔒 Security Hardening

### Content Security Policy

Add to `index.html`:

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' https://api.yourdomain.com wss://ws.yourdomain.com;
">
```

### Environment Variable Validation

```typescript
// src/config/env.ts
const requiredEnvVars = [
  'VITE_API_BASE_URL',
  'VITE_PUSHER_KEY',
  'VITE_PUSHER_CLUSTER'
];

requiredEnvVars.forEach((varName) => {
  if (!import.meta.env[varName]) {
    throw new Error(`Missing required environment variable: ${varName}`);
  }
});
```

### Dependency Security

```bash
# Audit dependencies
npm audit

# Fix vulnerabilities
npm audit fix

# Check for outdated packages
npm outdated
```

---

## 📊 Monitoring & Logging

### Application Monitoring

```typescript
// src/services/monitoring.ts
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay()
  ]
});
```

### Performance Monitoring

```typescript
// src/services/performance.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify(metric);
  fetch('/api/analytics', { method: 'POST', body });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### Logging Best Practices

```typescript
// Production logging
if (import.meta.env.PROD) {
  console.log = () => {};  // Disable console.log
  console.debug = () => {};
  // Keep console.error and console.warn
}
```

---

## 🔄 Rollback Procedures

### Quick Rollback

```bash
# Vercel
vercel rollback

# Netlify
netlify rollback

# Docker
docker stop roblox-dashboard
docker rm roblox-dashboard
docker run -d --name roblox-dashboard roblox-dashboard:previous-version
```

### Database Rollback

```bash
# Run Alembic downgrade
cd apps/backend
alembic downgrade -1

# Restore from backup
pg_restore -d roblox_dashboard backup.dump
```

---

## 🔧 Troubleshooting

### Build Failures

```bash
# Clear cache and rebuild
rm -rf node_modules dist .vite
npm install
npm run build
```

### Runtime Errors

1. Check browser console for errors
2. Review Sentry error logs
3. Verify environment variables are set
4. Check API connectivity

### Performance Issues

```bash
# Profile bundle
npm run build -- --mode analyze

# Check Lighthouse score
npx lighthouse https://yourdomain.com --view
```

---

## 📝 Post-Deployment Checklist

- [ ] Verify application loads correctly
- [ ] Test all critical user flows
- [ ] Check API connections
- [ ] Verify real-time features (Pusher)
- [ ] Test authentication
- [ ] Confirm analytics tracking
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify CDN cache invalidation
- [ ] Update documentation

---

## 🆘 Support & Resources

- **Documentation**: `/docs` folder
- **Issues**: GitHub Issues
- **Monitoring**: Sentry Dashboard
- **Analytics**: Google Analytics / Mixpanel
- **Status**: https://status.yourdomain.com

---

**Deployment Contact**: devops@yourdomain.com
**Emergency Contact**: on-call@yourdomain.com

---

**Last Updated**: 2025-10-01
**Version**: 1.0.0
**Status**: ✅ Production Ready
