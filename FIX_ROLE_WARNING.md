# 🚨 IMPORTANT: Fix "No Valid Role Found" Warning

## Quick Fix (30 seconds)

The warning `"No valid role found in user metadata, defaulting to student"` means your Clerk users need roles assigned.

### **Fastest Solution: Use Dev Role Switcher**

1. Open the app at http://localhost:5173
2. Look for the **role badge** in the **bottom-right corner**
3. Click it and select your desired role (Admin, Teacher, Student, or Parent)
4. Refresh the page

✅ Done! Your role is now saved.

---

## Alternative: Set Role via Clerk Dashboard

1. Go to https://dashboard.clerk.com
2. Navigate to **Users** → Select your user
3. Click **Public metadata** → **Edit**
4. Add:
   ```json
   {
     "role": "teacher"
   }
   ```
5. Save

---

## Automated Script (Multiple Users)

For setting up many users at once:

```bash
# Set your Clerk Secret Key
export CLERK_SECRET_KEY="sk_test_..."

# List all users and their roles
npm run setup:roles:list

# Set all users without roles to "student"
npm run setup:roles:default

# Or use the interactive script
npm run setup:roles
```

---

## Available Roles

| Role | Access |
|------|--------|
| `admin` | Full system access |
| `teacher` | Classes, students, grades |
| `student` | Learning materials, assignments |
| `parent` | Child progress, reports |

---

## More Information

- **Complete Guide**: [apps/dashboard/ROLE_SETUP_GUIDE.md](apps/dashboard/ROLE_SETUP_GUIDE.md)
- **Documentation**: [apps/dashboard/DOCUMENTATION_INDEX.md](apps/dashboard/DOCUMENTATION_INDEX.md)
- **Quick Reference**: [apps/dashboard/QUICK_REFERENCE.md](apps/dashboard/QUICK_REFERENCE.md)

---

**This is required for role-based routing to work correctly!** 🎯

