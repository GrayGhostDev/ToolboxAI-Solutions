import * as React from 'react';

// Mantine component type declarations for compatibility
// These are temporary types to help with migration

declare module '@mantine/core' {
  export const Alert: React.FC<any>;
  export const Button: React.FC<any>;
  export const Badge: React.FC<any>;
  export const ActionIcon: React.FC<any>;
  export const Card: React.FC<any>;
  export const Text: React.FC<any>;
  export const Title: React.FC<any>;
  export const Box: React.FC<any>;
  export const Container: React.FC<any>;
  export const Grid: React.FC<any>;
  export const SimpleGrid: React.FC<any>;
  export const Paper: React.FC<any>;
  export const TextInput: React.FC<any>;
  export const PasswordInput: React.FC<any>;
  export const Select: React.FC<any>;
  export const Checkbox: React.FC<any>;
  export const Switch: React.FC<any>;
  export const Modal: React.FC<any>;
  export const Tooltip: React.FC<any>;
  export const Avatar: React.FC<any>;
  export const Divider: React.FC<any>;
  export const List: React.FC<any>;
  export const Drawer: React.FC<any>;
  export const Header: React.FC<any>;
  export const Navbar: React.FC<any>;
  export const Tabs: React.FC<any>;
  export const Loader: React.FC<any>;
  export const Progress: React.FC<any>;
  export const RingProgress: React.FC<any>;
  export const Table: React.FC<any>;
  export const Collapse: React.FC<any>;
  export const Accordion: React.FC<any>;
  export const Stack: React.FC<any>;
  export const Group: React.FC<any>;
  export const Space: React.FC<any>;
  export const Center: React.FC<any>;
  export const Flex: React.FC<any>;
  export const Anchor: React.FC<any>;
  export const Image: React.FC<any>;
  export const Skeleton: React.FC<any>;
  export const LoadingOverlay: React.FC<any>;
  export const Spotlight: React.FC<any>;
  export const Timeline: React.FC<any>;
  export const Stepper: React.FC<any>;
  export const Menu: React.FC<any>;
  export const Popover: React.FC<any>;
  export const HoverCard: React.FC<any>;

  // Theme related
  export const MantineProvider: React.FC<any>;
  export const useMantineTheme: () => any;
  export const useMantineColorScheme: () => any;

  // Form components
  export const NumberInput: React.FC<any>;
  export const DateInput: React.FC<any>;
  export const TimeInput: React.FC<any>;
  export const Textarea: React.FC<any>;
  export const Radio: React.FC<any>;
  export const Slider: React.FC<any>;
  export const Rating: React.FC<any>;

  // Layout
  export const AppShell: React.FC<any>;
  export const Aside: React.FC<any>;
  export const Footer: React.FC<any>;

  // Utility
  export const Portal: React.FC<any>;
  export const FocusTrap: React.FC<any>;
  export const ScrollArea: React.FC<any>;

  // Charts (from @mantine/charts)
  export const LineChart: React.FC<any>;
  export const BarChart: React.FC<any>;
  export const AreaChart: React.FC<any>;
  export const PieChart: React.FC<any>;
  export const DonutChart: React.FC<any>;
}

declare module '@mantine/hooks' {
  export const useDisclosure: () => any;
  export const useLocalStorage: () => any;
  export const useToggle: () => any;
  export const usePrevious: () => any;
  export const useClickOutside: () => any;
  export const useMediaQuery: () => any;
  export const useViewportSize: () => any;
  export const useElementSize: () => any;
  export const useResizeObserver: () => any;
  export const useIntersection: () => any;
  export const useDebouncedValue: () => any;
  export const useThrottledValue: () => any;
  export const useForm: () => any;
}

declare module '@mantine/notifications' {
  export const notifications: any;
  export const Notifications: React.FC<any>;
  export const showNotification: (props: any) => void;
  export const hideNotification: (id: string) => void;
}

