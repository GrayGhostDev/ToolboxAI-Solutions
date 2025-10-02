/**
 * Mantine Component Bridge - Complete Mantine components with MUI-compatible names
 * This file provides proper Mantine components for legacy code using MUI-style imports
 * All components are fully functional Mantine components
 *
 * TypeScript 5.9+ with bundler resolution - explicit re-exports for proper type resolution
 */

// Explicit re-exports for commonly used Mantine core components (TypeScript 5.9 best practice)
export {
  // Layout Components
  Box, Container, Paper, Stack, Grid, SimpleGrid, Group, Flex, Center, Space, Divider,

  // Typography (Text exported as Typography alias below)
  Text, Title, Code, Mark, Highlight,

  // Buttons & Actions (ActionIcon exported as IconButton alias below)
  ActionIcon, Button, CloseButton, UnstyledButton, CopyButton, FileButton,

  // Form Inputs (TextInput exported as TextField alias below)
  TextInput, Textarea, PasswordInput, NumberInput, Select, MultiSelect, Checkbox, Radio, Switch,
  Slider, RangeSlider, Rating, ColorInput, ColorPicker, FileInput, JsonInput, PinInput, Autocomplete,
  SegmentedControl, Chip, TagsInput,

  // Data Display (Loader exported as CircularProgress, Progress as LinearProgress aliases below)
  Loader, Progress, Table, Card, Avatar, Badge, Image, Skeleton, RingProgress, ThemeIcon,
  Timeline, Stepper, Tabs, Accordion, List, NavLink,

  // Overlays (Modal exported as Dialog alias below)
  Modal, Drawer, Popover, Tooltip, Menu, HoverCard, Overlay, LoadingOverlay,

  // Notifications & Feedback
  Alert, Notification,

  // Navigation
  Anchor, Breadcrumbs, Pagination,

  // Misc (Transition exported as Fade alias below)
  Transition, Indicator, Collapse, ScrollArea, Affix, Portal, FocusTrap,
  AppShell, Burger, ColorSwatch, AspectRatio, BackgroundImage, Blockquote, Spoiler,

  // Hooks & Theme (useMantineTheme and MantineProvider exported as useTheme/ThemeProvider aliases below)
  useMantineTheme, MantineProvider, rem,

  // Input Components
  Input, InputBase, Combobox, Pill, PillsInput,

  // Advanced
  Fieldset, NativeSelect, NumberFormatter, SemiCircleProgress, TableOfContents, Tree, VisuallyHidden,

  // Floating
  FloatingIndicator
} from '@mantine/core';

// Export ALL types explicitly (TypeScript 5.9 requirement for bundler mode)
export type {
  BoxProps, ButtonProps, AvatarProps, MantineThemeOverride, MantineColorScheme, MantineColorsTuple, DEFAULT_THEME,
  TextProps, TitleProps, CardProps, ModalProps, DrawerProps, TableProps, TabsProps, AccordionProps,
  TextInputProps, PasswordInputProps, NumberInputProps, SelectProps, CheckboxProps, RadioProps, SwitchProps,
  AlertProps, BadgeProps, LoaderProps, ProgressProps, PaperProps, StackProps, GridProps, GroupProps, FlexProps
} from '@mantine/core';

// Export notifications separately
export { notifications } from '@mantine/notifications';

// MUI compatibility aliases
export { Text as Typography } from '@mantine/core';
export { ActionIcon as IconButton } from '@mantine/core';
export { Loader as CircularProgress } from '@mantine/core';
export { Progress as LinearProgress } from '@mantine/core';
export { Modal as Dialog } from '@mantine/core';
export { TextInput as TextField } from '@mantine/core';
export { Transition as Fade } from '@mantine/core';

// Export wrapper components from separate file
export * from './mui-imports-components';

// Theme-related exports
export { useMantineTheme as useTheme } from '@mantine/core';
export { MantineProvider as ThemeProvider } from '@mantine/core';

// Utility functions
export const createTheme = (options: any) => options;
export const alpha = (color: string, _opacity: number) => color;
export const styled = (component: any) => component;
