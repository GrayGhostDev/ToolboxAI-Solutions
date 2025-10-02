# Responsive Design Guide - Roblox Dashboard

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**Framework**: Mantine v8 with React 19

---

## 📱 Overview

This guide covers responsive design patterns for the Roblox dashboard using Mantine v8's responsive utilities. All components are designed to work seamlessly across desktop, tablet, and mobile devices.

---

## 🎯 Breakpoint System

### Mantine Default Breakpoints

```typescript
// From @mantine/core theme
const breakpoints = {
  xs: '36em',   // 576px
  sm: '48em',   // 768px
  md: '62em',   // 992px
  lg: '75em',   // 1200px
  xl: '88em',   // 1408px
};
```

### Usage in Components

```typescript
import { useMediaQuery } from '@mantine/hooks';

function MyComponent() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
  const isDesktop = useMediaQuery('(min-width: 1025px)');

  return (
    <Box>
      {isMobile && <MobileView />}
      {isTablet && <TabletView />}
      {isDesktop && <DesktopView />}
    </Box>
  );
}
```

---

## 🏗️ Grid System

### Mantine Grid

```typescript
import { Grid } from '@mantine/core';

// Responsive grid with different column spans
<Grid gutter="lg">
  <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
    <Card>Content</Card>
  </Grid.Col>
  <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
    <Card>Content</Card>
  </Grid.Col>
  <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
    <Card>Content</Card>
  </Grid.Col>
  <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
    <Card>Content</Card>
  </Grid.Col>
</Grid>
```

### SimpleGrid

```typescript
import { SimpleGrid } from '@mantine/core';

// Auto-fitting columns with responsive spacing
<SimpleGrid
  cols={{ base: 1, sm: 2, md: 3, lg: 4 }}
  spacing={{ base: 'sm', sm: 'md', md: 'lg' }}
>
  <Card>Item 1</Card>
  <Card>Item 2</Card>
  <Card>Item 3</Card>
  <Card>Item 4</Card>
</SimpleGrid>
```

---

## 📐 Responsive Components

### Roblox3DButton - Responsive

```typescript
import { Roblox3DButton } from '@/components/roblox';
import { useMediaQuery } from '@mantine/hooks';

function ResponsiveButton() {
  const isMobile = useMediaQuery('(max-width: 768px)');

  return (
    <Roblox3DButton
      iconName="TROPHY"
      label={isMobile ? "Win" : "View Achievements"}
      size={isMobile ? 'small' : 'medium'}
      fullWidth={isMobile}
      tooltip="View your achievements"
    />
  );
}
```

### Roblox3DNavigation - Adaptive

```typescript
import { Roblox3DNavigation } from '@/components/roblox';
import { useMediaQuery } from '@mantine/hooks';

function ResponsiveNav() {
  const isMobile = useMediaQuery('(max-width: 768px)');

  return (
    <Roblox3DNavigation
      items={navItems}
      onItemClick={handleClick}
      orientation={isMobile ? 'vertical' : 'horizontal'}
      size={isMobile ? 'small' : 'medium'}
      compact={isMobile}
      showLabels={!isMobile}
    />
  );
}
```

### Dashboard Grid - Responsive

```typescript
import { RobloxDashboardGrid } from '@/components/roblox';
import { useMediaQuery } from '@mantine/hooks';

function ResponsiveDashboard() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(max-width: 1024px)');

  const columns = isMobile ? 1 : isTablet ? 2 : 3;

  return (
    <RobloxDashboardGrid
      columns={columns}
      gap={isMobile ? 'sm' : 'lg'}
      widgets={widgets}
    />
  );
}
```

---

## 📊 Responsive Patterns

### Pattern 1: Stack to Grid

```typescript
// Mobile: Stacked vertically
// Desktop: Grid layout

import { Box } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';

function StackToGrid() {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (isMobile) {
    return (
      <Stack gap="md">
        <MetricCard />
        <MetricCard />
        <MetricCard />
      </Stack>
    );
  }

  return (
    <SimpleGrid cols={3} spacing="md">
      <MetricCard />
      <MetricCard />
      <MetricCard />
    </SimpleGrid>
  );
}
```

### Pattern 2: Drawer Navigation

```typescript
// Mobile: Drawer/Burger menu
// Desktop: Always visible sidebar

import { Drawer, Burger } from '@mantine/core';
import { useDisclosure, useMediaQuery } from '@mantine/hooks';

function ResponsiveNavigation() {
  const [opened, { toggle, close }] = useDisclosure(false);
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (isMobile) {
    return (
      <>
        <Burger opened={opened} onClick={toggle} />
        <Drawer opened={opened} onClose={close} title="Navigation">
          <Roblox3DNavigation items={navItems} orientation="vertical" />
        </Drawer>
      </>
    );
  }

  return (
    <Box w={250}>
      <Roblox3DNavigation items={navItems} orientation="vertical" />
    </Box>
  );
}
```

### Pattern 3: Responsive Typography

```typescript
import { Title, Text } from '@mantine/core';

// Responsive font sizes
<Title
  order={1}
  size={{ base: 'h3', sm: 'h2', md: 'h1' }}
>
  Dashboard
</Title>

<Text
  size={{ base: 'sm', sm: 'md', md: 'lg' }}
  lineClamp={{ base: 3, sm: 4, md: 0 }}
>
  Description text that adapts to screen size
</Text>
```

### Pattern 4: Responsive Spacing

```typescript
import { Stack, Box } from '@mantine/core';

// Adaptive spacing
<Stack
  gap={{ base: 'xs', sm: 'sm', md: 'md', lg: 'lg' }}
>
  <Box p={{ base: 'sm', sm: 'md', md: 'lg' }}>
    Content
  </Box>
</Stack>
```

---

