// Mantine Component Bridge - Pure Mantine exports with MUI-compatible names
// This file provides compatibility for legacy code still using MUI-style imports
// All components are from @mantine/core ONLY - no MUI dependencies

// Re-export everything directly from Mantine
export {
  // Core components
  Box,
  Button,
  Text,
  Title,
  Paper,
  Stack,
  Grid,
  Container,
  ActionIcon,
  Avatar,
  Card,
  Group,
  Image,
  List,
  Divider,
  TextInput,
  Select,
  Menu,
  Badge,
  Alert,
  Loader,
  Progress,
  Skeleton,
  Modal,
  Drawer,
  AppShell,
  Table,
  Tabs,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Rating,
  ScrollArea,
  useMantineTheme,
  MantineProvider,
} from '@mantine/core';

// Aliases for MUI compatibility
export { Text as Typography } from '@mantine/core';
export { ActionIcon as IconButton } from '@mantine/core';
export { Loader as CircularProgress } from '@mantine/core';
export { Progress as LinearProgress } from '@mantine/core';
export { Modal as Dialog } from '@mantine/core';
export { TextInput as TextField } from '@mantine/core';

// Component sub-parts as simple exports
export const CardContent = 'div' as const;
export const CardActions = 'div' as const;
export const CardMedia = 'div' as const;
export const CardHeader = 'div' as const;

export const ListItem = 'li' as const;
export const ListItemText = 'span' as const;
export const ListItemAvatar = 'div' as const;
export const ListItemIcon = 'div' as const;
export const ListItemButton = 'div' as const;

export const DialogTitle = 'h2' as const;
export const DialogContent = 'div' as const;
export const DialogActions = 'div' as const;
export const DialogContentText = 'p' as const;

export const FormControl = 'div' as const;
export const InputLabel = 'label' as const;
export const InputAdornment = 'div' as const;
export const FormControlLabel = 'label' as const;

export const TableBody = 'tbody' as const;
export const TableCell = 'td' as const;
export const TableContainer = 'div' as const;
export const TableHead = 'thead' as const;
export const TableRow = 'tr' as const;
export const TablePagination = 'div' as const;

export const AppBar = 'header' as const;
export const Toolbar = 'div' as const;

export const MenuItem = 'li' as const;
export const RadioGroup = 'div' as const;
export const Tab = 'button' as const;
export const AlertTitle = 'h3' as const;

export const ToggleButton = 'button' as const;
export const ToggleButtonGroup = 'div' as const;

// Theme-related exports
export { useMantineTheme as useTheme } from '@mantine/core';
export { MantineProvider as ThemeProvider } from '@mantine/core';

// Missing components exported as stubs
export const Chip = 'span' as const;
export const Pagination = 'div' as const;
export const Autocomplete = 'input' as const;
export const SegmentedControl = 'div' as const;

// Stub functions to prevent errors
export const createTheme = (options: any) => options;
export const alpha = (color: string, _opacity: number) => color;
export const styled = (component: any) => component;