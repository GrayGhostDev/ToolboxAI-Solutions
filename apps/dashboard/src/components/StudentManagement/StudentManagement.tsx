import React, { useState, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Checkbox from '@mui/material/Checkbox';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip';
import InputAdornment from '@mui/material/InputAdornment';
import Grid from '@mui/material/Grid';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';

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
import { useSnackbar } from 'notistack';
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

export const StudentManagement: React.FunctionComponent<StudentManagementProps> = ({
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
  const { enqueueSnackbar } = useSnackbar();

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
      enqueueSnackbar(error.response?.data?.message || 'Failed to load students', {
        variant: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [classId, enqueueSnackbar, onStudentCountChange]);

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
      enqueueSnackbar('Failed to load available students', { variant: 'error' });
    }
  }, [classId, enqueueSnackbar]);

  useEffect(() => {
    loadStudents();
  }, [loadStudents]);

  // Handle real-time updates
  const handleStudentEnrolled = (data: any) => {
    if (data.student) {
      setStudents(prev => [...prev, data.student]);
      setAvailableStudents(prev => prev.filter(s => s.id !== data.student.id));
      onStudentCountChange?.(students.length + 1);
      enqueueSnackbar(`${data.student.name} has been enrolled`, { variant: 'info' });
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
      enqueueSnackbar(`Student has been unenrolled`, { variant: 'info' });
    }
  };

  const handleBatchEnrollment = (data: any) => {
    if (data.enrolled) {
      loadStudents();
      loadAvailableStudents();
      enqueueSnackbar(`${data.enrolled.length} students have been enrolled`, {
        variant: 'info'
      });
    }
  };

  // Enroll single student
  const enrollStudent = async (studentId: string) => {
    try {
      await apiClient.post(`/api/v1/classes/${classId}/students/${studentId}`);
      await loadStudents();
      await loadAvailableStudents();
      enqueueSnackbar('Student enrolled successfully', { variant: 'success' });
    } catch (error: any) {
      enqueueSnackbar(error.response?.data?.message || 'Failed to enroll student', {
        variant: 'error',
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
      enqueueSnackbar('Student unenrolled successfully', { variant: 'success' });
    } catch (error: any) {
      enqueueSnackbar(error.response?.data?.message || 'Failed to unenroll student', {
        variant: 'error',
      });
    }
  };

  // Batch enroll students
  const batchEnrollStudents = async () => {
    if (selectedStudents.size === 0) {
      enqueueSnackbar('Please select students to enroll', { variant: 'warning' });
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
      enqueueSnackbar(`${selectedStudents.size} students enrolled successfully`, {
        variant: 'success',
      });
    } catch (error: any) {
      enqueueSnackbar(error.response?.data?.message || 'Failed to enroll students', {
        variant: 'error',
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
                onClick={(e: React.MouseEvent) => () => {
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
                            onClick={(e: React.MouseEvent) => () => {
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
                    onClick={(e: React.MouseEvent) => () => {
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
                              onClick={(e: React.MouseEvent) => (e) => e.stopPropagation()}
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
          <Button onClick={(e: React.MouseEvent) => () => {
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
              onClick={(e: React.MouseEvent) => batchEnrollStudents}
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
          <Button onClick={(e: React.MouseEvent) => () => {
            setRemoveDialogOpen(false);
            setStudentToRemove(null);
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={(e: React.MouseEvent) => () => studentToRemove && unenrollStudent(studentToRemove.id)}
          >
            Remove Student
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};