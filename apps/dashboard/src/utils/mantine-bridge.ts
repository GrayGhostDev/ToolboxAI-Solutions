/**
 * Mantine Bridge - Complete MUI to Mantine Migration Helper
 * This module provides direct exports from Mantine with MUI-compatible names
 * to enable gradual migration from Material UI to Mantine
 */

// Core Mantine Components
export {
  Box,
  Button,
  Container,
  Paper,
  Text,
  Title,
  Group,
  Stack,
  Grid,
  SimpleGrid,
  Center,
  Divider,
  Space,
  Avatar,
  Badge,
  ActionIcon,
  Loader,
  Progress,
  Card,
  Overlay,
  ScrollArea,
  AspectRatio,
  Image,
  BackgroundImage,
  Anchor,
  Breadcrumbs,
  Burger,
  CloseButton,
  CopyButton,
  FileButton,
  UnstyledButton,
  ThemeIcon,
  Timeline,
  List,
  Table,
  Skeleton,
  Indicator,
  Kbd,
  Mark,
  Highlight,
  Blockquote,
  Code,
  Alert,
  Notification,
  // Form Components
  TextInput,
  PasswordInput,
  Textarea,
  Select,
  MultiSelect,
  Autocomplete,
  NumberInput,
  Radio,
  Checkbox,
  Switch,
  Slider,
  RangeSlider,
  SegmentedControl,
  ColorPicker,
  ColorInput,
  FileInput,
  JsonInput,
  PinInput,
  Rating,
  TransferList,
  Chip,
  ChipsInput,
  TagsInput,
  // Navigation
  Tabs,
  Stepper,
  Pagination,
  NavLink,
  Affix,
  // Feedback
  Modal,
  Drawer,
  Dialog,
  LoadingOverlay,
  Tooltip,
  Popover,
  HoverCard,
  Menu,
  // Layout
  AppShell,
  Header,
  Footer,
  Navbar,
  Aside,
  MediaQuery,
  // Data Display
  Accordion,
  Spoiler,
  // Typography
  Text as Typography,
  Title as Heading,
  // Utilities
  Portal,
  Transition,
  Collapse,
  FocusTrap,
  // Dates (if using Mantine dates)
  // DatePicker,
  // DateTimePicker,
  // TimeInput,
  // Calendar,
  // DateInput,
  // DateRangePicker,
  // MonthPicker,
  // YearPicker,
} from '@mantine/core';

// Hooks
export {
  useDisclosure,
  useToggle,
  useClipboard,
  useColorScheme,
  useCounter,
  useDebounce,
  useDebouncedState,
  useDebouncedValue,
  useDocumentTitle,
  useDocumentVisibility,
  useElementSize,
  useEventListener,
  useFocusReturn,
  useFocusTrap,
  useFocusWithin,
  useFullscreen,
  useHotkeys,
  useHover,
  useIdle,
  useIntersection,
  useInterval,
  useListState,
  useLocalStorage,
  useLogger,
  useMediaQuery,
  useMergedRef,
  useMouse,
  useMove,
  useNetwork,
  useOs,
  usePageLeave,
  usePrevious,
  useQueue,
  useReducedMotion,
  useResizeObserver,
  useScrollIntoView,
  useScrollLock,
  useSessionStorage,
  useSetState,
  useShallowEffect,
  useTextSelection,
  useTimeout,
  useValidatedState,
  useViewportSize,
  useWindowEvent,
  useWindowScroll,
  useClickOutside,
  useColorScheme as useTheme,
  useInputState,
  useHash,
  useHeadroom,
  useEyeDropper,
  useFetch,
  useForceUpdate,
  useIsFirstRender,
  useIsomorphicEffect,
  useLatestRef,
  useLifecycles,
  useLockScroll,
  useMount,
  useRafState,
  useReactive,
  useRendersCount,
  useSearchParams,
  useSetState as useStateHistory,
  useUnmount,
  useUpdateEffect,
  useWhyDidYouUpdate,
} from '@mantine/hooks';

// Notifications
export { notifications } from '@mantine/notifications';

// Form handling (if using Mantine form)
export { useForm } from '@mantine/form';

