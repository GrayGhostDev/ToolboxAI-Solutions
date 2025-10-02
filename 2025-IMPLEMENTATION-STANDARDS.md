# 2025 Implementation Standards - Roblox Dashboard

**Last Updated**: 2025-10-01
**Status**: ✅ Official Standards
**Permission Mode**: acceptEdits ENABLED

---

## 🚨 CRITICAL REQUIREMENTS

### 1. React 19.1.0 Standards

**MANDATORY PATTERNS:**
- ✅ Functional components ONLY (no class components)
- ✅ React hooks for all state management
- ✅ Server components where applicable
- ✅ Concurrent rendering features
- ❌ NO deprecated lifecycle methods
- ❌ NO legacy context API

**Example:**
```typescript
// ✅ CORRECT: Modern React 19 functional component
import React, { useState, useEffect, memo } from 'react';

interface Props {
  userId: string;
}

export const UserProfile = memo(({ userId }: Props) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return <div>{user?.name}</div>;
});

// ❌ WRONG: Class component (deprecated)
class UserProfile extends React.Component { ... }
```

---

### 2. TypeScript 5.9.2 Standards

**MANDATORY:**
- ✅ Strict mode enabled
- ✅ Modern decorators
- ✅ Explicit return types for functions
- ✅ Interface over type for object shapes
- ❌ NO `any` types
- ❌ NO implicit returns without types

**tsconfig.json Requirements:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUncheckedIndexedAccess": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler"
  }
}
```

**Example:**
```typescript
// ✅ CORRECT: Strict typing with interfaces
interface UserData {
  id: string;
  name: string;
  email: string;
}

async function fetchUser(id: string): Promise<UserData> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}

// ❌ WRONG: Using any
async function fetchUser(id: any): Promise<any> { ... }
```

---

### 3. Mantine v8 UI Framework

**MANDATORY:**
- ✅ Use Mantine components exclusively
- ✅ Follow Mantine theme system
- ✅ Use Mantine hooks (@mantine/hooks)
- ❌ NO Material-UI components
- ❌ NO legacy UI libraries

**Example:**
```typescript
// ✅ CORRECT: Mantine v8 components
import { Box, Button, Text, Card } from '@mantine/core';
import { useDisclosure, useMediaQuery } from '@mantine/hooks';

export function MyComponent() {
  const [opened, { toggle }] = useDisclosure(false);
  const isMobile = useMediaQuery('(max-width: 768px)');

  return (
    <Card shadow="sm" padding="lg">
      <Text size="lg" fw={700}>Title</Text>
      <Button onClick={toggle}>Toggle</Button>
    </Card>
  );
}

// ❌ WRONG: Material-UI (deprecated in this project)
import { Box, Button } from '@mui/material';
```

---

### 4. Vite 6.0.1 Build Tool

**MANDATORY:**
- ✅ ESM modules only
- ✅ Optimized dependencies in vite.config
- ✅ Environment variable prefixing (VITE_)
- ❌ NO CommonJS modules
- ❌ NO webpack-specific patterns

**vite.config.js Example:**
```javascript
// ✅ CORRECT: Modern Vite 6 config (JavaScript not TypeScript for external drives)
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['react', 'react-dom', '@mantine/core']
  },
  server: {
    port: 5181
  }
});
```

---

### 5. Testing with Vitest 3.2.4

**MANDATORY:**
- ✅ Vitest for all tests
- ✅ React Testing Library
- ✅ Coverage > 80%
- ❌ NO Jest (use Vitest)
- ❌ NO Enzyme

**Example:**
```typescript
// ✅ CORRECT: Vitest + React Testing Library
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(
      <MantineProvider>
        <MyComponent />
      </MantineProvider>
    );
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

---

### 6. ESLint 9 Flat Config

**MANDATORY:**
- ✅ Flat config system (eslint.config.js)
- ✅ React hooks rules enabled
- ✅ TypeScript ESLint plugin
- ❌ NO .eslintrc.json (deprecated)

**eslint.config.js Example:**
```javascript
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import tseslint from '@typescript-eslint/eslint-plugin';

export default [
  js.configs.recommended,
  {
    plugins: {
      'react-hooks': reactHooks,
      '@typescript-eslint': tseslint
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn'
    }
  }
];
```

---

## 🎨 Roblox Theme Standards

### Color Palette (2025 Edition)

```typescript
// Official Roblox 2025 color palette
export const robloxColors2025 = {
  // Neon colors with enhanced vibrancy
  neon: {
    electricBlue: '#00ffff',    // Primary accent
    hotPink: '#ff00ff',         // Secondary accent
    toxicGreen: '#00ff00',      // Success/achievements
    laserOrange: '#ff8800',     // Warnings/levels
    plasmaYellow: '#ffff00',    // XP/rewards
    deepPurple: '#9945ff',      // Epic items
    ultraViolet: '#7b00ff',     // Legendary items
  },

  // Gradient overlays
  gradients: {
    xpBar: 'linear-gradient(90deg, #ff00ff 0%, #00ffff 100%)',
    achievement: 'linear-gradient(135deg, #ffff00 0%, #ff8800 100%)',
    legendary: 'linear-gradient(135deg, #7b00ff 0%, #ff00ff 100%)',
    cyberpunk: 'linear-gradient(45deg, #00ffff 0%, #9945ff 50%, #ff00ff 100%)'
  },

  // Game-specific colors
  gamification: {
    health: '#00ff00',
    mana: '#00ccff',
    xp: '#ff00ff',
    level: '#ffff00',
    achievement: '#ff8800'
  }
};
```

---

### Component Architecture

**MANDATORY PATTERNS:**

