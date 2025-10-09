# 2025 Implementation Standards

## 🚨 CRITICAL: Official Documentation Only

**MANDATORY RULE**: Use ONLY 2025 official implementation methods from source documentation.

### Official Documentation Sources
- **React**: https://react.dev (React 19 official docs)
- **TypeScript**: https://www.typescriptlang.org/docs (TypeScript 5.5+)
- **Vite**: https://vitejs.dev (Vite 6 docs)
- **Mantine**: https://mantine.dev (Mantine v8 docs)
- **Vitest**: https://vitest.dev (Vitest 3 docs)
- **Playwright**: https://playwright.dev
- **Three.js**: https://threejs.org/docs
- **React Query**: https://tanstack.com/query (when implemented)
- **Zustand**: https://docs.pmnd.rs/zustand (when implemented)

### ❌ DO NOT USE
- Stack Overflow answers (often outdated)
- Medium/Dev.to tutorials (may use deprecated patterns)
- YouTube tutorials (frequently use legacy code)
- ChatGPT/AI-generated code (without verification)
- Legacy documentation (pre-2024)
- Class components patterns
- Old React patterns (componentDidMount, etc.)

## React 19 Standards

### ✅ Functional Components Only
```typescript
// ✅ CORRECT - React 19 functional component
import { useState } from 'react';

interface Props {
  title: string;
  onUpdate: (value: string) => void;
}

export function MyComponent({ title, onUpdate }: Props) {
  const [value, setValue] = useState('');

  return (
    <div>
      <h1>{title}</h1>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
    </div>
  );
}
```

```typescript
// ❌ WRONG - Class components (deprecated)
class MyComponent extends React.Component {
  // Never use this pattern!
}
```

### ✅ Server Components (React 19)
```typescript
// ✅ CORRECT - Server Component with async data
async function UserProfile({ userId }: { userId: string }) {
  // Direct async/await in component body
  const user = await fetchUser(userId);

  return (
    <Card>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </Card>
  );
}
```

### ✅ Suspense Boundaries
```typescript
// ✅ CORRECT - Proper Suspense usage
import { Suspense } from 'react';
import { Skeleton } from '@mantine/core';

export function Dashboard() {
  return (
    <Suspense fallback={<Skeleton height={200} />}>
      <AsyncDashboardContent />
    </Suspense>
  );
}
```

### ✅ Modern Hooks
```typescript
// ✅ CORRECT - Use modern hooks
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';

function MyComponent() {
  // State
  const [count, setCount] = useState(0);

  // Memoized callback
  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  // Memoized value
  const expensiveValue = useMemo(() => {
    return computeExpensive(count);
  }, [count]);

  // Effects
  useEffect(() => {
    // Side effects
    return () => {
      // Cleanup
    };
  }, []);

  return <button onClick={handleClick}>{count}</button>;
}
```

```typescript
// ❌ WRONG - Lifecycle methods
componentDidMount() {
  // Never use this!
}
```

### ✅ Custom Hooks Pattern
```typescript
// ✅ CORRECT - Modern custom hook
import { useState, useEffect } from 'react';

export function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    function handleResize() {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    }

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return size;
}

// Usage
function MyComponent() {
  const { width, height } = useWindowSize();
  return <div>Window: {width}x{height}</div>;
}
```

## TypeScript 5.5+ Standards

### ✅ Strict Mode Required
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### ✅ Proper Type Definitions
```typescript
// ✅ CORRECT - Proper interfaces and types
interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'teacher' | 'student';
  createdAt: Date;
}

type UserRole = User['role'];

interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}

// Function with proper types
async function fetchUser(id: string): Promise<ApiResponse<User>> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

```typescript
// ❌ WRONG - Using 'any'
function fetchUser(id: any): Promise<any> {
  // Never use any!
}
```

### ✅ Generics
```typescript
// ✅ CORRECT - Proper generics
function useState<T>(initialValue: T): [T, (value: T) => void] {
  // Implementation
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick: (row: T) => void;
}

function DataTable<T extends { id: string }>({
  data,
  columns,
  onRowClick
}: DataTableProps<T>) {
  // Implementation
}
```

### ✅ Type Guards
```typescript
// ✅ CORRECT - Type guards
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    'email' in obj
  );
}