## 🎨 Component-Specific Guidelines

### Roblox3DButton

**Mobile (< 768px)**:
- Size: `small`
- Full width: `true`
- Show tooltips: Always
- Animation: Reduced

**Tablet (768px - 1024px)**:
- Size: `medium`
- Full width: `false`
- Normal animations

**Desktop (> 1024px)**:
- Size: `medium` or `large`
- All animations enabled

### Roblox3DNavigation

**Mobile**:
- Orientation: `vertical` in drawer
- Compact: `true` (icons only)
- Size: `small`

**Tablet**:
- Orientation: `horizontal`
- Compact: `false`
- Size: `medium`

**Desktop**:
- Orientation: `horizontal` or `vertical` sidebar
- All features enabled

### RobloxCharacterAvatar

**Mobile**:
- Size: `150px`
- Simplified controls
- Lower quality rendering for performance

**Tablet**:
- Size: `200px`
- Standard controls

**Desktop**:
- Size: `300px`
- Full controls and quality

---

## 🖼️ Image Optimization

### Responsive Images

```typescript
// Using picture element with multiple sources
<picture>
  <source
    media="(max-width: 768px)"
    srcSet="/images/avatar-small.webp"
  />
  <source
    media="(max-width: 1024px)"
    srcSet="/images/avatar-medium.webp"
  />
  <img
    src="/images/avatar-large.webp"
    alt="Character Avatar"
    loading="lazy"
  />
</picture>
```

### Mantine Image

```typescript
import { Image } from '@mantine/core';

<Image
  src="/images/banner.jpg"
  alt="Dashboard Banner"
  fit="cover"
  h={{ base: 200, sm: 300, md: 400 }}
  radius="md"
/>
```

---

## ⚡ Performance Considerations

### Lazy Loading for Mobile

```typescript
import { lazy, Suspense } from 'react';
import { useMediaQuery } from '@mantine/hooks';
import { Roblox3DLoader } from '@/components/roblox';

const Heavy3DComponent = lazy(() => import('./Heavy3DComponent'));

function OptimizedComponent() {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (isMobile) {
    // Load lighter alternative on mobile
    return <Simple2DVersion />;
  }

  return (
    <Suspense fallback={<Roblox3DLoader />}>
      <Heavy3DComponent />
    </Suspense>
  );
}
```

### Reduced Motion

```typescript
// Respect user preferences
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

<Roblox3DButton
  animated={!prefersReducedMotion}
  iconName="TROPHY"
  label="Achievements"
/>
```

---

## 🧪 Testing Responsive Design

### Manual Testing

```bash
# Test on different viewport sizes
# Chrome DevTools: Cmd+Shift+M (Mac) or Ctrl+Shift+M (Windows)

Common test sizes:
- iPhone SE: 375 × 667
- iPhone 12 Pro: 390 × 844
- iPad: 768 × 1024
- iPad Pro: 1024 × 1366
- Desktop: 1920 × 1080
```

### Automated Testing

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
});

// Test responsive behavior
describe('ResponsiveComponent', () => {
  it('renders mobile layout', () => {
    // Mock viewport
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(max-width: 768px)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
      })),
    });

    render(<ResponsiveComponent />);
    expect(screen.getByTestId('mobile-view')).toBeInTheDocument();
  });
});
```

---

## 📝 Best Practices

### 1. Mobile-First Approach

Start with mobile layout, enhance for larger screens:

```typescript
// Base styles for mobile
const baseStyles = {
  padding: 'sm',
  fontSize: '14px',
};

// Enhanced for larger screens
<Box
  p={{ base: 'sm', md: 'lg' }}
  fz={{ base: 14, md: 16, lg: 18 }}
>
  Content
</Box>
```

### 2. Touch-Friendly Targets

Minimum 44×44px touch targets on mobile:

```typescript
<Roblox3DButton
  size={isMobile ? 'medium' : 'small'}  // Ensures 44px minimum
  iconName="TROPHY"
/>
```

### 3. Avoid Horizontal Scroll

Use viewport units and max-width:

```typescript
<Container
  size="xl"
  px={{ base: 'sm', sm: 'md' }}
  style={{ maxWidth: '100vw', overflowX: 'hidden' }}
>
  Content
</Container>
```

### 4. Responsive Tables

```typescript
import { Table, ScrollArea } from '@mantine/core';

// Horizontal scroll on mobile
<ScrollArea>
  <Table>
    <thead>...</thead>
    <tbody>...</tbody>
  </Table>
</ScrollArea>
```

### 5. Conditional Rendering

```typescript
// Hide on mobile, show on desktop
<Box visibleFrom="md">
  <DesktopOnlyContent />
</Box>

// Show on mobile, hide on desktop
<Box hiddenFrom="md">
  <MobileOnlyContent />
</Box>
```

---

## 🎯 Checklist

### Responsive Design Checklist

- [ ] All layouts tested on mobile (320px - 768px)
- [ ] All layouts tested on tablet (768px - 1024px)
- [ ] All layouts tested on desktop (> 1024px)
- [ ] Touch targets minimum 44×44px
- [ ] No horizontal scrolling
- [ ] Images optimized for different sizes
- [ ] Fonts readable at all sizes
- [ ] Navigation works on all devices
- [ ] Forms easy to use on mobile
- [ ] 3D features gracefully degrade on mobile
- [ ] Performance acceptable on mobile (< 3s load)

---

## 📚 Resources

- **Mantine Responsive Styles**: https://mantine.dev/styles/responsive/
- **Mantine Hooks**: https://mantine.dev/hooks/use-media-query/
- **React 19 Best Practices**: https://react.dev/
- **Web.dev Mobile Guide**: https://web.dev/mobile/

---

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**Maintainer**: ToolboxAI Development Team
