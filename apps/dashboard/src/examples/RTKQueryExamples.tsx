/**
 * RTK Query Implementation Examples
 *
 * This file demonstrates advanced RTK Query patterns and best practices
 * for the ToolBoxAI dashboard, including:
 * - Optimistic updates
 * - Cache invalidation strategies
 * - Real-time synchronization
 * - Error handling and recovery
 * - Performance monitoring
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  Text,
  Button,
  Stack,
  Badge,
  Alert,
  Progress,
  Loader,
  List,
  Avatar,
  Modal,
  TextInput,
  Textarea,
  NumberInput,
  Select,
  Tabs,
  Divider,
  Group,
  Flex,
  ActionIcon,
} from '@mantine/core';
import {
  IconRefresh,
  IconPlus,
  IconEdit,
  IconTrash,
  IconChartBar,
  IconGauge,
  IconCircleCheck,
  IconExclamationMark,
  IconMail,
} from '@tabler/icons-react';

// RTK Query hooks and utilities
import {
  useGetClassesQuery,
  useCreateClassMutation,
  useUpdateClassMutation,
  useDeleteClassMutation,
  useGetDashboardOverviewQuery,
  useGetMessagesQuery,
  useSendMessageMutation,
  api,
} from '../store/api';

// Enhanced selectors
import {
  selectClassesWithStats,
  selectActiveClasses,
  selectCachePerformance,
  selectUnreadMessageCount,
} from '../store/api/selectors';

// Migration utilities
import { useMigrationProgress, useCacheMetrics } from '../store/api/hooks';

// Types
import { type ClassSummary } from '../types';
import { useAppSelector } from '../store';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box p="md">{children}</Box>}
    </div>
  );
}

// Example 1: Optimistic Class Management
function OptimisticClassManagement() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedClass, setSelectedClass] = useState<ClassSummary | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    grade_level: 1,
    max_students: 30,
  });

  // RTK Query hooks
  const {
    data: classes,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useGetClassesQuery(undefined, {
    // Advanced polling with smart intervals
    pollingInterval: 30000,
    // Only poll when window is focused
    refetchOnFocus: true,
    // Refetch when reconnecting
    refetchOnReconnect: true,
  });

  const [createClass, { isLoading: isCreating, error: createError }] = useCreateClassMutation();
  const [updateClass, { isLoading: isUpdating }] = useUpdateClassMutation();
  const [deleteClass, { isLoading: isDeleting }] = useDeleteClassMutation();

  // Enhanced selectors
  const classesWithStats = useAppSelector(selectClassesWithStats);
  const activeClasses = useAppSelector(selectActiveClasses);

  const handleCreateClass = useCallback(async () => {
    try {
      const result = await createClass(formData).unwrap();
      console.log('Class created:', result);
      setCreateDialogOpen(false);
      setFormData({ name: '', subject: '', grade_level: 1, max_students: 30 });
    } catch (error) {
      console.error('Failed to create class:', error);
      // Error is automatically handled by RTK Query middleware
    }
  }, [createClass, formData]);

  const handleUpdateClass = useCallback(async () => {
    if (!selectedClass) return;

    try {
      await updateClass({
        id: selectedClass.id,
        data: formData,
      }).unwrap();
      setEditDialogOpen(false);
      setSelectedClass(null);
    } catch (error) {
      console.error('Failed to update class:', error);
    }
  }, [updateClass, selectedClass, formData]);

  const handleDeleteClass = useCallback(async (classId: string) => {
    if (!window.confirm('Are you sure you want to delete this class?')) return;

    try {
      await deleteClass(classId).unwrap();
    } catch (error) {
      console.error('Failed to delete class:', error);
    }
  }, [deleteClass]);

  const openEditDialog = useCallback((classItem: ClassSummary) => {
    setSelectedClass(classItem);
    setFormData({
      name: classItem.name,
      subject: classItem.subject,
      grade_level: classItem.grade_level,
      max_students: classItem.max_students,
    });
    setEditDialogOpen(true);
  }, []);

  return (
    <Card withBorder>
      <Card.Section p="md">
        <Flex justify="space-between" align="center" mb="md">
          <Group gap="xs">
            <Text size="lg" fw={600}>
              Class Management (Optimistic Updates)
            </Text>
            {isFetching && <Loader size="xs" />}
          </Group>
          <Group gap="xs">
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => setCreateDialogOpen(true)}
              disabled={isCreating}
            >
              Create Class
            </Button>
            <Button
              leftSection={<IconRefresh size={16} />}
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              Refresh
            </Button>
          </Group>
        </Flex>

        {error && (
          <Alert color="red" mb="md">
            Failed to load classes: {error.toString()}
          </Alert>
        )}

        <Group gap="xs" mb="md">
          <Badge variant="light">{`Total: ${classes?.length || 0}`}</Badge>
          <Badge color="green">{`Active: ${activeClasses.length}`}</Badge>
          <Badge color="orange">{`Low Enrollment: ${classesWithStats.filter(c => c.utilization < 50).length}`}</Badge>
        </Group>

        <Stack gap="xs">
          {classesWithStats.map((classItem) => (
            <Card key={classItem.id} withBorder padding="sm">
              <Flex justify="space-between" align="flex-start">
                <Group gap="sm" align="flex-start">
                  <Avatar
                    color={classItem.is_online ? 'green' : 'gray'}
                    radius="sm"
                  >
                    {classItem.subject.charAt(0)}
                  </Avatar>
                  <Box>
                    <Group gap="xs" mb="xs">
                      <Text fw={500}>{classItem.name}</Text>
                      <Badge
                        color={classItem.status === 'online' ? 'green' : 'gray'}
                        size="sm"
                      >
                        {classItem.status}
                      </Badge>
                      <Badge
                        color={classItem.utilization > 80 ? 'red' : classItem.utilization > 60 ? 'orange' : 'green'}
                        size="sm"
                      >
                        {`${classItem.utilization.toFixed(0)}% full`}
                      </Badge>
                    </Group>
                    <Text size="sm" c="dimmed">
                      {classItem.subject} • Grade {classItem.grade_level} • {classItem.student_count}/{classItem.max_students} students
                    </Text>
                    <Text size="sm" c="dimmed">
                      Teacher: {classItem.teacher_name} • Progress: {classItem.average_progress}%
                    </Text>
                  </Box>
                </Group>
                <Group gap="xs">
                  <ActionIcon
                    variant="subtle"
                    onClick={() => openEditDialog(classItem)}
                    disabled={isUpdating}
                  >
                    <IconEdit size={16} />
                  </ActionIcon>
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    onClick={() => handleDeleteClass(classItem.id)}
                    disabled={isDeleting}
                  >
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              </Flex>
            </Card>
          ))}
        </Stack>

        {/* Create Class Modal */}
        <Modal
          opened={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          title="Create New Class"
          centered
        >
          <Stack gap="md">
            <TextInput
              label="Class Name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.currentTarget.value }))}
            />
            <TextInput
              label="Subject"
              value={formData.subject}
              onChange={(e) => setFormData(prev => ({ ...prev, subject: e.currentTarget.value }))}
            />
            <NumberInput
              label="Grade Level"
              value={formData.grade_level}
              onChange={(value) => setFormData(prev => ({ ...prev, grade_level: value || 1 }))}
              min={1}
              max={12}
            />
            <NumberInput
              label="Max Students"
              value={formData.max_students}
              onChange={(value) => setFormData(prev => ({ ...prev, max_students: value || 30 }))}
              min={1}
              max={100}
            />
            {createError && (
              <Alert color="red">
                Failed to create class: {createError.toString()}
              </Alert>
            )}
            <Group justify="flex-end" gap="sm">
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreateClass}
                disabled={isCreating || !formData.name || !formData.subject}
                loading={isCreating}
              >
                Create
              </Button>
            </Group>
          </Stack>
        </Modal>

        {/* Edit Class Modal */}
        <Modal
          opened={editDialogOpen}
          onClose={() => setEditDialogOpen(false)}
          title="Edit Class"
          centered
        >
          <Stack gap="md">
            <TextInput
              label="Class Name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.currentTarget.value }))}
            />
            <TextInput
              label="Subject"
              value={formData.subject}
              onChange={(e) => setFormData(prev => ({ ...prev, subject: e.currentTarget.value }))}
            />
            <NumberInput
              label="Grade Level"
              value={formData.grade_level}
              onChange={(value) => setFormData(prev => ({ ...prev, grade_level: value || 1 }))}
              min={1}
              max={12}
            />
            <NumberInput
              label="Max Students"
              value={formData.max_students}
              onChange={(value) => setFormData(prev => ({ ...prev, max_students: value || 30 }))}
              min={1}
              max={100}
            />
            <Group justify="flex-end" gap="sm">
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleUpdateClass}
                disabled={isUpdating || !formData.name || !formData.subject}
                loading={isUpdating}
              >
                Update
              </Button>
            </Group>
          </Stack>
        </Modal>
      </Card.Section>
    </Card>
  );
}

