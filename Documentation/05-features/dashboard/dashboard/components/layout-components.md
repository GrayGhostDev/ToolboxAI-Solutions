# Layout Components Documentation

## AppLayout Component

### Overview
The main application layout container that provides the structure for all dashboard pages.

### Location
`src/components/layout/AppLayout.tsx`

### Props Interface
```typescript
interface AppLayoutProps {
  role: UserRole;
  children: React.ReactNode;
}
```

### Features
- Responsive sidebar management
- Theme-aware styling
- Content area with proper padding
- Smooth transitions

### Usage Example
```tsx
<AppLayout role={currentUserRole}>
  <DashboardContent />
</AppLayout>
```

### State Management
- Uses Redux for sidebar open/closed state
- Responsive to screen size changes

### Styling
```typescript
const drawerWidth = 280; // Sidebar width
const mobileBreakpoint = 'md'; // Responsive breakpoint
```

---

## Sidebar Component

### Overview
Role-based navigation sidebar with user information and quick stats.

### Location
`src/components/layout/Sidebar.tsx`

### Props Interface
```typescript
interface SidebarProps {
  role: UserRole;
}
```

### Navigation Structure
```typescript
const navigationItems = {
  student: [
    { path: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
    { path: '/avatar', label: 'My Avatar', icon: PersonIcon },
    { path: '/progress', label: 'Progress', icon: TrendingUpIcon },
    { path: '/missions', label: 'Missions', icon: FlagIcon },
    { path: '/rewards', label: 'Rewards', icon: EmojiEventsIcon },
    { path: '/leaderboard', label: 'Leaderboard', icon: LeaderboardIcon },
    { path: '/play', label: 'Play', icon: SportsEsportsIcon }
  ],
  teacher: [
    { path: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
    { path: '/classes', label: 'Classes', icon: ClassIcon },
    { path: '/lessons', label: 'Lessons', icon: MenuBookIcon },
    { path: '/assessments', label: 'Assessments', icon: AssignmentIcon },
    { path: '/reports', label: 'Reports', icon: AssessmentIcon },
    { path: '/messages', label: 'Messages', icon: MessageIcon }
  ],
  admin: [
    { path: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
    { path: '/schools', label: 'Schools', icon: SchoolIcon },
    { path: '/users', label: 'Users', icon: PeopleIcon },
    { path: '/analytics', label: 'Analytics', icon: AnalyticsIcon },
    { path: '/compliance', label: 'Compliance', icon: VerifiedUserIcon },
    { path: '/integrations', label: 'Integrations', icon: ExtensionIcon }
  ],
  parent: [
    { path: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
    { path: '/progress', label: "Child's Progress", icon: TrendingUpIcon },
    { path: '/messages', label: 'Messages', icon: MessageIcon },
    { path: '/reports', label: 'Reports', icon: AssessmentIcon }
  ]
};
```

### User Info Section
```tsx
<Box sx={{ p: 2 }}>
  <Avatar src={user.avatar} />
  <Typography>{user.name}</Typography>
  <Typography variant="caption">{user.role}</Typography>
  
  {/* Student XP Bar */}
  {role === 'student' && (
    <LinearProgress 
      variant="determinate" 
      value={xpProgress} 
      sx={{ mt: 1 }}
    />
  )}
  
  {/* Teacher/Admin Quick Stats */}
  {(role === 'teacher' || role === 'admin') && (
    <Box sx={{ mt: 2 }}>
      <Typography variant="body2">
        Classes: {stats.classCount}
      </Typography>
      <Typography variant="body2">
        Students: {stats.studentCount}
      </Typography>
    </Box>
  )}
</Box>
```

### Mobile Responsiveness
- Drawer transforms to temporary drawer on mobile
- Swipe gestures supported
- Auto-close on navigation

---

## Topbar Component

### Overview
Application header with user controls, notifications, and settings.

### Location
`src/components/layout/Topbar.tsx`

### Features
- User profile menu
- Notification center
- Theme toggle (light/dark)
- Language selector
- Role switcher (dev mode)
- Search functionality

### Component Structure
```tsx
const Topbar: React.FC = () => {
  // State management
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);
  
  // Redux hooks
  const dispatch = useAppDispatch();
  const { user, theme, notifications } = useAppSelector(state => ({
    user: state.user,
    theme: state.settings.theme,
    notifications: state.notifications.items
  }));
  
  return (
    <AppBar position="fixed">
      <Toolbar>
        {/* Menu toggle button */}
        <IconButton onClick={toggleSidebar}>
          <MenuIcon />
        </IconButton>
        
        {/* App title */}
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          ToolBoxAI Dashboard
        </Typography>
        
        {/* Search bar */}
        <Search />
        
        {/* Action buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* Theme toggle */}
          <IconButton onClick={toggleTheme}>
            {theme === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
          </IconButton>
          
          {/* Notifications */}
          <IconButton onClick={openNotifications}>
            <Badge badgeContent={unreadCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          
          {/* User menu */}
          <IconButton onClick={openUserMenu}>
            <Avatar src={user.avatar} />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
```

### Notification Menu
```tsx
<Menu
  anchorEl={notificationAnchor}
  open={Boolean(notificationAnchor)}
  onClose={closeNotifications}
>
  <MenuItem>
    <ListItemText 
      primary="New Assignment"
      secondary="Math homework due tomorrow"
    />
  </MenuItem>
  <Divider />
  <MenuItem onClick={viewAllNotifications}>
    View all notifications
  </MenuItem>
</Menu>
```

