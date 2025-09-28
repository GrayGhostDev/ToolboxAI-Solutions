# Mantine Migration Guide

## Overview
This guide documents the complete migration from Material-UI (MUI) to Mantine UI framework, completed on September 27, 2025.

## Table of Contents
- [Why Mantine?](#why-mantine)
- [Migration Status](#migration-status)
- [Component Mappings](#component-mappings)
- [Icon Migrations](#icon-migrations)
- [Theme Migration](#theme-migration)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Why Mantine?

Mantine was chosen as the replacement for Material-UI for several reasons:
- **Modern React Support**: Full compatibility with React 19
- **Better Performance**: Smaller bundle size and faster rendering
- **Rich Component Library**: Over 100+ components out of the box
- **TypeScript First**: Built with TypeScript from the ground up
- **Excellent DX**: Better developer experience with intuitive APIs
- **Customization**: Easier theming and styling system
- **Active Development**: Regular updates and community support

## Migration Status

### ✅ Completed
- Core page components (DashboardHome, Classes, Messages, Settings, Register)
- Layout components (Sidebar, Topbar, AppLayout)
- Common components (ErrorBoundary, LoadingOverlay, NotificationToast)
- Atomic design components (Button, Box, Badge, Avatar)
- Theme system (Roblox-inspired Mantine theme)
- Pusher integration with hooks
- WebSocket compatibility layer

### 🔄 In Progress
- Roblox 3D components (partial migration)
- Complex form components
- Data visualization components

### 📋 Remaining
- Legacy example components
- Test file updates
- Complete MUI dependency removal

## Component Mappings

### Basic Components

| Material-UI | Mantine | Notes |
|------------|---------|-------|
| `Box` | `Box` | Similar API, style prop instead of sx |
| `Typography` | `Text` | Use size/fw props for variants |
| `Button` | `Button` | leftSection/rightSection for icons |
| `TextField` | `TextInput` | Built-in error/description props |
| `Paper` | `Paper` | Similar usage |
| `Container` | `Container` | Same concept |
| `Divider` | `Divider` | Identical usage |

### Layout Components

| Material-UI | Mantine | Notes |
|------------|---------|-------|
| `Grid` + `Grid2` | `Grid` + `Grid.Col` | Use span prop instead of xs/sm/md |
| `Stack` | `Stack` | gap prop for spacing |
| `Box` (flex) | `Group` | Horizontal layout helper |
| `AppBar` | `Header` or `Paper` | Use Header for app bars |
| `Toolbar` | `Group` | Horizontal grouping |
| `Drawer` | `Drawer` | Similar API |

### Form Components

| Material-UI | Mantine | Example |
|------------|---------|---------|
| `TextField` | `TextInput` | `<TextInput label="Name" />` |
| `TextField` (password) | `PasswordInput` | Built-in toggle visibility |
| `TextField` (multiline) | `Textarea` | `<Textarea rows={4} />` |
| `Select` | `Select` | Use data array format |
| `Checkbox` | `Checkbox` | Same usage |
| `Radio` | `Radio` | Use Radio.Group |
| `Switch` | `Switch` | Identical |
| `Slider` | `Slider` | Similar API |
| `Autocomplete` | `Autocomplete` | Data-driven approach |

### Feedback Components

| Material-UI | Mantine | Notes |
|------------|---------|-------|
| `Alert` | `Alert` | Use color prop |
| `CircularProgress` | `Loader` | Various variants available |
| `LinearProgress` | `Progress` | Animated by default |
| `Skeleton` | `Skeleton` | Similar usage |
| `Snackbar` | `notifications.show()` | Use notifications system |
| `Dialog` | `Modal` | Centered by default |
| `Tooltip` | `Tooltip` | Wrap component |
| `Badge` | `Badge` | More variants |
| `Chip` | `Badge` or `Chip` | Badge for display, Chip for selection |

### Data Display

| Material-UI | Mantine | Notes |
|------------|---------|-------|
| `Avatar` | `Avatar` | Avatar.Group for multiple |
| `List` | `Stack` or `NavLink` | NavLink for navigation |
| `Table` | `Table` | Similar structure |
| `Card` | `Card` | Use Card.Section |
| `CardContent` | `Card.Section` | Nested sections |
| `CardActions` | `Card.Section` | With Group component |
| `Tabs` | `Tabs` | Tabs.List, Tabs.Tab, Tabs.Panel |
| `Accordion` | `Accordion` | Similar API |

### Navigation

| Material-UI | Mantine | Notes |
|------------|---------|-------|
| `Menu` + `MenuItem` | `Menu` + `Menu.Item` | Trigger-based |
| `IconButton` | `ActionIcon` | Various variants |
| `BottomNavigation` | Custom with `Group` | Build custom |
| `Breadcrumbs` | `Breadcrumbs` | Similar |
| `Pagination` | `Pagination` | More features |
| `SpeedDial` | `Affix` + `ActionIcon` | Build custom |
| `Stepper` | `Stepper` | Similar API |

## Icon Migrations

### Installation
```bash
# Remove MUI icons
npm uninstall @mui/icons-material

# Install Tabler icons
npm install @tabler/icons-react
```

### Common Icon Mappings

| MUI Icon | Tabler Icon |
|----------|-------------|
| `MenuIcon` | `IconMenu2` |
| `CloseIcon` | `IconX` |
| `HomeIcon` | `IconHome` |
| `SettingsIcon` | `IconSettings` |
| `PersonIcon` | `IconUser` |
| `GroupIcon` | `IconUsers` |
| `SchoolIcon` | `IconSchool` |
| `DashboardIcon` | `IconDashboard` |
| `NotificationsIcon` | `IconBell` |
| `SearchIcon` | `IconSearch` |
| `AddIcon` | `IconPlus` |
| `EditIcon` | `IconEdit` |
| `DeleteIcon` | `IconTrash` |
| `CheckIcon` | `IconCheck` |
| `ErrorIcon` | `IconAlertCircle` |
| `InfoIcon` | `IconInfoCircle` |
| `WarningIcon` | `IconAlertTriangle` |
| `PlayArrowIcon` | `IconPlayerPlay` |
| `PauseIcon` | `IconPlayerPause` |
| `RefreshIcon` | `IconRefresh` |
| `DownloadIcon` | `IconDownload` |
| `UploadIcon` | `IconUpload` |
| `SendIcon` | `IconSend` |
| `SaveIcon` | `IconDeviceFloppy` |
| `FilterListIcon` | `IconFilter` |
| `SortIcon` | `IconArrowsSort` |
| `VisibilityIcon` | `IconEye` |
| `VisibilityOffIcon` | `IconEyeOff` |
| `LockIcon` | `IconLock` |
| `LogoutIcon` | `IconLogout` |

### Icon Usage Pattern

```typescript
// MUI (old)
import MenuIcon from '@mui/icons-material/Menu';
<IconButton onClick={handleClick}>
  <MenuIcon />
</IconButton>

// Mantine (new)
import { IconMenu2 } from '@tabler/icons-react';
<ActionIcon onClick={handleClick}>
  <IconMenu2 size={20} />
</ActionIcon>
```

## Theme Migration

### Theme File Location
- **Old**: `src/theme/robloxTheme.ts` (MUI)
- **New**: `src/theme/mantine-theme.ts` (Mantine)

### Theme Usage

```typescript
// Old (MUI)
import { useTheme } from '@mui/material/styles';
const theme = useTheme();
const primaryColor = theme.palette.primary.main;

// New (Mantine)
import { useMantineTheme } from '@mantine/core';
const theme = useMantineTheme();
const primaryColor = theme.colors.brand[6];
```

### Color System

```typescript
// MUI palette
theme.palette.primary.main → theme.colors.brand[6]
theme.palette.secondary.main → theme.colors.gray[6]
theme.palette.error.main → theme.colors.red[6]
theme.palette.warning.main → theme.colors.orange[6]
theme.palette.info.main → theme.colors.blue[6]
theme.palette.success.main → theme.colors.green[6]
theme.palette.text.primary → theme.colors.gray[9]
theme.palette.text.secondary → theme.colors.gray[6]
theme.palette.background.default → theme.colors.gray[0]
theme.palette.background.paper → theme.white
```

### Styling Approach

```typescript
// Old (MUI makeStyles)
const useStyles = makeStyles((theme) => ({
  root: {
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.paper,
  }
}));

// New (Mantine)
// Option 1: Inline styles
<Box style={{ padding: theme.spacing.md, backgroundColor: theme.white }}>

// Option 2: createStyles
const useStyles = createStyles((theme) => ({
  root: {
    padding: theme.spacing.md,
    backgroundColor: theme.white,
  }
}));

// Option 3: Component props
<Box p="md" bg="white">
```

## Common Patterns

### Form with Validation

```typescript
// Mantine form hook
import { useForm } from '@mantine/form';

function LoginForm() {
  const form = useForm({
    initialValues: {
      email: '',
      password: '',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      password: (value) => (value.length < 6 ? 'Password too short' : null),
    },
  });

  return (
    <form onSubmit={form.onSubmit((values) => console.log(values))}>
      <TextInput
        label="Email"
        placeholder="your@email.com"
        {...form.getInputProps('email')}
      />
      <PasswordInput
        label="Password"
        placeholder="Password"
        {...form.getInputProps('password')}
      />
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

### Modal Dialog

```typescript
// Mantine Modal
import { Modal, Button } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';

function MyModal() {
  const [opened, { open, close }] = useDisclosure(false);

  return (
    <>
      <Button onClick={open}>Open modal</Button>
      <Modal opened={opened} onClose={close} title="Modal Title">
        Modal content
      </Modal>
    </>
  );
}
```

### Notifications

```typescript
// Mantine notifications
import { notifications } from '@mantine/notifications';

// Show notification
notifications.show({
  title: 'Success',
  message: 'Operation completed successfully',
  color: 'green',
});

// Update notification
const id = notifications.show({
  loading: true,
  title: 'Loading',
  message: 'Please wait...',
});

notifications.update({
  id,
  title: 'Done',
  message: 'Completed!',
  loading: false,
  color: 'green',
});
```

### Responsive Grid

```typescript
// Mantine Grid
<Grid>
  <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
    Column 1
  </Grid.Col>
  <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
    Column 2
  </Grid.Col>
  <Grid.Col span={{ base: 12, md: 12, lg: 4 }}>
    Column 3
  </Grid.Col>
</Grid>
```

## Troubleshooting

### Common Issues

#### 1. Style Props Not Working
**Issue**: `sx` prop doesn't work on Mantine components
**Solution**: Use `style` prop or component-specific style props

```typescript
// Wrong
<Box sx={{ padding: 2 }}>

// Correct
<Box style={{ padding: '16px' }}>
// Or
<Box p={16}>
```

#### 2. Typography Variants Missing
**Issue**: No `variant` prop on Text component
**Solution**: Use `size` and `fw` (font-weight) props

```typescript
// MUI
<Typography variant="h1">Title</Typography>

// Mantine
<Text size="xl" fw={700}>Title</Text>
```

#### 3. Icon Buttons Not Styled
**Issue**: ActionIcon looks different from IconButton
**Solution**: Use appropriate variant and size

```typescript
<ActionIcon variant="subtle" size="lg">
  <IconMenu2 size={20} />
</ActionIcon>
```

#### 4. Form Validation
**Issue**: No built-in validation like MUI
**Solution**: Use @mantine/form hook

```typescript
import { useForm } from '@mantine/form';
```

#### 5. Theme Colors
**Issue**: Can't access theme.palette
**Solution**: Use theme.colors with array indices

```typescript
// Primary color
theme.colors[theme.primaryColor][6]
// Or specific color
theme.colors.blue[6]
```

### Migration Checklist

When migrating a component:

- [ ] Replace all MUI imports with Mantine equivalents
- [ ] Update all MUI icons to Tabler icons
- [ ] Change `sx` prop to `style` or component props
- [ ] Update Typography to Text with appropriate props
- [ ] Replace makeStyles with createStyles or inline styles
- [ ] Update Grid system to use span prop
- [ ] Replace Snackbar with notifications
- [ ] Update theme color references
- [ ] Test responsive behavior
- [ ] Verify accessibility

## Resources

- [Mantine Documentation](https://mantine.dev)
- [Tabler Icons](https://tabler-icons.io)
- [Migration Examples](./examples/migration/)
- [Component Demos](https://mantine.dev/core/button/)

## Support

For questions or issues with the migration:
1. Check this guide first
2. Review the Mantine documentation
3. Check the example components
4. Ask in the team chat

---

*Last Updated: September 27, 2025*
*Migration completed by: Claude AI with team supervision*