```typescript
// ✅ Component structure standard
import React, { memo } from 'react';
import { Box, Button } from '@mantine/core';
import { useMantineTheme } from '@mantine/core';
import type { ReactNode } from 'react';

interface ComponentProps {
  children?: ReactNode;
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
}

/**
 * Component description
 * @param props - Component props
 * @returns Rendered component
 */
export const MyComponent = memo(({
  children,
  variant = 'primary',
  onClick
}: ComponentProps) => {
  const theme = useMantineTheme();

  return (
    <Box>
      <Button variant={variant} onClick={onClick}>
        {children}
      </Button>
    </Box>
  );
});

MyComponent.displayName = 'MyComponent';
```

---

### Animation Standards

**MANDATORY:**
- ✅ Respect `prefers-reduced-motion`
- ✅ 60 FPS target
- ✅ CSS animations over JavaScript where possible
- ✅ Framer Motion for complex animations

**Example:**
```typescript
import { motion } from 'framer-motion';

export const AnimatedCard = () => {
  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: prefersReducedMotion ? 0 : 0.3
      }}
    >
      Content
    </motion.div>
  );
};
```

---

### Accessibility Standards

**MANDATORY:**
- ✅ WCAG 2.1 AA compliance minimum
- ✅ Semantic HTML
- ✅ ARIA labels where needed
- ✅ Keyboard navigation
- ✅ Focus indicators

**Example:**
```typescript
<Button
  aria-label="View achievements"
  onClick={handleClick}
  tabIndex={0}
>
  Achievements
</Button>
```

---

## 🔧 Development Workflow

### File Organization

```
src/
├── components/
│   └── roblox/           # Roblox-specific components
│       ├── Button/
│       │   ├── Roblox3DButton.tsx
│       │   ├── Roblox3DButton.test.tsx
│       │   └── index.ts
│       └── index.ts      # Barrel export
├── theme/
│   ├── mantine-theme.ts  # Mantine theme config
│   └── robloxTheme.ts    # Roblox colors
├── hooks/
│   └── useRobloxTheme.ts
├── utils/
│   └── animations.ts
└── types/
    └── roblox.ts
```

---

### Import Standards

```typescript
// ✅ CORRECT: Organized imports
// 1. React
import React, { useState, useEffect } from 'react';

// 2. External libraries
import { Box, Button } from '@mantine/core';
import { motion } from 'framer-motion';

// 3. Internal modules
import { Roblox3DButton } from '@/components/roblox';
import { useRobloxTheme } from '@/hooks/useRobloxTheme';

// 4. Types
import type { RobloxColors } from '@/types/roblox';

// 5. Styles
import styles from './Component.module.css';
```

---

### Performance Standards

**MANDATORY:**
- ✅ React.memo for expensive components
- ✅ Lazy loading for routes and heavy components
- ✅ Code splitting with dynamic imports
- ✅ Image optimization (WebP format)
- ✅ Bundle size < 500KB (initial load)

**Example:**
```typescript
import { lazy, Suspense } from 'react';
import { Roblox3DLoader } from '@/components/roblox';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

export const App = () => (
  <Suspense fallback={<Roblox3DLoader />}>
    <HeavyComponent />
  </Suspense>
);
```

---

## 📋 Quality Gates

### Before Committing

- [ ] ✅ All TypeScript errors resolved
- [ ] ✅ ESLint passes with no warnings
- [ ] ✅ All tests pass (npm test)
- [ ] ✅ Test coverage > 80%
- [ ] ✅ Build succeeds (npm run build)
- [ ] ✅ No console.log statements in production code
- [ ] ✅ Component documented with JSDoc
- [ ] ✅ Accessibility checked

---

## 🚫 Deprecated Patterns to AVOID

### ❌ Class Components
```typescript
// DON'T DO THIS
class MyComponent extends React.Component {
  render() { return <div>Bad</div>; }
}
```

### ❌ Any Types
```typescript
// DON'T DO THIS
function doSomething(data: any) { ... }
```

### ❌ Material-UI in New Code
```typescript
// DON'T DO THIS
import { Button } from '@mui/material';
```

### ❌ Legacy Context API
```typescript
// DON'T DO THIS
const MyContext = React.createContext();
```

### ❌ Inline Styles Without Theme
```typescript
// DON'T DO THIS
<div style={{ color: '#ff0000' }}>Text</div>

// DO THIS INSTEAD
const theme = useMantineTheme();
<div style={{ color: theme.colors.red[5] }}>Text</div>
```

---

## 📚 Official Documentation Sources

**ALWAYS refer to 2025 official docs:**

- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/docs/
- **Mantine**: https://mantine.dev/
- **Vite**: https://vitejs.dev/
- **Vitest**: https://vitest.dev/
- **Framer Motion**: https://www.framer.com/motion/

**❌ DO NOT use:**
- Outdated tutorials from 2020-2023
- Stack Overflow answers without verification
- Legacy documentation
- Deprecated API references

---

## 🤖 Auto-Accept Mode Guidelines

With `acceptEdits` enabled, all corrections are automatic. Focus on:

1. **Write correct code first time** - follow standards strictly
2. **Test thoroughly** - auto-corrections won't catch logic errors
3. **Document clearly** - JSDoc comments for all exports
4. **Performance first** - optimize as you code

---

## ✅ Summary Checklist

Before ANY code is written:

- [ ] React 19 functional components
- [ ] TypeScript 5.9 strict mode
- [ ] Mantine v8 components
- [ ] Proper JSDoc documentation
- [ ] Test file created
- [ ] Accessibility considered
- [ ] Performance optimized
- [ ] Theme colors used (no hardcoded values)
- [ ] Animations respect reduced-motion
- [ ] Official 2025 docs referenced

---

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**Maintainer**: ToolboxAI Development Team
**Status**: ✅ Official Standards - MANDATORY COMPLIANCE
