# UI Library Alternatives to Material-UI

## Recommended Alternatives

Due to persistent MUI module compatibility issues with Vite and Docker, here are the best alternatives:

## 1. **Ant Design (antd)** - RECOMMENDED
Best for enterprise applications with comprehensive components.

### Advantages:
- ✅ Excellent Vite compatibility
- ✅ No complex polyfills needed
- ✅ Comprehensive component library
- ✅ Built-in form validation
- ✅ Professional design system
- ✅ Great TypeScript support

### Installation:
```bash
npm uninstall @mui/material @mui/icons-material @mui/system @emotion/react @emotion/styled
npm install antd @ant-design/icons
```

### Basic Setup:
```tsx
// main.tsx
import 'antd/dist/reset.css';

// Component usage
import { Button, Card, Form, Input, Layout } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

function LoginForm() {
  return (
    <Card title="Login">
      <Form>
        <Form.Item name="username">
          <Input prefix={<UserOutlined />} placeholder="Username" />
        </Form.Item>
        <Form.Item name="password">
          <Input.Password prefix={<LockOutlined />} placeholder="Password" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block>
          Log in
        </Button>
      </Form>
    </Card>
  );
}
```

### Vite Config for Ant Design:
```ts
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['antd', '@ant-design/icons']
  }
});
```

## 2. **Mantine** - Modern Alternative
Best for modern React applications with hooks-first approach.

### Advantages:
- ✅ Built for modern React (hooks-first)
- ✅ Excellent Vite support
- ✅ Dark mode built-in
- ✅ Smaller bundle size than MUI
- ✅ No CSS-in-JS runtime

### Installation:
```bash
npm uninstall @mui/material @mui/icons-material @mui/system @emotion/react @emotion/styled
npm install @mantine/core @mantine/hooks @mantine/form @tabler/icons-react
```

### Basic Setup:
```tsx
// main.tsx
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';

function App() {
  return (
    <MantineProvider>
      <YourApp />
    </MantineProvider>
  );
}

// Component usage
import { Button, Card, TextInput, PasswordInput } from '@mantine/core';
import { IconUser, IconLock } from '@tabler/icons-react';

function LoginForm() {
  return (
    <Card shadow="sm" padding="lg">
      <TextInput
        label="Username"
        placeholder="Enter username"
        leftSection={<IconUser size={16} />}
      />
      <PasswordInput
        label="Password"
        placeholder="Enter password"
        leftSection={<IconLock size={16} />}
      />
      <Button fullWidth mt="md">
        Log in
      </Button>
    </Card>
  );
}
```

## 3. **Chakra UI**
Good for custom designs with utility-first approach.

### Advantages:
- ✅ Excellent accessibility
- ✅ Modular architecture
- ✅ Theme customization
- ✅ Works well with Vite

### Installation:
```bash
npm uninstall @mui/material @mui/icons-material @mui/system @emotion/react @emotion/styled
npm install @chakra-ui/react @chakra-ui/icons
```

## 4. **Tailwind UI + Headless UI**
Best for complete control with utility classes.

### Advantages:
- ✅ No runtime overhead
- ✅ Complete design control
- ✅ Excellent performance
- ✅ No bundler issues

### Installation:
```bash
npm uninstall @mui/material @mui/icons-material @mui/system @emotion/react @emotion/styled
npm install tailwindcss @headlessui/react heroicons
```

## Migration Strategy

### Phase 1: Install New Library
```bash
# For Ant Design (Recommended)
npm install antd @ant-design/icons

# Keep MUI temporarily for gradual migration
```

### Phase 2: Update Core Components
1. Start with simple components (Button, Card, Input)
2. Move to layout components (Grid, Layout)
3. Update complex components (Tables, Forms)
4. Replace icons

### Phase 3: Update Vite Config
```ts
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: [
      'antd',
      '@ant-design/icons',
      'react',
      'react-dom',
      '@clerk/clerk-react',
      'pusher-js'
    ],
    // Remove all MUI-related excludes
    exclude: ['fsevents']
  },
  server: {
    hmr: false // Keep disabled for Docker
  }
});
```

### Phase 4: Remove MUI
```bash
npm uninstall @mui/material @mui/icons-material @mui/system @mui/base @emotion/react @emotion/styled
```

## Component Mapping (MUI → Ant Design)

| MUI Component | Ant Design Component |
|--------------|---------------------|
| Box | div with className |
| Button | Button |
| TextField | Input |
| Card | Card |
| Grid | Row/Col |
| Typography | Typography.Text/Title |
| IconButton | Button with icon |
| Dialog | Modal |
| Snackbar | message/notification |
| AppBar | Header (Layout) |
| Drawer | Drawer |
| Tabs | Tabs |
| Table | Table |
| CircularProgress | Spin |
| Alert | Alert |

## Quick Start with Ant Design

### 1. Install Dependencies
```bash
cd apps/dashboard
npm install antd @ant-design/icons dayjs
```

### 2. Update main.tsx
```tsx
import 'antd/dist/reset.css';
import { ConfigProvider } from 'antd';

// Wrap app with ConfigProvider
<ConfigProvider theme={{
  token: {
    colorPrimary: '#1976d2',
  },
}}>
  <App />
</ConfigProvider>
```

### 3. Convert a Component
```tsx
// Before (MUI)
import { Button, TextField, Card, CardContent } from '@mui/material';

// After (Ant Design)
import { Button, Input, Card } from 'antd';
```

## Docker Compatibility

All recommended libraries work perfectly in Docker without:
- Complex polyfills
- Module resolution issues
- WebSocket HMR problems
- Import/export errors

## Decision Matrix

| Feature | Ant Design | Mantine | Chakra UI | Tailwind UI |
|---------|-----------|---------|-----------|-------------|
| Vite Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Component Library | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| TypeScript | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Bundle Size | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Learning Curve | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Docker Compatible | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Recommendation

**Use Ant Design (antd)** for this project because:
1. Closest to MUI in terms of component completeness
2. Excellent enterprise features
3. No module resolution issues
4. Works perfectly with Vite and Docker
5. Great TypeScript support
6. Active community and documentation

---

*Created: September 21, 2025*
*Reason: Persistent MUI module compatibility issues with Vite in Docker*