// Usage
function processData(data: unknown) {
  if (isUser(data)) {
    // TypeScript knows data is User here
    console.log(data.name);
  }
}
```

## Mantine v8 Standards

### ✅ Component Usage
```typescript
// ✅ CORRECT - Mantine v8 components
import {
  Box,
  Button,
  Text,
  Card,
  Grid,
  Stack,
  Group,
  TextInput,
  Modal
} from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';

function MyForm() {
  const [opened, setOpened] = useState(false);

  return (
    <>
      <Button
        leftSection={<IconPlus size={16} />}
        onClick={() => setOpened(true)}
      >
        Add Item
      </Button>

      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title="Add New Item"
      >
        <Stack gap="md">
          <TextInput label="Name" placeholder="Enter name" />
          <TextInput label="Email" placeholder="Enter email" />
          <Group justify="flex-end">
            <Button onClick={() => setOpened(false)}>Submit</Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
```

```typescript
// ❌ WRONG - Material-UI (deprecated in this project)
import { Button, TextField } from '@mui/material';
// Don't use MUI!
```

### ✅ Theme Usage
```typescript
// ✅ CORRECT - Mantine theme
import { useMantineTheme, useMantineColorScheme } from '@mantine/core';

function ThemedComponent() {
  const theme = useMantineTheme();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();

  return (
    <Box style={{ backgroundColor: theme.colors.dark[7] }}>
      <Button onClick={toggleColorScheme}>
        Toggle {colorScheme === 'dark' ? 'Light' : 'Dark'}
      </Button>
    </Box>
  );
}
```

### ✅ Forms
```typescript
// ✅ CORRECT - Mantine forms
import { useForm } from '@mantine/form';
import { TextInput, Button } from '@mantine/core';

interface FormValues {
  name: string;
  email: string;
}

function MyForm() {
  const form = useForm<FormValues>({
    initialValues: {
      name: '',
      email: ''
    },
    validate: {
      name: (value) => value.length < 2 ? 'Name is too short' : null,
      email: (value) => /^\S+@\S+$/.test(value) ? null : 'Invalid email'
    }
  });

  return (
    <form onSubmit={form.onSubmit((values) => console.log(values))}>
      <TextInput
        label="Name"
        placeholder="Your name"
        {...form.getInputProps('name')}
      />
      <TextInput
        label="Email"
        placeholder="your@email.com"
        {...form.getInputProps('email')}
      />
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

### ✅ Notifications
```typescript
// ✅ CORRECT - Mantine notifications
import { notifications } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';

function showSuccess() {
  notifications.show({
    title: 'Success',
    message: 'Operation completed successfully',
    color: 'teal',
    icon: <IconCheck size={16} />
  });
}

function showError() {
  notifications.show({
    title: 'Error',
    message: 'Something went wrong',
    color: 'red',
    icon: <IconX size={16} />
  });
}
```

## Vite 6 Standards

### ✅ Configuration
```typescript
// ✅ CORRECT - Modern Vite config
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks')
    }
  },

  server: {
    port: 5179,
    proxy: {
      '/api': 'http://localhost:8009'
    }
  },

  build: {
    target: 'es2022',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-mantine': ['@mantine/core', '@mantine/hooks']
        }
      }
    }
  }
});
```

### ✅ Environment Variables
```typescript
// ✅ CORRECT - Vite env variables
// .env file
VITE_API_URL=http://localhost:8009
VITE_PUSHER_KEY=abc123

// Usage
const apiUrl = import.meta.env.VITE_API_URL;
const pusherKey = import.meta.env.VITE_PUSHER_KEY;
```

```typescript
// ❌ WRONG - process.env (doesn't work in Vite)
const apiUrl = process.env.REACT_APP_API_URL; // Wrong!
```

## Testing Standards (Vitest 3)

### ✅ Component Tests
```typescript
// ✅ CORRECT - Vitest + Testing Library
import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const onClick = vi.fn();
    render(<MyComponent onUpdate={onClick} />);

    await userEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('updates state correctly', async () => {
    render(<MyComponent />);
    const input = screen.getByRole('textbox');

    await userEvent.type(input, 'Hello');
    expect(input).toHaveValue('Hello');
  });
});
```

### ✅ Async Testing
```typescript
// ✅ CORRECT - Async testing
import { render, screen, waitFor } from '@testing-library/react';

describe('AsyncComponent', () => {
  it('loads data', async () => {
    render(<AsyncComponent userId="123" />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });
});
```

### ✅ Mock API
```typescript
// ✅ CORRECT - MSW for API mocking
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'John Doe'
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Code Quality Standards

### ✅ ESLint 9 (Flat Config)
```javascript
// ✅ CORRECT - eslint.config.js
import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';

export default [
  js.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      '@typescript-eslint': typescript,
      'react': react,
      'react-hooks': reactHooks
    },
    rules: {
      'react/react-in-jsx-scope': 'off',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      '@typescript-eslint/no-explicit-any': 'error'
    }
  }
];
```

### ✅ Prettier Configuration
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

## Performance Standards

### ✅ Code Splitting
```typescript
// ✅ CORRECT - Lazy loading
import { lazy, Suspense } from 'react';
import { Skeleton } from '@mantine/core';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));

