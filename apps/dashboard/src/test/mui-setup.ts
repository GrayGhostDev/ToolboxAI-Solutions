/**
 * MUI Test Setup
 *
 * Comprehensive MUI mocking for tests to prevent DOM errors
 */

import React from 'react';
import { vi } from 'vitest';

// Mock all MUI components to prevent Emotion/styling issues
const createMockComponent = (name: string) => {
  const MockComponent = React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => {
    // Handle onClick events for buttons
    const handleClick = (e: React.MouseEvent) => {
      if (props.onClick) props.onClick(e);
    };

    // Handle onChange events for inputs
    const handleChange = (e: React.ChangeEvent) => {
      if (props.onChange) props.onChange(e);
    };

    // Handle special component behaviors
    const elementProps: any = {
      'data-testid': name.toLowerCase(),
      ref,
    };

    // Preserve important props for testing
    if (props.label) elementProps['aria-label'] = props.label;
    if (props.name) elementProps['name'] = props.name;
    if (props.type) elementProps['type'] = props.type;
    if (props.value !== undefined) elementProps['value'] = String(props.value);
    if (props.disabled) elementProps['disabled'] = props.disabled;
    if (props.role) elementProps['role'] = props.role;
    if (props.href) elementProps['href'] = props.href;
    if (props.placeholder) elementProps['placeholder'] = props.placeholder;
    if (props.onClick) elementProps['onClick'] = handleClick;
    if (props.onChange) elementProps['onChange'] = handleChange;

    // Handle specific component behaviors
    switch (name) {
      case 'TextField':
        return React.createElement('input', {
          ...elementProps,
          type: props.type || 'text',
        });
      case 'Button':
        return React.createElement('button', elementProps, children);
      case 'Select':
        return React.createElement('select', elementProps, children);
      case 'Checkbox':
        return React.createElement('input', {
          ...elementProps,
          type: 'checkbox',
          checked: props.checked,
        });
      case 'Switch':
        return React.createElement('input', {
          ...elementProps,
          type: 'checkbox',
          checked: props.checked,
        });
      default:
        return React.createElement('div', elementProps, children);
    }
  });

  MockComponent.displayName = name;
  return MockComponent;
};

