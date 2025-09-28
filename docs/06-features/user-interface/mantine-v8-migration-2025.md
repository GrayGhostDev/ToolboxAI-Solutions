# Mantine v8 Migration Guide - 2025 Implementation

## Overview

This document outlines the migration from Mantine v6/v7 to Mantine v8.3.x, including breaking changes, component updates, and new patterns implemented in the ToolboxAI Dashboard.

## Breaking Changes Addressed

### 1. **Layout Components Removal**

#### ❌ **Deprecated Components**
- `Header` - Removed in v8
- `Navbar` - Removed in v8  
- `Aside` - Removed in v8
- `Footer` - Removed in v8

#### ✅ **Replacement Strategy**
```typescript
// Before (v6/v7)
import { Header, Navbar } from '@mantine/core';
<Header height={64}>Content</Header>

// After (v8)
import { Paper, Box } from '@mantine/core';
<Paper h={64} style={{ position: 'fixed', top: 0 }}>Content</Paper>
```

### 2. **Styling System Changes**

#### ❌ **Deprecated `sx` Prop**
```typescript
// Before
<Box sx={{ padding: 16, backgroundColor: 'red' }}>

// After  
<Box style={{ padding: '1rem', backgroundColor: 'red' }}>
```

#### ✅ **New Styling Patterns**
- Use `style` prop for inline styles
- Use CSS modules for complex styling
- Use Mantine's style props (e.g., `h`, `w`, `p`, `m`)

### 3. **Props Standardization**

#### **Height/Width Props**
```typescript
// Before
height={64}
width="100%"

// After
h={64}
w="100%"
```

#### **Spacing Props**
```typescript
// Before
spacing="md"

// After
gap="md"
```

#### **Position Props**
```typescript
// Before
position="apart"

// After
justify="space-between"
```

## Component-Specific Updates

### **Topbar Component**
```typescript
// ✅ Updated Implementation
import { Paper, Group, Text, ActionIcon } from '@mantine/core';

export default function Topbar() {
  return (
    <Paper
      h={64}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 101,
        display: 'flex',
        alignItems: 'center',
        backdropFilter: 'blur(8px)',
        background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.95) 0%, rgba(245, 245, 255, 0.95) 100%)',
        borderBottom: '2px solid var(--mantine-color-cyan-6)',
        boxShadow: '0 4px 20px rgba(0, 188, 212, 0.3)',
      }}
    >
      <Group justify="space-between" w="100%" px="md">
        {/* Content */}
      </Group>
    </Paper>
  );
}
```

### **Menu Components**
```typescript
// ✅ Updated Menu Item Icons
// Before
<Menu.Item icon={<IconSettings size={16} />}>

// After
<Menu.Item leftSection={<IconSettings size={16} />}>
```

### **Text Color Props**
```typescript
// Before
<Text color="dimmed">

// After  
<Text c="dimmed">
```

## Theme Configuration Updates

### **Theme Structure (v8)**
```typescript
import { createTheme, MantineColorsTuple } from '@mantine/core';

export const theme = createTheme({
  primaryColor: 'roblox-cyan',
  colors: {
    'roblox-cyan': [/* color tuple */],
  },
  fontFamily: 'Inter, sans-serif',
  headings: {
    fontFamily: 'Inter, sans-serif',
    fontWeight: '700',
    sizes: {
      h1: { fontSize: '2.5rem', lineHeight: '1.2' },
    },
  },
  components: {
    Button: {
      defaultProps: { radius: 'md' },
      styles: {
        root: {
          fontWeight: 600,
          transition: 'all 250ms ease',
        },
      },
    },
  },
});
```

## PostCSS Configuration

### **ES Module Syntax**
```javascript
// ✅ Correct for "type": "module" in package.json
export default {
  plugins: {
    'postcss-preset-mantine': {},
    'postcss-simple-vars': {
      variables: {
        'mantine-breakpoint-xs': '36em',
        'mantine-breakpoint-sm': '48em',
        'mantine-breakpoint-md': '62em',
        'mantine-breakpoint-lg': '75em',
        'mantine-breakpoint-xl': '88em',
      },
    },
  },
};
```

## Component Migration Checklist

### **Layout Components**
- [ ] ✅ Replace `Header` with `Paper` or `Box`
- [ ] ✅ Replace `Navbar` with custom navigation using `Paper`
- [ ] ✅ Replace `Aside` with `Paper` sidebar
- [ ] ✅ Replace `Footer` with `Paper` footer

### **Styling Updates**
- [ ] ✅ Replace all `sx` props with `style` props
- [ ] ✅ Update `height`/`width` to `h`/`w`
- [ ] ✅ Update `spacing` to `gap`
- [ ] ✅ Update `position` to `justify`

### **Icon Props**
- [ ] ✅ Replace `icon` with `leftSection` in Menu.Item
- [ ] ✅ Update ActionIcon usage patterns

## Performance Optimizations

### **Bundle Size Reduction**
- Removed deprecated components
- Optimized imports to use tree-shaking
- Updated to modern Mantine architecture

### **Runtime Performance**
- Eliminated legacy layout calculations
- Improved CSS-in-JS performance with style props
- Better component re-render optimization

## Testing Strategy

### **Component Testing**
```typescript
// Test updated components
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import Topbar from './Topbar';

test('Topbar renders correctly with Mantine v8', () => {
  render(
    <MantineProvider>
      <Topbar />
    </MantineProvider>
  );
  
  expect(screen.getByRole('banner')).toBeInTheDocument();
});
```

### **Visual Regression Testing**
- Verify all components render correctly
- Check responsive behavior
- Validate theme application

## Migration Benefits

### **Modern Architecture**
- ✅ Latest Mantine v8.3.x features
- ✅ Improved performance and bundle size
- ✅ Better TypeScript support
- ✅ Enhanced accessibility

### **Future-Proof Design**
- ✅ Aligned with Mantine's long-term roadmap
- ✅ Compatible with React 18+ features
- ✅ Optimized for modern browsers

## Troubleshooting

### **Common Issues**

1. **Import Errors**
   ```typescript
   // Error: 'Header' is not exported from '@mantine/core'
   // Solution: Use Paper or Box instead
   import { Paper } from '@mantine/core';
   ```

2. **Styling Issues**
   ```typescript
   // Error: sx prop not recognized
   // Solution: Use style prop
   style={{ padding: '1rem' }} // ✅
   sx={{ padding: 16 }} // ❌
   ```

3. **Theme Conflicts**
   ```typescript
   // Ensure theme is properly configured for v8
   import { createTheme } from '@mantine/core';
   ```

### **Debug Commands**
```bash
# Check for deprecated component usage
grep -r "Header\|Navbar\|Aside\|Footer" apps/dashboard/src/

# Find sx prop usage
grep -r "sx=" apps/dashboard/src/

# Verify Mantine imports
grep -r "@mantine/core" apps/dashboard/src/
```

## Related Documentation

- [Pusher Migration Guide](./pusher-migration-2025.md)
- [Component Testing Strategy](../../05-implementation/testing/)
- [Theme Configuration](../../../dashboard/THEME_GUIDE.md)

---

*Last Updated: September 27, 2025*
*Mantine Version: v8.3.1*
*Migration Status: ✅ Complete*