function App() {
  return (
    <Suspense fallback={<Skeleton height={400} />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  );
}
```

### ✅ Memoization
```typescript
// ✅ CORRECT - Proper memoization
import { memo, useMemo, useCallback } from 'react';

interface Props {
  items: Item[];
  onItemClick: (id: string) => void;
}

export const ItemList = memo(function ItemList({ items, onItemClick }: Props) {
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => a.name.localeCompare(b.name));
  }, [items]);

  const handleClick = useCallback((id: string) => {
    onItemClick(id);
  }, [onItemClick]);

  return (
    <div>
      {sortedItems.map(item => (
        <Item key={item.id} item={item} onClick={handleClick} />
      ))}
    </div>
  );
});
```

## Accessibility Standards

### ✅ ARIA Labels
```typescript
// ✅ CORRECT - Proper accessibility
<Button
  aria-label="Close modal"
  onClick={onClose}
>
  <IconX />
</Button>

<TextInput
  label="Email"
  placeholder="your@email.com"
  aria-describedby="email-hint"
  aria-required="true"
/>
<Text id="email-hint" size="sm" c="dimmed">
  We'll never share your email
</Text>
```

### ✅ Keyboard Navigation
```typescript
// ✅ CORRECT - Keyboard support
function Modal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose();
      }
    }

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div role="dialog" aria-modal="true">
      {/* Modal content */}
    </div>
  );
}
```

## Git Commit Standards

### ✅ Conventional Commits
```bash
# Format: type(scope): description

feat(dashboard): add user profile component
fix(auth): resolve login redirect issue
docs(readme): update installation instructions
style(components): format code with Prettier
refactor(store): migrate from Redux to Zustand
test(hooks): add tests for useAuth hook
chore(deps): update Mantine to v8.3.2
```

## Documentation Standards

### ✅ Component Documentation
```typescript
/**
 * UserCard component displays user information in a card format.
 *
 * @param {string} userId - The ID of the user to display
 * @param {function} onEdit - Callback when edit button is clicked
 * @returns {JSX.Element} Rendered user card
 *
 * @example
 * ```tsx
 * <UserCard userId="123" onEdit={(id) => console.log(id)} />
 * ```
 */
export function UserCard({ userId, onEdit }: UserCardProps) {
  // Implementation
}
```

## Security Standards

### ✅ Input Validation
```typescript
// ✅ CORRECT - Validate user input
import { z } from 'zod';

const userSchema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
  age: z.number().min(0).max(150)
});

function validateUser(data: unknown) {
  return userSchema.parse(data); // Throws if invalid
}
```

### ✅ XSS Prevention
```typescript
// ✅ CORRECT - React handles XSS automatically
function UserComment({ comment }: { comment: string }) {
  // React escapes this automatically
  return <div>{comment}</div>;
}

// ❌ WRONG - dangerouslySetInnerHTML without sanitization
function UnsafeComment({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />; // Unsafe!
}
```

## Review Checklist

Before submitting code, verify:

- [ ] Uses React 19 patterns (no class components)
- [ ] TypeScript strict mode with no `any` types
- [ ] Mantine components (no Material-UI)
- [ ] Proper error handling
- [ ] Unit tests written (>80% coverage target)
- [ ] ESLint passes with no warnings
- [ ] TypeScript compiles with no errors
- [ ] Component is accessible (ARIA, keyboard nav)
- [ ] Performance optimized (memo, lazy loading)
- [ ] Documentation added/updated
- [ ] Follows conventional commits
- [ ] Reviewed official docs, not tutorials

---

**Last Updated**: 2025-10-01
**Standards Version**: 1.0.0
**Status**: Active
