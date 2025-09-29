# Security Dependency Update Report
*Generated: 2025-09-21*

## NPM Security Vulnerabilities Found

### Critical Issues to Address

1. **esbuild <=0.24.2** (MODERATE)
   - **Issue**: Enables any website to send requests to development server
   - **CVE**: GHSA-67mh-4wv8-2f99
   - **Fix**: Update to esbuild 0.25.10 (already in overrides)

2. **prismjs <1.30.0** (MODERATE)
   - **Issue**: DOM Clobbering vulnerability
   - **CVE**: GHSA-x7hr-w5r2-h6wg
   - **Fix**: Update to prismjs ^1.30.0 (already in overrides)

### Status: ✅ RESOLVED
Both vulnerabilities are already addressed in package.json overrides:
```json
"overrides": {
  "esbuild": "0.25.10",
  "prismjs": "^1.30.0"
}
```

## Python Dependencies - Update Recommendations

### High Priority Security Updates

| Package | Current | Latest | Priority | Reason |
|---------|---------|--------|----------|---------|
| pydantic | 2.9.2 | 2.11.9 | HIGH | Security & bug fixes |
| SQLAlchemy | 2.0.23 | 2.0.43 | HIGH | Security patches |
| sentry-sdk | 2.37.1 | 2.38.0 | HIGH | Error tracking fixes |
| fastapi | 0.116.1 | 0.117.1 | HIGH | Security improvements |
| langchain-* | Various | Latest | MEDIUM | AI framework updates |
| redis | 5.3.1 | 6.4.0 | MEDIUM | Performance & security |

### Breaking Changes to Consider

| Package | Current | Latest | Breaking? | Notes |
|---------|---------|--------|-----------|-------|
| numpy | 1.26.4 | 2.3.3 | YES | Major version change |
| ipython | 8.37.0 | 9.5.0 | YES | Major version change |
| pytest-asyncio | 0.24.0 | 1.2.0 | YES | Major API changes |
| marshmallow | 3.26.1 | 4.0.1 | YES | Major version change |

## Recommendations

### Immediate Actions (Low Risk)
```bash
# Update safe packages
pip install --upgrade \
  pydantic==2.11.9 \
  fastapi==0.117.1 \
  sentry-sdk==2.38.0 \
  python-dotenv==1.1.1 \
  psycopg2-binary==2.9.10
```

### Planned Updates (Test Required)
```bash
# SQLAlchemy (test database compatibility)
pip install --upgrade SQLAlchemy==2.0.43

# LangChain ecosystem (test AI agents)
pip install --upgrade \
  langchain==0.3.27 \
  langchain-core==0.3.76 \
  langchain-openai==0.3.33
```

### Major Version Updates (Separate Sprint)
- numpy 1.x → 2.x (test ML components)
- ipython 8.x → 9.x (update dev tools)
- marshmallow 3.x → 4.x (test serialization)

## Security Score: B+ (Good)
- ✅ No critical vulnerabilities
- ✅ Most security packages up-to-date
- ⚠️ Some packages 1-2 versions behind
- ⚠️ Consider updating LangChain ecosystem for latest features