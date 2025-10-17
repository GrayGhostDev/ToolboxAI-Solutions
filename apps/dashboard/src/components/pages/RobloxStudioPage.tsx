import React, { Component, Suspense, useState, useEffect, useCallback } from 'react';
import {
  Box, Button, Text, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader,
  Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio,
  Switch, Slider, Rating, Skeleton, Table, useMantineTheme, Typography
} from '@mantine/core';

// Helper function for color transparency (replaces MUI alpha)
const alpha = (color: string, opacity: number) => {
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
};
/**
 * RobloxStudioPage Component
 *
 * A dedicated page for the Roblox Studio Integration with proper error boundaries
 * Ensures the component is displayed properly without overlaying other content
 * Includes Celery task progress tracking for script optimization jobs
 */
import RobloxStudioIntegration from '../roblox/RobloxStudioIntegration';
import { useMultipleCeleryTasks } from '../../hooks/pusher/useCeleryTaskProgress';
import { TaskProgressList } from '../common/TaskProgressList';
import { showTaskNotification } from '../common/TaskProgressToast';

// Error Boundary for Roblox Studio Integration
class RobloxStudioErrorBoundary extends Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    console.warn('RobloxStudio Error:', error.message);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('RobloxStudio Component Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          style={{
            width: '100%',
            height: 'calc(100vh - 140px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem'
          }}
        >
          <Alert color="red" variant="light" title="Roblox Studio Integration Error">
            There was an issue loading the Roblox Studio integration. Please refresh the page or contact support.
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

const RobloxStudioPage: React.FunctionComponent<Record<string, any>> = () => {
  // Task progress tracking state
  const [showTaskPanel, setShowTaskPanel] = useState(false);

  // Get organization ID from user context (fallback to default for demo)
  const organizationId = 'default_org'; // TODO: Get from auth context

  // Track all Celery tasks for script optimization
  const {
    tasks,
    addTask,
    removeTask,
    activeTasks,
    completedTasks,
    failedTasks
  } = useMultipleCeleryTasks(organizationId);

  // Show task panel when there are active tasks
  useEffect(() => {
    if (activeTasks.length > 0) {
      setShowTaskPanel(true);
    }
  }, [activeTasks.length]);

  // Handle task removal
  const handleRemoveTask = useCallback((taskId: string) => {
    removeTask(taskId);
  }, [removeTask]);

  // Handle clear completed tasks
  const handleClearCompleted = useCallback(() => {
    completedTasks.forEach(task => removeTask(task.taskId));
  }, [completedTasks, removeTask]);

  return (
    <RobloxStudioErrorBoundary>
      <Box
        style={{
          width: '100%',
          height: 'calc(100vh - 140px)',  // Simple height calculation for navbar + toolbar + padding
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',  // Contain children but no complex scroll prevention
          position: 'relative'
        }}
      >
        {/* Task Progress Panel */}
        {showTaskPanel && tasks.length > 0 && (
          <Box style={{ marginBottom: '1rem', maxHeight: '300px' }}>
            <TaskProgressList
              tasks={tasks}
              onRemove={handleRemoveTask}
              onClearCompleted={handleClearCompleted}
              maxHeight={300}
              showCompact={true}
              title="Script Optimization Tasks"
            />
          </Box>
        )}

        <Suspense fallback={<Loader size="lg" style={{ margin: 'auto' }} />}>
          <RobloxStudioIntegration />
        </Suspense>
      </Box>
    </RobloxStudioErrorBoundary>
  );
};

export default RobloxStudioPage;