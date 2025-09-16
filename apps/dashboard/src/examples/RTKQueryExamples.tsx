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
  CardContent,
  Typography,
  Button,
  Stack,
  Chip,
  Alert,
  LinearProgress,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tab,
  Tabs,
  TabPanel,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

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
import { ClassSummary } from '../types';
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
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
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
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Class Management (Optimistic Updates)
            {isFetching && <CircularProgress size={20} sx={{ ml: 1 }} />}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button
              startIcon={<AddIcon />}
              variant="contained"
              onClick={() => setCreateDialogOpen(true)}
              disabled={isCreating}
            >
              Create Class
            </Button>
            <Button
              startIcon={<RefreshIcon />}
              variant="outlined"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              Refresh
            </Button>
          </Stack>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load classes: {error.toString()}
          </Alert>
        )}

        <Box display="flex" gap={2} mb={2}>
          <Chip label={`Total: ${classes?.length || 0}`} />
          <Chip label={`Active: ${activeClasses.length}`} color="success" />
          <Chip label={`Low Enrollment: ${classesWithStats.filter(c => c.utilization < 50).length}`} color="warning" />
        </Box>

        <List>
          {classesWithStats.map((classItem) => (
            <ListItem
              key={classItem.id}
              secondaryAction={
                <Stack direction="row" spacing={1}>
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => openEditDialog(classItem)}
                    disabled={isUpdating}
                  >
                    Edit
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteClass(classItem.id)}
                    disabled={isDeleting}
                  >
                    Delete
                  </Button>
                </Stack>
              }
            >
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: classItem.is_online ? 'success.main' : 'grey.500' }}>
                  {classItem.subject.charAt(0)}
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle1">{classItem.name}</Typography>
                    <Chip
                      label={classItem.status}
                      size="small"
                      color={classItem.status === 'online' ? 'success' : 'default'}
                    />
                    <Chip
                      label={`${classItem.utilization.toFixed(0)}% full`}
                      size="small"
                      color={classItem.utilization > 80 ? 'error' : classItem.utilization > 60 ? 'warning' : 'success'}
                    />
                  </Box>
                }
                secondary={
                  <>
                    {classItem.subject} • Grade {classItem.grade_level} • {classItem.student_count}/{classItem.max_students} students
                    <br />
                    Teacher: {classItem.teacher_name} • Progress: {classItem.average_progress}%
                  </>
                }
              />
            </ListItem>
          ))}
        </List>

        {/* Create Class Dialog */}
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Class</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Class Name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Subject"
                value={formData.subject}
                onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Grade Level"
                type="number"
                value={formData.grade_level}
                onChange={(e) => setFormData(prev => ({ ...prev, grade_level: parseInt(e.target.value) }))}
                fullWidth
              />
              <TextField
                label="Max Students"
                type="number"
                value={formData.max_students}
                onChange={(e) => setFormData(prev => ({ ...prev, max_students: parseInt(e.target.value) }))}
                fullWidth
              />
            </Stack>
            {createError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                Failed to create class: {createError.toString()}
              </Alert>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreateClass}
              variant="contained"
              disabled={isCreating || !formData.name || !formData.subject}
            >
              {isCreating ? 'Creating...' : 'Create'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit Class Dialog */}
        <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Edit Class</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Class Name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Subject"
                value={formData.subject}
                onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Grade Level"
                type="number"
                value={formData.grade_level}
                onChange={(e) => setFormData(prev => ({ ...prev, grade_level: parseInt(e.target.value) }))}
                fullWidth
              />
              <TextField
                label="Max Students"
                type="number"
                value={formData.max_students}
                onChange={(e) => setFormData(prev => ({ ...prev, max_students: parseInt(e.target.value) }))}
                fullWidth
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleUpdateClass}
              variant="contained"
              disabled={isUpdating || !formData.name || !formData.subject}
            >
              {isUpdating ? 'Updating...' : 'Update'}
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
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
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Cache Performance Monitor
        </Typography>

        <Stack spacing={3}>
          {/* Performance Metrics */}
          <Box>
            <Typography variant="subtitle1" gutterBottom>Performance Metrics</Typography>
            <Stack direction="row" spacing={2}>
              <Chip
                icon={<SpeedIcon />}
                label={`Cache Hit Ratio: ${cacheMetrics.formattedHitRatio}`}
                color={cacheMetrics.cacheHitRatio > 0.7 ? 'success' : cacheMetrics.cacheHitRatio > 0.5 ? 'warning' : 'error'}
              />
              <Chip
                icon={<AnalyticsIcon />}
                label={`Total Queries: ${cacheMetrics.cacheSize}`}
                color="info"
              />
              <Chip
                icon={migrationProgress.migrationComplete ? <CheckCircleIcon /> : <ErrorIcon />}
                label={migrationProgress.migrationComplete ? 'Migration Complete' : 'Migration in Progress'}
                color={migrationProgress.migrationComplete ? 'success' : 'warning'}
              />
            </Stack>
          </Box>

          {/* Detailed Statistics */}
          <Box>
            <Typography variant="subtitle1" gutterBottom>Detailed Statistics</Typography>
            <Stack spacing={2}>
              <Box>
                <Typography variant="body2" color="text.secondary">Query Success Rate</Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <LinearProgress
                    variant="determinate"
                    value={cachePerformance.queries.successRate}
                    sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="body2">{cachePerformance.queries.successRate.toFixed(1)}%</Typography>
                </Box>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">Mutation Success Rate</Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <LinearProgress
                    variant="determinate"
                    value={cachePerformance.mutations.successRate}
                    sx={{ flex: 1, height: 8, borderRadius: 4 }}
                    color="secondary"
                  />
                  <Typography variant="body2">{cachePerformance.mutations.successRate.toFixed(1)}%</Typography>
                </Box>
              </Box>
            </Stack>
          </Box>

          {/* Cache Operations */}
          <Box>
            <Typography variant="subtitle1" gutterBottom>Cache Operations</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Button
                size="small"
                variant="outlined"
                onClick={handlePrefetchData}
                startIcon={<RefreshIcon />}
              >
                Prefetch Data
              </Button>
              <Button
                size="small"
                variant="outlined"
                color="warning"
                onClick={() => handleInvalidateTags(['Dashboard', 'Class'])}
              >
                Invalidate Main Tags
              </Button>
              <Button
                size="small"
                variant="outlined"
                color="error"
                onClick={handleInvalidateAll}
              >
                Reset All Cache
              </Button>
            </Stack>
          </Box>

          {/* Migration Status */}
          <Box>
            <Typography variant="subtitle1" gutterBottom>Migration Status</Typography>
            <Alert severity={migrationProgress.migrationComplete ? "success" : "info"}>
              <Typography variant="body2">
                <strong>Status:</strong> {migrationProgress.migrationComplete ? 'Complete' : 'In Progress'}<br />
                <strong>RTK Queries:</strong> {migrationProgress.rtkQueries}<br />
                <strong>RTK Mutations:</strong> {migrationProgress.rtkMutations}<br />
                <strong>Active Legacy Slices:</strong> {migrationProgress.legacySlicesActive}<br />
                <strong>Cache Efficiency:</strong> {migrationProgress.cacheEfficiency}
              </Typography>
            </Alert>
          </Box>
        </Stack>
      </CardContent>
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
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Real-time Messages
            {isFetching && <CircularProgress size={16} sx={{ ml: 1 }} />}
          </Typography>
          <Chip
            label={`${unreadCount} unread`}
            color={unreadCount > 0 ? 'error' : 'default'}
            size="small"
          />
        </Box>

        {/* Send Message Form */}
        <Box mb={3}>
          <Typography variant="subtitle2" gutterBottom>Send Quick Message</Typography>
          <Stack spacing={2}>
            <TextField
              label="Message"
              multiline
              rows={3}
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              fullWidth
              placeholder="Type your message here..."
            />
            <FormControl fullWidth>
              <InputLabel>Recipients</InputLabel>
              <Select
                multiple
                value={recipientIds}
                onChange={(e) => setRecipientIds(typeof e.target.value === 'string' ? [e.target.value] : e.target.value)}
                label="Recipients"
              >
                <MenuItem value="teacher1">Math Teacher</MenuItem>
                <MenuItem value="teacher2">Science Teacher</MenuItem>
                <MenuItem value="admin1">School Admin</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={handleSendMessage}
              disabled={isSending || !messageText.trim() || recipientIds.length === 0}
              startIcon={isSending ? <CircularProgress size={16} /> : undefined}
            >
              {isSending ? 'Sending...' : 'Send Message'}
            </Button>
          </Stack>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Message List */}
        <Typography variant="subtitle2" gutterBottom>Recent Messages</Typography>
        {isLoading ? (
          <Box display="flex" justifyContent="center" p={2}>
            <CircularProgress />
          </Box>
        ) : (
          <List>
            {(messages || []).slice(0, 5).map((message) => (
              <ListItem key={message.id} alignItems="flex-start">
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: message.is_read ? 'grey.300' : 'primary.main' }}>
                    📧
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle2">{message.subject}</Typography>
                      {!message.is_read && <Chip label="New" size="small" color="primary" />}
                      {message.priority === 'high' && <Chip label="Priority" size="small" color="error" />}
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2" color="text.primary" sx={{ mt: 0.5 }}>
                        {message.body.substring(0, 100)}...
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(message.created_at).toLocaleString()}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
}

// Main Examples Component
export function RTKQueryExamples() {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        RTK Query Implementation Examples
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Demonstrating advanced RTK Query patterns including optimistic updates,
        cache management, and real-time synchronization.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab label="Optimistic Updates" />
          <Tab label="Cache Performance" />
          <Tab label="Real-time Messages" />
        </Tabs>
      </Box>

      <TabPanel value={currentTab} index={0}>
        <OptimisticClassManagement />
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <CachePerformanceMonitor />
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <RealtimeMessageSystem />
      </TabPanel>
    </Box>
  );
}

export default RTKQueryExamples;