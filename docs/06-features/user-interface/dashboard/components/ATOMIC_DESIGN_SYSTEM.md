# ⚛️ Atomic Design System

A comprehensive component library built with atomic design principles for the ToolBoxAI dashboard. This system promotes consistency, reusability, and maintainability across the entire application.

## 📚 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Component Levels](#component-levels)
- [Usage Examples](#usage-examples)
- [Custom Hooks](#custom-hooks)
- [Higher-Order Components](#higher-order-components)
- [Best Practices](#best-practices)
- [Performance](#performance)
- [Accessibility](#accessibility)

## 🎯 Overview

Our atomic design system is built on five distinct levels:

```
🔬 Atoms → 🧩 Molecules → 🏗️ Organisms → 📄 Templates → 🌐 Pages
```

Each level builds upon the previous one, creating a scalable and maintainable component hierarchy.

### Key Features

- **🎨 Roblox Theming**: Custom gaming-inspired design tokens and components
- **♿ Accessibility**: WCAG 2.1 AA compliant components with proper ARIA support
- **🔧 TypeScript**: Full type safety with comprehensive interfaces
- **🎭 Polymorphic**: Components can render as different HTML elements
- **🪝 Custom Hooks**: Reusable logic for common UI patterns
- **🔄 HOCs**: Component enhancement patterns for cross-cutting concerns
- **📱 Responsive**: Mobile-first design with flexible breakpoints
- **⚡ Performance**: Optimized with memoization and virtualization

## 🏗️ Architecture

```
src/components/atomic/
├── atoms/           # Basic building blocks
├── molecules/       # Simple combinations
├── organisms/       # Complex components
├── templates/       # Page layouts
├── compound/        # Advanced composition patterns
├── hoc/            # Higher-order components
└── examples/       # Usage demonstrations
```

## 🔬 Component Levels

### Atoms - Basic Building Blocks

Atoms are the foundational elements that cannot be broken down further:

```tsx
import { AtomicButton, AtomicInput, AtomicText } from '@/components/atomic/atoms';

// Basic button with Roblox theming
<AtomicButton variant="primary" size="md" robloxTheme>
  Click Me
</AtomicButton>

// Gaming avatar with level and status
<AtomicAvatar
  size="lg"
  level={42}
  status="online"
  robloxTheme
>
  Player
</AtomicAvatar>

// Polymorphic text component
<AtomicText
  as="h1"
  variant="h1"
  weight="bold"
  gradient
>
  Epic Title
</AtomicText>
```

### 🧩 Molecules - Simple Combinations

Molecules combine atoms to create functional units:

```tsx
import { FormField, Card } from '@/components/atomic/molecules';

// Complete form field with validation
<FormField
  label="Username"
  placeholder="Enter username"
  required
  helperText="Must be unique"
  showCharacterCount
  maxLength={20}
  state={hasError ? 'error' : 'default'}
  errorText={hasError ? 'Username taken' : undefined}
/>

// Gaming-themed card
<Card
  variant="roblox"
  title="Player Stats"
  subtitle="Level 42 Explorer"
  avatar={<AtomicAvatar level={42} />}
  actions={<AtomicButton>View</AtomicButton>}
>
  Card content here
</Card>
```

### 🏗️ Organisms - Complex Components

Organisms are groups of molecules functioning as distinct interface sections:

```tsx
import { Table } from '@/components/atomic/compound';

// Advanced data table with sorting and selection
<Table variant="roblox" sortable selectable>
  <Table.Header>
    <Table.Row>
      <Table.Cell as="th" sortable onSort={handleSort}>
        Player
      </Table.Cell>
      <Table.Cell as="th" align="right">
        Score
      </Table.Cell>
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {players.map(player => (
      <Table.Row key={player.id}>
        <Table.Cell>{player.name}</Table.Cell>
        <Table.Cell align="right">{player.score}</Table.Cell>
      </Table.Row>
    ))}
  </Table.Body>
</Table>
```

### 📄 Templates - Page Layouts

Templates define the structure of entire pages:

```tsx
import { DashboardTemplate } from '@/components/atomic/templates';

<DashboardTemplate
  header={<Header />}
  sidebar={<Sidebar />}
  breadcrumbs={<Breadcrumbs />}
  actions={<ActionBar />}
>
  <PageContent />
</DashboardTemplate>
```

## 🪝 Custom Hooks

Our hook library provides reusable logic for common patterns:

```tsx
import {
  useToggle,
  useDisclosure,
  useDebounce,
  useXPCalculator
} from '@/hooks/atomic';

function MyComponent() {
  // Simple boolean state management
  const sidebar = useToggle(false);

  // Modal/dropdown state with keyboard support
  const modal = useDisclosure({
    closeOnEscape: true,
    onClose: () => console.log('Modal closed')
  });

  // Debounced search
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  // Gaming-specific logic
  const { level, progress, nextLevelXP } = useXPCalculator(currentXP);

  return (
    <div>
      <AtomicButton onClick={sidebar.toggle}>
        Toggle Sidebar
      </AtomicButton>

      <AtomicButton onClick={modal.open}>
        Open Modal
      </AtomicButton>

      <Modal isOpen={modal.isOpen} onClose={modal.close}>
        Modal content
      </Modal>
    </div>
  );
}
```

## 🔄 Higher-Order Components

HOCs provide cross-cutting functionality:

```tsx
import {
  withLoading,
  withErrorBoundary,
  withAuth
} from '@/components/atomic/hoc';

// Component with loading state
const LoadingCard = withLoading(Card, {
  loadingText: 'Loading player data...',
  spinnerSize: 'md'
});

// Component with error boundary
const SafeComponent = withErrorBoundary(MyComponent, {
  onError: (error) => analytics.track('component_error', { error })
});

// Protected component requiring authentication
const ProtectedDashboard = withAuth(Dashboard, {
  requiredRole: 'admin',
  redirectTo: '/login'
});

// Composition of multiple HOCs
const EnhancedComponent = withAuth(
  withErrorBoundary(
    withLoading(MyComponent)
  )
);
```

## 💡 Best Practices

### Component Design

1. **Single Responsibility**: Each component should have one clear purpose
2. **Composition over Inheritance**: Use composition patterns for flexibility
3. **Props Interface**: Always define comprehensive TypeScript interfaces
4. **Default Props**: Provide sensible defaults for optional props
5. **Forwarded Refs**: Support ref forwarding for DOM access

```tsx
// ✅ Good: Clear purpose, typed props, forwarded ref
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading = false, children, ...props }, ref) => {
    return (
      <StyledButton
        ref={ref}
        variant={variant}
        size={size}
        disabled={loading}
        {...props}
      >
        {loading ? <Spinner /> : children}
      </StyledButton>
    );
  }
);
```

### State Management

1. **Local State First**: Use local state for component-specific data
2. **Lift State Up**: Move state up when multiple components need it
3. **Custom Hooks**: Extract stateful logic into reusable hooks
4. **Context Sparingly**: Use context for truly global state

### Performance Optimization

1. **Memoization**: Use React.memo for expensive renders
2. **useCallback/useMemo**: Optimize function and value references
3. **Virtualization**: Use virtual scrolling for large lists
4. **Code Splitting**: Lazy load heavy components

```tsx
// ✅ Optimized component
const ExpensiveList = React.memo(({ items, onItemClick }) => {
  const handleClick = useCallback((id) => {
    onItemClick(id);
  }, [onItemClick]);

  const sortedItems = useMemo(() => {
    return items.sort((a, b) => a.name.localeCompare(b.name));
  }, [items]);

  return (
    <VirtualizedList items={sortedItems} onItemClick={handleClick} />
  );
});
```

## ♿ Accessibility

All components follow WCAG 2.1 AA guidelines:

### Keyboard Navigation
- Tab order follows logical flow
- All interactive elements are keyboard accessible
- Escape key closes modals/dropdowns

### Screen Reader Support
- Proper ARIA labels and descriptions
- Semantic HTML structure
- Live regions for dynamic content

### Color and Contrast
- Minimum 4.5:1 contrast ratio
- Color is not the only means of conveying information
- High contrast mode support

```tsx
// ✅ Accessible button
<AtomicButton
  aria-label="Close modal"
  aria-describedby="modal-description"
  onClick={closeModal}
>
  ×
</AtomicButton>

// ✅ Accessible form field
<FormField
  id="email"
  label="Email Address"
  required
  aria-invalid={hasError}
  aria-describedby="email-error"
  errorText={hasError ? "Please enter a valid email" : undefined}
/>
```

## 🚀 Performance

### Bundle Size Optimization
- Tree shaking support with proper exports
- Code splitting at the organism level
- Minimal external dependencies

### Runtime Performance
- React.memo for expensive components
- useCallback/useMemo for optimization
- Virtual scrolling for large datasets
- Intersection Observer for lazy loading

### Loading Strategies
```tsx
// Lazy load heavy components
const GameEngine = lazy(() => import('./GameEngine'));

// Progressive enhancement
const OptionalFeature = lazy(() =>
  import('./OptionalFeature').catch(() => ({ default: () => null }))
);
```

## 🎮 Gaming Features

### Roblox Theme Integration
- Custom color palette with brand colors
- Gaming-specific animations and effects
- Level badges and achievement systems
- XP progress bars and status indicators

### Gaming Components
```tsx
// XP progress with animation
<XPBar
  currentXP={1500}
  maxXP={2000}
  level={15}
  animated
  showLevelUp
/>

// Achievement notification
<AchievementCard
  title="First Victory!"
  description="Won your first game"
  rarity="epic"
  unlocked
  animated
/>

// Player leaderboard
<LeaderboardTable
  players={players}
  highlightCurrentPlayer
  showAvatars
  sortable
/>
```

## 📱 Responsive Design

Components are built mobile-first with flexible breakpoints:

```tsx
// Responsive spacing
<AtomicBox
  p={{ xs: 2, sm: 4, md: 6 }}
  m={{ xs: 1, lg: 2 }}
>
  Content
</AtomicBox>

// Responsive grid
<AtomicGrid
  columns={{ xs: 1, sm: 2, lg: 3 }}
  gap={{ xs: 2, md: 4 }}
>
  {items.map(item => <GridItem key={item.id} />)}
</AtomicGrid>
```

## 🔧 Development Workflow

### Creating New Components

1. **Start with atoms**: Build basic elements first
2. **Compose molecules**: Combine atoms for functionality
3. **Build organisms**: Create complex interface sections
4. **Design templates**: Define page layouts
5. **Test thoroughly**: Unit tests, accessibility, performance

### Testing Strategy
```tsx
// Component testing
import { render, screen, fireEvent } from '@testing-library/react';
import { AtomicButton } from './Button';

test('button handles click events', () => {
  const handleClick = jest.fn();
  render(<AtomicButton onClick={handleClick}>Click me</AtomicButton>);

  fireEvent.click(screen.getByRole('button'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});

// Accessibility testing
import { axe, toHaveNoViolations } from 'jest-axe';

test('button is accessible', async () => {
  const { container } = render(<AtomicButton>Click me</AtomicButton>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## 🎯 Migration Guide

### From Existing Components

1. **Audit current components**: Identify reusable patterns
2. **Map to atomic levels**: Categorize existing components
3. **Refactor gradually**: Replace components incrementally
4. **Update imports**: Use new atomic structure
5. **Remove legacy code**: Clean up unused components

### Example Migration
```tsx
// Before (old component)
import { CustomCard } from '@/components/CustomCard';

// After (atomic design)
import { Card } from '@/components/atomic/molecules';
import { AtomicButton, AtomicText } from '@/components/atomic/atoms';

<Card
  variant="roblox"
  title="Same functionality"
  actions={<AtomicButton>Action</AtomicButton>}
>
  <AtomicText>Content</AtomicText>
</Card>
```

---

## 🎉 Getting Started

Check out the [AtomicDesignShowcase](./examples/AtomicDesignShowcase.tsx) for a comprehensive demonstration of all components working together!

---

*Built with ❤️ for the ToolBoxAI educational platform*