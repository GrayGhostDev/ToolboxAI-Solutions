import * as React from "react";
import { useState, useEffect } from "react";
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

interface User {
  id: string;
  email: string;
  displayName: string;
  role: string;
  schoolId?: string;
  classIds: string[];
  avatarUrl?: string;
  status: "active" | "suspended" | "pending";
  lastLogin?: string;
  createdAt: string;
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([
    {
      id: "1",
      email: "admin@toolboxai.com",
      displayName: "Admin User",
      role: "Admin",
      classIds: [],
      status: "active",
      lastLogin: "2024-01-15T10:30:00Z",
      createdAt: "2024-01-01",
    },
    {
      id: "2",
      email: "jane.smith@school.edu",
      displayName: "Jane Smith",
      role: "Teacher",
      schoolId: "1",
      classIds: ["class1", "class2"],
      status: "active",
      lastLogin: "2024-01-14T15:45:00Z",
      createdAt: "2024-01-02",
    },
    {
      id: "3",
      email: "alex.johnson@student.edu",
      displayName: "Alex Johnson",
      role: "Student",
      schoolId: "1",
      classIds: ["class1"],
      status: "active",
      lastLogin: "2024-01-14T16:20:00Z",
      createdAt: "2024-01-03",
    },
  ]);

  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    displayName: "",
    role: "",
  });

  const filteredUsers = users.filter((user) => {
    const matchesSearch = user.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === "all" || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const handleAdd = () => {
    setEditingUser(null);
    setFormData({ email: "", displayName: "", role: "" });
    setOpenDialog(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      email: user.email,
      displayName: user.displayName,
      role: user.role,
    });
    setOpenDialog(true);
  };

  const handleSave = () => {
    // TODO: Implement API call to save user
    setOpenDialog(false);
  };

  const handleDelete = (userId: string) => {
    // TODO: Implement API call to delete user
    setUsers(users.filter(u => u.id !== userId));
  };

  const handleSuspend = (userId: string) => {
    // TODO: Implement API call to suspend user
    setUsers(users.map(u => 
      u.id === userId ? { ...u, status: u.status === "suspended" ? "active" : "suspended" } : u
    ));
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
                {filteredUsers.map((user) => (
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

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? "Edit User" : "Add New User"}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="Display Name"
              value={formData.displayName}
              onChange={(e) => setFormData(prev => ({ ...prev, displayName: e.target.value }))}
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email />
                  </InputAdornment>
                ),
              }}
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                label="Role"
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