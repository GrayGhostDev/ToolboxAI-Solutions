# Dashboard Architecture 2025

## Overview

ToolboxAI Dashboard is a React 19.1.0-based educational platform with real-time features, 3D visualizations, and Roblox integration. This document outlines the modern 2025 architecture and implementation standards.

## Technology Stack (2025)

### Core Framework
- **React**: 19.1.0 (with Server Components support)
- **TypeScript**: 5.5.4 (strict mode)
- **Vite**: 6.0.1 (ESM-first bundler)
- **Node.js**: >=22

### UI Framework
- **Mantine**: v8.3.2 (replacing Material-UI)
  - @mantine/core - Component library
  - @mantine/hooks - Custom hooks
  - @mantine/form - Form management
  - @mantine/notifications - Toast notifications
  - @mantine/dates - Date/time components
  - @mantine/charts - Chart components
  - @mantine/spotlight - Command palette
  - @mantine/tiptap - Rich text editor
- **Icons**: @tabler/icons-react v3.35.0
- **Styling**: PostCSS with Mantine preset

### State Management
- **Redux Toolkit**: v2.2.7 (global state - legacy, being phased out)
- **Zustand**: (planned) - Modern state management
- **React Query**: (planned) - Server state management
- **Context API**: Auth, Theme, Pusher

### Real-time & Communication
- **Pusher**: v8.4.0 (primary real-time solution)
- **Axios**: v1.7.9 (HTTP client)
- **GraphQL**: v16.9.0 with Apollo Client v3.11.0

### 3D & Visualization
- **Three.js**: v0.160.1
- **@react-three/fiber**: v9.3.0
- **@react-three/drei**: v9.122.0
- **Chart.js**: v4.5.0
- **Recharts**: v2.15.4

### Testing
- **Vitest**: v3.2.4 (unit/integration tests)
- **Playwright**: v1.55.0 (E2E tests)
- **Testing Library**: v14.3.1 (React component testing)
- **MSW**: v2.11.2 (API mocking)
- **Happy-DOM**: v18.0.1 (DOM environment)

### Build & Development Tools
- **ESLint**: v9.35.0 (flat config system)
- **Prettier**: (code formatting)
- **Storybook**: v8.6.14 (component development)
- **TypeScript**: Strict mode with modern decorators

## Project Structure

```
apps/dashboard/
├── src/
│   ├── components/          # React components
│   │   ├── common/         # Shared UI components
│   │   ├── layout/         # Layout components
│   │   ├── features/       # Feature-specific components
│   │   ├── auth/           # Authentication components
│   │   ├── dashboards/     # Dashboard views
│   │   ├── roblox/         # Roblox integration
│   │   ├── three/          # 3D components
│   │   ├── admin/          # Admin components
│   │   ├── agents/         # AI agent UI
│   │   ├── analytics/      # Analytics views
│   │   ├── metrics/        # Metrics dashboards
│   │   ├── monitoring/     # System monitoring
│   │   ├── notifications/  # Notification system
│   │   ├── settings/       # Settings UI
│   │   ├── widgets/        # Dashboard widgets
│   │   └── ...
│   ├── hooks/              # Custom React hooks
│   │   ├── pusher/        # Pusher hooks
│   │   ├── auth/          # Authentication hooks
│   │   └── ...
│   ├── contexts/           # React contexts
│   │   ├── PusherContext.tsx
│   │   ├── ClerkAuthContext.tsx
│   │   ├── AuthContext.tsx (legacy)
│   │   └── ...
│   ├── store/              # Redux store (legacy)
│   ├── stores/             # Zustand stores (planned)
│   ├── services/           # API services
│   │   ├── api.ts
│   │   ├── pusher.ts
│   │   └── ...
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript types
│   ├── theme/              # Mantine theme
│   ├── config/             # Configuration
│   ├── routes/             # Route definitions
│   ├── pages/              # Page components
│   ├── graphql/            # GraphQL queries
│   ├── i18n/               # Internationalization
│   └── test/               # Test utilities
├── public/                 # Static assets
├── e2e/                    # E2E tests
├── tests/                  # Test files
├── .storybook/            # Storybook config
├── vite.config.js         # Vite configuration
├── tsconfig.json          # TypeScript config
├── eslint.config.js       # ESLint flat config
├── playwright.config.ts   # Playwright config
└── package.json
```

