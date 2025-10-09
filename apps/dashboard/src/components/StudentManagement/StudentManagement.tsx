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
  Grid,
  Switch,
  Group,
  Stack,
  Flex,
  Center,
} from '@mantine/core';
import {
  IconTrash,
  IconUserPlus,
  IconUserMinus,
  IconSearch,
  IconUsersGroup,
  IconSchool,
} from '@tabler/icons-react';
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

  // Set up Pusher for real-time updates
  const { service: pusherService } = usePusher();

  useEffect(() => {
    if (pusherService && classId) {
      const subscriptionIds: string[] = [];

      // Subscribe to student enrollment events
      const enrolledSubscription = pusherService.subscribe(`class-${classId}`, (message) => {
        if (message.type === 'student-enrolled') {
          handleStudentEnrolled(message.payload);
        }
      });
      subscriptionIds.push(enrolledSubscription);

      const unenrolledSubscription = pusherService.subscribe(`class-${classId}`, (message) => {
        if (message.type === 'student-unenrolled') {
          handleStudentUnenrolled(message.payload);
        }
      });
      subscriptionIds.push(unenrolledSubscription);

      const batchSubscription = pusherService.subscribe(`class-${classId}`, (message) => {
        if (message.type === 'batch-enrollment') {
          handleBatchEnrollment(message.payload);
        }
      });
      subscriptionIds.push(batchSubscription);

      return () => {
        subscriptionIds.forEach(id => pusherService.unsubscribe(id));
      };
    }
  }, [pusherService, classId]);

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
  const handleStudentEnrolled = (data: { student?: Student }) => {
    if (data.student) {
      setStudents(prev => [...prev, data.student]);
      setAvailableStudents(prev => prev.filter(s => s.id !== data.student.id));
      onStudentCountChange?.(students.length + 1);
      notifications.show({
        message: `${data.student.name} has been enrolled`,
        color: 'blue',
      });
    }
  };

  const handleStudentUnenrolled = (data: { studentId?: string }) => {
    if (data.studentId) {
      const removedStudent = students.find(s => s.id === data.studentId);
      setStudents(prev => prev.filter(s => s.id !== data.studentId));
      if (removedStudent) {
        setAvailableStudents(prev => [...prev, removedStudent]);
      }
      onStudentCountChange?.(students.length - 1);
      notifications.show({
        message: 'Student has been unenrolled',
        color: 'blue',
      });
    }
  };

  const handleBatchEnrollment = (data: { enrolled?: Student[] }) => {
    if (data.enrolled) {
      loadStudents();
      loadAvailableStudents();
      notifications.show({
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
        <Card.Section>
          <Flex justify="space-between" align="center" mb="md" p="lg">
            <Group>
              <IconSchool size={24} color="var(--mantine-color-blue-6)" />
              <Text size="lg" fw={600}>
                Student Management - {className}
              </Text>
              <Badge
                color={students.length >= maxStudents ? 'red' : 'blue'}
                size="sm"
              >
                {students.length} / {maxStudents}
              </Badge>
            </Group>
            <Group>
              <Group gap="xs">
                <Switch
                  checked={filterActive}
                  onChange={(event) => setFilterActive(event.currentTarget.checked)}
                  label="Active Only"
                  size="sm"
                />
              </Group>
              <Button
                variant="filled"
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
        </Card.Section>

        <Card.Section p="lg" pt={0}>
          <TextInput
            placeholder="Search students..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.currentTarget.value)}
            leftSection={<IconSearch size={16} />}
            mb="md"
            data-testid="search-students"
          />

          {loading ? (
            <Center py="xl">
              <Loader />
            </Center>
          ) : filteredStudents.length === 0 ? (
            <Alert variant="light" color="blue">
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
                        <Group gap="xs">
                          <Avatar src={student.avatar} alt={student.name} size="sm">
                            {student.name.charAt(0)}
                          </Avatar>
                          <Text>{student.name}</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text>{student.email}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          color={student.status === 'active' ? 'green' : 'gray'}
                          size="sm"
                        >
                          {student.status}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text>
                          {student.enrollmentDate
                            ? new Date(student.enrollmentDate).toLocaleDateString()
                            : 'N/A'}
                        </Text>
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'right' }}>
                        <Tooltip label="Remove from class">
                          <ActionIcon
                            color="red"
                            variant="subtle"
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
        </Card.Section>
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
        size="lg"
        title={
          <Flex justify="space-between" align="center" w="100%">
            <Text size="lg" fw={600}>Add Students to {className}</Text>
            <Group gap="xs">
              <Switch
                checked={batchMode}
                onChange={(event) => {
                  setBatchMode(event.currentTarget.checked);
                  setSelectedStudents(new Set());
                }}
                label="Batch Mode"
                size="sm"
              />
            </Group>
          </Flex>
        }
        data-testid="add-students-dialog"
      >
        <Stack>
          <TextInput
            placeholder="Search available students..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.currentTarget.value)}
            leftSection={<IconSearch size={16} />}
          />

          {filteredAvailableStudents.length === 0 ? (
            <Alert variant="light" color="blue">No available students to add</Alert>
          ) : (
            <Grid>
              {filteredAvailableStudents.map((student) => (
                <Grid.Col span={{ base: 12, sm: 6 }} key={student.id}>
                  <Card
                    withBorder
                    style={{
                      cursor: 'pointer',
                      backgroundColor: selectedStudents.has(student.id)
                        ? 'var(--mantine-color-blue-0)'
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
                      <Group>
                        {batchMode && (
                          <Checkbox
                            checked={selectedStudents.has(student.id)}
                            onClick={(event) => event.stopPropagation()}
                            onChange={() => toggleStudentSelection(student.id)}
                          />
                        )}
                        <Avatar src={student.avatar} alt={student.name} size="sm">
                          {student.name.charAt(0)}
                        </Avatar>
                        <Stack gap={0}>
                          <Text fw={500}>{student.name}</Text>
                          <Text size="xs" c="dimmed">
                            {student.email}
                          </Text>
                        </Stack>
                      </Group>
                      {!batchMode && (
                        <IconUserPlus size={20} color="var(--mantine-color-gray-6)" />
                      )}
                    </Flex>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          )}

          <Group justify="flex-end" mt="md">
            <Button
              variant="subtle"
              onClick={() => {
                setAddDialogOpen(false);
                setSelectedStudents(new Set());
                setBatchMode(false);
                setSearchTerm('');
              }}
            >
              Cancel
            </Button>
            {batchMode && (
              <Button
                variant="filled"
                leftSection={<IconUsersGroup size={16} />}
                onClick={batchEnrollStudents}
                disabled={selectedStudents.size === 0}
              >
                Add {selectedStudents.size} Students
              </Button>
            )}
          </Group>
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
        <Stack>
          <Alert variant="light" color="orange">
            This action will remove the student from the class. They can be re-enrolled later if needed.
          </Alert>
          {studentToRemove && (
            <Text>
              Are you sure you want to remove <Text component="span" fw={600}>{studentToRemove.name}</Text> from {className}?
            </Text>
          )}

          <Group justify="flex-end" mt="md">
            <Button
              variant="subtle"
              onClick={() => {
                setRemoveDialogOpen(false);
                setStudentToRemove(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="filled"
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