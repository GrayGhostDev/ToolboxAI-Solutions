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
  SimpleGrid,
} from '@mantine/core';

// Aliases for MUI compatibility
export { Text as Typography } from '@mantine/core';
export { ActionIcon as IconButton } from '@mantine/core';
export { Loader as CircularProgress } from '@mantine/core';
export { Progress as LinearProgress } from '@mantine/core';
export { Modal as Dialog } from '@mantine/core';
export { TextInput as TextField } from '@mantine/core';

// Component sub-parts using proper Mantine components
export { Card as CardContent } from '@mantine/core';
export { Box as CardActions } from '@mantine/core';
export { Box as CardMedia } from '@mantine/core';
export { Box as CardHeader } from '@mantine/core';

export { List as ListItem } from '@mantine/core';
export { Text as ListItemText } from '@mantine/core';
export { Box as ListItemAvatar } from '@mantine/core';
export { Box as ListItemIcon } from '@mantine/core';
export { Box as ListItemButton } from '@mantine/core';

export { Title as DialogTitle } from '@mantine/core';
export { Box as DialogContent } from '@mantine/core';
export { Box as DialogActions } from '@mantine/core';
export { Text as DialogContentText } from '@mantine/core';

export { Box as FormControl } from '@mantine/core';
export { Text as InputLabel } from '@mantine/core';
export { Box as InputAdornment } from '@mantine/core';
export { Box as FormControlLabel } from '@mantine/core';

export { Table as TableBody } from '@mantine/core';
export { Table as TableCell } from '@mantine/core';
export { Box as TableContainer } from '@mantine/core';
export { Table as TableHead } from '@mantine/core';
export { Table as TableRow } from '@mantine/core';
export { Box as TablePagination } from '@mantine/core';

export { Box as AppBar } from '@mantine/core';
export { Box as Toolbar } from '@mantine/core';

export { Menu as MenuItem } from '@mantine/core';
export { Box as RadioGroup } from '@mantine/core';
export { Tabs as Tab } from '@mantine/core';
export { Title as AlertTitle } from '@mantine/core';

export { Button as ToggleButton } from '@mantine/core';
export { Box as ToggleButtonGroup } from '@mantine/core';

// Theme-related exports
export { useMantineTheme as useTheme } from '@mantine/core';
export { MantineProvider as ThemeProvider } from '@mantine/core';

// Missing components exported properly
export { Badge as Chip } from '@mantine/core';
export { Pagination } from '@mantine/core';
export { Autocomplete } from '@mantine/core';
export { SegmentedControl } from '@mantine/core';

// Stub functions to prevent errors
export const createTheme = (options: any) => options;
export const alpha = (color: string, opacity: number) => {
  // Simple alpha implementation for color transparency
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};
export const styled = (component: any) => component;