declare module '@tabler/icons-react' {
  // Common icons used in the app
  export const IconUser: React.FC<any>;
  export const IconSettings: React.FC<any>;
  export const IconHome: React.FC<any>;
  export const IconDashboard: React.FC<any>;
  export const IconChevronDown: React.FC<any>;
  export const IconChevronUp: React.FC<any>;
  export const IconChevronLeft: React.FC<any>;
  export const IconChevronRight: React.FC<any>;
  export const IconPlus: React.FC<any>;
  export const IconMinus: React.FC<any>;
  export const IconX: React.FC<any>;
  export const IconCheck: React.FC<any>;
  export const IconEdit: React.FC<any>;
  export const IconTrash: React.FC<any>;
  export const IconSearch: React.FC<any>;
  export const IconFilter: React.FC<any>;
  export const IconDownload: React.FC<any>;
  export const IconUpload: React.FC<any>;
  export const IconEye: React.FC<any>;
  export const IconEyeOff: React.FC<any>;
  export const IconLock: React.FC<any>;
  export const IconUnlock: React.FC<any>;
  export const IconMail: React.FC<any>;
  export const IconPhone: React.FC<any>;
  export const IconCalendar: React.FC<any>;
  export const IconClock: React.FC<any>;
  export const IconStar: React.FC<any>;
  export const IconHeart: React.FC<any>;
  export const IconThumbUp: React.FC<any>;
  export const IconShare: React.FC<any>;
  export const IconCopy: React.FC<any>;
  export const IconExternalLink: React.FC<any>;
  export const IconRefresh: React.FC<any>;
  export const IconLogout: React.FC<any>;
  export const IconLogin: React.FC<any>;
  export const IconMenu: React.FC<any>;
  export const IconDotsVertical: React.FC<any>;
  export const IconBell: React.FC<any>;
  export const IconMessageCircle: React.FC<any>;
  export const IconPhoto: React.FC<any>;
  export const IconFile: React.FC<any>;
  export const IconFolder: React.FC<any>;
  export const IconBook: React.FC<any>;
  export const IconSchool: React.FC<any>;
  export const IconUsers: React.FC<any>;
  export const IconChartBar: React.FC<any>;
  export const IconReportAnalytics: React.FC<any>;
  export const IconBuildingStore: React.FC<any>;
  export const IconPalette: React.FC<any>;
  export const IconMoon: React.FC<any>;
  export const IconSun: React.FC<any>;
  export const IconPlayerPlay: React.FC<any>;
  export const IconPlayerPause: React.FC<any>;
  export const IconPlayerStop: React.FC<any>;
  export const IconVolume: React.FC<any>;
  export const IconVolumeOff: React.FC<any>;
  export const IconDeviceGamepad2: React.FC<any>;
  export const IconRocket: React.FC<any>;
  export const IconShield: React.FC<any>;
  export const IconCrown: React.FC<any>;
  export const IconTrophy: React.FC<any>;
  export const IconMedal: React.FC<any>;
  export const IconTarget: React.FC<any>;
  export const IconSword: React.FC<any>;
  export const IconWand: React.FC<any>;
  export const IconSparkles: React.FC<any>;
  export const IconRobot: React.FC<any>;
  export const IconCube: React.FC<any>;
  export const IconWorld: React.FC<any>;
  export const IconCode: React.FC<any>;
  export const IconTerminal: React.FC<any>;
  export const IconBug: React.FC<any>;
  export const IconFlask: React.FC<any>;
  export const IconTools: React.FC<any>;
  export const IconPuzzle: React.FC<any>;
  export const IconBrain: React.FC<any>;
  export const IconBulb: React.FC<any>;
  export const IconAlertCircle: React.FC<any>;
  export const IconInfoCircle: React.FC<any>;
  export const IconCheckCircle: React.FC<any>;
  export const IconXCircle: React.FC<any>;
  export const IconExclamationMark: React.FC<any>;
  export const IconQuestion: React.FC<any>;
  export const IconHelp: React.FC<any>;
  export const IconArrowUp: React.FC<any>;
  export const IconArrowDown: React.FC<any>;
  export const IconArrowLeft: React.FC<any>;
  export const IconArrowRight: React.FC<any>;

  // Catch-all for any other icons
  const Icon: React.FC<any>;
  export default Icon;
}