## Component Hierarchy

### Level 1: Application Root
- **main.tsx**: Entry point with providers
  - React.StrictMode
  - ErrorBoundary
  - BrowserRouter
  - Provider (Redux)
  - ThemeWrapper (Mantine)
  - AuthProvider (Clerk/Legacy)

### Level 2: App Component (App.tsx)
- Route configuration
- Auth-based navigation
- Layout selection
- Real-time setup (Pusher)
- 3D provider setup

### Level 3: Layout Components
- **AppLayout**: Main application layout
  - Header/Navigation
  - Sidebar
  - Content area
  - Footer
- **DashboardLayout**: Dashboard-specific layout
- **AdminLayout**: Admin panel layout

### Level 4: Feature Components
- **Dashboards**: Role-based dashboards (admin, teacher, student)
- **Roblox**: Roblox environment integration
- **Analytics**: Data visualization
- **Monitoring**: System health
- **Settings**: User preferences

### Level 5: Atomic Components
- **Buttons, Inputs, Cards**: Mantine-based
- **Modals, Toasts**: Notifications
- **Charts, Graphs**: Data visualization
- **3D Elements**: Three.js components

## Dependencies Analysis

### Current Status (as of analysis)
- **Total Components**: 196 .tsx files
- **Mantine Usage**: 219 imports (primary)
- **Material-UI Usage**: 34 imports (legacy - to be removed)
- **Migration Progress**: ~86% complete to Mantine

### Key Dependencies

#### Production Dependencies
```json
{
  "react": "^19.1.0",
  "react-dom": "^19.1.0",
  "@mantine/core": "^8.3.2",
  "@mantine/hooks": "^8.3.2",
  "@tabler/icons-react": "^3.35.0",
  "pusher-js": "^8.4.0",
  "@apollo/client": "^3.11.0",
  "@reduxjs/toolkit": "^2.2.7",
  "react-redux": "^9.1.2",
  "react-router-dom": "^6.26.2",
  "three": "^0.160.1",
  "@react-three/fiber": "^9.3.0"
}
```

#### Development Dependencies
```json
{
  "typescript": "^5.5.4",
  "vite": "^6.0.1",
  "vitest": "^3.2.4",
  "@playwright/test": "^1.55.0",
  "eslint": "^9.35.0",
  "storybook": "^8.6.14"
}
```

## Authentication Architecture

### Dual Auth Support
1. **Clerk Auth** (optional, enabled via `VITE_ENABLE_CLERK_AUTH`)
   - ClerkProviderWrapper
   - ClerkAuthProvider
   - useAuth hook from Clerk

2. **Legacy Auth** (default)
   - AuthContext
   - Custom JWT authentication
   - useUnifiedAuth hook for compatibility

### Unified Auth Pattern
```typescript
// useUnifiedAuth handles both auth systems
const { user, isAuthenticated, login, logout } = useUnifiedAuth();
```

## Real-time Communication

### Pusher Integration (Primary)
- **Service**: `services/pusher.ts`
- **Context**: `contexts/PusherContext.tsx`
- **Hooks**:
  - `usePusherChannel` - Channel subscription
  - `usePusherEvent` - Event listening
  - `usePusherPresence` - Presence tracking

### Channels
- `dashboard-updates` - General notifications
- `content-generation` - AI content updates
- `agent-status` - Agent activity
- `public` - Public announcements

## 3D Rendering Architecture

### Three.js Integration
- **Provider**: `components/three/ThreeProvider`
- **Main Scene**: `components/three/Scene3D`
- **Roblox Integration**: `components/roblox/FloatingCharactersV2`
- **Fallback**: `components/three/fallbacks/Canvas2D`

### Performance Optimization
- Lazy loading for 3D components
- Canvas2D fallback for low-end devices
- Performance monitoring
- Progressive enhancement

## Migration Status

