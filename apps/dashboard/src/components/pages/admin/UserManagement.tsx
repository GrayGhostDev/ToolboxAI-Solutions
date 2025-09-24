import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
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
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Grid from '@mui/material/Grid';

import {
  Search,
  Add,
  Edit,
  Delete,
  MoreVert,
  FilterList,
  Download,
  Upload,
  Lock,
  LockOpen,
  Email,
  CheckCircle,
  Cancel,
  PersonAdd,
  Person,
  Group,
  School,
  AdminPanelSettings,
} from '@mui/icons-material';
import { apiClient } from '../../../services/api';
import { useAppDispatch } from '../../../store';
import { addNotification } from '../../../store/slices/uiSlice';

interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'teacher' | 'student' | 'parent';
  status: 'active' | 'inactive' | 'suspended';
  createdAt: string;
  lastActive: string;
  school?: string;
  grade?: number;
  avatar?: string;
  verified: boolean;
}

interface EditUserDialogProps {
  open: boolean;
  user: User | null;
  onClose: () => void;
  onSave: (user: User) => void;
}

const EditUserDialog: React.FunctionComponent<EditUserDialogProps> = ({ open, user, onClose, onSave }) => {
  const [formData, setFormData] = useState<Partial<User>>({
    username: '',
    email: '',
    role: 'student',
    status: 'active',
    school: '',
    grade: undefined,
  });

  useEffect(() => {
    if (user) {
      setFormData(user);
    } else {
      setFormData({
        username: '',
        email: '',
        role: 'student',
        status: 'active',
        school: '',
        grade: undefined,
      });
    }
  }, [user]);

  const handleSubmit = () => {
    onSave(formData as User);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{user ? 'Edit User' : 'Add New User'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 2 }}>
          <TextField
            label="Username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            fullWidth
            required
          />
          <TextField
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            fullWidth
            required
          />
          <FormControl fullWidth>
            <InputLabel>Role</InputLabel>
            <Select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
              label="Role"
            >
              <MenuItem value="admin">Admin</MenuItem>
              <MenuItem value="teacher">Teacher</MenuItem>
              <MenuItem value="student">Student</MenuItem>
              <MenuItem value="parent">Parent</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
              label="Status"
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
              <MenuItem value="suspended">Suspended</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="School"
            value={formData.school}
            onChange={(e) => setFormData({ ...formData, school: e.target.value })}
            fullWidth
          />
          {(formData.role === 'student' || formData.role === 'parent') && (
            <TextField
              label="Grade"
              type="number"
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: parseInt(e.target.value) })}
              fullWidth
              inputProps={{ min: 1, max: 12 }}
            />
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={(e: React.MouseEvent) => onClose}>Cancel</Button>
        <Button onClick={(e: React.MouseEvent) => handleSubmit} variant="contained">
          {user ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const UserManagement: React.FunctionComponent<Record<string, any>> = () => {
  const dispatch = useAppDispatch();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [bulkActionMenu, setBulkActionMenu] = useState<null | HTMLElement>(null);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);

  // Mock data for demonstration
  const mockUsers: User[] = [
    {
      id: '1',
      username: 'admin',
      email: 'admin@toolboxai.com',
      role: 'admin',
      status: 'active',
      createdAt: '2025-01-01',
      lastActive: '2 minutes ago',
      school: 'ToolBoxAI HQ',
      verified: true,
    },
    {
      id: '2',
      username: 'jane.teacher',
      email: 'jane@school.edu',
      role: 'teacher',
      status: 'active',
      createdAt: '2025-01-15',
      lastActive: '1 hour ago',
      school: 'Lincoln Middle School',
      verified: true,
    },
    {
      id: '3',
      username: 'alice.student',
      email: 'alice@student.edu',
      role: 'student',
      status: 'active',
      createdAt: '2025-02-01',
      lastActive: '5 minutes ago',
      school: 'Lincoln Middle School',
      grade: 8,
      verified: false,
    },
    {
      id: '4',
      username: 'bob.parent',
      email: 'bob@parent.com',
      role: 'parent',
      status: 'inactive',
      createdAt: '2025-02-10',
      lastActive: '3 days ago',
      school: 'Lincoln Middle School',
      verified: true,
    },
    {
      id: '5',
      username: 'charlie.student',
      email: 'charlie@student.edu',
      role: 'student',
      status: 'suspended',
      createdAt: '2025-02-15',
      lastActive: '1 week ago',
      school: 'Washington High',
      grade: 9,
      verified: false,
    },
  ];

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      // Replace with actual API call
      // const response = await apiClient.get('/api/v1/admin/users');
      // setUsers(response.data);
      setUsers(mockUsers);
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to load users',
        })
      );
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setEditDialogOpen(true);
    setAnchorEl(null);
  };

  const handleDeleteUser = async (user: User) => {
    try {
      // await apiClient.delete(`/api/v1/admin/users/${user.id}`);
      setUsers(users.filter((u) => u.id !== user.id));
      dispatch(
        addNotification({
          type: 'success',
          message: `User ${user.username} deleted successfully`,
        })
      );
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to delete user',
        })
      );
    }
    setDeleteDialogOpen(false);
    setSelectedUser(null);
  };

  const handleSaveUser = async (user: User) => {
    try {
      if (selectedUser) {
        // Update existing user
        // await apiClient.put(`/api/v1/admin/users/${user.id}`, user);
        setUsers(users.map((u) => (u.id === user.id ? user : u)));
        dispatch(
          addNotification({
            type: 'success',
            message: 'User updated successfully',
          })
        );
      } else {
        // Create new user
        // const response = await apiClient.post('/api/v1/admin/users', user);
        const newUser = { ...user, id: Date.now().toString(), createdAt: new Date().toISOString() };
        setUsers([...users, newUser]);
        dispatch(
          addNotification({
            type: 'success',
            message: 'User created successfully',
          })
        );
      }
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to save user',
        })
      );
    }
  };

  const handleBulkAction = async (action: string) => {
    try {
      switch (action) {
        case 'activate':
          // await apiClient.post('/api/v1/admin/users/bulk-activate', { ids: selectedUsers });
          setUsers(
            users.map((u) => (selectedUsers.includes(u.id) ? { ...u, status: 'active' } : u))
          );
          break;
        case 'deactivate':
          // await apiClient.post('/api/v1/admin/users/bulk-deactivate', { ids: selectedUsers });
          setUsers(
            users.map((u) => (selectedUsers.includes(u.id) ? { ...u, status: 'inactive' } : u))
          );
          break;
        case 'delete':
          // await apiClient.post('/api/v1/admin/users/bulk-delete', { ids: selectedUsers });
          setUsers(users.filter((u) => !selectedUsers.includes(u.id)));
          break;
      }
      dispatch(
        addNotification({
          type: 'success',
          message: `Bulk action completed for ${selectedUsers.length} users`,
        })
      );
      setSelectedUsers([]);
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Bulk action failed',
        })
      );
    }
    setBulkActionMenu(null);
  };

  const handleExportUsers = () => {
    // Implement CSV export
    const csv = users.map((u) => `${u.username},${u.email},${u.role},${u.status}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'users.csv';
    a.click();
  };

  // Filter users
  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <AdminPanelSettings />;
      case 'teacher':
        return <School />;
      case 'student':
        return <Person />;
      case 'parent':
        return <Group />;
      default:
        return <Person />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'suspended':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        User Management
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Total Users
                  </Typography>
                  <Typography variant="h4">{users.length}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <Group />
                </Avatar>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Active Users
                  </Typography>
                  <Typography variant="h4">
                    {users.filter((u) => u.status === 'active').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircle />
                </Avatar>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Teachers
                  </Typography>
                  <Typography variant="h4">
                    {users.filter((u) => u.role === 'teacher').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <School />
                </Avatar>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Students
                  </Typography>
                  <Typography variant="h4">
                    {users.filter((u) => u.role === 'student').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  <Person />
                </Avatar>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* User Table */}
      <Card>
        <CardHeader
          title="Users"
          action={
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                startIcon={<Upload />}
                size="small"
              >
                Import
              </Button>
              <Button
                variant="outlined"
                startIcon={<Download />}
                size="small"
                onClick={(e: React.MouseEvent) => handleExportUsers}
              >
                Export
              </Button>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={(e: React.MouseEvent) => () => {
                  setSelectedUser(null);
                  setEditDialogOpen(true);
                }}
              >
                Add User
              </Button>
            </Stack>
          }
        />
        <CardContent>
          {/* Filters */}
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
              sx={{ flexGrow: 1, maxWidth: 300 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                label="Role"
              >
                <MenuItem value="all">All Roles</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
                <MenuItem value="teacher">Teacher</MenuItem>
                <MenuItem value="student">Student</MenuItem>
                <MenuItem value="parent">Parent</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="suspended">Suspended</MenuItem>
              </Select>
            </FormControl>
            {selectedUsers.length > 0 && (
              <Button
                variant="outlined"
                startIcon={<FilterList />}
                onClick={(e: React.MouseEvent) => (e) => setBulkActionMenu(e.currentTarget)}
              >
                Bulk Actions ({selectedUsers.length})
              </Button>
            )}
          </Stack>

          {/* Table */}
          {loading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <input
                        type="checkbox"
                        checked={selectedUsers.length === filteredUsers.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedUsers(filteredUsers.map((u) => u.id));
                          } else {
                            setSelectedUsers([]);
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>School</TableCell>
                    <TableCell>Last Active</TableCell>
                    <TableCell>Verified</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredUsers
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((user) => (
                      <TableRow key={user.id} hover>
                        <TableCell padding="checkbox">
                          <input
                            type="checkbox"
                            checked={selectedUsers.includes(user.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedUsers([...selectedUsers, user.id]);
                              } else {
                                setSelectedUsers(selectedUsers.filter((id) => id !== user.id));
                              }
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" spacing={2} alignItems="center">
                            <Avatar sx={{ width: 32, height: 32 }}>
                              {user.username[0].toUpperCase()}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight={500}>
                                {user.username}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
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
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={user.status}
                            size="small"
                            color={getStatusColor(user.status)}
                          />
                        </TableCell>
                        <TableCell>{user.school || '-'}</TableCell>
                        <TableCell>
                          <Typography variant="caption">{user.lastActive}</Typography>
                        </TableCell>
                        <TableCell>
                          {user.verified ? (
                            <CheckCircle color="success" fontSize="small" />
                          ) : (
                            <Cancel color="error" fontSize="small" />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={(e: React.MouseEvent) => (e) => {
                              setSelectedUser(user);
                              setAnchorEl(e.currentTarget);
                            }}
                          >
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredUsers.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </CardContent>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem
          onClick={(e: React.MouseEvent) => () => {
            if (selectedUser) handleEditUser(selectedUser);
          }}
        >
          <Edit fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem
          onClick={() => {
            // Send password reset email
            dispatch(
              addNotification({
                type: 'success',
                message: `Password reset email sent to ${selectedUser?.email}`,
              })
            );
            setAnchorEl(null);
          }}
        >
          <Lock fontSize="small" sx={{ mr: 1 }} />
          Reset Password
        </MenuItem>
        <MenuItem
          onClick={(e: React.MouseEvent) => () => {
            // Toggle user status
            if (selectedUser) {
              const newStatus = selectedUser.status === 'active' ? 'inactive' : 'active';
              setUsers(
                users.map((u) => (u.id === selectedUser.id ? { ...u, status: newStatus } : u))
              );
            }
            setAnchorEl(null);
          }}
        >
          {selectedUser?.status === 'active' ? (
            <>
              <Lock fontSize="small" sx={{ mr: 1 }} />
              Deactivate
            </>
          ) : (
            <>
              <LockOpen fontSize="small" sx={{ mr: 1 }} />
              Activate
            </>
          )}
        </MenuItem>
        <MenuItem
          onClick={(e: React.MouseEvent) => () => {
            setDeleteDialogOpen(true);
            setAnchorEl(null);
          }}
          sx={{ color: 'error.main' }}
        >
          <Delete fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Bulk Action Menu */}
      <Menu
        anchorEl={bulkActionMenu}
        open={Boolean(bulkActionMenu)}
        onClose={() => setBulkActionMenu(null)}
      >
        <MenuItem onClick={(e: React.MouseEvent) => () => handleBulkAction('activate')}>
          <CheckCircle fontSize="small" sx={{ mr: 1 }} />
          Activate Selected
        </MenuItem>
        <MenuItem onClick={(e: React.MouseEvent) => () => handleBulkAction('deactivate')}>
          <Cancel fontSize="small" sx={{ mr: 1 }} />
          Deactivate Selected
        </MenuItem>
        <MenuItem onClick={(e: React.MouseEvent) => () => handleBulkAction('delete')} sx={{ color: 'error.main' }}>
          <Delete fontSize="small" sx={{ mr: 1 }} />
          Delete Selected
        </MenuItem>
      </Menu>

      {/* Edit User Dialog */}
      <EditUserDialog
        open={editDialogOpen}
        user={selectedUser}
        onClose={() => {
          setEditDialogOpen(false);
          setSelectedUser(null);
        }}
        onSave={handleSaveUser}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user <strong>{selectedUser?.username}</strong>? This
            action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={(e: React.MouseEvent) => () => selectedUser && handleDeleteUser(selectedUser)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;