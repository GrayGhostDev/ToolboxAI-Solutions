import {
  Box, Button, Text, Paper, Stack, Grid, Container, ActionIcon, Avatar, Card,
  List, Divider, TextInput, Select, Chip, Badge, Alert, Loader, Progress,
  Modal, Menu, Tooltip, Checkbox, Switch, Slider, Autocomplete, Skeleton,
  Table, Group
} from '@mantine/core';
import {
  IconSearch, IconPlus, IconEye, IconEdit, IconTrash, IconDotsVertical,
  IconPeople, IconSchedule, IconTrendingUp, IconRefresh, IconUsers
} from '@tabler/icons-react';
import * as React from 'react';

import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { setClasses, removeClass, setClassOnlineStatus } from '../../store/slices/classesSlice';
import { listClasses } from '../../services/api';
import { getClassDetailsRoute } from '../../config/routes';
import CreateClassDialog from '../dialogs/CreateClassDialog';
import VirtualizedList from '../common/VirtualizedList';
import { performanceUtils } from '../common/PerformanceMonitor';
interface ClassCardData {
  id: string;
  name: string;
  grade: number;
  studentCount: number;
  schedule: string;
  averageXP: number;
  completionRate: number;
  nextLesson: string;
  isOnline: boolean;
  studentAvatars: string[];
}
// Memoized class card component for better performance
const ClassCard = React.memo<{
  classData: ClassCardData;
  onMenuClick: (event: React.MouseEvent<HTMLElement>, classData: ClassCardData) => void;
  onCardClick: (classData: ClassCardData) => void;
}>(({ classData, onMenuClick, onCardClick }) => {
  const handleMenuClick = React.useCallback((event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    onMenuClick(event, classData);
  }, [onMenuClick, classData]);
  const handleCardClick = React.useCallback(() => {
    onCardClick(classData);
  }, [onCardClick, classData]);
  const performanceMark = React.useMemo(() => performanceUtils.measureComponent('ClassCard'), []);
  React.useEffect(() => {
    performanceMark.start();
    return () => {
      performanceMark.end();
    };
  }, [performanceMark]);
  return (
    <Card
      onClick={handleCardClick}
      withBorder
      style={{
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        height: '280px', // Fixed height for virtual scrolling
      }}
    >
      <Group justify="space-between" align="center" p="md">
        <Text size="md" fw={600} truncate>
          {classData.name}
        </Text>
        <ActionIcon size="sm" onClick={handleMenuClick}>
          <IconDotsVertical />
        </ActionIcon>
      </Group>
      <Stack gap="md" p="md" pt={0}>
        <Group>
          <IconPeople size={16} color="blue" />
          <Text size="sm" c="dimmed">
            Grade {classData.grade} • {classData.studentCount} students
          </Text>
        </Group>
        <Group>
          <IconSchedule size={16} />
          <Text size="sm" c="dimmed" truncate>
            {classData.schedule}
          </Text>
        </Group>
        <Box>
          <Group justify="space-between" mb="xs">
            <Text size="sm" c="dimmed">
              Progress
            </Text>
            <Text size="sm" c="dimmed">
              {Math.round(classData.completionRate * 100)}%
            </Text>
          </Group>
          <Progress
            value={classData.completionRate * 100}
            size="sm"
            radius="md"
          />
        </Box>
        <Group justify="space-between">
          <Group>
            <IconTrendingUp size={16} color="green" />
            <Text size="sm" c="dimmed">
              Avg XP: {classData.averageXP}
            </Text>
          </Group>
          <Chip
            size="xs"
            color={classData.isOnline ? 'green' : 'gray'}
            variant="outline"
          >
            {classData.isOnline ? 'Online' : 'Offline'}
          </Chip>
        </Group>
        {classData.studentAvatars.length > 0 && (
          <Avatar.Group>
            {classData.studentAvatars.slice(0, 4).map((avatar, index) => (
              <Avatar key={index} src={avatar} size="sm" />
            ))}
            {classData.studentAvatars.length > 4 && (
              <Avatar size="sm">+{classData.studentAvatars.length - 4}</Avatar>
            )}
          </Avatar.Group>
        )}
      </Stack>
    </Card>
  );
});
ClassCard.displayName = 'ClassCard';
// Memoized search and filters component
const ClassFilters = React.memo<{
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onCreateClass: () => void;
}>(({ searchTerm, onSearchChange, onCreateClass }) => {
  const handleSearchChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    onSearchChange(event.target.value);
  }, [onSearchChange]);
  return (
    <Group justify="space-between" mb="lg">
      <TextInput
        placeholder="Search classes..."
        value={searchTerm}
        onChange={handleSearchChange}
        leftSection={<IconSearch size={16} />}
        style={{ minWidth: 300 }}
      />
      <Button
        leftSection={<IconPlus />}
        onClick={onCreateClass}
        style={{ minWidth: 140 }}
      >
        New Class
      </Button>
    </Group>
  );
});
ClassFilters.displayName = 'ClassFilters';
export default function ClassesOptimized() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  // State management with useState
  const [classes, setClassesState] = React.useState<ClassCardData[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedClass, setSelectedClass] = React.useState<ClassCardData | null>(null);
  const [createClassOpen, setCreateClassOpen] = React.useState(false);
  // Performance tracking
  const performanceMark = React.useMemo(() => performanceUtils.measureComponent('ClassesPage'), []);
  React.useEffect(() => {
    performanceMark.start();
    fetchClasses();
    return () => {
      performanceMark.end();
    };
  }, [performanceMark]);
  // Memoized filtered classes for performance
  const filteredClasses = React.useMemo(() => {
    if (!searchTerm) return classes;
    const lowercaseSearch = searchTerm.toLowerCase();
    return classes.filter(classItem =>
      classItem.name.toLowerCase().includes(lowercaseSearch) ||
      classItem.grade.toString().includes(lowercaseSearch) ||
      classItem.schedule.toLowerCase().includes(lowercaseSearch)
    );
  }, [classes, searchTerm]);
  // Optimized fetch function with useCallback
  const fetchClasses = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await listClasses();
      // Transform API response to match component interface
      const transformedClasses: ClassCardData[] = data.map((classItem: any) => ({
        id: classItem.id,
        name: classItem.name,
        grade: classItem.grade_level || classItem.grade,
        studentCount: classItem.student_count || classItem.studentCount || 0,
        schedule: classItem.schedule || 'Schedule not set',
        averageXP: Math.round((classItem.average_progress || 0) * 100),
        completionRate: classItem.average_progress || 0,
        nextLesson: classItem.next_lesson || 'No upcoming lessons',
        isOnline: classItem.is_online || false,
        studentAvatars: [], // Will be populated when we have student endpoints
      }));
      setClassesState(transformedClasses);
    } catch (error: any) {
      console.error('Failed to fetch classes:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to load classes. Please try again.';
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        // Handle Pydantic validation errors
        errorMessage = errorDetail.map((err: any) =>
          err.msg || err.message || 'Validation error'
        ).join(', ');
      }
      dispatch(addNotification({
        type: 'error',
        message: errorMessage,
      }));
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  // Memoized event handlers
  const handleMenuClick = React.useCallback((event: React.MouseEvent<HTMLElement>, classData: ClassCardData) => {
    setAnchorEl(event.currentTarget);
    setSelectedClass(classData);
  }, []);
  const handleMenuClose = React.useCallback(() => {
    setAnchorEl(null);
    setSelectedClass(null);
  }, []);
  const handleCardClick = React.useCallback((classData: ClassCardData) => {
    navigate(getClassDetailsRoute(classData.id));
  }, [navigate]);
  const handleCreateClass = React.useCallback(() => {
    setCreateClassOpen(true);
  }, []);
  const handleCreateClassClose = React.useCallback(() => {
    setCreateClassOpen(false);
  }, []);
  const handleCreateClassSuccess = React.useCallback(() => {
    setCreateClassOpen(false);
    fetchClasses();
  }, [fetchClasses]);
  const handleDeleteClass = React.useCallback(async () => {
    if (selectedClass) {
      try {
        // TODO: Implement delete API call
        setClassesState(prev => prev.filter(c => c.id !== selectedClass.id));
        dispatch(addNotification({
          type: 'success',
          message: 'Class deleted successfully',
        }));
      } catch (error) {
        dispatch(addNotification({
          type: 'error',
          message: 'Failed to delete class',
        }));
      }
    }
    handleMenuClose();
  }, [selectedClass, dispatch, handleMenuClose]);
  // Render item function for virtualized list
  const renderClassItem = React.useCallback((item: ClassCardData, index: number) => (
    <ClassCard
      key={item.id}
      classData={item}
      onMenuClick={handleMenuClick}
      onCardClick={handleCardClick}
    />
  ), [handleMenuClick, handleCardClick]);
  if (loading && classes.length === 0) {
    return (
      <Group justify="center" align="center" style={{ height: 400 }}>
        <Text>Loading classes...</Text>
      </Group>
    );
  }
  return (
    <Box>
      <Group justify="space-between" align="center" mb="lg">
        <Text size="xl" fw={600}>
          Classes
        </Text>
        <Button
          variant="outline"
          leftSection={<IconRefresh />}
          onClick={fetchClasses}
          disabled={loading}
        >
          Refresh
        </Button>
      </Group>
      <ClassFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onCreateClass={handleCreateClass}
      />
      {/* Use VirtualizedList for large datasets */}
      {filteredClasses.length > 20 ? (
        <VirtualizedList
          items={filteredClasses}
          itemHeight={300} // Include margins
          height={600}
          renderItem={renderClassItem}
          overscanCount={5}
        />
      ) : (
        /* Use regular grid for smaller datasets */
        <Grid gutter="md">
          {filteredClasses.map((classData) => (
            <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 3 }} key={classData.id}>
              <ClassCard
                classData={classData}
                onMenuClick={handleMenuClick}
                onCardClick={handleCardClick}
              />
            </Grid.Col>
          ))}
        </Grid>
      )}
      {filteredClasses.length === 0 && !loading && (
        <Group justify="center" align="center" style={{ height: 200 }}>
          <Text c="dimmed">
            {searchTerm ? 'No classes match your search.' : 'No classes available.'}
          </Text>
        </Group>
      )}
      {/* Context Menu */}
      <Menu opened={Boolean(anchorEl)} onClose={handleMenuClose}>
        <Menu.Item leftSection={<IconEye />} onClick={() => selectedClass && handleCardClick(selectedClass)}>
          View Details
        </Menu.Item>
        <Menu.Item leftSection={<IconEdit />} onClick={handleMenuClose}>
          Edit Class
        </Menu.Item>
        <Menu.Item leftSection={<IconTrash />} onClick={handleDeleteClass} color="red">
          Delete Class
        </Menu.Item>
      </Menu>
      {/* Create Class Dialog */}
      <CreateClassDialog
        open={createClassOpen}
        onClose={handleCreateClassClose}
        onSuccess={handleCreateClassSuccess}
      />
    </Box>
  );
}