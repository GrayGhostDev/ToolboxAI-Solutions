# 🚀 Role-Based Auth - Quick Reference

## User Roles & Routes

| Role | Overview | Key Routes |
|------|----------|-----------|
| 👨‍💼 **Admin** | `/admin/overview` | schools, users, compliance, analytics, integrations |
| 👨‍🏫 **Teacher** | `/teacher/overview` | classes, lessons, assessments, reports, messages |
| 👨‍🎓 **Student** | `/student/overview` | missions, progress, rewards, leaderboard, play |
| 👨‍👩‍👧 **Parent** | `/parent/overview` | progress, reports, messages |

## Setting Roles

### 🎯 Clerk Dashboard (Easiest)
```
Users → Select User → Edit Public Metadata
{ "role": "teacher" }
```

### 💻 Programmatically
```typescript
// During sign-up
await signUp.create({
  emailAddress: 'user@example.com',
  publicMetadata: { role: 'teacher' }
});

// Update existing user
const { updateRole } = useUpdateClerkRole();
await updateRole('teacher');
```

### 🔧 Bulk Setup Script
```bash
export CLERK_SECRET_KEY="sk_..."
node scripts/setup-clerk-roles.js
```

## Testing Roles

### Development Mode
- Bottom-right corner has role switcher widget
- Click role buttons to switch between roles
- Page auto-reloads to apply new route

### Bypass Mode
```env
VITE_BYPASS_AUTH=true
```
Edit `src/store/slices/userSlice.ts` to change default role

## How It Works

```
1. Login → Clerk authenticates
2. Read role from publicMetadata
3. Sync to Redux store
4. RoleBasedRouter redirects to /{role}/overview
5. Sidebar shows role-specific menu
6. Routes protected by RoleGuard
```

## Key Files

| File | Purpose |
|------|---------|
| `src/utils/auth-utils.ts` | Role utility functions |
| `src/hooks/useClerkRoleSync.ts` | Auto-sync Clerk ↔ Redux |
| `src/components/auth/RoleBasedRouter.tsx` | Routing enforcement |
| `src/routes.tsx` | Role-prefixed routes |
| `src/components/layout/Sidebar.tsx` | Role-based navigation |

## Quick Fixes

### Wrong dashboard showing?
→ Check Clerk publicMetadata has correct role

### Sidebar active state wrong?
→ Clear browser cache, verify route paths

### Routes not protecting?
→ Ensure RoleGuard wraps route components

### Default role not working?
→ Check `getUserRoleFromClerk()` in auth-utils.ts

### Redux context error?
→ Ensure Redux Provider wraps all auth providers (see `REDUX_PROVIDER_FIX.md`)

## Documentation

- 📖 Full Guide: `ROLE_BASED_AUTH.md`
- ✅ Implementation Status: `IMPLEMENTATION_SUMMARY.md`
- 🔧 This Quick Reference: `QUICK_REFERENCE.md`

---

**Status:** ✅ Production Ready  
**Default Role:** Student  
**Auto-Redirect:** Enabled  
**Role Sync:** Automatic

