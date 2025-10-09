/**
 * Real-time Notifications Component (Migrated to Mantine v8)
 * Displays system notifications from WebSocket
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Badge,
  ActionIcon,
  Popover,
  Text,
  Button,
  Divider,
  Paper,
  Alert,
  Group,
  Stack,
  Indicator,
} from '@mantine/core';
import {
  IconBell,
  IconBellRinging,
  IconCircleCheck,
  IconAlertCircle,
  IconAlertTriangle,
  IconInfoCircle,
  IconTrophy,
  IconFileText,
  IconSchool,
  IconX,
  IconChecks,
} from '@tabler/icons-react';
import { useAppSelector, useAppDispatch } from '../../store';
import {
  selectNotifications,
  selectUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications
} from '../../store/slices/realtimeSlice';
import { type SystemNotification } from '../../types/websocket';
import { formatDistanceToNow } from 'date-fns';

interface RealtimeNotificationsProps {
  maxNotifications?: number;
  autoMarkReadDelay?: number;
}

export const RealtimeNotifications: React.FunctionComponent<RealtimeNotificationsProps> = ({
  maxNotifications = 20,
  autoMarkReadDelay = 5000
}) => {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector(selectNotifications);
  const unreadCount = useAppSelector(selectUnreadNotificationCount);
  const [opened, setOpened] = useState(false);
  const [autoMarkReadTimer, setAutoMarkReadTimer] = useState<number | null>(null);

  const visibleNotifications = notifications.slice(0, maxNotifications);

  // Get icon for notification type
  const getNotificationIcon = (notification: SystemNotification) => {
    if (notification.type === 'achievement') return <IconTrophy size={20} color="var(--mantine-color-yellow-6)" />;
    if (notification.type === 'quiz') return <IconFileText size={20} color="var(--mantine-color-blue-6)" />;
    if (notification.type === 'lesson') return <IconSchool size={20} color="var(--mantine-color-grape-6)" />;

    switch (notification.severity) {
      case 'success':
        return <IconCircleCheck size={20} color="var(--mantine-color-green-6)" />;
      case 'error':
        return <IconAlertCircle size={20} color="var(--mantine-color-red-6)" />;
      case 'warning':
        return <IconAlertTriangle size={20} color="var(--mantine-color-yellow-6)" />;
      default:
        return <IconInfoCircle size={20} color="var(--mantine-color-blue-6)" />;
    }
  };

  // Get severity color
  const getSeverityColor = (severity?: string): 'green' | 'red' | 'yellow' | 'blue' => {
    switch (severity) {
      case 'success':
        return 'green';
      case 'error':
        return 'red';
      case 'warning':
        return 'yellow';
      default:
        return 'blue';
    }
  };

  // Handle popover open
  const handleOpen = () => {
    setOpened(true);

    // Auto mark as read after delay
    if (autoMarkReadDelay > 0 && unreadCount > 0) {
      const timer = window.setTimeout(() => {
        dispatch(markAllNotificationsRead());
      }, autoMarkReadDelay);
      setAutoMarkReadTimer(timer);
    }
  };

  // Handle popover close
  const handleClose = () => {
    setOpened(false);

    // Clear auto-read timer
    if (autoMarkReadTimer) {
      clearTimeout(autoMarkReadTimer);
      setAutoMarkReadTimer(null);
    }
  };

  // Handle mark as read
  const handleMarkRead = (notificationId: string) => {
    dispatch(markNotificationRead(notificationId));
  };

  // Handle mark all as read
  const handleMarkAllRead = () => {
    dispatch(markAllNotificationsRead());
  };

  // Handle clear all
  const handleClearAll = () => {
    dispatch(clearNotifications());
    handleClose();
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (autoMarkReadTimer) {
        clearTimeout(autoMarkReadTimer);
      }
    };
  }, [autoMarkReadTimer]);

  return (
    <Popover
      width={400}
      position="bottom-end"
      shadow="md"
      opened={opened}
      onChange={setOpened}
    >
      <Popover.Target>
        <Indicator
          inline
          label={unreadCount}
          size={16}
          color="red"
          disabled={unreadCount === 0}
        >
          <ActionIcon
            variant="subtle"
            color="gray"
            size="lg"
            onClick={() => (opened ? handleClose() : handleOpen())}
            style={{
              animation: unreadCount > 0 ? 'shake 0.5s' : 'none',
            }}
          >
            {unreadCount > 0 ? <IconBellRinging size={20} /> : <IconBell size={20} />}
          </ActionIcon>
        </Indicator>
      </Popover.Target>

      <Popover.Dropdown p={0}>
        <Paper style={{ maxHeight: 600, overflow: 'hidden' }}>
          {/* Header */}
          <Box
            p="md"
            style={{
              borderBottom: '1px solid var(--mantine-color-gray-3)',
            }}
          >
            <Group justify="space-between">
              <Group gap="xs">
                <Text size="lg" fw={600}>
                  Notifications
                </Text>
                {unreadCount > 0 && (
                  <Badge color="red" size="sm">
                    {unreadCount}
                  </Badge>
                )}
              </Group>
              <Group gap="xs">
                {unreadCount > 0 && (
                  <ActionIcon
                    variant="subtle"
                    size="sm"
                    onClick={handleMarkAllRead}
                    title="Mark all as read"
                  >
                    <IconChecks size={16} />
                  </ActionIcon>
                )}
                <ActionIcon
                  variant="subtle"
                  size="sm"
                  onClick={handleClearAll}
                  title="Clear all"
                >
                  <IconX size={16} />
                </ActionIcon>
              </Group>
            </Group>
          </Box>

          {/* Notification List */}
          {visibleNotifications.length === 0 ? (
            <Stack align="center" py="xl" gap="md">
              <IconBell size={48} color="var(--mantine-color-gray-4)" />
              <Text c="dimmed">
                No notifications
              </Text>
            </Stack>
          ) : (
            <Box style={{ maxHeight: 480, overflowY: 'auto' }}>
              {visibleNotifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <Box
                    p="sm"
                    onClick={() => !notification.read && handleMarkRead(notification.id)}
                    style={{
                      backgroundColor: notification.read ? 'transparent' : 'var(--mantine-color-gray-0)',
                      cursor: notification.read ? 'default' : 'pointer',
                    }}
                  >
                    <Group align="flex-start" wrap="nowrap">
                      <Box mt={4}>
                        {getNotificationIcon(notification)}
                      </Box>
                      <Stack gap={4} style={{ flex: 1 }}>
                        <Group justify="space-between" wrap="nowrap">
                          <Text
                            size="sm"
                            fw={notification.read ? 400 : 600}
                          >
                            {notification.title}
                          </Text>
                          {!notification.read && (
                            <Box
                              style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                backgroundColor: 'var(--mantine-color-blue-6)',
                                flexShrink: 0,
                              }}
                            />
                          )}
                        </Group>
                        <Text size="xs" c="dimmed">
                          {notification.message}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {formatDistanceToNow(new Date(notification.timestamp), {
                            addSuffix: true
                          })}
                        </Text>
                      </Stack>
                    </Group>
                  </Box>
                  {index < visibleNotifications.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </Box>
          )}

          {/* Footer */}
          {notifications.length > 0 && (
            <Box
              p="xs"
              style={{
                borderTop: '1px solid var(--mantine-color-gray-3)',
                textAlign: 'center',
              }}
            >
              {notifications.length > maxNotifications && (
                <Text size="xs" c="dimmed" mb="xs">
                  Showing {maxNotifications} of {notifications.length} notifications
                </Text>
              )}
              <Button
                size="xs"
                variant="subtle"
                onClick={handleClearAll}
              >
                Clear All
              </Button>
            </Box>
          )}
        </Paper>
      </Popover.Dropdown>
    </Popover>
  );
};

// Notification toast for immediate alerts
export const RealtimeNotificationToast: React.FunctionComponent<Record<string, any>> = () => {
  const notifications = useAppSelector(selectNotifications);
  const [latestNotification, setLatestNotification] = useState<SystemNotification | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Show toast for new unread notifications
    const unreadNotifications = notifications.filter(n => !n.read);
    if (unreadNotifications.length > 0) {
      const latest = unreadNotifications[0];
      if (latest.id !== latestNotification?.id) {
        setLatestNotification(latest);
        setVisible(true);

        // Auto-hide after 5 seconds
        setTimeout(() => setVisible(false), 5000);
      }
    }
  }, [notifications, latestNotification]);

  if (!latestNotification || !visible) return null;

  return (
    <Alert
      color={getSeverityColor(latestNotification.severity)}
      withCloseButton
      onClose={() => setVisible(false)}
      style={{
        position: 'fixed',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        minWidth: 300,
        maxWidth: 500,
      }}
    >
      <Text size="sm" fw={600}>{latestNotification.title}</Text>
      <Text size="sm">{latestNotification.message}</Text>
    </Alert>
  );
};