// Tabler Icons - Most common MUI icon replacements
export {
  IconCheck,
  IconX,
  IconPlus,
  IconMinus,
  IconEdit,
  IconTrash,
  IconSearch,
  IconFilter,
  IconDownload,
  IconUpload,
  IconEye,
  IconEyeOff,
  IconHome,
  IconDashboard,
  IconSettings,
  IconUser,
  IconUsers,
  IconChevronDown,
  IconChevronUp,
  IconChevronLeft,
  IconChevronRight,
  IconMenu,
  IconMenu2,
  IconDotsVertical,
  IconBell,
  IconMessageCircle,
  IconStar,
  IconHeart,
  IconShare,
  IconRefresh,
  IconLogout,
  IconLogin,
  IconSchool,
  IconBook,
  IconChartBar,
  IconReportAnalytics,
  IconPalette,
  IconMoon,
  IconSun,
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconVolume,
  IconVolumeOff,
  IconInfoCircle,
  IconAlertCircle,
  IconAlertTriangle,
  IconCircleCheck,
  IconCircleX,
  IconLoader,
  IconLoader2,
  IconArrowLeft,
  IconArrowRight,
  IconArrowUp,
  IconArrowDown,
  IconCopy,
  IconClipboard,
  IconCalendar,
  IconClock,
  IconMail,
  IconPhone,
  IconMapPin,
  IconLink,
  IconExternalLink,
  IconFile,
  IconFileText,
  IconFolder,
  IconPhoto,
  IconCamera,
  IconMicrophone,
  IconVideo,
  IconHeadphones,
  IconWifi,
  IconBluetooth,
  IconBattery,
  IconPower,
  IconLock,
  IconLockOpen,
  IconShield,
  IconKey,
  IconFingerprint,
  IconEye as IconVisibility,
  IconEyeOff as IconVisibilityOff,
  IconPlus as IconAdd,
  IconMinus as IconRemove,
  IconX as IconClose,
  IconChevronDown as IconExpandMore,
  IconChevronUp as IconExpandLess,
  IconMenu as IconMenuIcon,
  IconDotsVertical as IconMoreVert,
  IconBell as IconNotifications,
  IconMessageCircle as IconMessage,
  IconHeart as IconFavorite,
  IconLogout as IconExitToApp,
  IconUsers as IconGroup,
  IconChartBar as IconBarChart,
  IconReportAnalytics as IconAssessment,
  IconMoon as IconDarkMode,
  IconSun as IconLightMode,
  IconPlayerPlay as IconPlayArrow,
  IconPlayerPause as IconPause,
  IconPlayerStop as IconStop,
  IconVolume as IconVolumeUp,
  IconInfoCircle as IconInfo,
  IconAlertTriangle as IconWarning,
  IconCircleX as IconError,
  IconCircleCheck as IconCheckCircle,
} from '@tabler/icons-react';

// MUI-style component aliases for easier migration
export const MuiBox = Box;
export const MuiButton = Button;
export const MuiContainer = Container;
export const MuiPaper = Paper;
export const MuiTypography = Text;
export const MuiGrid = Grid;
export const MuiCard = Card;
export const MuiCardContent = Box; // Use Box for card content
export const MuiCardActions = Group; // Use Group for card actions
export const MuiCardHeader = Box; // Use Box with custom styling
export const MuiDivider = Divider;
export const MuiAvatar = Avatar;
export const MuiBadge = Badge;
export const MuiIconButton = ActionIcon;
export const MuiCircularProgress = Loader;
export const MuiLinearProgress = Progress;
export const MuiTextField = TextInput;
export const MuiSelect = Select;
export const MuiCheckbox = Checkbox;
export const MuiSwitch = Switch;
export const MuiRadio = Radio;
export const MuiSlider = Slider;
export const MuiTooltip = Tooltip;
export const MuiDialog = Modal;
export const MuiDialogTitle = Title;
export const MuiDialogContent = Box;
export const MuiDialogActions = Group;
export const MuiDrawer = Drawer;
export const MuiAppBar = Header;
export const MuiToolbar = Group;
export const MuiTabs = Tabs;
export const MuiTab = Tabs.Tab;
export const MuiAccordion = Accordion;
export const MuiAccordionSummary = Accordion.Control;
export const MuiAccordionDetails = Accordion.Panel;
export const MuiList = List;
export const MuiListItem = List.Item;
export const MuiListItemText = Text;
export const MuiListItemIcon = Box;
export const MuiTable = Table;
export const MuiTableBody = 'tbody' as const;
export const MuiTableCell = 'td' as const;
export const MuiTableContainer = ScrollArea;
export const MuiTableHead = 'thead' as const;
export const MuiTableRow = 'tr' as const;
export const MuiCollapse = Collapse;
export const MuiAlert = Alert;
export const MuiChip = Badge; // Or use Chip from Mantine if available
export const MuiFormControl = Box;
export const MuiInputLabel = Text;
export const MuiMenuItem = Menu.Item;
export const MuiMenu = Menu;
export const MuiSnackbar = Notification;
export const MuiSkeleton = Skeleton;
export const MuiStack = Stack;

// Theme-related exports
import { useMantineTheme, MantineProvider } from '@mantine/core';
export { useMantineTheme as useTheme, MantineProvider as ThemeProvider };

// Emotion/styled components compatibility layer
export const styled = (_component: any) => {
  console.warn('styled-components from MUI detected. Please migrate to Mantine styles or CSS modules.');
  return _component;
};

