# Clerk Authentication Migration Guide (2025)

## Overview

This guide documents the migration from native JWT authentication to Clerk authentication service for the ToolboxAI platform. The migration was completed on 2025-09-21.

## Migration Components

### 1. Frontend (React + Vite)

#### Dependencies Added
- `@clerk/clerk-react`: ^5.47.0

#### Key Files Created/Modified

##### New Files
- `/apps/dashboard/src/contexts/ClerkAuthContext.tsx` - New auth context using Clerk hooks
- `/apps/dashboard/src/components/auth/ClerkLogin.tsx` - Clerk sign-in component
- `/apps/dashboard/src/components/auth/ClerkSignUp.tsx` - Clerk sign-up component
- `/apps/dashboard/src/components/auth/ClerkProtectedRoute.tsx` - Route protection wrapper

##### Modified Files
- `/apps/dashboard/src/main.tsx` - Wrapped app with ClerkProvider
- `/apps/dashboard/src/App.tsx` - Updated routing to use Clerk components
- `/apps/dashboard/.env.local` - Added Clerk environment variables

#### Environment Variables (Frontend)
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
VITE_CLERK_SIGN_IN_URL=https://casual-firefly-39.accounts.dev/sign-in
VITE_CLERK_SIGN_UP_URL=https://casual-firefly-39.accounts.dev/sign-up
VITE_CLERK_AFTER_SIGN_IN_URL=/dashboard
VITE_CLERK_AFTER_SIGN_UP_URL=/dashboard
VITE_ENABLE_CLERK_AUTH=true
```

### 2. Backend (FastAPI)

#### Dependencies Added
- `python-jose[cryptography]`: 3.3.0
- `httpx`: 0.27.0

#### Key Files Created

##### New Files
- `/apps/backend/api/auth/clerk_auth.py` - Clerk JWT verification module
- `/apps/backend/api/webhooks/clerk_webhooks.py` - Webhook handlers for user lifecycle

#### Backend Configuration
```python
# Clerk JWT verification using JWKS
CLERK_SECRET_KEY=sk_test_3ArqrdCHHmjxHvgtAt2zxr2Znd8L8ziEWUiH8NDI49
CLERK_WEBHOOK_SIGNING_SECRET=whsec_yfJVjj0muO9lOYGyOEMH3cbVBXS7Znct
CLERK_JWKS_URL=https://casual-firefly-39.clerk.accounts.dev/.well-known/jwks.json
CLERK_FRONTEND_API_URL=https://casual-firefly-39.clerk.accounts.dev
```

### 3. Docker Configuration

#### Updated Files
- `/infrastructure/docker/docker-compose.dev.yml` - Added Clerk environment variables
- `/infrastructure/docker/Dockerfile.backend` - Added Clerk dependencies
- `/.env.docker` - Complete Docker environment configuration

#### Docker Environment Setup
```bash
# Use the Docker-specific environment file
docker-compose -f infrastructure/docker/docker-compose.dev.yml --env-file .env.docker up -d
```

### 4. CORS Configuration

Updated `/toolboxai_settings/settings.py` to include Clerk domains:
```python
# Clerk Authentication Domains (2025)
"https://casual-firefly-39.clerk.accounts.dev",
"https://casual-firefly-39.accounts.dev",
"https://clerk.casual-firefly-39.lcl.dev",
"https://accounts.clerk.dev",
```

## Migration Steps

### For Local Development

1. **Install dependencies**
   ```bash
   # Frontend
   cd apps/dashboard
   npm install

   # Backend
   pip install python-jose[cryptography] httpx
   ```

2. **Configure environment**
   ```bash
   # Copy environment templates
   cp apps/dashboard/.env.local.example apps/dashboard/.env.local
   cp .env.example .env

   # Add Clerk credentials to both files
   ```

3. **Start services**
   ```bash
   # Start backend
   cd apps/backend
   uvicorn main:app --host 127.0.0.1 --port 8009 --reload

   # Start frontend
   cd apps/dashboard
   npm run dev
   ```

4. **Test authentication**
   - Navigate to http://localhost:5179/sign-in
   - Create a new account or sign in
   - Verify dashboard access

### For Docker Development

1. **Build containers**
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.dev.yml build
   ```

2. **Start services with Clerk configuration**
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.dev.yml --env-file .env.docker up -d
   ```

3. **Verify health**
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.dev.yml ps
   docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend
   ```

## Authentication Flow

### Sign Up Flow
1. User navigates to `/sign-up`
2. Clerk SignUp component handles registration
3. User metadata (role) set via `unsafeMetadata`
4. Webhook triggers `user.created` event
5. Backend creates local user record
6. User redirected to dashboard

### Sign In Flow
1. User navigates to `/sign-in`
2. Clerk SignIn component handles authentication
3. JWT token issued by Clerk
4. Frontend stores session
5. API requests include Bearer token
6. Backend verifies via JWKS