### Completed
- ✅ React 19 migration
- ✅ Vite 6 migration
- ✅ TypeScript 5.5 upgrade
- ✅ ESLint 9 flat config
- ✅ Mantine v8 integration (86%)
- ✅ Pusher real-time (replacing WebSocket)

### In Progress
- 🔄 Material-UI removal (14% remaining)
- 🔄 Redux → Zustand migration (planning)
- 🔄 React Query integration (planning)
- 🔄 Storybook documentation
- 🔄 Component testing coverage

### Planned
- ⏳ Server Components adoption
- ⏳ React Suspense optimization
- ⏳ Concurrent rendering features
- ⏳ E2E test coverage expansion
- ⏳ Performance optimization
- ⏳ Accessibility improvements

## Development Workflow

### Local Development
```bash
npm run dev              # Start Vite dev server (port 5179)
npm run test             # Run Vitest tests
npm run test:watch       # Watch mode
npm run lint             # ESLint check
npm run typecheck        # TypeScript check
npm run storybook        # Start Storybook (port 6006)
```

### Production Build
```bash
npm run build            # Production build
npm run preview          # Preview production build
npm run build:analyze    # Analyze bundle size
```

### Quality Checks
```bash
npm run validate         # Typecheck + Lint + Test
npm run ci               # Full CI pipeline
npm run format           # Format with Prettier
```

## API Integration

### Backend Proxy (Vite)
All `/api/*` requests proxy to backend:
- **Target**: `http://127.0.0.1:8009` (local)
- **Docker**: Uses `VITE_PROXY_TARGET` env var

### Endpoints
- `/api/v1/*` - REST API
- `/auth/*` - Authentication
- `/dashboard/*` - Dashboard data
- `/realtime/*` - Real-time triggers
- `/pusher/*` - Pusher auth
- `/ws/*` - WebSocket (legacy)

## Environment Configuration

### Required Variables
```bash
# API
VITE_API_BASE_URL=http://127.0.0.1:8009
VITE_WS_URL=http://127.0.0.1:8009

# Pusher
VITE_PUSHER_KEY=your-key
VITE_PUSHER_CLUSTER=your-cluster
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth

# Authentication
VITE_ENABLE_CLERK_AUTH=false
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...

# Features
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_3D=true
```

## Performance Targets

### Build Metrics
- **Bundle Size**: < 250kb (gzipped)
- **Initial Load**: < 2s on 3G
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90

### Runtime Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Test Coverage
- **Unit Tests**: > 80%
- **Integration Tests**: > 70%
- **E2E Tests**: Critical paths covered

## Known Issues & Technical Debt

### Material-UI Migration
- 34 remaining MUI imports to migrate
- Legacy theme system to remove
- Emotion dependencies to clean up

### State Management
- Redux Toolkit is legacy, complex
- Need Zustand migration for simplicity
- React Query needed for server state

### Testing
- Coverage below target (current ~60%)
- E2E tests need expansion
- Visual regression testing needed

### Performance
- Bundle size optimization needed
- Code splitting not optimal
- 3D rendering can be CPU-intensive

## Accessibility

### Current Status
- Basic WCAG 2.1 compliance
- Keyboard navigation supported
- Screen reader compatibility (partial)
- High contrast mode supported

### Improvements Needed
- ARIA labels expansion
- Focus management enhancement
- Voice control support
- Better error announcements

## Security Considerations

### Implemented
- JWT authentication
- CSRF protection
- XSS prevention (React)
- Content Security Policy headers
- Secure WebSocket/Pusher connections

### To Implement
- Rate limiting (client-side)
- Input validation enhancement
- Security headers optimization
- Dependency vulnerability scanning

## Browser Support

### Target Browsers
- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile Safari: Last 2 versions
- Chrome Android: Last 2 versions

### Minimum Requirements
- ES2022 support
- WebGL for 3D features
- WebSocket support
- LocalStorage/SessionStorage

## Next Steps

See [CLAUDE.md](../CLAUDE.md) for detailed implementation tasks and priorities.

---

**Last Updated**: 2025-10-01
**Architecture Version**: 2.0.0
**Status**: Active Development
