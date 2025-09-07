import * as React from "react";
import { useState, useEffect } from "react";
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  suspendUser,
  type User as UserType,
  type UserCreate,
  type UserUpdate,
} from "../../../services/api";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Stack,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Avatar,
  InputAdornment,
} from "@mui/material";
import { Add, Edit, Delete, Person, Search, Email } from "@mui/icons-material";

interface UserFormData {
  email: string;
  username: string;
  password?: string;
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
    role: "Student", // Default role to prevent validation error
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
      role: "Student", // Default role to prevent validation error
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
    
    // Validate required fields
    if (!formData.email || !formData.username || !formData.firstName || 
        !formData.lastName || !formData.role) {
      setError("Please fill in all required fields.");
      return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address.");
      return;
    }
    
    // Validate password for new users
    if (!editingUser && (!formData.password || formData.password.length < 8)) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    
    try {
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
        await updateUser(editingUser.id, updateData);
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
        await createUser(createData);
      }
      
      setOpenDialog(false);
      fetchUsers(); // Refresh the list
    } catch (err) {
      setError("Failed to save user. Please try again.");
      console.error("Error saving user:", err);
    }
  };

  const handleDelete = async (userId: string) => {
    if (!window.confirm("Are you sure you want to delete this user?")) {
      return;
    }
    
    setError(null);
    try {
      await deleteUser(userId);
      fetchUsers(); // Refresh the list
    } catch (err) {
      setError("Failed to delete user. Please try again.");
      console.error("Error deleting user:", err);
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
    switch (role) {
      case "Admin": return "error";
      case "Teacher": return "primary";
      case "Student": return "success";
      case "Parent": return "info";
      default: return "default";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "success";
      case "suspended": return "error";
      case "pending": return "warning";
      default: return "default";
    }
  };

  return (
    <Box>
      {error && (
        <Box sx={{ mb: 2 }}>
          <Typography color="error">{error}</Typography>
        </Box>
      )}
      <Stack direction="row" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Users Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleAdd}
        >
          Add User
        </Button>
      </Stack>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{ flex: 1 }}
            />
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={roleFilter}
                label="Role"
                onChange={(e) => setRoleFilter(e.target.value)}
              >
                <MenuItem value="all">All Roles</MenuItem>
                <MenuItem value="Admin">Admin</MenuItem>
                <MenuItem value="Teacher">Teacher</MenuItem>
                <MenuItem value="Student">Student</MenuItem>
                <MenuItem value="Parent">Parent</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Last Login</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <Stack direction="row" alignItems="center" spacing={2}>
                        <Avatar src={user.avatarUrl}>
                          {user.displayName.charAt(0)}
                        </Avatar>
                        <Typography fontWeight={500}>{user.displayName}</Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.role}
                        color={getRoleColor(user.role) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.status}
                        color={getStatusColor(user.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : "Never"}
                    </TableCell>
                    <TableCell>
                      <IconButton onClick={() => handleEdit(user)} size="small">
                        <Edit />
                      </IconButton>
                      <Button
                        size="small"
                        onClick={() => handleSuspend(user.id)}
                        color={user.status === "suspended" ? "success" : "warning"}
                      >
                        {user.status === "suspended" ? "Activate" : "Suspend"}
                      </Button>
                      <IconButton 
                        onClick={() => handleDelete(user.id)} 
                        size="small"
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)} 
        maxWidth="sm" 
        fullWidth
        keepMounted={false}
        disableRestoreFocus={false}
        disablePortal={false}
      >
        <DialogTitle>
          {editingUser ? "Edit User" : "Add New User"}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="First Name *"
              value={formData.firstName}
              onChange={(e) => setFormData(prev => ({ ...prev, firstName: e.target.value }))}
              required
              error={!formData.firstName && formData.firstName !== ""}
              helperText={!formData.firstName && formData.firstName !== "" ? "First name is required" : ""}
              autoFocus
            />
            <TextField
              fullWidth
              label="Last Name *"
              value={formData.lastName}
              onChange={(e) => setFormData(prev => ({ ...prev, lastName: e.target.value }))}
              required
              error={!formData.lastName && formData.lastName !== ""}
              helperText={!formData.lastName && formData.lastName !== "" ? "Last name is required" : ""}
            />
            <TextField
              fullWidth
              label="Display Name"
              value={formData.displayName}
              onChange={(e) => setFormData(prev => ({ ...prev, displayName: e.target.value }))}
              placeholder="Optional - defaults to First Last"
            />
            <TextField
              fullWidth
              label="Username *"
              value={formData.username}
              onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
              required
              error={!formData.username && formData.username !== ""}
              helperText={!formData.username && formData.username !== "" ? "Username is required (min 3 characters)" : ""}
            />
            <TextField
              fullWidth
              label="Email *"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              required
              error={!formData.email && formData.email !== ""}
              helperText={!formData.email && formData.email !== "" ? "Valid email is required" : ""}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email />
                  </InputAdornment>
                ),
              }}
            />
            {!editingUser && (
              <TextField
                fullWidth
                label="Password *"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Minimum 8 characters"
                required
                error={!editingUser && formData.password !== "" && formData.password.length < 8}
                helperText={!editingUser && formData.password !== "" && formData.password.length < 8 ? "Password must be at least 8 characters" : ""}
              />
            )}
            {editingUser && (
              <TextField
                fullWidth
                label="New Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Leave blank to keep current password"
              />
            )}
            <FormControl fullWidth required>
              <InputLabel>Role *</InputLabel>
              <Select
                value={formData.role}
                label="Role *"
                onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
              >
                <MenuItem value="Admin">Admin</MenuItem>
                <MenuItem value="Teacher">Teacher</MenuItem>
                <MenuItem value="Student">Student</MenuItem>
                <MenuItem value="Parent">Parent</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>
            {editingUser ? "Update" : "Create"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}