### Token Verification
```python
# Backend verification process
1. Extract token from Authorization header
2. Fetch JWKS keys from Clerk
3. Verify signature using RS256
4. Extract user claims
5. Map to local user model
```

## Webhook Events

### Supported Events
- `user.created` - New user registration
- `user.updated` - Profile updates
- `user.deleted` - Account deletion
- `session.created` - User login
- `session.ended` - User logout
- `organization.created` - New organization
- `organization.member.created` - User joins org

### Webhook Endpoint
```
POST /api/webhooks/clerk
```

## Migration Checklist

### Frontend
- [x] Install @clerk/clerk-react
- [x] Create ClerkProvider wrapper
- [x] Implement ClerkAuthContext
- [x] Create sign-in/sign-up components
- [x] Add protected routes
- [x] Update App.tsx routing
- [x] Configure environment variables

### Backend
- [x] Install python-jose and httpx
- [x] Create clerk_auth.py module
- [x] Implement JWKS verification
- [x] Create webhook handlers
- [x] Register webhook routes
- [x] Update CORS configuration

### Docker
- [x] Update docker-compose.dev.yml
- [x] Add Clerk env vars to services
- [x] Update backend Dockerfile
- [x] Create .env.docker file
- [x] Test containerized flow

### Testing
- [ ] Test local sign-up flow
- [ ] Test local sign-in flow
- [ ] Test Docker sign-up flow
- [ ] Test Docker sign-in flow
- [ ] Test webhook events
- [ ] Test role-based access

## Rollback Plan

If issues arise, revert to JWT authentication:

1. **Frontend**
   ```bash
   # In App.tsx, change:
   const useClerkAuth = false; // Disable Clerk
   ```

2. **Backend**
   ```python
   # Use backward compatibility function
   from apps.backend.api.auth.clerk_auth import get_current_user_compatible
   ```

3. **Archived Files**
   All original auth files are preserved in:
   ```
   /Archive/2025-09-21/auth/
   ├── frontend/
   │   ├── AuthContext.tsx
   │   ├── Login.tsx
   │   └── Register.tsx
   └── backend/
       ├── auth.py
       ├── password_management.py
       └── websocket_auth.py
   ```

## Troubleshooting

### Common Issues

1. **CORS errors**
   - Verify Clerk domains in CORS_ORIGINS
   - Check browser console for specific domain
   - Add to toolboxai_settings/settings.py

2. **JWT verification fails**
   - Check CLERK_JWKS_URL is accessible
   - Verify CLERK_SECRET_KEY is set
   - Clear JWKS cache if keys rotated

3. **Docker connection issues**
   - Ensure .env.docker is used
   - Check network connectivity
   - Verify service health checks

4. **Webhook failures**
   - Verify CLERK_WEBHOOK_SIGNING_SECRET
   - Check webhook logs in Clerk dashboard
   - Test with curl locally

### Debug Commands

```bash
# Test Clerk webhook endpoint
curl -X POST http://localhost:8009/api/webhooks/clerk \
  -H "Content-Type: application/json" \
  -H "svix-signature: sha256=test" \
  -d '{"type":"user.created","data":{}}'

# Check Docker logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main

# Verify CORS headers
curl -I -X OPTIONS http://localhost:8009/api/v1/auth/login \
  -H "Origin: https://casual-firefly-39.accounts.dev" \
  -H "Access-Control-Request-Method: POST"
```

## Security Considerations

1. **Secret Management**
   - Never commit Clerk keys to repository
   - Use environment variables
   - Rotate keys regularly

2. **CORS Configuration**
   - Only allow necessary Clerk domains
   - Use exact domain matches
   - No wildcard origins in production

3. **Webhook Security**
   - Always verify webhook signatures
   - Use HTTPS in production
   - Implement replay protection

4. **Token Storage**
   - Tokens handled by Clerk SDK
   - No local storage of sensitive data
   - Session management via Clerk

## Production Deployment

### Environment Variables
Set in production environment:
```bash
CLERK_SECRET_KEY=<production-secret>
CLERK_PUBLISHABLE_KEY=<production-key>
CLERK_WEBHOOK_SIGNING_SECRET=<production-webhook-secret>
ENVIRONMENT=production
```

### Database Migration
```sql
-- Add Clerk fields to users table
ALTER TABLE users ADD COLUMN clerk_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
CREATE INDEX idx_users_clerk_id ON users(clerk_id);
```

### Monitoring
- Set up Clerk webhook monitoring
- Configure error tracking (Sentry)
- Monitor authentication metrics
- Track user conversion rates

## Support Resources

- [Clerk Documentation](https://clerk.com/docs)
- [Clerk React SDK](https://clerk.com/docs/quickstarts/react)
- [JWT Verification](https://clerk.com/docs/backend-requests/making/jwt-templates)
- [Webhook Events](https://clerk.com/docs/users/sync-data-to-your-backend)

---

*Migration completed: 2025-09-21*
*Documentation version: 1.0.0*