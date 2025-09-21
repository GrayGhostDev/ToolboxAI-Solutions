// @ts-nocheck - Temporary fix for Phase 3
/**
 * UserManagementPanel Component
 * Comprehensive user management interface for administrators
 */
import React, { memo, useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Alert from '@mui/material/Alert';
import Tooltip from '@mui/material/Tooltip';
import Checkbox from '@mui/material/Checkbox';
import LinearProgress from '@mui/material/LinearProgress';
import Badge from '@mui/material/Badge';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  PersonAdd as AddUserIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Send as SendIcon,
  Lock as ResetPasswordIcon,
  AdminPanelSettings as AdminIcon,
  School as TeacherIcon,
  Person as StudentIcon,
  Groups as GroupIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { User, UserRole } from '@/types';
export interface ExtendedUser extends User {
  status: 'active' | 'inactive' | 'suspended' | 'pending';
  lastLogin?: string;
  createdAt: string;
  phoneNumber?: string;
  department?: string;
  permissions?: string[];
  loginCount?: number;
}
export interface UserManagementPanelProps {
  onUserEdit?: (user: ExtendedUser) => void;
  onUserDelete?: (userId: string) => void;
  onUserBlock?: (userId: string, blocked: boolean) => void;
  onInviteUser?: () => void;
  allowBulkActions?: boolean;
  showFilters?: boolean;
}
export const UserManagementPanel = memo<UserManagementPanelProps>(({
  onUserEdit,
  onUserDelete,
  onUserBlock,
  onInviteUser,
  allowBulkActions = true,
  showFilters = true,
}) => {
  const theme = useTheme();
  const [users, setUsers] = useState<ExtendedUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  // Search and filter
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<UserRole | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  // Selection
  const [selected, setSelected] = useState<string[]>([]);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedUser, setSelectedUser] = useState<ExtendedUser | null>(null);
  // Dialogs
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  // Edit form state
  const [editFormData, setEditFormData] = useState<Partial<ExtendedUser>>({});
  // Fetch users
  useEffect(() => {
    fetchUsers();
  }, []);
  const fetchUsers = async () => {
    setLoading(true);
    try {
      // In a real app, this would fetch from the API
      // const response = await api.get('/admin/users');
      // setUsers(response.data);
      // Mock data for demonstration
      const mockUsers: ExtendedUser[] = [
        {
          id: '1',
          email: 'admin@example.com',
          displayName: 'Admin User',
          role: 'admin',
          avatarUrl: undefined,
          status: 'active',
          lastLogin: new Date().toISOString(),
          createdAt: new Date(2024, 0, 1).toISOString(),
          department: 'Administration',
          loginCount: 245,
        },
        {
          id: '2',
          email: 'teacher1@example.com',
          displayName: 'Sarah Johnson',
          role: 'teacher',
          avatarUrl: undefined,
          status: 'active',
          lastLogin: new Date().toISOString(),
          createdAt: new Date(2024, 2, 15).toISOString(),
          department: 'Mathematics',
          loginCount: 189,
        },
        {
          id: '3',
          email: 'student1@example.com',
          displayName: 'John Smith',
          role: 'student',
          avatarUrl: undefined,
          status: 'active',
          lastLogin: new Date().toISOString(),
          createdAt: new Date(2024, 5, 20).toISOString(),
          department: 'Grade 10',
          loginCount: 67,
        },
        {
          id: '4',
          email: 'teacher2@example.com',
          displayName: 'Michael Brown',
          role: 'teacher',
          avatarUrl: undefined,
          status: 'suspended',
          lastLogin: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          createdAt: new Date(2024, 1, 10).toISOString(),
          department: 'Science',
          loginCount: 134,
        },
        {
          id: '5',
          email: 'student2@example.com',
          displayName: 'Emily Davis',
          role: 'student',
          avatarUrl: undefined,
          status: 'pending',
          createdAt: new Date().toISOString(),
          department: 'Grade 11',
          loginCount: 0,
        },
      ];
      setUsers(mockUsers);
    } catch (err) {
      setError('Failed to fetch users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelected(filteredUsers.map(user => user.id));
    } else {
      setSelected([]);
    }
  };
  const handleSelectUser = (userId: string) => {
    const selectedIndex = selected.indexOf(userId);
    let newSelected: string[] = [];
    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, userId);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }
    setSelected(newSelected);
  };
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, user: ExtendedUser) => {
    setAnchorEl(event.currentTarget);
    setSelectedUser(user);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedUser(null);
  };
  const handleEditUser = (user: ExtendedUser) => {
    setEditFormData(user);
    setEditDialogOpen(true);
    handleMenuClose();
  };
  const handleDeleteUser = (user: ExtendedUser) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };
  const handleBlockUser = async (user: ExtendedUser) => {
    const newStatus = user.status === 'active' ? 'suspended' : 'active';
    setUsers(prev =>
      prev.map(u => u.id === user.id ? { ...u, status: newStatus } : u)
    );
    onUserBlock?.(user.id, newStatus === 'suspended');
    handleMenuClose();
  };
  const handleBulkAction = (action: string) => {
    switch (action) {
      case 'delete':
        // Handle bulk delete
        break;
      case 'block':
        // Handle bulk block
        break;
      case 'export':
        // Handle export
        break;
    }
  };
  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return <AdminIcon fontSize="small" />;
      case 'teacher':
        return <TeacherIcon fontSize="small" />;
      case 'student':
        return <StudentIcon fontSize="small" />;
      default:
        return <Person Icon fontSize="small" />;
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'suspended':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };
  const filteredUsers = users.filter(user => {
    const matchesSearch = searchTerm
      ? user.displayName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
      : true;
    const matchesRole = filterRole === 'all' || user.role === filterRole;
    const matchesStatus = filterStatus === 'all' || user.status === filterStatus;
    return matchesSearch && matchesRole && matchesStatus;
  });
  const paginatedUsers = filteredUsers.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" fontWeight="bold">
            User Management
          </Typography>
          <Stack direction="row" spacing={1}>
            {allowBulkActions && selected.length > 0 && (
              <>
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={(e: React.MouseEvent) => () => handleBulkAction('delete')}
                >
                  Delete ({selected.length})
                </Button>
                <Button
                  size="small"
                  startIcon={<BlockIcon />}
                  onClick={(e: React.MouseEvent) => () => handleBulkAction('block')}
                >
                  Block ({selected.length})
                </Button>
              </>
            )}
            <Button
              variant="contained"
              size="small"
              startIcon={<AddUserIcon />}
              onClick={(e: React.MouseEvent) => () => setInviteDialogOpen(true)}
            >
              Invite User
            </Button>
            <IconButton size="small">
              <ExportIcon />
            </IconButton>
          </Stack>
        </Stack>
        {/* Filters */}
        {showFilters && (
          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <TextField
              size="small"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ flex: 1, maxWidth: 300 }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={filterRole}
                label="Role"
                onChange={(e) => setFilterRole(e.target.value as UserRole | 'all')}
              >
                <MenuItem value="all">All Roles</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
                <MenuItem value="teacher">Teacher</MenuItem>
                <MenuItem value="student">Student</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterStatus}
                label="Status"
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="suspended">Suspended</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        )}
      </Box>
      {/* Loading indicator */}
      {loading && <LinearProgress />}
      {/* Error message */}
      {error && (
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      )}
      {/* Table */}
      <TableContainer sx={{ flex: 1 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {allowBulkActions && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={
                      selected.length > 0 && selected.length < filteredUsers.length
                    }
                    checked={
                      filteredUsers.length > 0 && selected.length === filteredUsers.length
                    }
                    onChange={handleSelectAll}
                  />
                </TableCell>
              )}
              <TableCell>User</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell>Login Count</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedUsers.map(user => (
              <TableRow
                key={user.id}
                hover
                selected={selected.includes(user.id)}
              >
                {allowBulkActions && (
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selected.includes(user.id)}
                      onChange={() => handleSelectUser(user.id)}
                    />
                  </TableCell>
                )}
                <TableCell>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar
                      src={user.avatarUrl}
                      sx={{
                        width: 32,
                        height: 32,
                        backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      }}
                    >
                      {user.displayName?.charAt(0) || user.email.charAt(0)}
                    </Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight={500}>
                        {user.displayName || 'No name'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.email}
                      </Typography>
                    </Box>
                  </Stack>
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.role}
                    size="small"
                    icon={getRoleIcon(user.role)}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {user.department || '-'}
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
                  <Typography variant="body2">
                    {user.lastLogin
                      ? format(new Date(user.lastLogin), 'MMM dd, yyyy')
                      : 'Never'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {user.loginCount || 0}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {format(new Date(user.createdAt), 'MMM dd, yyyy')}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={(e: React.MouseEvent) => (e) => handleMenuOpen(e, user)}
                  >
                    <MoreIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {/* Pagination */}
      <TablePagination
        component="div"
        count={filteredUsers.length}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10));
          setPage(0);
        }}
      />
      {/* Action menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={(e: React.MouseEvent) => () => selectedUser && handleEditUser(selectedUser)}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} /> Edit
        </MenuItem>
        <MenuItem onClick={(e: React.MouseEvent) => () => selectedUser && handleBlockUser(selectedUser)}>
          <BlockIcon fontSize="small" sx={{ mr: 1 }} />
          {selectedUser?.status === 'active' ? 'Suspend' : 'Activate'}
        </MenuItem>
        <MenuItem onClick={(e: React.MouseEvent) => () => selectedUser && handleDeleteUser(selectedUser)}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} /> Delete
        </MenuItem>
        <MenuItem>
          <ResetPasswordIcon fontSize="small" sx={{ mr: 1 }} /> Reset Password
        </MenuItem>
        <MenuItem>
          <EmailIcon fontSize="small" sx={{ mr: 1 }} /> Send Email
        </MenuItem>
      </Menu>
      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Display Name"
              value={editFormData.displayName || ''}
              onChange={(e) =>
                setEditFormData({ ...editFormData, displayName: e.target.value })
              }
              fullWidth
            />
            <TextField
              label="Email"
              value={editFormData.email || ''}
              onChange={(e) =>
                setEditFormData({ ...editFormData, email: e.target.value })
              }
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={editFormData.role || 'student'}
                label="Role"
                onChange={(e) =>
                  setEditFormData({ ...editFormData, role: e.target.value as UserRole })
                }
              >
                <MenuItem value="admin">Admin</MenuItem>
                <MenuItem value="teacher">Teacher</MenuItem>
                <MenuItem value="student">Student</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={editFormData.status || 'active'}
                label="Status"
                onChange={(e) =>
                  setEditFormData({ ...editFormData, status: e.target.value as any })
                }
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="suspended">Suspended</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Department"
              value={editFormData.department || ''}
              onChange={(e) =>
                setEditFormData({ ...editFormData, department: e.target.value })
              }
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={(e: React.MouseEvent) => () => {
              // Save changes
              if (selectedUser && editFormData) {
                setUsers(prev =>
                  prev.map(u =>
                    u.id === selectedUser.id ? { ...u, ...editFormData } as ExtendedUser : u
                  )
                );
                onUserEdit?.(editFormData as ExtendedUser);
              }
              setEditDialogOpen(false);
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user "{selectedUser?.displayName || selectedUser?.email}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={(e: React.MouseEvent) => () => {
              if (selectedUser) {
                setUsers(prev => prev.filter(u => u.id !== selectedUser.id));
                onUserDelete?.(selectedUser.id);
              }
              setDeleteDialogOpen(false);
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      {/* Invite User Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite New User</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Email Address" type="email" fullWidth />
            <TextField label="Display Name" fullWidth />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select defaultValue="student" label="Role">
                <MenuItem value="admin">Admin</MenuItem>
                <MenuItem value="teacher">Teacher</MenuItem>
                <MenuItem value="student">Student</MenuItem>
              </Select>
            </FormControl>
            <TextField label="Department" fullWidth />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Send invitation email"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setInviteDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={(e: React.MouseEvent) => () => {
              onInviteUser?.();
              setInviteDialogOpen(false);
            }}
          >
            Send Invitation
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
});
UserManagementPanel.displayName = 'UserManagementPanel';
export default UserManagementPanel;