// Example 2: Cache Performance Monitor
function CachePerformanceMonitor() {
  const cacheMetrics = useCacheMetrics();
  const migrationProgress = useMigrationProgress();
  const cachePerformance = useAppSelector(selectCachePerformance);

  // Manual cache operations
  const handleInvalidateAll = useCallback(() => {
    api.util.resetApiState();
  }, []);

  const handleInvalidateTags = useCallback((tags: string[]) => {
    tags.forEach(tag => {
      api.util.invalidateTags([tag]);
    });
  }, []);

  const handlePrefetchData = useCallback(() => {
    api.util.prefetch('getDashboardOverview', undefined, { force: true });
    api.util.prefetch('getClasses', undefined, { force: true });
  }, []);

  return (
    <Card withBorder>
      <Card.Section p="md">
        <Text size="lg" fw={600} mb="md">
          Cache Performance Monitor
        </Text>

        <Stack gap="lg">
          {/* Performance Metrics */}
          <Box>
            <Text size="md" fw={500} mb="sm">Performance Metrics</Text>
            <Group gap="sm">
              <Badge
                leftSection={<IconGauge size={14} />}
                color={cacheMetrics.cacheHitRatio > 0.7 ? 'green' : cacheMetrics.cacheHitRatio > 0.5 ? 'orange' : 'red'}
                size="lg"
              >
                Cache Hit Ratio: {cacheMetrics.formattedHitRatio}
              </Badge>
              <Badge
                leftSection={<IconChartBar size={14} />}
                color="blue"
                size="lg"
              >
                Total Queries: {cacheMetrics.cacheSize}
              </Badge>
              <Badge
                leftSection={migrationProgress.migrationComplete ? <IconCircleCheck size={14} /> : <IconExclamationMark size={14} />}
                color={migrationProgress.migrationComplete ? 'green' : 'orange'}
                size="lg"
              >
                {migrationProgress.migrationComplete ? 'Migration Complete' : 'Migration in Progress'}
              </Badge>
            </Group>
          </Box>

          {/* Detailed Statistics */}
          <Box>
            <Text size="md" fw={500} mb="sm">Detailed Statistics</Text>
            <Stack gap="md">
              <Box>
                <Text size="sm" c="dimmed" mb="xs">Query Success Rate</Text>
                <Flex align="center" gap="sm">
                  <Progress
                    value={cachePerformance.queries.successRate}
                    style={{ flex: 1 }}
                    radius="md"
                    size="md"
                  />
                  <Text size="sm">{cachePerformance.queries.successRate.toFixed(1)}%</Text>
                </Flex>
              </Box>

              <Box>
                <Text size="sm" c="dimmed" mb="xs">Mutation Success Rate</Text>
                <Flex align="center" gap="sm">
                  <Progress
                    value={cachePerformance.mutations.successRate}
                    style={{ flex: 1 }}
                    radius="md"
                    size="md"
                    color="violet"
                  />
                  <Text size="sm">{cachePerformance.mutations.successRate.toFixed(1)}%</Text>
                </Flex>
              </Box>
            </Stack>
          </Box>

          {/* Cache Operations */}
          <Box>
            <Text size="md" fw={500} mb="sm">Cache Operations</Text>
            <Group gap="xs">
              <Button
                size="sm"
                variant="outline"
                onClick={handlePrefetchData}
                leftSection={<IconRefresh size={14} />}
              >
                Prefetch Data
              </Button>
              <Button
                size="sm"
                variant="outline"
                color="orange"
                onClick={() => handleInvalidateTags(['Dashboard', 'Class'])}
              >
                Invalidate Main Tags
              </Button>
              <Button
                size="sm"
                variant="outline"
                color="red"
                onClick={handleInvalidateAll}
              >
                Reset All Cache
              </Button>
            </Group>
          </Box>

          {/* Migration Status */}
          <Box>
            <Text size="md" fw={500} mb="sm">Migration Status</Text>
            <Alert color={migrationProgress.migrationComplete ? 'green' : 'blue'}>
              <Text size="sm">
                <Text fw={600} component="span">Status:</Text> {migrationProgress.migrationComplete ? 'Complete' : 'In Progress'}<br />
                <Text fw={600} component="span">RTK Queries:</Text> {migrationProgress.rtkQueries}<br />
                <Text fw={600} component="span">RTK Mutations:</Text> {migrationProgress.rtkMutations}<br />
                <Text fw={600} component="span">Active Legacy Slices:</Text> {migrationProgress.legacySlicesActive}<br />
                <Text fw={600} component="span">Cache Efficiency:</Text> {migrationProgress.cacheEfficiency}
              </Text>
            </Alert>
          </Box>
        </Stack>
      </Card.Section>
    </Card>
  );
}

