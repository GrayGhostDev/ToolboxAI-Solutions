/**
 * ActivityFeed Component
 * Displays recent system activities with real-time updates
 */

import React, { memo, useEffect, useState, useCallback } from 'react';
import {
  Container,
  Paper,
  Stack,
  ActionIcon,
  Badge,
  Loader,
  Alert,
  useMantineTheme,
  Text,
  Avatar,
  Group,
  Divider,
  Title,
  ScrollArea,
  Button,
} from '@mantine/core';
import {
  IconUser,
  IconSchool,
  IconTrophy,
  IconMessage,
  IconAlertTriangle,
  IconAlertCircle,
  IconInfoCircle,
  IconDotsVertical,
  IconRefresh,
  IconFilter,
} from '@tabler/icons-react';
import { formatDistanceToNow } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';
import { usePusherChannel } from '@/hooks/usePusher';

export interface Activity {
  id: string;
  type: 'user' | 'system' | 'education' | 'achievement' | 'message' | 'warning' | 'error';
  action: string;
  description: string;
  user?: {
    id: string;
    name: string;
    avatar?: string;
    role?: string;
  };
  metadata?: Record<string, unknown>;
  timestamp: string;
  importance: 'low' | 'medium' | 'high' | 'critical';
  read?: boolean;
}

export interface ActivityFeedProps {
  activities?: Activity[];
  maxItems?: number;
  showFilters?: boolean;
  onActivityClick?: (activity: Activity) => void;
  onRefresh?: () => Promise<void>;
  loading?: boolean;
  error?: string | null;
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableRealtime?: boolean;
}

const MotionBox = motion.div;

