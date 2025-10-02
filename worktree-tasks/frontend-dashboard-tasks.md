# Frontend Dashboard Worktree Tasks
**Branch**: development-infrastructure-dashboard
**Ports**: Backend(8015), Dashboard(5186), MCP(9883), Coordinator(8894)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` before writing ANY code!

**Requirements**:
- ✅ React 19.1.0 with server components
- ✅ TypeScript 5.9.2 strict mode
- ✅ Vite 6.0.1 with ESM optimization
- ✅ Mantine v8 UI framework
- ✅ Vitest 3.2.4 for testing
- ✅ Auto-accept enabled for corrections
- ❌ NO Material-UI, class components, or Webpack

## Primary Objectives

### 1. **Modern React 19 Dashboard Architecture**
   - Implement server components for data fetching
   - Use React Suspense for loading states
   - Implement concurrent features
   - Optimize with lazy loading and code splitting

### 2. **Component Library Development**
   - Build reusable Mantine-based components
   - Create custom hooks for common patterns
   - Implement design system tokens
   - Add Storybook for component documentation

### 3. **State Management**
   - Use Zustand for global state (modern alternative to Redux)
   - Implement React Query for server state
   - Context API for theme and auth
   - Local state with useState/useReducer

### 4. **Real-time Features**
   - Pusher integration for live updates
   - WebSocket fallback handling
   - Optimistic UI updates
   - Real-time notifications system

## Current Tasks

### Phase 1: Architecture Setup (Priority: HIGH)
- [ ] Review current dashboard structure in `apps/dashboard/`
- [ ] Analyze component architecture and dependencies
- [ ] Create component hierarchy documentation
- [ ] Design new dashboard layout with Mantine Grid
- [ ] Setup Storybook for component development
- [ ] Configure Vite 6 with optimal settings
- [ ] Setup path aliases in tsconfig.json

### Phase 2: Component Migration (Priority: HIGH)
- [ ] Identify all Material-UI components to migrate
- [ ] Create Mantine component mappings
- [ ] Build base component library:
  - Button variants
  - Input components
  - Card layouts
  - Modal dialogs
  - Navigation components
  - Data tables
  - Charts and graphs
- [ ] Implement theme system with Mantine
- [ ] Add dark mode support
- [ ] Create responsive breakpoint system

### Phase 3: State Management (Priority: MEDIUM)
- [ ] Setup Zustand stores:
  - User state store
  - Dashboard state store
  - Notification store
  - Settings store
- [ ] Configure React Query:
  - Query client setup
  - Cache configuration
  - Optimistic updates
  - Infinite queries for lists
- [ ] Implement auth context with Clerk/Legacy support
- [ ] Add persistence layer for user preferences

### Phase 4: Real-time Integration (Priority: MEDIUM)
- [ ] Setup Pusher client configuration
- [ ] Create custom Pusher hooks:
  - `usePusherChannel`
  - `usePusherEvent`
  - `usePusherPresence`
- [ ] Implement channel subscription management
- [ ] Add real-time dashboard updates
- [ ] Create notification toast system
- [ ] Implement presence indicators

### Phase 5: Performance Optimization (Priority: HIGH)
- [ ] Implement React.lazy for route-based code splitting
- [ ] Add Suspense boundaries with fallbacks
- [ ] Optimize bundle size with Vite's rollup
- [ ] Implement virtual scrolling for large lists
- [ ] Add memoization for expensive components
- [ ] Configure service worker for offline support
- [ ] Optimize images with modern formats (WebP, AVIF)

### Phase 6: Testing (Priority: HIGH)
- [ ] Setup Vitest 3.2.4 with React Testing Library
- [ ] Write unit tests for components
- [ ] Create integration tests for flows
- [ ] Add E2E tests with Playwright
- [ ] Implement visual regression testing
- [ ] Setup coverage reporting (>80% target)
- [ ] Add accessibility testing with axe-core

### Phase 7: Developer Experience (Priority: MEDIUM)
- [ ] Configure ESLint 9 with React 19 rules
- [ ] Setup Prettier with consistent formatting
- [ ] Add TypeScript strict mode checks
- [ ] Create component templates/generators
- [ ] Document coding standards
- [ ] Setup pre-commit hooks
- [ ] Add commit linting

## File Locations

### Source Files
- **Components**: `apps/dashboard/src/components/`
  - `common/` - Shared components
  - `layout/` - Layout components
  - `features/` - Feature-specific components
- **Pages**: `apps/dashboard/src/pages/`
- **Hooks**: `apps/dashboard/src/hooks/`
- **Stores**: `apps/dashboard/src/stores/`
- **Utils**: `apps/dashboard/src/utils/`
- **Types**: `apps/dashboard/src/types/`
- **Styles**: `apps/dashboard/src/styles/`

### Configuration Files
- `apps/dashboard/vite.config.ts` - Vite configuration
- `apps/dashboard/tsconfig.json` - TypeScript config
- `apps/dashboard/vitest.config.ts` - Test configuration
- `apps/dashboard/eslint.config.js` - ESLint 9 flat config
- `apps/dashboard/.prettierrc` - Code formatting

## Technology Stack (2025)

### Core Framework
```json
{
  "react": "^19.1.0",
  "react-dom": "^19.1.0",
  "typescript": "^5.9.2",
  "vite": "^6.0.1"
}
```

### UI Framework
```json
{
  "@mantine/core": "^8.0.0",
  "@mantine/hooks": "^8.0.0",
  "@mantine/form": "^8.0.0",
  "@mantine/notifications": "^8.0.0",
  "@mantine/modals": "^8.0.0",
  "@tabler/icons-react": "^3.0.0"
}
```

### State Management
```json
{
  "zustand": "^5.0.0",
  "@tanstack/react-query": "^5.0.0",
  "pusher-js": "^8.4.0"
}
```

### Testing
```json
{
  "vitest": "^3.2.4",
  "@testing-library/react": "^16.0.0",
  "@testing-library/user-event": "^14.5.0",
  "@playwright/test": "^1.49.0"
}
```

### Build & Dev Tools
```json
{
  "@vitejs/plugin-react": "^4.3.0",
  "eslint": "^9.35.0",
  "prettier": "^3.4.0"
}
```

## Component Examples (2025 Standards)

### React 19 Server Component
```typescript
// ✅ CORRECT - Server Component with async data
async function DashboardStats() {
  const stats = await fetchStats(); // Direct async in component

  return (
    <Grid>
      <Grid.Col span={3}>
        <StatsCard {...stats.users} />
      </Grid.Col>
      <Grid.Col span={3}>
        <StatsCard {...stats.revenue} />
      </Grid.Col>
    </Grid>
  );
}
```

### Custom Hook with React Query
```typescript
// ✅ CORRECT - Modern data fetching
import { useQuery } from '@tanstack/react-query';

