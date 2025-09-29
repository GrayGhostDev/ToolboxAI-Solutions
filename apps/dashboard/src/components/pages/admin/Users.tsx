import { useState, useEffect } from "react";
import { Box, Card, Text, Button, Table, Badge, ActionIcon, Stack, TextInput, Modal, Select, Avatar, Group } from '@mantine/core';

import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  suspendUser,
} from "../../../services/api";
import type { User as UserType, UserCreate, UserUpdate } from "@/types/api";
import { IconPlus, IconEdit, IconTrash, IconSearch, IconMail } from "@tabler/icons-react";
interface UserFormData {
  email: string;
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  displayName: string;
  role: string;
  schoolId?: string;
}
export default function Users() {
  const [users, setUsers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<UserType | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    email: "",
    username: "",
    password: "",
    firstName: "",
    lastName: "",
    displayName: "",
    role: "student", // Default role to prevent validation error
    schoolId: "",
  });
  // Fetch users on component mount and when filters change
  useEffect(() => {
    fetchUsers();
  }, [searchTerm, roleFilter]);
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { search: searchTerm };
      if (roleFilter !== "all") {
        params.role = roleFilter;
      }
      const data = await listUsers(params);
      // Convert snake_case to camelCase for frontend
      const mappedUsers = data.map((user: any) => ({
        ...user,
        firstName: user.first_name,
        lastName: user.last_name,
        displayName: user.display_name || `${user.first_name} ${user.last_name}`,
        avatarUrl: user.avatar_url,
        schoolId: user.school_id,
        schoolName: user.school_name,
        classIds: user.class_ids || [],
        isActive: user.is_active,
        isVerified: user.is_verified,
        totalXP: user.total_xp,
        lastLogin: user.last_login,
        createdAt: user.created_at,
        updatedAt: user.updated_at,
      }));
      setUsers(mappedUsers);
    } catch (err) {
      setError("Failed to load users. Please try again.");
      console.error("Error fetching users:", err);
    } finally {
      setLoading(false);
    }
  };
  const handleAdd = () => {
    setEditingUser(null);
    setFormData({
      email: "",
      username: "",
      password: "",
      firstName: "",
      lastName: "",
      displayName: "",
      role: "student", // Default role to prevent validation error
      schoolId: "",
    });
    setOpenDialog(true);
  };
  const handleEdit = (user: UserType) => {
    setEditingUser(user);
    setFormData({
      email: user.email,
      username: user.username,
      password: "", // Don't populate password when editing
      firstName: user.firstName,
      lastName: user.lastName,
      displayName: user.displayName,
      role: user.role,
      schoolId: user.schoolId || "",
    });
    setOpenDialog(true);
  };
  const handleSave = async () => {
    setError(null);
    setLoading(true);
    // Validate required fields
    if (!formData.email || !formData.username || !formData.firstName || 
        !formData.lastName || !formData.role) {
      setError("Please fill in all required fields.");
      setLoading(false);
      return;
    }
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address.");
      setLoading(false);
      return;
    }
    // Validate password for new users
    if (!editingUser && (!formData.password || formData.password.length < 8)) {
      setError("Password must be at least 8 characters long.");
      setLoading(false);
      return;
    }
    try {
      let savedUser: any;
      if (editingUser) {
        // Update existing user
        const updateData: UserUpdate = {
          email: formData.email,
          username: formData.username,
          firstName: formData.firstName,
          lastName: formData.lastName,
          displayName: formData.displayName,
          role: formData.role,
          schoolId: formData.schoolId || undefined,
        };
        // Only include password if it was changed
        if (formData.password) {
          updateData.password = formData.password;
        }
        savedUser = await updateUser(editingUser.id, updateData);
        // Update the user in the list immediately
        setUsers(prev => prev.map(user => 
          user.id === editingUser.id ? { ...savedUser, 
            firstName: savedUser.first_name || savedUser.firstName,
            lastName: savedUser.last_name || savedUser.lastName,
            displayName: savedUser.display_name || savedUser.displayName,
            avatarUrl: savedUser.avatar_url || savedUser.avatarUrl,
            schoolId: savedUser.school_id || savedUser.schoolId
          } : user
        ));
      } else {
        // Create new user
        const createData: UserCreate = {
          email: formData.email,
          username: formData.username,
          password: formData.password || "TempPassword123!", // Provide default if not set
          firstName: formData.firstName,
          lastName: formData.lastName,
          displayName: formData.displayName || `${formData.firstName} ${formData.lastName}`,
          role: formData.role,
          schoolId: formData.schoolId || undefined,
        };
        savedUser = await createUser(createData);
        // Add the new user to the list immediately
        const newUser = {
          ...savedUser,
          firstName: savedUser.first_name || savedUser.firstName,
          lastName: savedUser.last_name || savedUser.lastName,
          displayName: savedUser.display_name || savedUser.displayName,
          avatarUrl: savedUser.avatar_url || savedUser.avatarUrl,
          schoolId: savedUser.school_id || savedUser.schoolId
        };
        setUsers(prev => [newUser, ...prev]);
      }
      setOpenDialog(false);
      // Also refresh from server to ensure consistency
      await fetchUsers();
    } catch (err) {
      setError("Failed to save user. Please try again.");
      console.error("Error saving user:", err);
    } finally {
      setLoading(false);
    }
  };
  const handleDelete = async (userId: string) => {
    if (!window.confirm("Are you sure you want to delete this user?")) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await deleteUser(userId);
      // Remove the user from the list immediately
      setUsers(prev => prev.filter(user => user.id !== userId));
      // Also refresh from server to ensure consistency
      await fetchUsers();
    } catch (err) {
      setError("Failed to delete user. Please try again.");
      console.error("Error deleting user:", err);
    } finally {
      setLoading(false);
    }
  };
  const handleSuspend = async (userId: string) => {
    setError(null);
    try {
      await suspendUser(userId);
      fetchUsers(); // Refresh the list
    } catch (err) {
      setError("Failed to suspend/activate user. Please try again.");
      console.error("Error suspending user:", err);
    }
  };
  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case "admin": return "red";
      case "teacher": return "blue";
      case "student": return "green";
      case "parent": return "cyan";
      default: return "gray";
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "green";
      case "suspended": return "red";
      case "pending": return "orange";
      default: return "gray";
    }
  };
  return (
    <Box>
      {error && (
        <Box mb="md" p="md" style={{ backgroundColor: 'var(--mantine-color-red-1)', borderRadius: 'var(--mantine-radius-sm)' }}>
          <Text c="red">{error}</Text>
        </Box>
      )}
      <Group justify="space-between" mb="lg">
        <Text size="xl" fw={600}>
          Users Management
        </Text>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={handleAdd}
        >
          Add User
        </Button>
      </Group>
      <Card mb="lg">
        <Group align="center" gap="md">
          <TextInput
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftSection={<IconSearch size={16} />}
            style={{ flex: 1 }}
          />
          <Select
            placeholder="Role"
            value={roleFilter}
            onChange={(value) => setRoleFilter(value || "all")}
            data={[
              { value: "all", label: "All Roles" },
              { value: "admin", label: "Admin" },
              { value: "teacher", label: "Teacher" },
              { value: "student", label: "Student" },
              { value: "parent", label: "Parent" },
            ]}
            w={120}
          />
        </Group>
      </Card>
      <Card>
        <Table.ScrollContainer minWidth={800}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>User</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Role</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Last Login</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {loading && users.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={6} ta="center">
                    <Text>Loading users...</Text>
                  </Table.Td>
                </Table.Tr>
              ) : users.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={6} ta="center">
                    <Text>No users found. Add your first user!</Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                users.map((user) => (
                  <Table.Tr key={user.id}>
                    <Table.Td>
                      <Group gap="sm">
                        <Avatar src={user.avatarUrl} size="sm">
                          {user.displayName?.charAt(0) || 'U'}
                        </Avatar>
                        <Text fw={500}>{user.displayName}</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>{user.email}</Table.Td>
                    <Table.Td>
                      <Badge
                        color={getRoleColor(user.role)}
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
                    <Table.Td>
                      {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : "Never"}
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          onClick={() => handleEdit(user)}
                          size="sm"
                          disabled={loading}
                          variant="subtle"
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                        <Button
                          size="xs"
                          onClick={() => handleSuspend(user.id)}
                          color={user.status === "suspended" ? "green" : "orange"}
                          disabled={loading}
                          variant="light"
                        >
                          {user.status === "suspended" ? "Activate" : "Suspend"}
                        </Button>
                        <ActionIcon
                          onClick={() => handleDelete(user.id)}
                          size="sm"
                          color="red"
                          disabled={loading}
                          variant="subtle"
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Card>
      <Modal
        opened={openDialog}
        onClose={() => setOpenDialog(false)}
        title={editingUser ? "Edit User" : "Add New User"}
        size="md"
      >
        <Stack gap="md">
          <TextInput
            label="First Name"
            value={formData.firstName}
            onChange={(e) => setFormData(prev => ({ ...prev, firstName: e.target.value }))}
            required
            withAsterisk
            error={!formData.firstName && formData.firstName !== "" ? "First name is required" : undefined}
          />
          <TextInput
            label="Last Name"
            value={formData.lastName}
            onChange={(e) => setFormData(prev => ({ ...prev, lastName: e.target.value }))}
            required
            withAsterisk
            error={!formData.lastName && formData.lastName !== "" ? "Last name is required" : undefined}
          />
          <TextInput
            label="Display Name"
            value={formData.displayName}
            onChange={(e) => setFormData(prev => ({ ...prev, displayName: e.target.value }))}
            placeholder="Optional - defaults to First Last"
          />
          <TextInput
            label="Username"
            value={formData.username}
            onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
            required
            withAsterisk
            error={!formData.username && formData.username !== "" ? "Username is required (min 3 characters)" : undefined}
          />
          <TextInput
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            required
            withAsterisk
            leftSection={<IconMail size={16} />}
            error={!formData.email && formData.email !== "" ? "Valid email is required" : undefined}
          />
          {!editingUser && (
            <TextInput
              label="Password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              placeholder="Minimum 8 characters"
              required
              withAsterisk
              error={!editingUser && formData.password !== "" && formData.password.length < 8 ? "Password must be at least 8 characters" : undefined}
            />
          )}
          {editingUser && (
            <TextInput
              label="New Password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              placeholder="Leave blank to keep current password"
            />
          )}
          <Select
            label="Role"
            value={formData.role}
            onChange={(value) => setFormData(prev => ({ ...prev, role: value || "student" }))}
            data={[
              { value: "admin", label: "Admin" },
              { value: "teacher", label: "Teacher" },
              { value: "student", label: "Student" },
              { value: "parent", label: "Parent" },
            ]}
            required
            withAsterisk
          />

          <Group justify="flex-end" mt="md">
            <Button
              variant="subtle"
              onClick={() => setOpenDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              loading={loading}
            >
              {editingUser ? "Update" : "Create"}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}