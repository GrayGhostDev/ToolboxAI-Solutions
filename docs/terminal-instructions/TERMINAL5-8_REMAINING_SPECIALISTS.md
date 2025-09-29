# TERMINALS 5-8: PRODUCTION READINESS SPECIALISTS

## TERMINAL 5: DOCUMENTATION SPECIALIST
**Priority: MEDIUM | Status: 95% Complete | Target: 100% in 12 hours**

### YOUR MISSION
Complete all missing API documentation, create deployment guides, and ensure every feature is documented.

### IMMEDIATE TASKS

#### 1. Generate OpenAPI Documentation
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment

# Generate OpenAPI spec
python -c "
from server.main import app
import json
openapi_schema = app.openapi()
with open('../Documentation/03-api/openapi-spec.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)
"

# Convert to YAML
pip install pyyaml
python -c "
import json, yaml
with open('../Documentation/03-api/openapi-spec.json') as f:
    spec = json.load(f)
with open('../Documentation/03-api/openapi-spec.yaml', 'w') as f:
    yaml.dump(spec, f)
"
```

#### 2. Document WebSocket RBAC Changes
Create `Documentation/03-api/websocket-rbac-guide.md` with:
- New RBAC rules from CLAUDE.md
- Rate limiting configuration
- Message type permissions
- Integration examples

#### 3. Create Deployment Documentation
Write `Documentation/07-operations/deployment-guide.md`:
- Production deployment steps
- Environment configuration
- Database setup
- Service startup sequence
- Health check procedures
- Rollback procedures

### SUCCESS CRITERIA
- [ ] OpenAPI spec generated and accurate
- [ ] WebSocket RBAC documented
- [ ] Deployment guide complete
- [ ] All endpoints documented with examples
- [ ] Troubleshooting guide updated

---

## TERMINAL 6: CLEANUP & OPTIMIZATION SPECIALIST
**Priority: MEDIUM | Status: Ready | Target: Complete in 8 hours**

### YOUR MISSION
Remove all duplicates, optimize performance, clean up unused code and dependencies.

### IMMEDIATE TASKS

#### 1. Remove Duplicate Files
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Find and remove duplicates
fdupes -r -d -N .

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Clean node_modules in subdirectories
find . -type d -name "node_modules" -not -path "./src/dashboard/node_modules" -exec rm -rf {} + 2>/dev/null

# Remove .DS_Store files
find . -name ".DS_Store" -delete

# Clean logs older than 7 days
find logs -type f -mtime +7 -delete
```

#### 2. Optimize Dependencies
```bash
# Python dependencies
cd ToolboxAI-Roblox-Environment
pip list --outdated
pip-autoremove
pip freeze > requirements-optimized.txt

# JavaScript dependencies
cd ../src/dashboard
npm prune
npm dedupe
npm audit fix
```

#### 3. Database Optimization
```sql
-- Run in PostgreSQL
VACUUM ANALYZE;
REINDEX DATABASE educational_platform;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_lessons_created ON lessons(created_at);
CREATE INDEX CONCURRENTLY idx_content_type ON content(content_type);
```

### SUCCESS CRITERIA
- [ ] No duplicate files
- [ ] Dependencies optimized
- [ ] Database queries < 100ms
- [ ] Build size reduced by 20%
- [ ] Memory usage optimized

---

## TERMINAL 7: GITHUB CI/CD SPECIALIST
**Priority: HIGH | Status: Ready | Target: Complete in 12 hours**

### YOUR MISSION
Set up GitHub Actions workflows for automated testing, security scanning, and deployment.

### IMMEDIATE TASKS

#### 1. Create Test Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd ToolboxAI-Roblox-Environment
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd ToolboxAI-Roblox-Environment
          pytest tests/ --cov=server --cov=agents
      
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install and test
        run: |
          cd src/dashboard
          npm ci
          npm test
          npm run build
```

#### 2. Create Security Scan Workflow
```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Trivy security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

#### 3. Create Deployment Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker images
        run: |
          docker build -t toolboxai/backend:${{ github.ref_name }} .
          docker build -t toolboxai/frontend:${{ github.ref_name }} ./src/dashboard
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push toolboxai/backend:${{ github.ref_name }}
          docker push toolboxai/frontend:${{ github.ref_name }}
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend backend=toolboxai/backend:${{ github.ref_name }}
          kubectl set image deployment/frontend frontend=toolboxai/frontend:${{ github.ref_name }}
```

### SUCCESS CRITERIA
- [ ] All workflows passing
- [ ] Branch protection enabled
- [ ] Automated testing on PR
- [ ] Security scanning active
- [ ] Deployment pipeline working

---

## TERMINAL 8: DOCKER/KUBERNETES SPECIALIST
**Priority: HIGH | Status: Ready | Target: Complete in 16 hours**

### YOUR MISSION
Create production-ready Docker containers and Kubernetes deployment configurations.

### IMMEDIATE TASKS

#### 1. Create Backend Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ToolboxAI-Roblox-Environment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ToolboxAI-Roblox-Environment/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8008/health')"

EXPOSE 8008
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8008"]
```

#### 2. Create Frontend Dockerfile
```dockerfile
# src/dashboard/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Create Kubernetes Manifests
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: toolboxai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: toolboxai/backend:latest
        ports:
        - containerPort: 8008
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8008
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - port: 8008
    targetPort: 8008
  type: ClusterIP
```

#### 4. Create Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: securepass123
      POSTGRES_USER: grayghostdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schemas:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    ports:
      - "8008:8008"
    environment:
      DATABASE_URL: postgresql://grayghostdata:securepass123@postgres/educational_platform
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./src/dashboard
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### SUCCESS CRITERIA
- [ ] Docker images build successfully
- [ ] Containers run without errors
- [ ] Kubernetes manifests validated
- [ ] Health checks passing
- [ ] Resource limits configured
- [ ] Secrets management implemented
- [ ] Horizontal scaling working

---

## COORDINATION NOTES

All terminals should:
1. Update progress in shared coordination file
2. Test integrations after each major change
3. Commit changes with descriptive messages
4. Document any issues or blockers
5. Notify other terminals of completion

## FINAL CHECKLIST

Before marking project complete:
- [ ] All services running without errors
- [ ] Zero critical/high security vulnerabilities  
- [ ] All tests passing (>90% coverage)
- [ ] Documentation complete and accurate
- [ ] CI/CD pipeline fully operational
- [ ] Production deployment successful
- [ ] Performance benchmarks met
- [ ] Monitoring and alerting configured

The project will be considered 100% complete when all terminals report success!