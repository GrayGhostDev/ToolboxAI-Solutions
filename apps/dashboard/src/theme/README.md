# Mantine v8 Theme Configuration - Roblox Dashboard

This directory contains the modernized Mantine v8 compatible theme system for the Roblox Dashboard application.

## What Was Fixed

### 1. **Removed Deprecated Properties**
- ❌ Removed `colorScheme` property (deprecated in v8)
- ❌ Removed `globalStyles` property (not supported in v8)
- ✅ Added proper `MantineColorsTuple` type annotations

### 2. **Updated Component Styles**
- ✅ Replaced `theme.colorScheme` references with `light-dark()` CSS function
- ✅ Updated component style function signatures for v8 compatibility
- ✅ Fixed Modal styles to use `content` instead of `modal` property

### 3. **Modernized Color Scheme Handling**
- ✅ Uses Mantine v8's `light-dark()` CSS function for automatic color switching
- ✅ Leverages CSS custom properties (`var(--mantine-color-*)`)
- ✅ Color scheme is now controlled via `MantineProvider` props

### 4. **Global Styles Migration**
- ✅ Created separate `global-styles.css` file for global styles
- ✅ Added CSS utility classes for game effects
- ✅ Maintained same visual design with modern CSS approaches

## Files Structure

```
src/theme/
├── mantine-theme.ts      # Main theme configuration (v8 compatible)
├── global-styles.css     # Global CSS styles and animations
├── index.ts             # Centralized exports and utilities
└── README.md            # This documentation
```

## Usage

### 1. Basic Setup

```tsx
// App.tsx
import { MantineProvider } from '@mantine/core';
import { theme } from './theme';
import './theme/global-styles.css'; // Import global styles

function App() {
  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      <YourApp />
    </MantineProvider>
  );
}
```

### 2. Using Theme in Components

```tsx
// Component.tsx
import { useMantineTheme } from '@mantine/core';
import { getThemedStyles } from '../theme';

function MyComponent() {
  const theme = useMantineTheme();
  const styles = getThemedStyles(theme);

  return (
    <div style={styles.gameCard}>
      <h1 style={styles.neonText()}>Roblox Style!</h1>
    </div>
  );
}
```

### 3. Color Scheme Switching

```tsx
// ThemeToggle.tsx
import { Button } from '@mantine/core';
import { useComputedColorScheme, useMantineColorScheme } from '@mantine/core';

function ThemeToggle() {
  const { setColorScheme } = useMantineColorScheme();
  const computedColorScheme = useComputedColorScheme('light');

  return (
    <Button
      onClick={() => setColorScheme(computedColorScheme === 'dark' ? 'light' : 'dark')}
    >
      Toggle {computedColorScheme === 'dark' ? 'Light' : 'Dark'} Mode
    </Button>
  );
}
```

### 4. Using Roblox Colors

```tsx
// Component.tsx
import { Box } from '@mantine/core';
import { robloxColors } from '../theme';

function RobloxButton() {
  return (
    <Box
      bg={robloxColors.brand[5]}
      c={robloxColors.neon[2]}
      p="md"
      style={{ borderRadius: '8px' }}
    >
      Roblox Styled Box
    </Box>
  );
}
```

## Available Exports

### Theme Configuration
- `mantineTheme` - Main Mantine v8 theme object
- `theme` - Alias for mantineTheme
- `robloxColors` - Complete color palette with proper TypeScript types

### Utilities
- `themeUtils` - Color manipulation utilities
- `getThemedStyles()` - Pre-built style patterns
- `themePatterns` - CSS pattern constants for v8

### Global Styles
- `globalStyles` - JavaScript object with global styles
- `globalStylesCSS` - CSS string for injection
- `global-styles.css` - Standalone CSS file

## Migration Benefits

1. **Future-Proof**: Compatible with Mantine v8 and future versions
2. **Performance**: Better CSS-in-JS performance with modern patterns
3. **Type Safety**: Full TypeScript support with proper type annotations
4. **Maintainability**: Clear separation of concerns between theme and global styles
5. **Developer Experience**: Better autocomplete and error detection

## CSS Utility Classes

The global CSS file includes utility classes for game effects:

```css
.roblox-glow        /* Glowing animation effect */
.roblox-float       /* Floating animation */
.roblox-pulse       /* Pulsing animation */
.glass-morphism     /* Glass morphism background */
.neon-border        /* Neon glow border effect */
.neon-text          /* Neon text effect */
```

## Backward Compatibility

The theme system maintains backward compatibility through:
- Alias exports (`robloxTheme` → `mantineTheme`)
- Same color palette structure
- Preserved visual design
- Similar component styling patterns

## Development

To test the theme:

```bash
# Check TypeScript compilation
npx tsc --noEmit src/theme/mantine-theme.ts --skipLibCheck

# Run the development server
npm run dev
```

The theme is now fully compatible with Mantine v8 and ready for production use!