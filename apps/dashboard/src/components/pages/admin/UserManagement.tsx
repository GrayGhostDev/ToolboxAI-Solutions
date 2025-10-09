import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Table,
  Button,
  Badge,
  Avatar,
  TextInput,
  Menu,
  Modal,
  Select,
  Text,
  Stack,
  Alert,
  Loader,
  Switch,
  Grid,
  ActionIcon,
  Group,
  Pagination,
  Checkbox,
  Tooltip,
} from '@mantine/core';
import {
  IconSearch,
  IconPlus,
  IconEdit,
  IconTrash,
  IconDots,
  IconFilter,
  IconDownload,
  IconUpload,
  IconLock,
  IconLockOpen,
  IconMail,
  IconCheck,
  IconX,
  IconUserPlus,
  IconUser,
  IconUsers,
  IconSchool,
  IconShield,
} from '@tabler/icons-react';
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

const EditUserDialog: React.FC<EditUserDialogProps> = ({ open, user, onClose, onSave }) => {
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
    <Modal opened={open} onClose={onClose} title={user ? 'Edit User' : 'Add New User'} size="sm">
      <Stack gap="md">
        <TextInput
          label="Username"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
        />
        <TextInput
          label="Email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          required
        />
        <Select
          label="Role"
          value={formData.role}
          onChange={(value) => setFormData({ ...formData, role: value as any })}
          data={[
            { value: 'admin', label: 'Admin' },
            { value: 'teacher', label: 'Teacher' },
            { value: 'student', label: 'Student' },
            { value: 'parent', label: 'Parent' },
          ]}
        />
        <Select
          label="Status"
          value={formData.status}
          onChange={(value) => setFormData({ ...formData, status: value as any })}
          data={[
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' },
            { value: 'suspended', label: 'Suspended' },
          ]}
        />
        <TextInput
          label="School"
          value={formData.school}
          onChange={(e) => setFormData({ ...formData, school: e.target.value })}
        />
        {(formData.role === 'student' || formData.role === 'parent') && (
          <TextInput
            label="Grade"
            type="number"
            value={formData.grade}
            onChange={(e) => setFormData({ ...formData, grade: parseInt(e.target.value) })}
            min={1}
            max={12}
          />
        )}
        <Group justify="flex-end" mt="md">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>
            {user ? 'Update' : 'Create'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
};

const UserManagement: React.FC = () => {
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
        return <IconShield size={16} />;
      case 'teacher':
        return <IconSchool size={16} />;
      case 'student':
        return <IconUser size={16} />;
      case 'parent':
        return <IconUsers size={16} />;
      default:
        return <IconUser size={16} />;
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
      <Text size="xl" fw={700} mb="lg">
        User Management
      </Text>

      {/* Statistics Cards */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card padding="lg">
            <Group justify="space-between">
              <Box>
                <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                  Total Users
                </Text>
                <Text fw={700} size="xl">{users.length}</Text>
              </Box>
              <Avatar color="blue" radius="md" size="lg">
                <IconUsers size="1.5rem" />
              </Avatar>
            </Group>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card padding="lg">
            <Group justify="space-between">
              <Box>
                <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                  Active Users
                </Text>
                <Text fw={700} size="xl">
                  {users.filter((u) => u.status === 'active').length}
                </Text>
              </Box>
              <Avatar color="green" radius="md" size="lg">
                <IconCheck size="1.5rem" />
              </Avatar>
            </Group>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card padding="lg">
            <Group justify="space-between">
              <Box>
                <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                  Teachers
                </Text>
                <Text fw={700} size="xl">
                  {users.filter((u) => u.role === 'teacher').length}
                </Text>
              </Box>
              <Avatar color="cyan" radius="md" size="lg">
                <IconSchool size="1.5rem" />
              </Avatar>
            </Group>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card padding="lg">
            <Group justify="space-between">
              <Box>
                <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                  Students
                </Text>
                <Text fw={700} size="xl">
                  {users.filter((u) => u.role === 'student').length}
                </Text>
              </Box>
              <Avatar color="violet" radius="md" size="lg">
                <IconUser size="1.5rem" />
              </Avatar>
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* User Table */}
      <Card padding="lg">
        <Group justify="space-between" mb="md">
          <Text size="lg" fw={600}>Users</Text>
          <Group gap="xs">
            <Button
              variant="outline"
              leftSection={<IconUpload size="1rem" />}
              size="sm"
            >
              Import
            </Button>
            <Button
              variant="outline"
              leftSection={<IconDownload size="1rem" />}
              size="sm"
              onClick={handleExportUsers}
            >
              Export
            </Button>
            <Button
              leftSection={<IconPlus size="1rem" />}
              onClick={() => {
                setSelectedUser(null);
                setEditDialogOpen(true);
              }}
            >
              Add User
            </Button>
          </Group>
        </Group>

        {/* Filters */}
        <Group mb="md" gap="sm">
          <TextInput
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flexGrow: 1, maxWidth: 300 }}
            leftSection={<IconSearch size="1rem" />}
          />
          <Select
            placeholder="All Roles"
            value={roleFilter}
            onChange={(value) => setRoleFilter(value || 'all')}
            style={{ minWidth: 120 }}
            data={[
              { value: 'all', label: 'All Roles' },
              { value: 'admin', label: 'Admin' },
              { value: 'teacher', label: 'Teacher' },
              { value: 'student', label: 'Student' },
              { value: 'parent', label: 'Parent' },
            ]}
          />
          <Select
            placeholder="All Status"
            value={statusFilter}
            onChange={(value) => setStatusFilter(value || 'all')}
            style={{ minWidth: 120 }}
            data={[
              { value: 'all', label: 'All Status' },
              { value: 'active', label: 'Active' },
              { value: 'inactive', label: 'Inactive' },
              { value: 'suspended', label: 'Suspended' },
            ]}
          />
          {selectedUsers.length > 0 && (
            <Button
              variant="outline"
              leftSection={<IconFilter size="1rem" />}
              onClick={(e) => setBulkActionMenu(e.currentTarget)}
            >
              Bulk Actions ({selectedUsers.length})
            </Button>
          )}
        </Group>

        {/* Table */}
        {loading ? (
          <Box style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
            <Loader />
          </Box>
        ) : (
          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th style={{ width: '50px' }}>
                    <Checkbox
                      checked={selectedUsers.length === filteredUsers.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedUsers(filteredUsers.map((u) => u.id));
                        } else {
                          setSelectedUsers([]);
                        }
                      }}
                    />
                  </Table.Th>
                  <Table.Th>User</Table.Th>
                  <Table.Th>Role</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>School</Table.Th>
                  <Table.Th>Last Active</Table.Th>
                  <Table.Th>Verified</Table.Th>
                  <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredUsers
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((user) => (
                    <Table.Tr key={user.id}>
                      <Table.Td>
                        <Checkbox
                          checked={selectedUsers.includes(user.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedUsers([...selectedUsers, user.id]);
                            } else {
                              setSelectedUsers(selectedUsers.filter((id) => id !== user.id));
                            }
                          }}
                        />
                      </Table.Td>
                      <Table.Td>
                        <Group gap="sm">
                          <Avatar size="sm" radius="xl">
                            {user.username[0].toUpperCase()}
                          </Avatar>
                          <Box>
                            <Text size="sm" fw={500}>
                              {user.username}
                            </Text>
                            <Text size="xs" c="dimmed">
                              {user.email}
                            </Text>
                          </Box>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          leftSection={getRoleIcon(user.role)}
                          variant="outline"
                          size="sm"
                        >
                          {user.role}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          color={getStatusColor(user.status)}
                          size="sm"
                        >
                          {user.status}
                        </Badge>
                      </Table.Td>
                      <Table.Td>{user.school || '-'}</Table.Td>
                      <Table.Td>
                        <Text size="xs">{user.lastActive}</Text>
                      </Table.Td>
                      <Table.Td>
                        {user.verified ? (
                          <IconCheck color="var(--mantine-color-green-6)" size="1rem" />
                        ) : (
                          <IconX color="var(--mantine-color-red-6)" size="1rem" />
                        )}
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'right' }}>
                        <ActionIcon
                          variant="subtle"
                          onClick={(e) => {
                            setSelectedUser(user);
                            setAnchorEl(e.currentTarget);
                          }}
                        >
                          <IconDots size="1rem" />
                        </ActionIcon>
                      </Table.Td>
                    </Table.Tr>
                  ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}

        <Group justify="space-between" mt="md">
          <Text size="sm" c="dimmed">
            Showing {page * rowsPerPage + 1} to {Math.min((page + 1) * rowsPerPage, filteredUsers.length)} of {filteredUsers.length} entries
          </Text>
          <Pagination
            total={Math.ceil(filteredUsers.length / rowsPerPage)}
            value={page + 1}
            onChange={(newPage) => setPage(newPage - 1)}
          />
        </Group>
      </Card>

      {/* Action Menu */}
      <Menu opened={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
        <Menu.Item
          leftSection={<IconEdit size="1rem" />}
          onClick={() => {
            if (selectedUser) handleEditUser(selectedUser);
          }}
        >
          Edit
        </Menu.Item>
        <Menu.Item
          leftSection={<IconLock size="1rem" />}
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
          Reset Password
        </Menu.Item>
        <Menu.Item
          leftSection={selectedUser?.status === 'active' ? <IconLock size="1rem" /> : <IconLockOpen size="1rem" />}
          onClick={() => {
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
          {selectedUser?.status === 'active' ? 'Deactivate' : 'Activate'}
        </Menu.Item>
        <Menu.Item
          leftSection={<IconTrash size="1rem" />}
          color="red"
          onClick={() => {
            setDeleteDialogOpen(true);
            setAnchorEl(null);
          }}
        >
          Delete
        </Menu.Item>
      </Menu>

      {/* Bulk Action Menu */}
      <Menu opened={Boolean(bulkActionMenu)} onClose={() => setBulkActionMenu(null)}>
        <Menu.Item
          leftSection={<IconCheck size="1rem" />}
          onClick={() => handleBulkAction('activate')}
        >
          Activate Selected
        </Menu.Item>
        <Menu.Item
          leftSection={<IconX size="1rem" />}
          onClick={() => handleBulkAction('deactivate')}
        >
          Deactivate Selected
        </Menu.Item>
        <Menu.Item
          leftSection={<IconTrash size="1rem" />}
          color="red"
          onClick={() => handleBulkAction('delete')}
        >
          Delete Selected
        </Menu.Item>
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
      <Modal
        opened={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        title="Confirm Delete"
        centered
      >
        <Text mb="lg">
          Are you sure you want to delete user <Text component="span" fw={700}>{selectedUser?.username}</Text>? This
          action cannot be undone.
        </Text>
        <Group justify="flex-end">
          <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            color="red"
            onClick={() => selectedUser && handleDeleteUser(selectedUser)}
          >
            Delete
          </Button>
        </Group>
      </Modal>
    </Box>
  );
};

export default UserManagement;