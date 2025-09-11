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
  Paper,
  Chip,
  IconButton,
  Stack,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import { Add, Edit, Delete, School } from "@mui/icons-material";

interface School {
  id: string;
  name: string;
  address: string;
  studentCount: number;
  teacherCount: number;
  status: "active" | "inactive";
  createdAt: string;
}

export default function Schools() {
  const [schools, setSchools] = useState<School[]>([
    {
      id: "1",
      name: "Lincoln Elementary",
      address: "123 Main St, Springfield, IL",
      studentCount: 456,
      teacherCount: 23,
      status: "active",
      createdAt: "2024-01-15",
    },
    {
      id: "2", 
      name: "Jefferson Middle School",
      address: "456 Oak Ave, Springfield, IL",
      studentCount: 678,
      teacherCount: 34,
      status: "active",
      createdAt: "2024-01-20",
    },
  ]);

  const [openDialog, setOpenDialog] = useState(false);
  const [editingSchool, setEditingSchool] = useState<School | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    address: "",
  });

  const handleAdd = () => {
    setEditingSchool(null);
    setFormData({ name: "", address: "" });
    setOpenDialog(true);
  };

  const handleEdit = (school: School) => {
    setEditingSchool(school);
    setFormData({ name: school.name, address: school.address });
    setOpenDialog(true);
  };

  const handleSave = () => {
    // TODO: Implement API call to save school
    setOpenDialog(false);
  };

  const handleDelete = (schoolId: string) => {
    // TODO: Implement API call to delete school
    setSchools(schools.filter(s => s.id !== schoolId));
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Schools Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleAdd}
        >
          Add School
        </Button>
      </Stack>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>School Name</TableCell>
                  <TableCell>Address</TableCell>
                  <TableCell>Students</TableCell>
                  <TableCell>Teachers</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {schools.map((school) => (
                  <TableRow key={school.id}>
                    <TableCell>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <School />
                        <Typography fontWeight={500}>{school.name}</Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>{school.address}</TableCell>
                    <TableCell>{school.studentCount}</TableCell>
                    <TableCell>{school.teacherCount}</TableCell>
                    <TableCell>
                      <Chip
                        label={school.status}
                        color={school.status === "active" ? "success" : "default"}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{school.createdAt}</TableCell>
                    <TableCell>
                      <IconButton onClick={() => handleEdit(school)} size="small">
                        <Edit />
                      </IconButton>
                      <IconButton 
                        onClick={() => handleDelete(school.id)} 
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
          {editingSchool ? "Edit School" : "Add New School"}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="School Name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            />
            <TextField
              fullWidth
              label="Address"
              value={formData.address}
              onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>
            {editingSchool ? "Update" : "Create"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}