// Mock all commonly used MUI components
export const mockMuiComponents = () => {
  vi.mock('@mui/material', () => ({
    Box: createMockComponent('Box'),
    Button: createMockComponent('Button'),
    TextField: createMockComponent('TextField'),
    Typography: createMockComponent('Typography'),
    Alert: createMockComponent('Alert'),
    AlertTitle: createMockComponent('AlertTitle'),
    Stack: createMockComponent('Stack'),
    Card: createMockComponent('Card'),
    CardContent: createMockComponent('CardContent'),
    CardActions: createMockComponent('CardActions'),
    CardHeader: createMockComponent('CardHeader'),
    Paper: createMockComponent('Paper'),
    Divider: createMockComponent('Divider'),
    IconButton: createMockComponent('IconButton'),
    InputAdornment: createMockComponent('InputAdornment'),
    MenuItem: createMockComponent('MenuItem'),
    Select: createMockComponent('Select'),
    FormControl: createMockComponent('FormControl'),
    FormGroup: createMockComponent('FormGroup'),
    InputLabel: createMockComponent('InputLabel'),
    Chip: createMockComponent('Chip'),
    Grid: createMockComponent('Grid'),
    Container: createMockComponent('Container'),
    AppBar: createMockComponent('AppBar'),
    Toolbar: createMockComponent('Toolbar'),
    List: createMockComponent('List'),
    ListItem: createMockComponent('ListItem'),
    ListItemText: createMockComponent('ListItemText'),
    ListItemIcon: createMockComponent('ListItemIcon'),
    ListItemButton: createMockComponent('ListItemButton'),
    ListItemSecondaryAction: createMockComponent('ListItemSecondaryAction'),
    Drawer: createMockComponent('Drawer'),
    Dialog: createMockComponent('Dialog'),
    DialogTitle: createMockComponent('DialogTitle'),
    DialogContent: createMockComponent('DialogContent'),
    DialogActions: createMockComponent('DialogActions'),
    Tabs: createMockComponent('Tabs'),
    Tab: createMockComponent('Tab'),
    Avatar: createMockComponent('Avatar'),
    AvatarGroup: createMockComponent('AvatarGroup'),
    Badge: createMockComponent('Badge'),
    Checkbox: createMockComponent('Checkbox'),
    Radio: createMockComponent('Radio'),
    RadioGroup: createMockComponent('RadioGroup'),
    FormControlLabel: createMockComponent('FormControlLabel'),
    Switch: createMockComponent('Switch'),
    Slider: createMockComponent('Slider'),
    CircularProgress: createMockComponent('CircularProgress'),
    LinearProgress: createMockComponent('LinearProgress'),
    Skeleton: createMockComponent('Skeleton'),
    Tooltip: createMockComponent('Tooltip'),
    Snackbar: createMockComponent('Snackbar'),
    Accordion: createMockComponent('Accordion'),
    AccordionSummary: createMockComponent('AccordionSummary'),
    AccordionDetails: createMockComponent('AccordionDetails'),
    SpeedDial: createMockComponent('SpeedDial'),
    SpeedDialAction: createMockComponent('SpeedDialAction'),
    SpeedDialIcon: createMockComponent('SpeedDialIcon'),
    Backdrop: createMockComponent('Backdrop'),
    Breadcrumbs: createMockComponent('Breadcrumbs'),
    Stepper: createMockComponent('Stepper'),
    Step: createMockComponent('Step'),
    StepLabel: createMockComponent('StepLabel'),
    Pagination: createMockComponent('Pagination'),
    Rating: createMockComponent('Rating'),
    ToggleButton: createMockComponent('ToggleButton'),
    ToggleButtonGroup: createMockComponent('ToggleButtonGroup'),
    DataGrid: createMockComponent('DataGrid'),
    Table: createMockComponent('Table'),
    TableBody: createMockComponent('TableBody'),
    TableCell: createMockComponent('TableCell'),
    TableContainer: createMockComponent('TableContainer'),
    TableHead: createMockComponent('TableHead'),
    TableRow: createMockComponent('TableRow'),
    Menu: createMockComponent('Menu'),
    Modal: createMockComponent('Modal'),
    Popper: createMockComponent('Popper'),
    ThemeProvider: vi.fn(({ children }) => children),
    CssBaseline: vi.fn(() => null),
    createTheme: vi.fn(() => ({})),
    useTheme: vi.fn(() => ({})),
    styled: vi.fn(() => createMockComponent('styled')),
  }));

  // Mock MUI Grid2 (Unstable_Grid2)
  vi.mock('@mui/material/Unstable_Grid2', () => ({
    default: createMockComponent('Grid2'),
  }));

  // Mock MUI Grid default export
  vi.mock('@mui/material/Grid', () => ({
    default: createMockComponent('Grid'),
  }));

  // Mock MUI icons
  vi.mock('@mui/icons-material', () => ({
    Visibility: createMockComponent('VisibilityIcon'),
    VisibilityOff: createMockComponent('VisibilityOffIcon'),
    Email: createMockComponent('EmailIcon'),
    Lock: createMockComponent('LockIcon'),
    Person: createMockComponent('PersonIcon'),
    School: createMockComponent('SchoolIcon'),
    Home: createMockComponent('HomeIcon'),
    Assessment: createMockComponent('AssessmentIcon'),
    Class: createMockComponent('ClassIcon'),
    Message: createMockComponent('MessageIcon'),
    Settings: createMockComponent('SettingsIcon'),
    ExitToApp: createMockComponent('ExitToAppIcon'),
    Add: createMockComponent('AddIcon'),
    Edit: createMockComponent('EditIcon'),
    Delete: createMockComponent('DeleteIcon'),
    Search: createMockComponent('SearchIcon'),
    FilterList: createMockComponent('FilterListIcon'),
    Sort: createMockComponent('SortIcon'),
    ExpandMore: createMockComponent('ExpandMoreIcon'),
    ExpandLess: createMockComponent('ExpandLessIcon'),
    ChevronLeft: createMockComponent('ChevronLeftIcon'),
    ChevronRight: createMockComponent('ChevronRightIcon'),
    Close: createMockComponent('CloseIcon'),
    Check: createMockComponent('CheckIcon'),
    Clear: createMockComponent('ClearIcon'),
    Menu: createMockComponent('MenuIcon'),
    MoreVert: createMockComponent('MoreVertIcon'),
    Refresh: createMockComponent('RefreshIcon'),
    Save: createMockComponent('SaveIcon'),
    Upload: createMockComponent('UploadIcon'),
    Download: createMockComponent('DownloadIcon'),
    Share: createMockComponent('ShareIcon'),
    Favorite: createMockComponent('FavoriteIcon'),
    Star: createMockComponent('StarIcon'),
    Warning: createMockComponent('WarningIcon'),
    Error: createMockComponent('ErrorIcon'),
    Info: createMockComponent('InfoIcon'),
    Help: createMockComponent('HelpIcon'),
    Notifications: createMockComponent('NotificationsIcon'),
    AccountCircle: createMockComponent('AccountCircleIcon'),
    Dashboard: createMockComponent('DashboardIcon'),
    Groups: createMockComponent('GroupsIcon'),
    Assignment: createMockComponent('AssignmentIcon'),
    Grade: createMockComponent('GradeIcon'),
    Schedule: createMockComponent('ScheduleIcon'),
    CalendarToday: createMockComponent('CalendarTodayIcon'),
    AttachFile: createMockComponent('AttachFileIcon'),
    CloudUpload: createMockComponent('CloudUploadIcon'),
    CloudDownload: createMockComponent('CloudDownloadIcon'),
    Print: createMockComponent('PrintIcon'),
    Fullscreen: createMockComponent('FullscreenIcon'),
    FullscreenExit: createMockComponent('FullscreenExitIcon'),
    Brightness4: createMockComponent('Brightness4Icon'),
    Brightness7: createMockComponent('Brightness7Icon'),
    Language: createMockComponent('LanguageIcon'),
    Translate: createMockComponent('TranslateIcon'),
    Security: createMockComponent('SecurityIcon'),
    VpnKey: createMockComponent('VpnKeyIcon'),
    LockOpen: createMockComponent('LockOpenIcon'),
    Shield: createMockComponent('ShieldIcon'),
    VerifiedUser: createMockComponent('VerifiedUserIcon'),
    // Additional icons used in the Classes component
    People: createMockComponent('PeopleIcon'),
    TrendingUp: createMockComponent('TrendingUpIcon'),
    RocketLaunch: createMockComponent('RocketLaunchIcon'),
    // Additional icons used in Settings component
    Palette: createMockComponent('PaletteIcon'),
    Accessibility: createMockComponent('AccessibilityIcon'),
    Storage: createMockComponent('StorageIcon'),
    PhotoCamera: createMockComponent('PhotoCameraIcon'),
    Smartphone: createMockComponent('SmartphoneIcon'),
    // Dashboard icons
    Analytics: createMockComponent('AnalyticsIcon'),
    TrendingDown: createMockComponent('TrendingDownIcon'),
    Speed: createMockComponent('SpeedIcon'),
    Timeline: createMockComponent('TimelineIcon'),
    BarChart: createMockComponent('BarChartIcon'),
    PieChart: createMockComponent('PieChartIcon'),
    ShowChart: createMockComponent('ShowChartIcon'),
    // Additional commonly used icons
    Cancel: createMockComponent('CancelIcon'),
    CheckCircle: createMockComponent('CheckCircleIcon'),
    ErrorOutline: createMockComponent('ErrorOutlineIcon'),
    InfoOutlined: createMockComponent('InfoOutlinedIcon'),
    WarningAmber: createMockComponent('WarningAmberIcon'),
    Folder: createMockComponent('FolderIcon'),
    FolderOpen: createMockComponent('FolderOpenIcon'),
    InsertDriveFile: createMockComponent('InsertDriveFileIcon'),
    ContentCopy: createMockComponent('ContentCopyIcon'),
    ContentPaste: createMockComponent('ContentPasteIcon'),
    PlayArrow: createMockComponent('PlayArrowIcon'),
    Pause: createMockComponent('PauseIcon'),
    Stop: createMockComponent('StopIcon'),
    SkipNext: createMockComponent('SkipNextIcon'),
    SkipPrevious: createMockComponent('SkipPreviousIcon'),
    VolumeUp: createMockComponent('VolumeUpIcon'),
    VolumeDown: createMockComponent('VolumeDownIcon'),
    VolumeMute: createMockComponent('VolumeMuteIcon'),
    VolumeOff: createMockComponent('VolumeOffIcon'),
  }));
};

// Call the mock setup
mockMuiComponents();