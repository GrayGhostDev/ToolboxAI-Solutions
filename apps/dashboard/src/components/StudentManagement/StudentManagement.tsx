import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Checkbox,
  Avatar,
  Chip,
  Alert,
  CircularProgress,
  Tooltip,
  InputAdornment,
  Grid,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  PersonAdd as PersonAddIcon,
  PersonRemove as PersonRemoveIcon,
  Search as SearchIcon,
  GroupAdd as GroupAddIcon,
  School as SchoolIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { notifications } from '@mantine/notifications';
import { apiClient } from '../../services/api';
import { usePusher } from '../../hooks/usePusher';

interface Student {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  enrollmentDate?: string;
  status: 'active' | 'inactive';
  grade?: string;
  lastActivity?: string;
}

interface StudentManagementProps {
  classId: string;
  className: string;
  teacherId: string;
  maxStudents?: number;
  onStudentCountChange?: (count: number) => void;
}

export const StudentManagement: React.FC<StudentManagementProps> = ({
  classId,
  className,
  teacherId,
  maxStudents = 30,
  onStudentCountChange,
}) => {
  const [students, setStudents] = useState<Student[]>([]);
  const [availableStudents, setAvailableStudents] = useState<Student[]>([]);
  const [selectedStudents, setSelectedStudents] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [studentToRemove, setStudentToRemove] = useState<Student | null>(null);
  const [batchMode, setBatchMode] = useState(false);
  const [filterActive, setFilterActive] = useState(true);
  // Using Mantine notifications instead of notistack

  // Set up Pusher for real-time updates
  const pusherClient = usePusher();

  useEffect(() => {
    if (pusherClient && classId) {
      const channel = pusherClient.subscribe(`class-${classId}`);

      channel.bind('student-enrolled', (data: any) => {
        handleStudentEnrolled(data);
      });

      channel.bind('student-unenrolled', (data: any) => {
        handleStudentUnenrolled(data);
      });

      channel.bind('batch-enrollment', (data: any) => {
        handleBatchEnrollment(data);
      });

      return () => {
        channel.unbind_all();
        pusherClient.unsubscribe(`class-${classId}`);
      };
    }
  }, [pusherClient, classId]);

  // Load enrolled students
  const loadStudents = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/api/v1/classes/${classId}/students`);
      setStudents(response.data.data || []);
      onStudentCountChange?.(response.data.data?.length || 0);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.message || 'Failed to load students',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  }, [classId, onStudentCountChange]);

  // Load available students for enrollment
  const loadAvailableStudents = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/users/students', {
        params: {
          exclude_class: classId,
        },
      });
      setAvailableStudents(response.data.data || []);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: 'Failed to load available students',
        color: 'red',
      });
    }
  }, [classId]);

  useEffect(() => {
    loadStudents();
  }, [loadStudents]);

  // Handle real-time updates
  const handleStudentEnrolled = (data: any) => {
    if (data.student) {
      setStudents(prev => [...prev, data.student]);
      setAvailableStudents(prev => prev.filter(s => s.id !== data.student.id));
      onStudentCountChange?.(students.length + 1);
      notifications.show({
        title: 'Student Enrolled',
        message: `${data.student.name} has been enrolled`,
        color: 'blue',
      });
    }
  };

  const handleStudentUnenrolled = (data: any) => {
    if (data.studentId) {
      const removedStudent = students.find(s => s.id === data.studentId);
      setStudents(prev => prev.filter(s => s.id !== data.studentId));
      if (removedStudent) {
        setAvailableStudents(prev => [...prev, removedStudent]);
      }
      onStudentCountChange?.(students.length - 1);
      notifications.show({
        title: 'Student Unenrolled',
        message: 'Student has been unenrolled',
        color: 'blue',
      });
    }
  };

  const handleBatchEnrollment = (data: any) => {
    if (data.enrolled) {
      loadStudents();
      loadAvailableStudents();
      notifications.show({
        title: 'Batch Enrollment',
        message: `${data.enrolled.length} students have been enrolled`,
        color: 'blue',
      });
    }
  };

  // Enroll single student
  const enrollStudent = async (studentId: string) => {
    try {
      await apiClient.post(`/api/v1/classes/${classId}/students/${studentId}`);
      await loadStudents();
      await loadAvailableStudents();
      notifications.show({
        title: 'Success',
        message: 'Student enrolled successfully',
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.message || 'Failed to enroll student',
        color: 'red',
      });
    }
  };

  // Unenroll single student
  const unenrollStudent = async (studentId: string) => {
    try {
      await apiClient.delete(`/api/v1/classes/${classId}/students/${studentId}`);
      await loadStudents();
      await loadAvailableStudents();
      setStudentToRemove(null);
      setRemoveDialogOpen(false);
      notifications.show({
        title: 'Success',
        message: 'Student unenrolled successfully',
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.message || 'Failed to unenroll student',
        color: 'red',
      });
    }
  };

  // Batch enroll students
  const batchEnrollStudents = async () => {
    if (selectedStudents.size === 0) {
      notifications.show({
        title: 'Warning',
        message: 'Please select students to enroll',
        color: 'yellow',
      });
      return;
    }

    try {
      await apiClient.post(`/api/v1/classes/${classId}/students/batch`, {
        student_ids: Array.from(selectedStudents),
        action: 'enroll',
      });
      await loadStudents();
      await loadAvailableStudents();
      setSelectedStudents(new Set());
      setAddDialogOpen(false);
      setBatchMode(false);
      notifications.show({
        title: 'Success',
        message: `${selectedStudents.size} students enrolled successfully`,
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.message || 'Failed to enroll students',
        color: 'red',
      });
    }
  };

  // Toggle student selection for batch operations
  const toggleStudentSelection = (studentId: string) => {
    const newSelection = new Set(selectedStudents);
    if (newSelection.has(studentId)) {
      newSelection.delete(studentId);
    } else {
      newSelection.add(studentId);
    }
    setSelectedStudents(newSelection);
  };

  // Filter students based on search
  const filteredStudents = students.filter(student => {
    const matchesSearch =
      student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = !filterActive || student.status === 'active';
    return matchesSearch && matchesFilter;
  });

  const filteredAvailableStudents = availableStudents.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box data-testid="student-management">
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Box display="flex" alignItems="center" gap={2}>
              <SchoolIcon color="primary" />
              <Typography variant="h6">
                Student Management - {className}
              </Typography>
              <Chip
                label={`${students.length} / ${maxStudents}`}
                color={students.length >= maxStudents ? 'error' : 'primary'}
                size="small"
              />
            </Box>
            <Box display="flex" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={filterActive}
                    onChange={(e) => setFilterActive(e.target.checked)}
                  />
                }
                label="Active Only"
              />
              <Button
                variant="contained"
                startIcon={<PersonAddIcon />}
                onClick={() => {
                  loadAvailableStudents();
                  setAddDialogOpen(true);
                }}
                disabled={students.length >= maxStudents}
                data-testid="add-students-button"
              >
                Add Students
              </Button>
            </Box>
          </Box>

          <TextField
            fullWidth
            placeholder="Search students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            data-testid="search-students"
          />

          {loading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : filteredStudents.length === 0 ? (
            <Alert severity="info">
              {searchTerm
                ? 'No students match your search criteria'
                : 'No students enrolled in this class yet'}
            </Alert>
          ) : (
            <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
              <Table data-testid="enrolled-students-table">
                <TableHead>
                  <TableRow>
                    <TableCell>Student</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Enrolled Date</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredStudents.map((student) => (
                    <TableRow key={student.id} data-testid={`student-row-${student.id}`}>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Avatar src={student.avatar} alt={student.name}>
                            {student.name.charAt(0)}
                          </Avatar>
                          <Typography>{student.name}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{student.email}</TableCell>
                      <TableCell>
                        <Chip
                          label={student.status}
                          color={student.status === 'active' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {student.enrollmentDate
                          ? new Date(student.enrollmentDate).toLocaleDateString()
                          : 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Remove from class">
                          <IconButton
                            color="error"
                            onClick={() => {
                              setStudentToRemove(student);
                              setRemoveDialogOpen(true);
                            }}
                            data-testid={`remove-student-${student.id}`}
                          >
                            <PersonRemoveIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Add Students Dialog */}
      <Dialog
        open={addDialogOpen}
        onClose={() => {
          setAddDialogOpen(false);
          setSelectedStudents(new Set());
          setBatchMode(false);
          setSearchTerm('');
        }}
        maxWidth="md"
        fullWidth
        data-testid="add-students-dialog"
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Add Students to {className}</Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={batchMode}
                  onChange={(e) => {
                    setBatchMode(e.target.checked);
                    setSelectedStudents(new Set());
                  }}
                />
              }
              label="Batch Mode"
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            placeholder="Search available students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          {filteredAvailableStudents.length === 0 ? (
            <Alert severity="info">No available students to add</Alert>
          ) : (
            <Grid container spacing={2}>
              {filteredAvailableStudents.map((student) => (
                <Grid item xs={12} sm={6} key={student.id}>
                  <Card
                    variant="outlined"
                    sx={{
                      cursor: 'pointer',
                      bgcolor: selectedStudents.has(student.id) ? 'action.selected' : 'background.paper',
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                    onClick={() => {
                      if (batchMode) {
                        toggleStudentSelection(student.id);
                      } else {
                        enrollStudent(student.id);
                        setAddDialogOpen(false);
                      }
                    }}
                    data-testid={`available-student-${student.id}`}
                  >
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box display="flex" alignItems="center" gap={1}>
                          {batchMode && (
                            <Checkbox
                              checked={selectedStudents.has(student.id)}
                              onClick={(e) => e.stopPropagation()}
                              onChange={() => toggleStudentSelection(student.id)}
                            />
                          )}
                          <Avatar src={student.avatar} alt={student.name}>
                            {student.name.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="body1">{student.name}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {student.email}
                            </Typography>
                          </Box>
                        </Box>
                        {!batchMode && (
                          <PersonAddIcon color="action" />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setAddDialogOpen(false);
            setSelectedStudents(new Set());
            setBatchMode(false);
            setSearchTerm('');
          }}>
            Cancel
          </Button>
          {batchMode && (
            <Button
              variant="contained"
              startIcon={<GroupAddIcon />}
              onClick={batchEnrollStudents}
              disabled={selectedStudents.size === 0}
            >
              Add {selectedStudents.size} Students
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Remove Student Confirmation Dialog */}
      <Dialog
        open={removeDialogOpen}
        onClose={() => {
          setRemoveDialogOpen(false);
          setStudentToRemove(null);
        }}
        data-testid="remove-student-dialog"
      >
        <DialogTitle>Confirm Removal</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action will remove the student from the class. They can be re-enrolled later if needed.
          </Alert>
          {studentToRemove && (
            <Typography>
              Are you sure you want to remove <strong>{studentToRemove.name}</strong> from {className}?
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setRemoveDialogOpen(false);
            setStudentToRemove(null);
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => studentToRemove && unenrollStudent(studentToRemove.id)}
          >
            Remove Student
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};