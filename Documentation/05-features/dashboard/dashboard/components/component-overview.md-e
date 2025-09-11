# Dashboard Component Documentation

## Overview

The ToolBoxAI Dashboard is built with React 18 and TypeScript, using Material-UI v5 for the design system. This documentation provides comprehensive details about all dashboard components.

## Architecture

```
src/dashboard/src/
├── components/
│   ├── layout/         # Main layout components
│   ├── pages/          # Page-level components
│   ├── widgets/        # Reusable widget components
│   ├── common/         # Shared utility components
│   ├── modals/         # Modal/dialog components
│   └── notifications/  # Notification system
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
├── services/           # API services
├── store/              # Redux state management
└── utils/              # Utility functions
```

## Component Categories

### 1. Layout Components
- **AppLayout** - Main application wrapper with sidebar
- **Sidebar** - Role-based navigation menu
- **Topbar** - Application header with user controls

### 2. Page Components

#### Student Pages
- **DashboardHome** - Student dashboard overview
- **Avatar** - Avatar customization
- **Progress** - Learning progress tracking
- **Missions** - Quest/mission management
- **Rewards** - Achievement system
- **Leaderboard** - Ranking display
- **Play** - Roblox game launcher

#### Teacher Pages
- **Classes** - Classroom management
- **Lessons** - Lesson planning
- **Assessments** - Quiz/test creation
- **Reports** - Student progress reports

#### Admin Pages
- **Schools** - School administration
- **Users** - User management
- **Analytics** - System analytics

#### Shared Pages
- **Login/Register** - Authentication
- **Messages** - Communication system
- **Settings** - User preferences
- **Compliance** - COPPA compliance
- **Integrations** - LMS integrations

### 3. Widget Components
- **ProgressCharts** - Data visualization widgets
- **ConnectionStatus** - WebSocket connection indicator
- **RealTimeAnalytics** - Live data displays
- **StudentProgressTracker** - Individual progress widget

### 4. Common Components
- **ErrorBoundary** - Error handling wrapper
- **LoadingOverlay** - Loading states
- **RoleGuard** - Access control wrapper

### 5. Notification Components
- **NotificationToast** - Global notifications
- **RealtimeToast** - WebSocket notifications

## State Management

The dashboard uses Redux Toolkit for state management with the following slices:

- **auth** - Authentication state
- **user** - User profile data
- **dashboard** - Dashboard-specific data
- **gamification** - XP and achievements
- **notifications** - Alert management

## Routing

React Router v6 handles navigation with role-based route protection:

```typescript
interface RouteConfig {
  path: string;
  component: React.ComponentType;
  roles: UserRole[];
  exact?: boolean;
}
```

## API Integration

Components interact with the backend through service modules:

- **authService** - Authentication endpoints
- **dashboardService** - Dashboard data
- **classService** - Class management
- **lessonService** - Lesson operations
- **analyticsService** - Analytics data

## WebSocket Integration

Real-time features use WebSocket connections:

- Live notifications
- Progress updates
- Collaborative features
- System broadcasts

## Theming

Material-UI theme configuration supports:

- Light/dark mode toggle
- Custom color palettes per role
- Responsive breakpoints
- Typography scaling

## Performance Optimizations

- **Code splitting** - Lazy loading for routes
- **Memoization** - React.memo for expensive components
- **Virtual scrolling** - For large lists
- **Debouncing** - For search/filter operations
- **Caching** - API response caching

## Accessibility Features

- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- Color contrast compliance

## Testing Strategy

Components are tested using:

- **Unit tests** - Jest + React Testing Library
- **Integration tests** - API interaction testing
- **E2E tests** - Cypress for user workflows
- **Visual regression** - Storybook + Chromatic

## Development Guidelines

### Component Creation
1. Use functional components with hooks
2. Define TypeScript interfaces for props
3. Include JSDoc comments
4. Follow naming conventions
5. Implement error boundaries

### Code Style
- ESLint configuration enforced
- Prettier for formatting
- Consistent file structure
- Meaningful variable names
- Comment complex logic

### Best Practices
- Keep components focused (single responsibility)
- Extract reusable logic to hooks
- Use proper TypeScript types
- Handle loading and error states
- Implement proper cleanup in useEffect

## Component Documentation

Detailed documentation for each component is available in:

- [Layout Components](./layout-components.md)
- [Page Components](./page-components.md)
- [Widget Components](./widget-components.md)
- [Common Components](./common-components.md)
- [Custom Hooks](./custom-hooks.md)

## Quick Start

### Creating a New Component

```typescript
import React from 'react';
import { Box, Typography } from '@mui/material';
import { useAppSelector } from '../../hooks/redux';

interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

/**
 * MyComponent - Brief description
 * @param {MyComponentProps} props - Component props
 * @returns {JSX.Element} Rendered component
 */
const MyComponent: React.FC<MyComponentProps> = ({ title, onAction }) => {
  const user = useAppSelector(state => state.user);
  
  return (
    <Box>
      <Typography variant="h4">{title}</Typography>
      {/* Component content */}
    </Box>
  );
};

export default MyComponent;
```

### Using Components

```typescript
import MyComponent from './components/MyComponent';

function App() {
  return (
    <MyComponent 
      title="Example" 
      onAction={() => console.log('Action')}
    />
  );
}
```

## Resources

- [React Documentation](https://react.dev)
- [Material-UI Documentation](https://mui.com)
- [Redux Toolkit](https://redux-toolkit.js.org)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [React Router](https://reactrouter.com)

## Version History

- **v2.0.0** - Current version with TypeScript migration
- **v1.5.0** - Added real-time features
- **v1.0.0** - Initial release

## Support

For questions or issues:
- Check the [FAQ](../../../09-meta/faq.md)
- Review [Troubleshooting Guide](../../../04-implementation/troubleshooting.md)
- Contact development team