// Example 3: Real-time Message System
function RealtimeMessageSystem() {
  const [messageText, setMessageText] = useState('');
  const [recipientIds, setRecipientIds] = useState<string[]>([]);

  // RTK Query hooks with real-time updates
  const {
    data: messages,
    isLoading,
    isFetching,
  } = useGetMessagesQuery({
    unread_only: false,
  }, {
    pollingInterval: 5000, // Poll every 5 seconds for new messages
  });

  const [sendMessage, { isLoading: isSending }] = useSendMessageMutation();

  const unreadCount = useAppSelector(selectUnreadMessageCount);

  const handleSendMessage = useCallback(async () => {
    if (!messageText.trim() || recipientIds.length === 0) return;

    try {
      await sendMessage({
        subject: 'Quick Message',
        body: messageText,
        recipient_ids: recipientIds,
      }).unwrap();

      setMessageText('');
      setRecipientIds([]);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [sendMessage, messageText, recipientIds]);

  return (
    <Card withBorder>
      <Card.Section p="md">
        <Flex justify="space-between" align="center" mb="md">
          <Group gap="xs">
            <Text size="lg" fw={600}>
              Real-time Messages
            </Text>
            {isFetching && <Loader size="xs" />}
          </Group>
          <Badge
            color={unreadCount > 0 ? 'red' : 'gray'}
            size="sm"
          >
            {unreadCount} unread
          </Badge>
        </Flex>

        {/* Send Message Form */}
        <Box mb="lg">
          <Text size="md" fw={500} mb="sm">Send Quick Message</Text>
          <Stack gap="md">
            <Textarea
              label="Message"
              value={messageText}
              onChange={(e) => setMessageText(e.currentTarget.value)}
              placeholder="Type your message here..."
              minRows={3}
              autosize
            />
            <Select
              label="Recipients"
              placeholder="Select recipients"
              data={[
                { value: 'teacher1', label: 'Math Teacher' },
                { value: 'teacher2', label: 'Science Teacher' },
                { value: 'admin1', label: 'School Admin' }
              ]}
              value={recipientIds[0] || ''}
              onChange={(value) => setRecipientIds(value ? [value] : [])}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isSending || !messageText.trim() || recipientIds.length === 0}
              loading={isSending}
            >
              Send Message
            </Button>
          </Stack>
        </Box>

        <Divider mb="md" />

        {/* Message List */}
        <Text size="md" fw={500} mb="sm">Recent Messages</Text>
        {isLoading ? (
          <Flex justify="center" p="md">
            <Loader />
          </Flex>
        ) : (
          <Stack gap="xs">
            {(messages || []).slice(0, 5).map((message) => (
              <Card key={message.id} withBorder padding="sm">
                <Group gap="sm" align="flex-start">
                  <Avatar
                    color={message.is_read ? 'gray' : 'blue'}
                    radius="sm"
                  >
                    <IconMail size={16} />
                  </Avatar>
                  <Box style={{ flex: 1 }}>
                    <Group gap="xs" mb="xs">
                      <Text fw={500}>{message.subject}</Text>
                      {!message.is_read && <Badge color="blue" size="sm">New</Badge>}
                      {message.priority === 'high' && <Badge color="red" size="sm">Priority</Badge>}
                    </Group>
                    <Text size="sm" mb="xs">
                      {message.body.substring(0, 100)}...
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(message.created_at).toLocaleString()}
                    </Text>
                  </Box>
                </Group>
              </Card>
            ))}
          </Stack>
        )}
      </Card.Section>
    </Card>
  );
}

// Main Examples Component
export function RTKQueryExamples() {
  const [currentTab, setCurrentTab] = useState<string | null>('optimistic');

  return (
    <Box>
      <Text size="xl" fw={700} mb="xs">
        RTK Query Implementation Examples
      </Text>
      <Text size="md" c="dimmed" mb="lg">
        Demonstrating advanced RTK Query patterns including optimistic updates,
        cache management, and real-time synchronization.
      </Text>

      <Tabs value={currentTab} onChange={setCurrentTab}>
        <Tabs.List>
          <Tabs.Tab value="optimistic">Optimistic Updates</Tabs.Tab>
          <Tabs.Tab value="cache">Cache Performance</Tabs.Tab>
          <Tabs.Tab value="realtime">Real-time Messages</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="optimistic" pt="md">
          <OptimisticClassManagement />
        </Tabs.Panel>

        <Tabs.Panel value="cache" pt="md">
          <CachePerformanceMonitor />
        </Tabs.Panel>

        <Tabs.Panel value="realtime" pt="md">
          <RealtimeMessageSystem />
        </Tabs.Panel>
      </Tabs>
    </Box>
  );
}

export default RTKQueryExamples;