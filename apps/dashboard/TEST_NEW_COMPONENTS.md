# Testing New Dashboard Components

## Quick Start Guide

### 1. Start Development Server

```bash
cd apps/dashboard
npm run dev
```

The dashboard will be available at `http://localhost:5173`

---

## Component Testing Checklist

### ✅ Layout Transitions (Sidebar)

**Test Steps:**
1. Open dashboard
2. Click the hamburger menu (☰) in top-left
3. **Expected**: Sidebar should smoothly slide in/out over 300ms
4. **Look for**: No content jumping, smooth animation

**Status**: ⬜ Pass / ⬜ Fail

---

### ✅ Breadcrumbs Navigation

**Test Steps:**
1. Navigate to different pages (e.g., `/lessons`, `/classes`, `/settings`)
2. **Expected**: Breadcrumb trail appears showing: `Home > Lessons`
3. Click on breadcrumb links
4. **Expected**: Navigation works correctly

**Pages to Test:**
- `/` - No breadcrumbs (home page)
- `/lessons` - `Home > Lessons`
- `/classes` - `Home > Classes`
- `/analytics` - `Home > Analytics`

**Status**: ⬜ Pass / ⬜ Fail

---

### ✅ Command Palette (Cmd+K)

**Test Steps:**
1. Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)
2. **Expected**: Search modal opens
3. Type "lessons" in search
4. **Expected**: Actions like "View Lessons", "Create New Lesson" appear
5. Click an action
6. **Expected**: Navigate to that page

**Test Different Roles:**
- Admin: Should see "Manage Users", "Analytics", "Compliance"
- Teacher: Should see "Create Lesson", "My Classes"
- Student: Should see "Missions", "Play", "Rewards"

**Status**: ⬜ Pass / ⬜ Fail

---

### ✅ Page Transitions

**Test Steps:**
1. Navigate between pages (use sidebar or command palette)
2. **Expected**: Smooth fade/slide animation between pages
3. **Duration**: ~300ms

**Test Routes:**
- Home → Lessons → Classes → Home

**Status**: ⬜ Pass / ⬜ Fail

---

### ✅ Mobile Responsiveness

**Test Steps:**
1. Open Chrome DevTools (F12)
2. Click "Toggle Device Toolbar" (mobile icon)
3. Select "iPhone 14 Pro" or "iPad"
4. **Test Sidebar:**
   - Click menu button
   - **Expected**: Sidebar appears with dark overlay
   - Click overlay or navigation item
   - **Expected**: Sidebar closes automatically

**Breakpoints to Test:**
- 768px and below - Mobile overlay mode
- 769px and above - Desktop persistent mode

**Status**: ⬜ Pass / ⬜ Fail

---

### ✅ New Components Usage Examples

#### MetricCard

Add to any dashboard page:

```tsx
import { MetricCard } from '@/components/cards';
import { IconUsers } from '@tabler/icons-react';

<MetricCard
  icon={<IconUsers size={24} />}
  label="Active Students"
  value={142}
  trend={{ value: 12, direction: 'up', label: 'vs last week' }}
  color="blue"
  onClick={() => navigate('/students')}
/>
```

#### EmptyState

Add to list views when no data:

```tsx
import { EmptyState } from '@/components/feedback';
import { IconSchool } from '@tabler/icons-react';

{lessons.length === 0 ? (
  <EmptyState
    icon={<IconSchool size={40} />}
    title="No lessons yet"
    description="Create your first lesson to start teaching"
    action={{
      label: "Create Lesson",
      onClick: () => setCreateLessonOpen(true)
    }}
  />
) : (
  <LessonsList lessons={lessons} />
)}
```

#### LoadingButton

Replace existing buttons:

```tsx
import { LoadingButton } from '@/components/common/LoadingButton';
import { IconSave } from '@tabler/icons-react';

<LoadingButton 
  loading={isSaving}
  success={saveSuccess}
  successMessage="Saved!"
  onClick={handleSave}
  leftSection={<IconSave size={16} />}
>
  Save Changes
</LoadingButton>
```

---

## Visual Regression Testing

### Before/After Comparisons

**Sidebar Toggle:**
- Before: ⬜ Content jumps immediately
- After: ✅ Smooth 300ms transition

**Navigation:**
- Before: ⬜ No breadcrumbs, unclear location
- After: ✅ Clear breadcrumb trail

**Page Changes:**
- Before: ⬜ Instant, jarring
- After: ✅ Smooth fade/slide

**Mobile:**
- Before: ⬜ Sidebar covers content, hard to close
- After: ✅ Overlay appears, auto-closes

---

## Performance Checks

### Lighthouse Audit

```bash
# Run in Chrome DevTools
1. Open dashboard
2. F12 → Lighthouse tab
3. Select "Desktop" or "Mobile"
4. Click "Analyze page load"
```

**Target Scores:**
- Performance: > 90
- Accessibility: > 95
- Best Practices: > 90
- SEO: > 90

### Check for Console Errors

Open Console (F12) and verify:
- ⬜ No red errors
- ⬜ No warning about layout shifts
- ⬜ No React warnings
- ⬜ Command Palette hotkey logs (expected)

---

## Browser Compatibility

Test in multiple browsers:

- ⬜ Chrome (latest)
- ⬜ Firefox (latest)
- ⬜ Safari (latest)
- ⬜ Edge (latest)

**Features to verify:**
- Sidebar transitions
- Cmd+K shortcut
- Page transitions
- Mobile overlay

---

## Known Limitations

1. **TypeScript Warnings**: Pre-existing TS errors in codebase (not from new components)
2. **Command Palette Search**: Currently searches action labels only (no fuzzy search yet)
3. **Breadcrumbs**: Don't support dynamic routes like `/classes/:id` yet
4. **Page Transitions**: May flicker briefly on slow connections

---

## Success Criteria

✅ All 5 core features working:
- [x] Smooth sidebar transitions
- [x] Breadcrumbs navigation
- [x] Command palette (Cmd+K)
- [x] Page transitions
- [x] Mobile responsiveness

✅ No new console errors introduced
✅ Lighthouse accessibility score > 95
✅ Works on all major browsers
✅ Smooth animations (no jank)

---

## Troubleshooting

### Sidebar doesn't close on mobile
**Fix**: Verify `useMediaQuery` hook is working. Check browser width is < 768px.

### Command Palette doesn't open
**Fix**: Ensure Spotlight is not already open. Check console for errors.

### Page transitions feel slow
**Fix**: Animations are intentionally 300ms. If too slow, edit `PageTransition.tsx` duration.

### Breadcrumbs not showing
**Fix**: Breadcrumbs hidden on home page (`/`). Navigate to another route.

---

## Next Steps After Testing

1. ✅ Verify all tests pass
2. ⏳ Update existing components to use new patterns
3. ⏳ Replace old buttons with LoadingButton
4. ⏳ Add EmptyState to all list views
5. ⏳ Update DashboardHome to use MetricCard
6. ⏳ Run full E2E test suite
7. ⏳ Merge to main branch

---

**Testing Date**: _____________  
**Tested By**: _____________  
**Overall Result**: ⬜ Pass / ⬜ Fail  
**Notes**: ___________________________________________
