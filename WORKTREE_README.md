# Frontend Dashboard Development Worktree

Modern React 19 dashboard development environment following 2025 implementation standards.

## 🚀 Quick Start

```bash
# Navigate to worktree
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions/parallel-worktrees/frontend-dashboard

# Install dependencies (from main repo apps/dashboard)
cd ../../apps/dashboard
npm install

# Start development server
npm run dev           # Dashboard at http://localhost:5179

# Start Storybook
npm run storybook     # Storybook at http://localhost:6006

# Run tests
npm run test          # Vitest
npm run test:coverage # With coverage
```

## 📁 Worktree Structure

```
parallel-worktrees/frontend-dashboard/
├── docs/                               # All documentation here
│   ├── DASHBOARD_ARCHITECTURE_2025.md  # Architecture overview
│   ├── 2025-IMPLEMENTATION-STANDARDS.md# Development standards
│   ├── MUI_TO_MANTINE_MIGRATION_AUDIT.md # Migration roadmap
│   ├── PROGRESS_SUMMARY.md              # Work completed
│   ├── components/                      # Component library examples
│   ├── stores/                          # Zustand store examples
│   └── api/                             # React Query config
├── apps/                                # → Main repo
├── core/                                # → Main repo
└── WORKTREE_README.md                   # This file
```

## 🎯 Current Status

- **Branch**: `frontend-dashboard-development`
- **React**: 19.1.0 with Server Components support
- **TypeScript**: 5.5.4 strict mode
- **UI**: Mantine v8.3.2 (86% migrated from MUI)
- **State**: Zustand + React Query
- **Testing**: Vitest 3.2.4 + Playwright 1.55.0

## 📚 Essential Documentation

1. **[Dashboard Architecture](./docs/DASHBOARD_ARCHITECTURE_2025.md)** - Complete system overview
2. **[Implementation Standards](./docs/2025-IMPLEMENTATION-STANDARDS.md)** - 2025 patterns and best practices
3. **[Migration Audit](./docs/MUI_TO_MANTINE_MIGRATION_AUDIT.md)** - MUI → Mantine migration guide
4. **[Progress Summary](./docs/PROGRESS_SUMMARY.md)** - Work completed and next steps

## 🏗️ What's Included

### ✅ Base Component Library
- **DashboardCard**: Reusable dashboard widget component
- **Button Stories**: Comprehensive Mantine button examples
- **Card Stories**: Card layout and section examples

### ✅ State Management (Zustand)
- **useDashboardStore**: Sidebar, views, widgets with persistence
- **useUserStore**: Auth, preferences, theme management

### ✅ React Query Setup
- **queryClient**: Smart caching (5min stale, 10min gc)
- **queryKeys**: Centralized key factory
- **Examples**: Queries, mutations, infinite queries

### ✅ Storybook Configuration
- Updated for Mantine v8
- MantineProvider with theme
- Comprehensive component docs

## 🚀 Quick Examples

### Using DashboardCard

```tsx
import { DashboardCard } from '@/components/base/DashboardCard';

<DashboardCard
  title="Active Users"
  badge={{ label: "Live", color: "green" }}
  onMenuClick={() => console.log('menu')}
>
  <Text size="xl" fw={700}>1,234</Text>
</DashboardCard>
```

### Using Zustand Store

```tsx
import { useDashboardStore } from '@/stores/useDashboardStore';

const { sidebarOpen, toggleSidebar } = useDashboardStore();
```

### Using React Query

```tsx
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/api/queryClient';

const { data, isLoading } = useQuery({
  queryKey: queryKeys.user(userId),
  queryFn: () => fetchUser(userId)
});
```

## 📋 Next Steps

### Immediate
1. Begin MUI migration (Error Components first)
2. Create Form, Table, Modal components
3. Add React Query data hooks
4. Write unit tests for base components

### This Week
1. Complete high-priority MUI migrations
2. Expand component library
3. Migrate Redux to Zustand
4. Add Storybook coverage

### This Month
1. Complete all MUI migrations
2. Remove MUI dependencies
3. E2E test coverage
4. Performance optimization

## 🔗 Useful Links

- **React 19**: https://react.dev
- **Mantine v8**: https://mantine.dev
- **Zustand**: https://docs.pmnd.rs/zustand
- **React Query**: https://tanstack.com/query
- **Vitest**: https://vitest.dev

## 📝 Development Rules

- ✅ React 19 functional components only
- ✅ TypeScript 5.5 strict mode
- ✅ Mantine v8 components (no MUI)
- ✅ Official 2025 documentation only
- ✅ 80%+ test coverage required
- ✅ Storybook stories for all components

---

**Branch**: `frontend-dashboard-development`
**Status**: ✅ Ready for Development
**Last Updated**: 2025-10-01

See [PROGRESS_SUMMARY.md](./docs/PROGRESS_SUMMARY.md) for detailed work completed.
