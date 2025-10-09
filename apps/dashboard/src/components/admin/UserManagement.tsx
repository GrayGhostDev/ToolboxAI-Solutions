/* eslint-disable @typescript-eslint/no-unused-vars */
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Box,
  Stack,
  Avatar,
  Badge,
  ActionIcon,
  Skeleton,
  Alert,
  Table,
  Paper,
  Grid,
  Select,
  TextInput,
  Button,
  Modal,
  Tabs,
  Tooltip,
  Menu,
  Switch,
  Group,
  SimpleGrid,
} from '@mantine/core';
import {
  IconUser,
  IconPlus,
  IconEdit,
  IconTrash,
  IconDotsVertical,
  IconSearch,
  IconFilter,
  IconDownload,
  IconUpload,
  IconRefresh,
  IconSchool,
  IconShield,
  IconUserPlus,
  IconBan,
  IconCheck,
  IconAlertTriangle,
  IconUsers,
  IconSecurity,
} from '@tabler/icons-react';
import { useMantineTheme } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { 
  listUsers, 
  createUser, 
  updateUser, 
  deleteUser, 
  suspendUser, 
  listSchools
} from '../../services/api';
import type { User, UserCreate, UserUpdate } from '@/types/api';

interface UserWithStats extends User {
  lastLogin?: string;
  loginCount?: number;
  createdLessons?: number;
  studentsManaged?: number;
  status: 'active' | 'inactive' | 'suspended' | 'pending';
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
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  const { isConnected, subscribe, unsubscribe } = useWebSocketContext();
  
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
    email: '',
    username: '',
    firstName: '',
    lastName: '',
    displayName: '',
    role: 'student',
    schoolId: '',
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
          is_active: filters.status === 'active' ? true : filters.status === 'inactive' ? false : undefined,
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
        createdLessons: user.created_lessons || (user.role === 'teacher' ? Math.floor(Math.random() * 20) + 5 : 0),
        studentsManaged: user.students_managed || (user.role === 'teacher' ? Math.floor(Math.random() * 30) + 10 : 0),
        status: user.is_active === false ? 'suspended' : 
                user.is_verified === false ? 'pending' : 'active',
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
        firstName: 'User',
        lastName: `${index + 1}`,
        displayName: `User ${index + 1}`,
        avatarUrl: undefined,
        role: ['student', 'teacher', 'admin', 'parent'][Math.floor(Math.random() * 4)] as any,
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
        status: Math.random() > 0.9 ? 'suspended' : Math.random() > 0.8 ? 'pending' : 'active',
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

    const subscriptionId = subscribe('user_management', (message: any) => {
      if (message.type === 'USER_UPDATED') {
        setUsers(prevUsers =>
          prevUsers.map(user =>
            user.id === message.payload.userId
              ? { ...user, ...message.payload.updates }
              : user
          )
        );
      } else if (message.type === 'USER_CREATED') {
        setUsers(prevUsers => [message.payload.user, ...prevUsers]);
      } else if (message.type === 'USER_DELETED') {
        setUsers(prevUsers => prevUsers.filter(user => user.id !== message.payload.userId));
      }
    });

