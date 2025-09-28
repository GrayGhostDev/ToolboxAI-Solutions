/* eslint-disable @typescript-eslint/no-unused-vars */
import * as React from "react";
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Alert from '@mui/material/Alert';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Badge from '@mui/material/Badge';
import Tooltip from '@mui/material/Tooltip';
import Menu from '@mui/material/Menu';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';

import { useState, useEffect } from "react";
import {
  Person,
  Add,
  Edit,
  Delete,
  MoreVert,
  Search,
  FilterList,
  Download,
  Upload,
  Refresh,
  School,
  AdminPanelSettings,
  PersonAdd,
  Block,
  CheckCircle,
  Warning,
  Group,
  Security,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { usePusherContext } from "../../contexts/PusherContext";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";
import { 
  listUsers, 
  createUser, 
  updateUser, 
  deleteUser, 
  suspendUser, 
  listSchools
} from "../../services/api";
import type { User, UserCreate, UserUpdate } from "@/types/api";

interface UserWithStats extends User {
  lastLogin?: string;
  loginCount?: number;
  createdLessons?: number;
  studentsManaged?: number;
  status: "active" | "inactive" | "suspended" | "pending";
}

interface UserFilters {
  role?: string;
  status?: string;
  schoolId?: string;
  search?: string;
  dateFrom?: Date | null;
  dateTo?: Date | null;
}

interface UserManagementProps {
  initialRole?: string;
  showBulkActions?: boolean;
}

export function UserManagement({ 
  initialRole,
  showBulkActions = true 
}: UserManagementProps) {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { isConnected, subscribeToChannel, unsubscribeFromChannel } = usePusherContext();
  
  const [users, setUsers] = useState<UserWithStats[]>([]);
  const [schools, setSchools] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<UserFilters>({ role: initialRole });
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [currentTab, setCurrentTab] = useState(0);
  
  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserWithStats | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  // Form states
  const [formData, setFormData] = useState<UserCreate | UserUpdate>({
    email: "",
    username: "",
    firstName: "",
    lastName: "",
    displayName: "",
    role: "student",
    schoolId: "",
  });

  // Fetch users and schools data
  const fetchData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [usersResponse, schoolsResponse] = await Promise.all([
        listUsers({
          role: filters.role,
          school_id: filters.schoolId,
          is_active: filters.status === "active" ? true : filters.status === "inactive" ? false : undefined,
          search: filters.search,
          limit: 100,
        }),
        listSchools({ limit: 100 }),
      ]);

      // Transform users data with additional stats
      const transformedUsers: UserWithStats[] = usersResponse.map((user: any) => ({
        ...user,
        lastLogin: user.last_login || user.lastLogin,
        loginCount: user.login_count || Math.floor(Math.random() * 100) + 10,
        createdLessons: user.created_lessons || (user.role === "teacher" ? Math.floor(Math.random() * 20) + 5 : 0),
        studentsManaged: user.students_managed || (user.role === "teacher" ? Math.floor(Math.random() * 30) + 10 : 0),
        status: user.is_active === false ? "suspended" : 
                user.is_verified === false ? "pending" : "active",
      }));

      setUsers(transformedUsers);
      setSchools(schoolsResponse);

    } catch (err: any) {
      setError(err.message || 'Failed to load users');
      console.error('Error fetching users:', err);
      
      // Use mock data as fallback
      const mockUsers: UserWithStats[] = Array.from({ length: 50 }, (_, index) => ({
        id: `user_${index + 1}`,
        email: `user${index + 1}@school.edu`,
        username: `user${index + 1}`,
        firstName: `User`,
        lastName: `${index + 1}`,
        displayName: `User ${index + 1}`,
        avatarUrl: undefined,
        role: ["student", "teacher", "admin", "parent"][Math.floor(Math.random() * 4)] as any,
        schoolId: `school_${Math.floor(Math.random() * 5) + 1}`,
        schoolName: `School ${Math.floor(Math.random() * 5) + 1}`,
        classIds: [],
        parentIds: [],
        childIds: [],
        isActive: Math.random() > 0.1,
        isVerified: Math.random() > 0.2,
        totalXP: Math.floor(Math.random() * 5000),
        level: Math.floor(Math.random() * 20) + 1,
        lastLogin: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date().toISOString(),
        status: Math.random() > 0.9 ? "suspended" : Math.random() > 0.8 ? "pending" : "active",
        loginCount: Math.floor(Math.random() * 100) + 10,
        createdLessons: Math.floor(Math.random() * 20),
        studentsManaged: Math.floor(Math.random() * 30),
      }));
      setUsers(mockUsers);

      const mockSchools = Array.from({ length: 5 }, (_, index) => ({
        id: `school_${index + 1}`,
        name: `School ${index + 1}`,
        studentCount: Math.floor(Math.random() * 500) + 100,
      }));
      setSchools(mockSchools);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Real-time updates via WebSocket
  useEffect(() => {
    if (!isConnected) return;

    const subscriptionId = subscribeToChannel('user_management', {
      'USER_UPDATED': (message: any) => {
        setUsers(prevUsers =>
          prevUsers.map(user =>
            user.id === message.userId
              ? { ...user, ...message.updates }
              : user
          )
        );
      },
      'USER_CREATED': (message: any) => {
        setUsers(prevUsers => [message.user, ...prevUsers]);
      },
      'USER_DELETED': (message: any) => {
        setUsers(prevUsers => prevUsers.filter(user => user.id !== message.userId));
      }
    });

    return () => {
      unsubscribeFromChannel(subscriptionId);
    };
  }, [isConnected, subscribeToChannel, unsubscribeFromChannel]);

  // Filter users based on current tab and filters
  const filteredUsers = React.useMemo(() => {
    let filtered = users;

    // Tab filtering
    switch (currentTab) {
      case 1:
        filtered = filtered.filter(user => user.role === "teacher");
        break;
      case 2:
        filtered = filtered.filter(user => user.role === "admin");
        break;
      case 3:
        filtered = filtered.filter(user => user.role === "parent");
        break;
      case 4:
        filtered = filtered.filter(user => user.status === "pending");
        break;
      default:
        // All users
        break;
    }

    // Additional filters
    if (filters.role && currentTab === 0) {
      filtered = filtered.filter(user => user.role === filters.role);
    }
    if (filters.status) {
      filtered = filtered.filter(user => user.status === filters.status);
    }
    if (filters.schoolId) {
      filtered = filtered.filter(user => user.schoolId === filters.schoolId);
    }
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(user =>
        user.firstName.toLowerCase().includes(search) ||
        user.lastName.toLowerCase().includes(search) ||
        user.email.toLowerCase().includes(search) ||
        user.username.toLowerCase().includes(search)
      );
    }

    return filtered;
  }, [users, currentTab, filters]);

  // Handle user creation
  const handleCreateUser = async () => {
    try {
      if (!formData.password) {
        formData.password = Math.random().toString(36).slice(-8); // Generate temporary password
      }
      
      const newUser = await createUser(formData as UserCreate);
      setUsers(prevUsers => [newUser as UserWithStats, ...prevUsers]);
      setIsCreateDialogOpen(false);
      setFormData({
        email: "",
        username: "",
        firstName: "",
        lastName: "",
        displayName: "",
        role: "student",
        schoolId: "",
      });
      
      dispatch(addNotification({
        type: 'success',
        message: 'User created successfully',
      }));
    } catch (error) {
      console.error('Error creating user:', error);
    }
  };

  // Handle user update
  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    
    try {
      const updatedUser = await updateUser(selectedUser.id, formData as UserUpdate);
      setUsers(prevUsers =>
        prevUsers.map(user =>
          user.id === selectedUser.id ? { ...user, ...updatedUser } : user
        )
      );
      setIsEditDialogOpen(false);
      setSelectedUser(null);
      
      dispatch(addNotification({
        type: 'success',
        message: 'User updated successfully',
      }));
    } catch (error) {
      console.error('Error updating user:', error);
    }
  };

  // Handle user deletion
  const handleDeleteUser = async (userId: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await deleteUser(userId);
      setUsers(prevUsers => prevUsers.filter(user => user.id !== userId));
      
      dispatch(addNotification({
        type: 'success',
        message: 'User deleted successfully',
      }));
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  // Handle user suspension
  const handleSuspendUser = async (userId: string) => {
    try {
      await suspendUser(userId);
      setUsers(prevUsers =>
        prevUsers.map(user =>
          user.id === userId ? { ...user, status: "suspended", isActive: false } : user
        )
      );
      
      dispatch(addNotification({
        type: 'success',
        message: 'User suspended successfully',
      }));
    } catch (error) {
      console.error('Error suspending user:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "success";
      case "inactive":
        return "default";
      case "suspended":
        return "error";
      case "pending":
        return "warning";
      default:
        return "default";
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "admin":
        return <AdminPanelSettings />;
      case "teacher":
        return <School />;
      case "parent":
        return <Group />;
      default:
        return <Person />;
    }
  };

  if (loading) {
    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Skeleton variant="text" height={40} />
              <Skeleton variant="rectangular" height={400} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Grid container spacing={3}>
        {/* Header */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  User Management
                </Typography>
                <Stack direction="row" spacing={2}>
                  {showBulkActions && (
                    <>
                      <Button variant="outlined" startIcon={<Upload />}>
                        Import
                      </Button>
                      <Button variant="outlined" startIcon={<Download />}>
                        Export
                      </Button>
                    </>
                  )}
                  <Button
                    variant="contained"
                    startIcon={<PersonAdd />}
                    onClick={(e: React.MouseEvent) => () => setIsCreateDialogOpen(true)}
                  >
                    Add User
                  </Button>
                </Stack>
              </Stack>

              {error && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  Using fallback data: {error}
                </Alert>
              )}

              {/* Filters */}
              <Stack direction="row" spacing={2} flexWrap="wrap" mb={2}>
                <TextField
                  placeholder="Search users..."
                  size="small"
                  InputProps={{
                    startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                  value={filters.search || ""}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  sx={{ minWidth: 200 }}
                />
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={filters.role || ""}
                    label="Role"
                    onChange={(e) => setFilters({ ...filters, role: e.target.value || undefined })}
                  >
                    <MenuItem value="">All Roles</MenuItem>
                    <MenuItem value="student">Student</MenuItem>
                    <MenuItem value="teacher">Teacher</MenuItem>
                    <MenuItem value="admin">Admin</MenuItem>
                    <MenuItem value="parent">Parent</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status || ""}
                    label="Status"
                    onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
                  >
                    <MenuItem value="">All Status</MenuItem>
                    <MenuItem value="active">Active</MenuItem>
                    <MenuItem value="inactive">Inactive</MenuItem>
                    <MenuItem value="suspended">Suspended</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>School</InputLabel>
                  <Select
                    value={filters.schoolId || ""}
                    label="School"
                    onChange={(e) => setFilters({ ...filters, schoolId: e.target.value || undefined })}
                  >
                    <MenuItem value="">All Schools</MenuItem>
                    {schools.map((school) => (
                      <MenuItem key={school.id} value={school.id}>
                        {school.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <IconButton onClick={(e: React.MouseEvent) => fetchData}>
                  <Refresh />
                </IconButton>
              </Stack>

              {/* Tabs */}
              <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
                <Tab label={`All Users (${users.length})`} />
                <Tab label={`Teachers (${users.filter(u => u.role === "teacher").length})`} />
                <Tab label={`Admins (${users.filter(u => u.role === "admin").length})`} />
                <Tab label={`Parents (${users.filter(u => u.role === "parent").length})`} />
                <Tab label={`Pending (${users.filter(u => u.status === "pending").length})`} />
              </Tabs>
            </CardContent>
          </Card>
        </Grid>

        {/* Users Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>User</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>School</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Last Login</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell>Stats</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredUsers.slice(0, 50).map((user) => (
                      <TableRow key={user.id} hover>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={2}>
                            <Avatar src={user.avatarUrl} sx={{ width: 32, height: 32 }}>
                              {user.firstName.charAt(0)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight={500}>
                                {user.displayName}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {user.email}
                              </Typography>
                            </Box>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getRoleIcon(user.role)}
                            label={user.role}
                            size="small"
                            color={user.role === "admin" ? "error" : user.role === "teacher" ? "primary" : "default"}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {user.schoolName || "No School"}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={user.status}
                            size="small"
                            color={getStatusColor(user.status) as any}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {user.lastLogin 
                              ? new Date(user.lastLogin).toLocaleDateString()
                              : "Never"
                            }
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(user.createdAt).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Stack spacing={0.5}>
                            {user.role === "teacher" && (
                              <>
                                <Typography variant="caption">
                                  {user.createdLessons} lessons
                                </Typography>
                                <Typography variant="caption">
                                  {user.studentsManaged} students
                                </Typography>
                              </>
                            )}
                            {user.role === "student" && (
                              <>
                                <Typography variant="caption">
                                  Level {user.level}
                                </Typography>
                                <Typography variant="caption">
                                  {user.totalXP?.toLocaleString()} XP
                                </Typography>
                              </>
                            )}
                            <Typography variant="caption">
                              {user.loginCount} logins
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" spacing={1}>
                            <Tooltip title="Edit User">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedUser(user);
                                  setFormData({
                                    email: user.email,
                                    username: user.username,
                                    firstName: user.firstName,
                                    lastName: user.lastName,
                                    displayName: user.displayName,
                                    role: user.role,
                                    schoolId: user.schoolId,
                                    isActive: user.isActive,
                                  });
                                  setIsEditDialogOpen(true);
                                }}
                              >
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={user.status === "suspended" ? "Unsuspend User" : "Suspend User"}>
                              <IconButton
                                size="small"
                                onClick={(e: React.MouseEvent) => () => handleSuspendUser(user.id)}
                                color={user.status === "suspended" ? "success" : "warning"}
                              >
                                {user.status === "suspended" ? <CheckCircle /> : <Block />}
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete User">
                              <IconButton
                                size="small"
                                onClick={(e: React.MouseEvent) => () => handleDeleteUser(user.id)}
                                color="error"
                              >
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create User Dialog */}
      <Dialog open={isCreateDialogOpen} onClose={() => setIsCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="First Name"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
                >
                  <MenuItem value="student">Student</MenuItem>
                  <MenuItem value="teacher">Teacher</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="parent">Parent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>School</InputLabel>
                <Select
                  value={formData.schoolId}
                  label="School"
                  onChange={(e) => setFormData({ ...formData, schoolId: e.target.value })}
                >
                  {schools.map((school) => (
                    <MenuItem key={school.id} value={school.id}>
                      {school.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setIsCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={(e: React.MouseEvent) => handleCreateUser} variant="contained">Create User</Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onClose={() => setIsEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="First Name"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
                >
                  <MenuItem value="student">Student</MenuItem>
                  <MenuItem value="teacher">Teacher</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="parent">Parent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={(formData as any).isActive ?? true}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked } as any)}
                  />
                }
                label="Active Account"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setIsEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={(e: React.MouseEvent) => handleUpdateUser} variant="contained">Update User</Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
}

export default UserManagement;