export function useUserProfile(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const response = await fetch(`/api/users/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch');
      return response.json() as Promise<User>;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Usage
function UserProfile({ userId }: Props) {
  const { data: user, isLoading, error } = useUserProfile(userId);

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorBanner error={error} />;

  return <Card>{user.name}</Card>;
}
```

### Zustand Store
```typescript
// ✅ CORRECT - Modern global state
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface DashboardState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      toggleSidebar: () => set((state) => ({
        sidebarOpen: !state.sidebarOpen
      })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'dashboard-storage' }
  )
);
```

### Pusher Integration
```typescript
// ✅ CORRECT - Real-time updates
import { usePusherEvent } from '@/hooks/pusher';

function LiveNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  usePusherEvent('dashboard-updates', 'notification', (data) => {
    setNotifications(prev => [data, ...prev]);
    notifications.show({
      title: data.title,
      message: data.message,
    });
  });

  return <NotificationList items={notifications} />;
}
```

### Mantine Component
```typescript
// ✅ CORRECT - Mantine v8 with TypeScript
import { Card, Text, Button, Group } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';

interface DashboardCardProps {
  title: string;
  value: number;
  change: number;
  onAdd?: () => void;
}

export function DashboardCard({ title, value, change, onAdd }: DashboardCardProps) {
  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Group justify="space-between" mb="xs">
        <Text fw={500}>{title}</Text>
        {onAdd && (
          <Button size="xs" leftSection={<IconPlus size={14} />} onClick={onAdd}>
            Add
          </Button>
        )}
      </Group>
      <Text size="xl" fw={700}>{value}</Text>
      <Text size="sm" c={change >= 0 ? 'teal' : 'red'}>
        {change >= 0 ? '+' : ''}{change}% from last month
      </Text>
    </Card>
  );
}
```

## Testing Standards

### Component Test
```typescript
// ✅ CORRECT - Vitest + React Testing Library
import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/utils';
import { DashboardCard } from './DashboardCard';

describe('DashboardCard', () => {
  it('renders with correct data', () => {
    render(<DashboardCard title="Users" value={1234} change={12.5} />);

    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
    expect(screen.getByText('+12.5% from last month')).toBeInTheDocument();
  });

  it('calls onAdd when button clicked', async () => {
    const onAdd = vi.fn();
    render(<DashboardCard title="Users" value={1234} change={12.5} onAdd={onAdd} />);

    await userEvent.click(screen.getByRole('button', { name: /add/i }));
    expect(onAdd).toHaveBeenCalledOnce();
  });
});
```

## Commands

### Development
```bash
cd apps/dashboard

# Start dev server (Vite 6)
npm run dev

# Type checking
npm run typecheck

# Linting (ESLint 9)
npm run lint
npm run lint:fix

# Testing
npm run test
npm run test:watch
npm run test:coverage

# Build
npm run build
npm run preview

# Storybook
npm run storybook
npm run build-storybook
```

### Code Quality
```bash
# Format code
npm run format

# Check types + lint + test
npm run validate

# Pre-commit checks
npm run pre-commit
```

## Performance Targets

- **Initial Load**: < 2s on 3G
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90
- **Bundle Size**: < 250kb (gzipped)
- **Test Coverage**: > 80%
- **Accessibility**: WCAG 2.1 AA compliant

## Success Metrics

- ✅ All Material-UI components migrated to Mantine
- ✅ React 19 features implemented (Server Components, Concurrent)
- ✅ Zero TypeScript errors in strict mode
- ✅ > 80% test coverage with Vitest
- ✅ Real-time features working via Pusher
- ✅ Lighthouse performance score > 90
- ✅ Bundle size optimized with code splitting
- ✅ Storybook documentation complete

---

**REMEMBER**: Use ONLY 2025 official documentation. Auto-accept is enabled. Modern patterns only!