    return () => {
      unsubscribe(subscriptionId);
    };
  }, [isConnected, subscribe, unsubscribe]);

  // Filter users based on current tab and filters
  const filteredUsers = React.useMemo(() => {
    let filtered = users;

    // Tab filtering
    switch (currentTab) {
      case 1:
        filtered = filtered.filter(user => user.role === 'teacher');
        break;
      case 2:
        filtered = filtered.filter(user => user.role === 'admin');
        break;
      case 3:
        filtered = filtered.filter(user => user.role === 'parent');
        break;
      case 4:
        filtered = filtered.filter(user => user.status === 'pending');
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
        email: '',
        username: '',
        firstName: '',
        lastName: '',
        displayName: '',
        role: 'student',
        schoolId: '',
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
          user.id === userId ? { ...user, status: 'suspended', isActive: false } : user
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
      case 'active':
        return 'green';
      case 'inactive':
        return 'gray';
      case 'suspended':
        return 'red';
      case 'pending':
        return 'orange';
      default:
        return 'gray';
    }
  };

  const getRoleIcon = (role: string) => {
    const iconProps = { size: 16 };
    switch (role) {
      case 'admin':
        return <IconShield {...iconProps} />;
      case 'teacher':
        return <IconSchool {...iconProps} />;
      case 'parent':
        return <IconUsers {...iconProps} />;
      default:
        return <IconUser {...iconProps} />;
    }
  };

  if (loading) {
    return (
      <SimpleGrid cols={1} spacing="lg">
        <Card>
          <Skeleton height={40} mb="md" />
          <Skeleton height={400} />
        </Card>
      </SimpleGrid>
    );
  }

  return (
    <>
      <SimpleGrid cols={1} spacing="lg">
        {/* Header */}
        <Card>
          <Stack justify="space-between" align="center" direction="row" mb="md">
            <Text size="xl" fw={600}>
              User Management
            </Text>
            <Group gap="sm">
              {showBulkActions && (
                <>
                  <Button variant="outline" leftSection={<IconUpload size={16} />}>
                    Import
                  </Button>
                  <Button variant="outline" leftSection={<IconDownload size={16} />}>
                    Export
                  </Button>
                </>
              )}
              <Button
                variant="filled"
                leftSection={<IconUserPlus size={16} />}
                onClick={() => setIsCreateDialogOpen(true)}
              >
                Add User
              </Button>
            </Group>
          </Stack>

          {error && (
            <Alert color="orange" mb="md">
              Using fallback data: {error}
            </Alert>
          )}

          {/* Filters */}
          <Group gap="sm" wrap="wrap" mb="md">
            <TextInput
              placeholder="Search users..."
              leftSection={<IconSearch size={16} />}
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              style={{ minWidth: 200 }}
            />
            <Select
              placeholder="All Roles"
              data={[
                { value: '', label: 'All Roles' },
                { value: 'student', label: 'Student' },
                { value: 'teacher', label: 'Teacher' },
                { value: 'admin', label: 'Admin' },
                { value: 'parent', label: 'Parent' },
              ]}
              value={filters.role || ''}
              onChange={(value) => setFilters({ ...filters, role: value || undefined })}
              style={{ minWidth: 120 }}
              clearable
            />
            <Select
              placeholder="All Status"
              data={[
                { value: '', label: 'All Status' },
                { value: 'active', label: 'Active' },
                { value: 'inactive', label: 'Inactive' },
                { value: 'suspended', label: 'Suspended' },
                { value: 'pending', label: 'Pending' },
              ]}
              value={filters.status || ''}
              onChange={(value) => setFilters({ ...filters, status: value || undefined })}
              style={{ minWidth: 120 }}
              clearable
            />
            <Select
              placeholder="All Schools"
              data={[
                { value: '', label: 'All Schools' },
                ...schools.map((school) => ({
                  value: school.id,
                  label: school.name,
                })),
              ]}
              value={filters.schoolId || ''}
              onChange={(value) => setFilters({ ...filters, schoolId: value || undefined })}
              style={{ minWidth: 150 }}
              clearable
            />
            <ActionIcon onClick={fetchData} variant="light">
              <IconRefresh size={16} />
            </ActionIcon>
          </Group>

          {/* Tabs */}
          <Tabs value={currentTab.toString()} onChange={(value) => setCurrentTab(parseInt(value || '0'))}>
            <Tabs.List>
              <Tabs.Tab value="0">{`All Users (${users.length})`}</Tabs.Tab>
              <Tabs.Tab value="1">{`Teachers (${users.filter(u => u.role === 'teacher').length})`}</Tabs.Tab>
              <Tabs.Tab value="2">{`Admins (${users.filter(u => u.role === 'admin').length})`}</Tabs.Tab>
              <Tabs.Tab value="3">{`Parents (${users.filter(u => u.role === 'parent').length})`}</Tabs.Tab>
              <Tabs.Tab value="4">{`Pending (${users.filter(u => u.status === 'pending').length})`}</Tabs.Tab>
            </Tabs.List>
          </Tabs>
        </Card>

        {/* Users Table */}
        <Card>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>User</Table.Th>
                <Table.Th>Role</Table.Th>
                <Table.Th>School</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Last Login</Table.Th>
                <Table.Th>Created</Table.Th>
                <Table.Th>Stats</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {filteredUsers.slice(0, 50).map((user) => (
                <Table.Tr key={user.id}>
                  <Table.Td>
                    <Group gap="sm">
                      <Avatar src={user.avatarUrl} size="sm">
                        {user.firstName.charAt(0)}
                      </Avatar>
                      <Box>
                        <Text size="sm" fw={500}>
                          {user.displayName}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {user.email}
                        </Text>
                      </Box>
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Badge
                      variant="light"
                      color={user.role === 'admin' ? 'red' : user.role === 'teacher' ? 'blue' : 'gray'}
                      leftSection={getRoleIcon(user.role)}
                    >
                      {user.role}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {user.schoolName || 'No School'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge
                      variant="light"
                      color={getStatusColor(user.status)}
                    >
                      {user.status}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {user.lastLogin
                        ? new Date(user.lastLogin).toLocaleDateString()
                        : 'Never'
                      }
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {new Date(user.createdAt).toLocaleDateString()}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Stack gap={2}>
                      {user.role === 'teacher' && (
                        <>
                          <Text size="xs">
                            {user.createdLessons} lessons
                          </Text>
                          <Text size="xs">
                            {user.studentsManaged} students
                          </Text>
                        </>
                      )}
                      {user.role === 'student' && (
                        <>
                          <Text size="xs">
                            Level {user.level}
                          </Text>
                          <Text size="xs">
                            {user.totalXP?.toLocaleString()} XP
                          </Text>
                        </>
                      )}
                      <Text size="xs">
                        {user.loginCount} logins
                      </Text>
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="Edit User">
                        <ActionIcon
                          size="sm"
                          variant="light"
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
                          <IconEdit size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label={user.status === 'suspended' ? 'Unsuspend User' : 'Suspend User'}>
                        <ActionIcon
                          size="sm"
                          variant="light"
                          color={user.status === 'suspended' ? 'green' : 'orange'}
                          onClick={() => handleSuspendUser(user.id)}
                        >
                          {user.status === 'suspended' ? <IconCheck size={16} /> : <IconBan size={16} />}
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Delete User">
                        <ActionIcon
                          size="sm"
                          variant="light"
                          color="red"
                          onClick={() => handleDeleteUser(user.id)}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      </SimpleGrid>

      {/* Create User Dialog */}
      <Modal
        opened={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        title="Create New User"
        size="lg"
      >
        <Stack gap="md">
          <SimpleGrid cols={2} spacing="md">
            <TextInput
              label="First Name"
              value={formData.firstName}
              onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
            />
            <TextInput
              label="Last Name"
              value={formData.lastName}
              onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
            />
            <TextInput
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <TextInput
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
            <Select
              label="Role"
              data={[
                { value: 'student', label: 'Student' },
                { value: 'teacher', label: 'Teacher' },
                { value: 'admin', label: 'Admin' },
                { value: 'parent', label: 'Parent' },
              ]}
              value={formData.role}
              onChange={(value) => setFormData({ ...formData, role: value as any })}
            />
            <Select
              label="School"
              data={schools.map((school) => ({
                value: school.id,
                label: school.name,
              }))}
              value={formData.schoolId}
              onChange={(value) => setFormData({ ...formData, schoolId: value || '' })}
            />
          </SimpleGrid>
          <Group justify="flex-end" gap="sm">
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateUser}>Create User</Button>
          </Group>
        </Stack>
      </Modal>

      {/* Edit User Dialog */}
      <Modal
        opened={isEditDialogOpen}
        onClose={() => setIsEditDialogOpen(false)}
        title="Edit User"
        size="lg"
      >
        <Stack gap="md">
          <SimpleGrid cols={2} spacing="md">
            <TextInput
              label="First Name"
              value={formData.firstName}
              onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
            />
            <TextInput
              label="Last Name"
              value={formData.lastName}
              onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
            />
            <TextInput
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <Select
              label="Role"
              data={[
                { value: 'student', label: 'Student' },
                { value: 'teacher', label: 'Teacher' },
                { value: 'admin', label: 'Admin' },
                { value: 'parent', label: 'Parent' },
              ]}
              value={formData.role}
              onChange={(value) => setFormData({ ...formData, role: value as any })}
            />
          </SimpleGrid>
          <Switch
            label="Active Account"
            checked={(formData as any).isActive ?? true}
            onChange={(e) => setFormData({ ...formData, isActive: e.currentTarget.checked } as any)}
          />
          <Group justify="flex-end" gap="sm">
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateUser}>Update User</Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

export default UserManagement;