### User Menu
```tsx
<Menu
  anchorEl={anchorEl}
  open={Boolean(anchorEl)}
  onClose={closeUserMenu}
>
  <MenuItem onClick={goToProfile}>
    <ListItemIcon><PersonIcon /></ListItemIcon>
    Profile
  </MenuItem>
  <MenuItem onClick={goToSettings}>
    <ListItemIcon><SettingsIcon /></ListItemIcon>
    Settings
  </MenuItem>
  <Divider />
  <MenuItem onClick={logout}>
    <ListItemIcon><LogoutIcon /></ListItemIcon>
    Logout
  </MenuItem>
</Menu>
```

### Theme Integration
```typescript
const theme = useTheme();
const isDarkMode = theme.palette.mode === 'dark';

const toggleTheme = () => {
  dispatch(setTheme(isDarkMode ? 'light' : 'dark'));
};
```

### Search Component
```tsx
const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.common.white, 0.15),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.white, 0.25),
  },
  marginLeft: theme.spacing(1),
  width: 'auto',
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: 'inherit',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '12ch',
    [theme.breakpoints.up('sm')]: {
      width: '20ch',
      '&:focus': {
        width: '30ch',
      },
    },
  },
}));
```

---

## Layout Utilities

### useResponsive Hook
```typescript
export const useResponsive = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));
  
  return { isMobile, isTablet, isDesktop };
};
```

### Layout Constants
```typescript
export const LAYOUT_CONSTANTS = {
  DRAWER_WIDTH: 280,
  TOPBAR_HEIGHT: 64,
  MOBILE_DRAWER_WIDTH: 240,
  CONTENT_PADDING: 3,
  SIDEBAR_TRANSITION_DURATION: 225,
};
```

### Layout Context Provider
```typescript
interface LayoutContextType {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const LayoutContext = React.createContext<LayoutContextType>({
  sidebarOpen: true,
  toggleSidebar: () => {},
  setSidebarOpen: () => {},
});

export const LayoutProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  const toggleSidebar = () => setSidebarOpen(prev => !prev);
  
  return (
    <LayoutContext.Provider value={{ sidebarOpen, toggleSidebar, setSidebarOpen }}>
      {children}
    </LayoutContext.Provider>
  );
};
```

---

## Styling Guidelines

### Theme Customization
```typescript
const layoutTheme = createTheme({
  components: {
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#f5f5f5',
          borderRight: '1px solid rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          zIndex: 1201, // Above drawer
        },
      },
    },
  },
});
```

### Responsive Breakpoints
```typescript
const breakpoints = {
  mobile: 0,     // 0-767px
  tablet: 768,   // 768-1023px
  desktop: 1024, // 1024px+
  wide: 1440,    // 1440px+
};
```

---

## Performance Optimizations

### Memoization
```typescript
const MemoizedSidebar = React.memo(Sidebar, (prevProps, nextProps) => {
  return prevProps.role === nextProps.role;
});
```

### Lazy Loading
```typescript
const LazyTopbar = React.lazy(() => import('./Topbar'));
```

### Debounced Search
```typescript
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    dispatch(searchAction(query));
  }, 300),
  [dispatch]
);
```

---

## Accessibility

### ARIA Labels
```typescript
<IconButton
  aria-label="toggle theme"
  aria-pressed={isDarkMode}
  onClick={toggleTheme}
>
  {isDarkMode ? <LightModeIcon /> : <DarkModeIcon />}
</IconButton>
```

### Keyboard Navigation
```typescript
const handleKeyDown = (event: React.KeyboardEvent) => {
  if (event.key === 'Escape') {
    setSidebarOpen(false);
  }
};
```

### Focus Management
```typescript
useEffect(() => {
  if (sidebarOpen) {
    sidebarRef.current?.focus();
  }
}, [sidebarOpen]);
```

---

## Testing

### Unit Tests
```typescript
describe('AppLayout', () => {
  it('renders children correctly', () => {
    render(
      <AppLayout role="student">
        <div>Test Content</div>
      </AppLayout>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
  
  it('applies correct role-based styling', () => {
    const { container } = render(<AppLayout role="teacher" />);
    expect(container.firstChild).toHaveClass('teacher-layout');
  });
});
```

### Integration Tests
```typescript
describe('Layout Integration', () => {
  it('toggles sidebar on button click', async () => {
    render(<App />);
    const toggleButton = screen.getByLabelText('toggle sidebar');
    
    fireEvent.click(toggleButton);
    await waitFor(() => {
      expect(screen.getByRole('navigation')).toHaveStyle({ width: '0' });
    });
  });
});
```

---

## Common Issues & Solutions

### Issue: Sidebar overlaps content
**Solution**: Ensure proper margin-left on content area
```css
.content {
  margin-left: ${DRAWER_WIDTH}px;
  transition: margin-left 225ms;
}
```

### Issue: Theme toggle not persisting
**Solution**: Save theme preference to localStorage
```typescript
useEffect(() => {
  localStorage.setItem('theme', theme);
}, [theme]);
```

### Issue: Mobile drawer not closing on navigation
**Solution**: Add close handler to navigation items
```typescript
const handleNavigation = (path: string) => {
  navigate(path);
  if (isMobile) {
    setSidebarOpen(false);
  }
};
```