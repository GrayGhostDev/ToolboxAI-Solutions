import * as React from "react";
import { useState, useEffect } from "react";
import {
  listSchools,
  createSchool,
  updateSchool,
  deleteSchool,
  activateSchool,
  type School as SchoolType,
  type SchoolCreate,
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

interface SchoolFormData {
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  phone?: string;
  email?: string;
  principal_name?: string;
  district?: string;
  max_students: number;
}

export default function Schools() {
  const [schools, setSchools] = useState<SchoolType[]>([
  ]);

  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingSchool, setEditingSchool] = useState<SchoolType | null>(null);
  const [formData, setFormData] = useState<SchoolFormData>({
    name: "",
    address: "",
    city: "",
    state: "",
    zip_code: "",
    phone: "",
    email: "",
    principal_name: "",
    district: "",
    max_students: 500,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Fetch schools on component mount
  useEffect(() => {
    fetchSchools();
  }, []);

  const fetchSchools = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSchools({ search: searchTerm });
      setSchools(data);
    } catch (err) {
      setError("Failed to load schools. Please try again.");
      console.error("Error fetching schools:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingSchool(null);
    setFormData({
      name: "",
      address: "",
      city: "",
      state: "",
      zip_code: "",
      phone: "",
      email: "",
      principal_name: "",
      district: "",
      max_students: 500,
    });
    setOpenDialog(true);
  };

  const handleEdit = (school: SchoolType) => {
    setEditingSchool(school);
    setFormData({
      name: school.name,
      address: school.address,
      city: school.city,
      state: school.state,
      zip_code: school.zip_code,
      phone: school.phone || "",
      email: school.email || "",
      principal_name: school.principal_name || "",
      district: school.district || "",
      max_students: school.max_students,
    });
    setOpenDialog(true);
  };

  const handleSave = async () => {
    setError(null);
    try {
      const schoolData: SchoolCreate = {
        ...formData,
        is_active: true,
      };

      if (editingSchool) {
        // Update existing school
        await updateSchool(editingSchool.id, schoolData);
      } else {
        // Create new school
        await createSchool(schoolData);
      }
      
      setOpenDialog(false);
      fetchSchools(); // Refresh the list
    } catch (err) {
      setError("Failed to save school. Please try again.");
      console.error("Error saving school:", err);
    }
  };

  const handleDelete = async (schoolId: string) => {
    if (!window.confirm("Are you sure you want to delete this school?")) {
      return;
    }
    
    setError(null);
    try {
      await deleteSchool(schoolId);
      fetchSchools(); // Refresh the list
    } catch (err) {
      setError("Failed to delete school. Please try again.");
      console.error("Error deleting school:", err);
    }
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

      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)} 
        maxWidth="md" 
        fullWidth
        keepMounted={false}
        disableRestoreFocus={false}
        disablePortal={false}
      >
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
              required
              autoFocus
            />
            <TextField
              fullWidth
              label="Address"
              value={formData.address}
              onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
              required
            />
            <Stack direction="row" spacing={2}>
              <TextField
                fullWidth
                label="City"
                value={formData.city}
                onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                required
              />
              <TextField
                fullWidth
                label="State"
                value={formData.state}
                onChange={(e) => setFormData(prev => ({ ...prev, state: e.target.value }))}
                required
                inputProps={{ minLength: 2, maxLength: 50 }}
                placeholder="e.g., CA"
              />
              <TextField
                fullWidth
                label="Zip Code"
                value={formData.zip_code}
                onChange={(e) => setFormData(prev => ({ ...prev, zip_code: e.target.value }))}
                required
                inputProps={{ minLength: 5, maxLength: 10 }}
                placeholder="e.g., 12345"
              />
            </Stack>
            <Stack direction="row" spacing={2}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="Optional"
              />
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="Optional"
              />
            </Stack>
            <Stack direction="row" spacing={2}>
              <TextField
                fullWidth
                label="Principal Name"
                value={formData.principal_name}
                onChange={(e) => setFormData(prev => ({ ...prev, principal_name: e.target.value }))}
                placeholder="Optional"
              />
              <TextField
                fullWidth
                label="District"
                value={formData.district}
                onChange={(e) => setFormData(prev => ({ ...prev, district: e.target.value }))}
                placeholder="Optional"
              />
            </Stack>
            <TextField
              fullWidth
              label="Maximum Students"
              type="number"
              value={formData.max_students}
              onChange={(e) => setFormData(prev => ({ ...prev, max_students: parseInt(e.target.value) || 500 }))}
              inputProps={{ min: 1, max: 10000 }}
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