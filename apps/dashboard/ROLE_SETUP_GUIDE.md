# 🎯 User Role Setup Guide

## Problem Identified

The warning `"No valid role found in user metadata, defaulting to student"` appears because your Clerk users don't have the `role` field set in their `publicMetadata`.

---

## Quick Fix Options

### Option 1: Set Role via Clerk Dashboard (Recommended)

1. **Go to Clerk Dashboard**
   - Visit: https://dashboard.clerk.com
   - Navigate to: Users → [Select User]

2. **Edit User Metadata**
   - Click on the user you want to edit
   - Find "Public metadata" section
   - Click "Edit"

3. **Add Role Field**
   ```json
   {
     "role": "teacher"
   }
   ```
   Replace `"teacher"` with one of:
   - `"admin"` - Administrator
   - `"teacher"` - Teacher
   - `"student"` - Student
   - `"parent"` - Parent

4. **Save Changes**

---

### Option 2: Use the Dev Role Switcher (Development Only)

The app has a built-in development tool at the bottom right corner:

1. **Look for the Role Switcher Badge**
   - Should appear in bottom right corner
   - Only visible in development mode

2. **Click and Select Role**
   - Choose: Admin, Teacher, Student, or Parent
   - Changes save automatically to Clerk

3. **Refresh the Page**
   - Role should now persist

---

### Option 3: Programmatic Setup via API

If you have many users, use Clerk's API:

```bash
# Install Clerk Backend SDK
npm install @clerk/backend

# Set your Clerk Secret Key
export CLERK_SECRET_KEY="sk_test_..."
```

Then create a script:

```typescript
import { clerkClient } from '@clerk/backend';

async function setUserRole(userId: string, role: 'admin' | 'teacher' | 'student' | 'parent') {
  await clerkClient.users.updateUserMetadata(userId, {
    publicMetadata: {
      role: role
    }
  });
}

// Usage
await setUserRole('user_xxxxx', 'teacher');
```

---

## Understanding the Role System

### How Roles Work

1. **Stored in Clerk**: Role is stored in `user.publicMetadata.role`
2. **Synced to Redux**: Automatically synced to Redux store
3. **Controls Access**: Routes and features are filtered by role
4. **Persistent**: Saved across sessions

### Default Behavior

- **No role set?** → Defaults to `student`
- **Invalid role?** → Defaults to `student`
- **First login?** → May need manual role assignment

---

## Setting Up Your First Users

### For Testing (Development)

1. **Sign up test users** at `/sign-up`
2. **Use Dev Role Switcher** to change roles
3. **Test each role's dashboard**

### For Production

1. **Admin user**: Set first user as `admin` via Clerk Dashboard
2. **Invite teachers**: They sign up, you assign `teacher` role
3. **Students/Parents**: Auto-assign or bulk import with roles

---

## Recommended Role Assignment

| User Type | Role | Dashboard Access |
|-----------|------|------------------|
| School Admin | `admin` | Full system access |
| Teachers | `teacher` | Classes, students, grades |
| Students | `student` | Learning materials, assignments |
| Parents | `parent` | Child's progress, reports |

---

## Troubleshooting

### "Still seeing student role after changing"

1. Clear browser cache
2. Sign out completely
3. Sign back in
4. Check Clerk Dashboard to verify role saved

### "Dev Role Switcher not appearing"

1. Ensure you're in development mode
2. Check `.env`: `VITE_APP_ENV=development`
3. Look for the badge at bottom-right corner

### "Cannot update metadata"

1. Check Clerk Secret Key is set
2. Verify user has active session
3. Ensure proper permissions in Clerk Dashboard

---

## Bulk User Setup Script

For setting up multiple users at once:

```typescript
// scripts/setup-user-roles.ts
import { clerkClient } from '@clerk/backend';

const USER_ROLES = [
  { email: 'admin@school.com', role: 'admin' },
  { email: 'teacher1@school.com', role: 'teacher' },
  { email: 'teacher2@school.com', role: 'teacher' },
  { email: 'student1@school.com', role: 'student' },
  // ... add more
];

async function setupRoles() {
  for (const { email, role } of USER_ROLES) {
    try {
      // Find user by email
      const users = await clerkClient.users.getUserList({
        emailAddress: [email]
      });
      
      if (users.length > 0) {
        const user = users[0];
        
        // Update role
        await clerkClient.users.updateUserMetadata(user.id, {
          publicMetadata: { role }
        });
        
        console.log(`✅ Set ${email} → ${role}`);
      } else {
        console.log(`❌ User not found: ${email}`);
      }
    } catch (error) {
      console.error(`Error setting role for ${email}:`, error);
    }
  }
}

setupRoles();
```

Run with:
```bash
npx tsx scripts/setup-user-roles.ts
```

---

## Next Steps

1. ✅ **Set roles for existing users** (via Dashboard or script)
2. ✅ **Test each role's dashboard** (sign in as each role)
3. ✅ **Verify routing works** (check access restrictions)
4. ✅ **Document your role structure** (for your team)

---

## Additional Resources

- [Clerk User Metadata Docs](https://clerk.com/docs/users/metadata)
- [Clerk Backend API](https://clerk.com/docs/reference/backend-api)
- [Role-Based Access Control Guide](ROLE_BASED_AUTH.md)
- [Quick Reference](QUICK_REFERENCE.md)

---

**Status:** ✅ Complete  
**Last Updated:** November 2, 2025  
**Priority:** 🔥 HIGH - Required for proper role-based routing

