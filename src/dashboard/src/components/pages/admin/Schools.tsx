import * as React from "react";
import {
  listSchools,
  createSchool,
  updateSchool,
  deleteSchool,
  activateSchool,
  type School as SchoolType,
  type SchoolCreate,
} from "../../../services/api";
import { useRealTimeData } from "../../../hooks/useRealTimeData";
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
  // Use real-time data hook
  const {
    data: schools,
    loading,
    error,
    create: createSchoolOptimistic,
    update: updateSchoolOptimistic,
    remove: removeSchoolOptimistic,
    refresh: fetchSchools
  } = useRealTimeData<SchoolType>({
    fetchFn: () => listSchools({ search: searchTerm }),
    createFn: createSchool,
    updateFn: updateSchool,
    deleteFn: deleteSchool,
    channel: 'schools_updates'
  });

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

  // Refetch when search term changes
  React.useEffect(() => {
    fetchSchools();
  }, [searchTerm, fetchSchools]);

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
    try {
      const schoolData: SchoolCreate = {
        ...formData,
        is_active: true,
      };

      if (editingSchool) {
        // Update existing school with optimistic update
        await updateSchoolOptimistic(editingSchool.id, schoolData);
      } else {
        // Create new school with optimistic update
        await createSchoolOptimistic(schoolData);
      }
      
      setOpenDialog(false);
    } catch (err) {
      console.error("Error saving school:", err);
      // Error handling is done by the real-time hook
    }
  };

  const handleDelete = async (schoolId: string) => {
    // The confirmation and error handling is done by the real-time hook
    await removeSchoolOptimistic(schoolId);
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
          {error && (
            <Box sx={{ mb: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
              <Typography color="error">{error}</Typography>
            </Box>
          )}
          
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
                {loading && schools.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography>Loading schools...</Typography>
                    </TableCell>
                  </TableRow>
                ) : schools.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography>No schools found. Add your first school!</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  schools.map((school) => (
                    <TableRow key={school.id}>
                      <TableCell>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <School />
                          <Typography fontWeight={500}>{school.name}</Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>{school.address}</TableCell>
                      <TableCell>{school.studentCount || 0}</TableCell>
                      <TableCell>{school.teacherCount || 0}</TableCell>
                      <TableCell>
                        <Chip
                          label={school.status}
                          color={school.status === "active" ? "success" : "default"}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{school.createdAt}</TableCell>
                      <TableCell>
                        <IconButton 
                          onClick={() => handleEdit(school)} 
                          size="small"
                          disabled={loading}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton 
                          onClick={() => handleDelete(school.id)} 
                          size="small"
                          color="error"
                          disabled={loading}
                        >
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
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
          <Button 
            onClick={() => setOpenDialog(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSave}
            disabled={loading || !formData.name || !formData.address || !formData.city || !formData.state || !formData.zip_code}
          >
            {loading ? "Saving..." : (editingSchool ? "Update" : "Create")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}