/**
 * User Management Dashboard
 *
 * Allows admins to:
 * - View all users
 * - Assign roles
 * - Manage user permissions
 * - View user activity
 */

import { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Table,
  Badge,
  Button,
  Select,
  TextInput,
  Group,
  Modal,
  Alert,
  LoadingOverlay,
  Card,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
} from '@mantine/core';
import {
  IconUserPlus,
  IconEdit,
  IconTrash,
  IconSearch,
  IconCheck,
  IconX,
  IconAlertCircle,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import type { UserRole } from '../../types';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  createdAt: string;
  lastActive: string;
  status: 'active' | 'inactive' | 'suspended';
}

const ROLE_COLORS = {
  admin: 'red',
  teacher: 'blue',
  student: 'green',
  parent: 'orange',
} as const;

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Administrator' },
  { value: 'teacher', label: 'Teacher' },
  { value: 'student', label: 'Student' },
  { value: 'parent', label: 'Parent' },
];

export function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [newRole, setNewRole] = useState<UserRole>('student');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('clerkToken')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load users');

      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error loading users:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load users',
        color: 'red',
        icon: <IconX />,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async () => {
    if (!selectedUser) return;

    setUpdating(true);
    try {
      const response = await fetch(`/api/admin/users/${selectedUser.id}/role`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('clerkToken')}`,
        },
        body: JSON.stringify({ role: newRole }),
      });

      if (!response.ok) throw new Error('Failed to update role');

      // Update local state
      setUsers(users.map(u =>
        u.id === selectedUser.id ? { ...u, role: newRole } : u
      ));

      showNotification({
        title: 'Success',
        message: `Updated ${selectedUser.email}'s role to ${newRole}`,
        color: 'green',
        icon: <IconCheck />,
      });

      setRoleModalOpen(false);
      setSelectedUser(null);
    } catch (error) {
      console.error('Error updating role:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to update user role',
        color: 'red',
        icon: <IconX />,
      });
    } finally {
      setUpdating(false);
    }
  };

  const openRoleModal = (user: User) => {
    setSelectedUser(user);
    setNewRole(user.role);
    setRoleModalOpen(true);
  };

  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.firstName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.lastName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getRoleBadge = (role: UserRole) => (
    <Badge color={ROLE_COLORS[role]} variant="filled">
      {role.charAt(0).toUpperCase() + role.slice(1)}
    </Badge>
  );

  const getStatusBadge = (status: User['status']) => {
    const colors = {
      active: 'green',
      inactive: 'gray',
      suspended: 'red',
    };
    return (
      <Badge color={colors[status]} variant="light">
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <Container size="xl" py="xl">
      <Stack gap="lg">
        {/* Header */}
        <Group justify="space-between">
          <Title order={2}>User Management</Title>
          <Button
            leftSection={<IconUserPlus size={16} />}
            onClick={() => {/* TODO: Add user creation */}}
          >
            Add User
          </Button>
        </Group>

        {/* Info Alert */}
        <Alert icon={<IconAlertCircle />} color="blue" variant="light">
          Manage user roles and permissions. Role changes take effect immediately.
        </Alert>

        {/* Search Bar */}
        <Card>
          <TextInput
            placeholder="Search by email, name..."
            leftSection={<IconSearch size={16} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="md"
          />
        </Card>

        {/* Users Table */}
        <Card pos="relative">
          <LoadingOverlay visible={loading} />

          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>User</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Role</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Last Active</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {filteredUsers.map((user) => (
                <Table.Tr key={user.id}>
                  <Table.Td>
                    <Text fw={500}>
                      {user.firstName} {user.lastName}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {user.email}
                    </Text>
                  </Table.Td>
                  <Table.Td>{getRoleBadge(user.role)}</Table.Td>
                  <Table.Td>{getStatusBadge(user.status)}</Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {new Date(user.lastActive).toLocaleDateString()}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="Edit Role">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          onClick={() => openRoleModal(user)}
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Delete User">
                        <ActionIcon
                          variant="light"
                          color="red"
                          onClick={() => {/* TODO: Delete user */}}
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

          {filteredUsers.length === 0 && !loading && (
            <Text ta="center" py="xl" c="dimmed">
              No users found matching your search.
            </Text>
          )}
        </Card>

        {/* Role Update Modal */}
        <Modal
          opened={roleModalOpen}
          onClose={() => setRoleModalOpen(false)}
          title="Update User Role"
          centered
        >
          <Stack gap="md">
            {selectedUser && (
              <>
                <Text size="sm">
                  Update role for <strong>{selectedUser.email}</strong>
                </Text>

                <Select
                  label="New Role"
                  data={ROLE_OPTIONS}
                  value={newRole}
                  onChange={(value) => setNewRole(value as UserRole)}
                  required
                />

                <Alert icon={<IconAlertCircle />} color="orange" variant="light">
                  Role changes take effect immediately and cannot be undone.
                </Alert>

                <Group justify="flex-end" gap="sm">
                  <Button
                    variant="light"
                    onClick={() => setRoleModalOpen(false)}
                    disabled={updating}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleUpdateRole}
                    loading={updating}
                    leftSection={<IconCheck size={16} />}
                  >
                    Update Role
                  </Button>
                </Group>
              </>
            )}
          </Stack>
        </Modal>
      </Stack>
    </Container>
  );
}

export default UserManagement;