export const ActivityFeed = memo<ActivityFeedProps>(({
  activities: initialActivities = [],
  maxItems = 20,
  showFilters = true,
  onActivityClick,
  onRefresh,
  loading = false,
  error = null,
  autoRefresh = true,
  refreshInterval = 60000, // 1 minute
  enableRealtime = true,
}) => {
  const theme = useMantineTheme();
  const [activities, setActivities] = useState<Activity[]>(initialActivities);
  const [filteredType, setFilteredType] = useState<string | null>(null);
  const [menuOpened, setMenuOpened] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);

  // Setup Pusher for real-time updates
  const handleNewActivity = useCallback((data: Activity) => {
    setActivities(prev => [data, ...prev].slice(0, maxItems));
  }, [maxItems]);

  usePusherChannel(
    'admin-activities',
    {
      'new-activity': handleNewActivity,
    },
    {
      enabled: enableRealtime,
      autoSubscribe: true,
      dependencies: [enableRealtime, maxItems],
    }
  );

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !onRefresh) {
      return undefined;
    }

    const interval = setInterval(() => {
      void onRefresh();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, onRefresh]);

  // Update activities when prop changes
  useEffect(() => {
    setActivities(initialActivities);
  }, [initialActivities]);

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'user':
        return <IconUser size={20} />;
      case 'system':
        return <IconInfoCircle size={20} />;
      case 'education':
        return <IconSchool size={20} />;
      case 'achievement':
        return <IconTrophy size={20} />;
      case 'message':
        return <IconMessage size={20} />;
      case 'warning':
        return <IconAlertTriangle size={20} />;
      case 'error':
        return <IconAlertCircle size={20} />;
      default:
        return <IconInfoCircle size={20} />;
    }
  };

  const getActivityColor = (type: Activity['type'], importance: Activity['importance']) => {
    if (importance === 'critical') return theme.colors.red[6];
    if (importance === 'high') return theme.colors.orange[6];

    switch (type) {
      case 'error':
        return theme.colors.red[6];
      case 'warning':
        return theme.colors.orange[6];
      case 'achievement':
        return theme.colors.green[6];
      case 'education':
        return theme.colors.blue[6];
      default:
        return theme.colors.gray[6];
    }
  };

  const handleMenuOpen = (activity: Activity) => {
    setMenuOpened(true);
    setSelectedActivity(activity);
  };

  const handleMenuClose = () => {
    setMenuOpened(false);
    setSelectedActivity(null);
  };

  const handleMarkAsRead = () => {
    if (selectedActivity) {
      setActivities(prev =>
        prev.map(a => a.id === selectedActivity.id ? { ...a, read: true } : a)
      );
    }
    handleMenuClose();
  };

  const handleDelete = () => {
    if (selectedActivity) {
      setActivities(prev => prev.filter(a => a.id !== selectedActivity.id));
    }
    handleMenuClose();
  };

  const filteredActivities = filteredType
    ? activities.filter(a => a.type === filteredType)
    : activities;

  const unreadCount = activities.filter(a => !a.read).length;

  if (loading) {
    return (
      <Paper p="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper p="md">
        <Alert color="red">{error}</Alert>
      </Paper>
    );
  }

  return (
    <Paper
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Container p="md" style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
        <Group justify="space-between" align="center">
          <Group gap="sm">
            <Title order={4} fw={700}>
              Recent Activity
            </Title>
            {unreadCount > 0 && (
              <Badge color="red" variant="filled">
                {unreadCount}
              </Badge>
            )}
          </Group>
          <Group gap="xs">
            {showFilters && (
              <ActionIcon size="sm" variant="subtle">
                <IconFilter size={16} />
              </ActionIcon>
            )}
            {onRefresh && (
              <ActionIcon size="sm" variant="subtle" onClick={() => void onRefresh?.()}>
                <IconRefresh size={16} />
              </ActionIcon>
            )}
          </Group>
        </Group>

        {/* Filter chips */}
        {showFilters && (
          <Group gap="xs" mt="sm">
            <Button
              size="xs"
              radius="xl"
              variant={!filteredType ? 'filled' : 'light'}
              onClick={() => setFilteredType(null)}
            >
              All
            </Button>
            {['user', 'system', 'education', 'achievement'].map((type) => (
              <Button
                key={type}
                size="xs"
                radius="xl"
                variant={filteredType === type ? 'filled' : 'light'}
                onClick={() => setFilteredType(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </Button>
            ))}
          </Group>
        )}
      </Container>

      {/* Activity list */}
      <ScrollArea style={{ flex: 1 }} p="md">
        <Stack gap="sm">
          <AnimatePresence>
            {filteredActivities.length === 0 ? (
              <Container ta="center" py="xl">
                <Text c="dimmed">
                  No activities to display
                </Text>
              </Container>
            ) : (
              filteredActivities.map((activity, index) => (
                <MotionBox
                  key={activity.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Container>
                    <Paper
                      component="button"
                      type="button"
                      onClick={() => onActivityClick?.(activity)}
                      withBorder={!activity.read}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        cursor: 'pointer',
                        opacity: activity.read ? 0.7 : 1,
                        backgroundColor: activity.read
                          ? 'transparent'
                          : `color-mix(in srgb, ${theme.colors.blue[6]} 6%, transparent)`,
                        borderRadius: theme.radius.sm,
                        padding: theme.spacing.sm,
                        borderColor: activity.read ? 'transparent' : `color-mix(in srgb, ${theme.colors.blue[6]} 12%, transparent)`,
                        transition: 'background-color 120ms ease, transform 120ms ease',
                      }}
                      onMouseEnter={(event: React.MouseEvent<HTMLButtonElement>) => {
                        event.currentTarget.style.backgroundColor = `color-mix(in srgb, ${theme.colors.blue[6]} 10%, transparent)`;
                      }}
                      onMouseLeave={(event: React.MouseEvent<HTMLButtonElement>) => {
                        event.currentTarget.style.backgroundColor = activity.read
                          ? 'transparent'
                          : `color-mix(in srgb, ${theme.colors.blue[6]} 6%, transparent)`;
                      }}
                    >
                    <Group gap="md" align="flex-start">
                      <Avatar
                        size="md"
                        style={{
                          backgroundColor: `color-mix(in srgb, ${getActivityColor(activity.type, activity.importance)} 10%, transparent)`,
                          color: getActivityColor(activity.type, activity.importance),
                        }}
                      >
                        {activity.user?.avatar ? (
                          <img src={activity.user.avatar} alt={activity.user.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                          getActivityIcon(activity.type)
                        )}
                      </Avatar>

                      <Container style={{ flex: 1 }}>
                        <Group gap="xs" align="center" mb="xs">
                          <Text size="sm" fw={500}>
                            {activity.action}
                          </Text>
                          {activity.importance === 'critical' && (
                            <Badge color="red" size="sm">
                              Critical
                            </Badge>
                          )}
                          {activity.importance === 'high' && (
                            <Badge color="orange" size="sm">
                              Important
                            </Badge>
                          )}
                        </Group>

                        <Stack gap="xs">
                          <Text size="sm" c="dimmed">
                            {activity.description}
                          </Text>
                         <Group gap="xs" align="center">
                           {activity.user && (
                              <Badge size="sm" variant="light" color="gray">
                                {activity.user.name}
                              </Badge>
                            )}
                            <Text size="xs" c="dimmed">
                              {formatDistanceToNow(new Date(activity.timestamp), {
                                addSuffix: true,
                              })}
                            </Text>
                          </Group>
                        </Stack>
                      </Container>

                      <ActionIcon
                        size="sm"
                        variant="subtle"
                        onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                          e.stopPropagation();
                          handleMenuOpen(activity);
                        }}
                      >
                        <IconDotsVertical size={16} />
                      </ActionIcon>
                    </Group>
                    </Paper>
                  </Container>
                </MotionBox>
              ))
            )}
          </AnimatePresence>
        </Stack>
      </ScrollArea>

      {/* Context menu - using Portal for positioning */}
      {menuOpened && selectedActivity && (
        <Container style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }}>
          <Container
            onClick={handleMenuClose}
            style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
          />
          <Paper
            shadow="md"
            p="xs"
            style={{
              position: 'absolute',
              top: 100,
              right: 20,
              minWidth: 200,
              zIndex: 10000,
            }}
          >
            <Stack gap="xs">
              <Button
                variant="subtle"
                color="gray"
                onClick={handleMarkAsRead}
                fullWidth
              >
                {selectedActivity?.read ? 'Mark as unread' : 'Mark as read'}
              </Button>
              <Button
                variant="subtle"
                color="red"
                onClick={handleDelete}
                fullWidth
              >
                Delete
              </Button>
              <Divider />
              <Button
                variant="subtle"
                color="gray"
                onClick={handleMenuClose}
                fullWidth
              >
                View details
              </Button>
            </Stack>
          </Paper>
        </Container>
      )}
    </Paper>
  );
});

ActivityFeed.displayName = 'ActivityFeed';

export default ActivityFeed;