// Helper function to convert MUI props to Mantine props
export function muiToMantineProps(muiProps: Record<string, any>): Record<string, any> {
  const mantineProps: Record<string, any> = { ...muiProps };

  // Convert common MUI props to Mantine equivalents
  if ('variant' in mantineProps) {
    // Handle Typography/Text variants
    if (mantineProps.variant?.startsWith('h')) {
      const level = parseInt(mantineProps.variant.slice(1));
      mantineProps.order = level;
      delete mantineProps.variant;
    }
    // Handle Button variants
    if (mantineProps.variant === 'contained') mantineProps.variant = 'filled';
    if (mantineProps.variant === 'outlined') mantineProps.variant = 'outline';
  }

  // Convert color props
  if (mantineProps.color === 'primary') mantineProps.color = 'blue';
  if (mantineProps.color === 'secondary') mantineProps.color = 'gray';
  if (mantineProps.color === 'error') mantineProps.color = 'red';
  if (mantineProps.color === 'warning') mantineProps.color = 'yellow';
  if (mantineProps.color === 'info') mantineProps.color = 'cyan';
  if (mantineProps.color === 'success') mantineProps.color = 'green';

  // Convert size props
  if (mantineProps.size === 'small') mantineProps.size = 'sm';
  if (mantineProps.size === 'medium') mantineProps.size = 'md';
  if (mantineProps.size === 'large') mantineProps.size = 'lg';

  // Convert other common props
  if ('fullWidth' in mantineProps) {
    mantineProps.w = '100%';
    delete mantineProps.fullWidth;
  }

  if ('disableElevation' in mantineProps) {
    delete mantineProps.disableElevation;
  }

  if ('disableRipple' in mantineProps) {
    delete mantineProps.disableRipple;
  }

  if ('gutterBottom' in mantineProps) {
    mantineProps.mb = 'md';
    delete mantineProps.gutterBottom;
  }

  if ('noWrap' in mantineProps) {
    mantineProps.truncate = true;
    delete mantineProps.noWrap;
  }

  if ('align' in mantineProps) {
    mantineProps.ta = mantineProps.align;
    delete mantineProps.align;
  }

  // Handle sx prop (simplified conversion)
  if ('sx' in mantineProps) {
    // Convert MUI sx to Mantine style prop
    const sx = mantineProps.sx;
    if (typeof sx === 'object') {
      // Basic mapping of common properties
      if (sx.mt) mantineProps.mt = sx.mt;
      if (sx.mb) mantineProps.mb = sx.mb;
      if (sx.ml) mantineProps.ml = sx.ml;
      if (sx.mr) mantineProps.mr = sx.mr;
      if (sx.p) mantineProps.p = sx.p;
      if (sx.pt) mantineProps.pt = sx.pt;
      if (sx.pb) mantineProps.pb = sx.pb;
      if (sx.pl) mantineProps.pl = sx.pl;
      if (sx.pr) mantineProps.pr = sx.pr;
      if (sx.m) mantineProps.m = sx.m;
      if (sx.width) mantineProps.w = sx.width;
      if (sx.height) mantineProps.h = sx.height;
      if (sx.minWidth) mantineProps.miw = sx.minWidth;
      if (sx.minHeight) mantineProps.mih = sx.minHeight;
      if (sx.maxWidth) mantineProps.maw = sx.maxWidth;
      if (sx.maxHeight) mantineProps.mah = sx.maxHeight;
      if (sx.display) mantineProps.display = sx.display;
      if (sx.flexDirection) mantineProps.style = { ...mantineProps.style, flexDirection: sx.flexDirection };
      if (sx.justifyContent) mantineProps.justify = sx.justifyContent;
      if (sx.alignItems) mantineProps.align = sx.alignItems;
      if (sx.bgcolor) mantineProps.bg = sx.bgcolor;
      if (sx.color) mantineProps.c = sx.color;
    }
    delete mantineProps.sx;
  }

  return mantineProps;
}

// Re-export everything as default for compatibility
const MantineBridge = {
  Box,
  Button,
  Container,
  Paper,
  Text,
  Typography: Text,
  Title,
  Group,
  Stack,
  Grid,
  Card,
  Divider,
  Avatar,
  Badge,
  ActionIcon,
  IconButton: ActionIcon,
  Loader,
  CircularProgress: Loader,
  Progress,
  LinearProgress: Progress,
  TextInput,
  TextField: TextInput,
  Select,
  Checkbox,
  Switch,
  Radio,
  Slider,
  Tooltip,
  Modal,
  Dialog: Modal,
  Drawer,
  Header,
  AppBar: Header,
  Tabs,
  Tab: Tabs.Tab,
  Accordion,
  List,
  Table,
  Collapse,
  Alert,
  Chip: Badge,
  notifications,
  useTheme: useMantineTheme,
  ThemeProvider: MantineProvider,
  styled,
  muiToMantineProps,
};

export default MantineBridge;