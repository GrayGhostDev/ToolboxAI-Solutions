import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  Text,
  Table,
  Paper,
  ActionIcon,
  Button,
  Modal,
  TextInput,
  Checkbox,
  Avatar,
  Badge,
  Alert,
  Loader,
  Tooltip,
  Group,
  Stack,
  Switch,
  Grid,
  GridCol,
  Center,
  Flex,
} from '@mantine/core';
import {
  IconTrash,
  IconUserPlus,
  IconUserMinus,
  IconSearch,
  IconUsersPlus,
  IconSchool,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { apiClient } from '@/services/api';
import { usePusherChannel } from '@/hooks/usePusher';

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
  maxStudents?: number;
  onStudentCountChange?: (count: number) => void;
}

interface StudentEnrolledEvent {
  student: Student;
}

interface StudentUnenrolledEvent {
  studentId: string;
}

interface BatchEnrollmentEvent {
  enrolled: Student[];
}

export const StudentManagement: React.FC<StudentManagementProps> = ({
  classId,
  className,
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

  // Load enrolled students
  const loadStudents = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/api/v1/classes/${classId}/students`);
      setStudents(response.data.data || []);
      onStudentCountChange?.(response.data.data?.length || 0);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      notifications.show({
        title: 'Error',
        message: err.response?.data?.message || 'Failed to load students',
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
    } catch (_error: unknown) {
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
  const handleStudentEnrolled = useCallback((data: StudentEnrolledEvent) => {
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
  }, [onStudentCountChange, students.length]);

  const handleStudentUnenrolled = useCallback((data: StudentUnenrolledEvent) => {
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
  }, [onStudentCountChange, students]);

  const handleBatchEnrollment = useCallback((data: BatchEnrollmentEvent) => {
    if (data.enrolled) {
      loadStudents();
      loadAvailableStudents();
      notifications.show({
        title: 'Batch Enrollment Complete',
        message: `${data.enrolled.length} students have been enrolled`,
        color: 'green',
      });
    }
  }, [loadStudents, loadAvailableStudents]);

  // Set up Pusher channel for real-time updates
  usePusherChannel(
    `class-${classId}`,
    {
      'student-enrolled': handleStudentEnrolled,
      'student-unenrolled': handleStudentUnenrolled,
      'batch-enrollment': handleBatchEnrollment,
    },
    {
      enabled: true,
      autoSubscribe: true,
      dependencies: [handleStudentEnrolled, handleStudentUnenrolled, handleBatchEnrollment],
    }
  );

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
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      notifications.show({
        title: 'Error',
        message: err.response?.data?.message || 'Failed to enroll student',
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
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      notifications.show({
        title: 'Error',
        message: err.response?.data?.message || 'Failed to unenroll student',
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
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      notifications.show({
        title: 'Error',
        message: err.response?.data?.message || 'Failed to enroll students',
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
      <Card shadow="sm" padding="lg">
        <Stack gap="md">
          <Flex justify="space-between" align="center">
            <Group gap="md">
              <IconSchool size={24} color="var(--mantine-color-blue-6)" />
              <Text size="lg" fw={600}>
                Student Management - {className}
              </Text>
              <Badge
                color={students.length >= maxStudents ? 'red' : 'blue'}
                size="lg"
              >
                {students.length} / {maxStudents}
              </Badge>
            </Group>
            <Group gap="sm">
              <Switch
                checked={filterActive}
                onChange={(e) => setFilterActive(e.currentTarget.checked)}
                label="Active Only"
              />
              <Button
                leftSection={<IconUserPlus size={16} />}
                onClick={() => {
                  loadAvailableStudents();
                  setAddDialogOpen(true);
                }}
                disabled={students.length >= maxStudents}
                data-testid="add-students-button"
              >
                Add Students
              </Button>
            </Group>
          </Flex>

          <TextInput
            placeholder="Search students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.currentTarget.value)}
            leftSection={<IconSearch size={16} />}
            data-testid="search-students"
          />

          {loading ? (
            <Center py={40}>
              <Loader size="lg" />
            </Center>
          ) : filteredStudents.length === 0 ? (
            <Alert color="blue" title="No Students">
              {searchTerm
                ? 'No students match your search criteria'
                : 'No students enrolled in this class yet'}
            </Alert>
          ) : (
            <Paper withBorder>
              <Table data-testid="enrolled-students-table">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Student</Table.Th>
                    <Table.Th>Email</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Enrolled Date</Table.Th>
                    <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {filteredStudents.map((student) => (
                    <Table.Tr key={student.id} data-testid={`student-row-${student.id}`}>
                      <Table.Td>
                        <Group gap="sm">
                          <Avatar src={student.avatar} alt={student.name}>
                            {student.name.charAt(0)}
                          </Avatar>
                          <Text>{student.name}</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>{student.email}</Table.Td>
                      <Table.Td>
                        <Badge color={student.status === 'active' ? 'green' : 'gray'}>
                          {student.status}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        {student.enrollmentDate
                          ? new Date(student.enrollmentDate).toLocaleDateString()
                          : 'N/A'}
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'right' }}>
                        <Tooltip label="Remove from class">
                          <ActionIcon
                            color="red"
                            onClick={() => {
                              setStudentToRemove(student);
                              setRemoveDialogOpen(true);
                            }}
                            data-testid={`remove-student-${student.id}`}
                          >
                            <IconUserMinus size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Paper>
          )}
        </Stack>
      </Card>

      {/* Add Students Modal */}
      <Modal
        opened={addDialogOpen}
        onClose={() => {
          setAddDialogOpen(false);
          setSelectedStudents(new Set());
          setBatchMode(false);
          setSearchTerm('');
        }}
        title={
          <Flex justify="space-between" align="center" style={{ width: '100%' }}>
            <Text size="lg" fw={600}>Add Students to {className}</Text>
            <Switch
              checked={batchMode}
              onChange={(e) => {
                setBatchMode(e.currentTarget.checked);
                setSelectedStudents(new Set());
              }}
              label="Batch Mode"
            />
          </Flex>
        }
        size="lg"
        data-testid="add-students-dialog"
      >
        <Stack gap="md">
          <TextInput
            placeholder="Search available students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.currentTarget.value)}
            leftSection={<IconSearch size={16} />}
          />

          {filteredAvailableStudents.length === 0 ? (
            <Alert color="blue" title="No Students Available">
              No available students to add
            </Alert>
          ) : (
            <Grid>
              {filteredAvailableStudents.map((student) => (
                <GridCol span={{ base: 12, sm: 6 }} key={student.id}>
                  <Card
                    withBorder
                    style={{
                      cursor: 'pointer',
                      backgroundColor: selectedStudents.has(student.id)
                        ? 'var(--mantine-color-blue-light)'
                        : undefined,
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
                    <Flex justify="space-between" align="center">
                      <Group gap="sm">
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
                          <Text fw={500}>{student.name}</Text>
                          <Text size="sm" c="dimmed">
                            {student.email}
                          </Text>
                        </Box>
                      </Group>
                      {!batchMode && <IconUserPlus size={20} />}
                    </Flex>
                  </Card>
                </GridCol>
              ))}
            </Grid>
          )}

          {batchMode && (
            <Group justify="flex-end" mt="md">
              <Button
                variant="default"
                onClick={() => {
                  setAddDialogOpen(false);
                  setSelectedStudents(new Set());
                  setBatchMode(false);
                  setSearchTerm('');
                }}
              >
                Cancel
              </Button>
              <Button
                leftSection={<IconUsersPlus size={16} />}
                onClick={batchEnrollStudents}
                disabled={selectedStudents.size === 0}
              >
                Add {selectedStudents.size} Students
              </Button>
            </Group>
          )}
        </Stack>
      </Modal>

      {/* Remove Student Confirmation Modal */}
      <Modal
        opened={removeDialogOpen}
        onClose={() => {
          setRemoveDialogOpen(false);
          setStudentToRemove(null);
        }}
        title="Confirm Removal"
        data-testid="remove-student-dialog"
      >
        <Stack gap="md">
          <Alert color="yellow" title="Warning">
            This action will remove the student from the class. They can be re-enrolled later if needed.
          </Alert>
          {studentToRemove && (
            <Text>
              Are you sure you want to remove <strong>{studentToRemove.name}</strong> from {className}?
            </Text>
          )}
          <Group justify="flex-end" mt="md">
            <Button
              variant="default"
              onClick={() => {
                setRemoveDialogOpen(false);
                setStudentToRemove(null);
              }}
            >
              Cancel
            </Button>
            <Button
              color="red"
              leftSection={<IconTrash size={16} />}
              onClick={() => studentToRemove && unenrollStudent(studentToRemove.id)}
            >
              Remove Student
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
};

