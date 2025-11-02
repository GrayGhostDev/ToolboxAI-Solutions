/**
 * MUI to Mantine Migration Compatibility Layer
 *
 * This file provides a compatibility layer for components that haven't been
 * fully migrated from MUI to Mantine yet. It re-exports Mantine components
 * with MUI-compatible names to minimize breaking changes during migration.
 */

import React from 'react';

// Import all necessary Mantine components
import {
  Box,
  Button,
  Text as Typography,
  Paper,
  Stack,
  Grid,
  Container,
  ActionIcon as IconButton,
  Avatar,
  Card,
  List,
  Divider,
  TextInput as TextField,
  Select,
  Badge as Chip,
  Badge,
  Alert,
  Loader as CircularProgress,
  Progress as LinearProgress,
  Modal as Dialog,
  Drawer,
  Tabs,
  Menu,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Skeleton
} from '@mantine/core';

// Additional components that might be needed
import { Text } from '@mantine/core';

// Export with MUI-compatible names for backward compatibility
export {
  Box,
  Button,
  Typography,
  Text,
  Paper,
  Stack,
  Grid,
  Container,
  IconButton,
  Avatar,
  Card,
  List,
  Divider,
  TextField,
  Select,
  Chip,
  Badge,
  Alert,
  CircularProgress,
  LinearProgress,
  Dialog,
  Drawer,
  Tabs,
  Menu,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Skeleton
};

// MUI-specific components that don't have direct Mantine equivalents
// Export as simple function components without JSX
export const CardContent = ({ children, ...props }: any) => React.createElement(Box, { p: 'md', ...props }, children);
export const CardActions = ({ children, ...props }: any) => React.createElement(Box, { p: 'md', pt: 0, ...props }, children);
export const ListItem = ({ children, ...props }: any) => React.createElement(List.Item, props, children);
export const ListItemAvatar = ({ children, ...props }: any) => React.createElement(Box, { ...props }, children);
export const ListItemText = ({ primary, secondary, ...props }: any) =>
  React.createElement(Box, props,
    React.createElement(Text, null, primary),
    secondary && React.createElement(Text, { size: 'sm', c: 'dimmed' }, secondary)
  );
export const DialogTitle = ({ children, ...props }: any) => React.createElement(Text, { size: 'lg', fw: 600, ...props }, children);
export const DialogContent = ({ children, ...props }: any) => React.createElement(Box, { p: 'md', ...props }, children);
export const DialogActions = ({ children, ...props }: any) => React.createElement(Box, { p: 'md', pt: 0, ...props }, children);
export const AppBar = ({ children, ...props }: any) => React.createElement(Box, props, children);
export const Toolbar = ({ children, ...props }: any) => React.createElement(Box, { p: 'md', ...props }, children);
export const Tab = ({ children, ...props }: any) => React.createElement(Tabs.Tab, props, children);
export const MenuItem = ({ children, ...props }: any) => React.createElement(Menu.Item, props, children);
export const RadioGroup = ({ children, ...props }: any) => React.createElement(Radio.Group, props, children);
export const FormControl = ({ children, ...props }: any) => React.createElement(Box, props, children);
export const FormControlLabel = ({ label, control, ...props }: any) =>
  React.createElement(Box, props,
    control,
    React.createElement(Text, { ml: 'xs' }, label)
  );
export const InputLabel = ({ children, ...props }: any) => React.createElement(Text, { size: 'sm', fw: 500, ...props }, children);
export const Rating = ({ ...props }) => React.createElement(Box, props, 'Rating Component'); // Placeholder
export const Autocomplete = ({ ...props }) => React.createElement(Select, props); // Use Select as fallback
export const Table = ({ children, ...props }: any) => React.createElement('table', props, children);

// Default export for backward compatibility
export default {
  Box,
  Button,
  Typography,
  Text,
  Paper,
  Stack,
  Grid,
  Container,
  IconButton,
  Avatar,
  Card,
  CardContent,
  CardActions,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
  TextField,
  Select,
  MenuItem,
  Chip,
  Badge,
  Alert,
  CircularProgress,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Drawer,
  AppBar,
  Toolbar,
  Tabs,
  Tab,
  Menu,
  Tooltip,
  Checkbox,
  Radio,
  RadioGroup,
  FormControl,
  FormControlLabel,
  InputLabel,
  Switch,
  Slider,
  Rating,
  Autocomplete,
  Skeleton,
  Table
};