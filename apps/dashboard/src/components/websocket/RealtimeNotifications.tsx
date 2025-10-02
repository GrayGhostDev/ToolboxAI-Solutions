/**
 * Real-time Notifications Component
 * Displays system notifications from WebSocket
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Badge,
  ActionIcon,
  Popover,
  List,
  Text,
  Button,
  Divider,
  Paper,
  Alert
} from '@mantine/core';
import {
  Notifications as NotificationsIcon,
  NotificationsActive as ActiveNotificationsIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  EmojiEvents as AchievementIcon,
  Quiz as QuizIcon,
  School as LessonIcon,
  Clear as ClearIcon,
  DoneAll as MarkAllReadIcon
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../store';
import {
  selectNotifications,
  selectUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications
} from '../../store/slices/realtimeSlice';
import { SystemNotification } from '../../types/websocket';
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
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [autoMarkReadTimer, setAutoMarkReadTimer] = useState<number | null>(null);

  const visibleNotifications = notifications.slice(0, maxNotifications);
  const open = Boolean(anchorEl);

  // Get icon for notification type
  const getNotificationIcon = (notification: SystemNotification) => {
    if (notification.type === 'achievement') return <AchievementIcon color="warning" />;
    if (notification.type === 'quiz') return <QuizIcon color="primary" />;
    if (notification.type === 'lesson') return <LessonIcon color="secondary" />;

    switch (notification.severity) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  // Get severity color
  const getSeverityColor = (severity?: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (severity) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  // Handle popover open
  const handleOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);

    // Auto mark as read after delay
    if (autoMarkReadDelay > 0 && unreadCount > 0) {
      const timer = setTimeout(() => {
        dispatch(markAllNotificationsRead());
      }, autoMarkReadDelay);
      setAutoMarkReadTimer(timer);
    }
  };

  // Handle popover close
  const handleClose = () => {
    setAnchorEl(null);

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
    <>
      <IconButton
        color="inherit"
        onClick={(e: React.MouseEvent) => handleOpen}
        sx={{
          animation: unreadCount > 0 ? 'shake 0.5s' : 'none',
          '@keyframes shake': {
            '0%, 100%': { transform: 'translateX(0)' },
            '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-2px)' },
            '20%, 40%, 60%, 80%': { transform: 'translateX(2px)' }
          }
        }}
      >
        <Badge badgeContent={unreadCount} color="error">
          {unreadCount > 0 ? <ActiveNotificationsIcon /> : <NotificationsIcon />}
        </Badge>
      </IconButton>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Paper sx={{ width: 400, maxHeight: 600 }}>
          {/* Header */}
          <Box
            sx={{
              p: 2,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: 1,
              borderColor: 'divider'
            }}
          >
            <Typography variant="h6">
              Notifications
              {unreadCount > 0 && (
                <Chip
                  label={unreadCount}
                  size="small"
                  color="error"
                  sx={{ ml: 1 }}
                />
              )}
            </Typography>
            <Box>
              {unreadCount > 0 && (
                <IconButton size="small" onClick={(e: React.MouseEvent) => handleMarkAllRead}>
                  <MarkAllReadIcon />
                </IconButton>
              )}
              <IconButton size="small" onClick={(e: React.MouseEvent) => handleClearAll}>
                <ClearIcon />
              </IconButton>
            </Box>
          </Box>

          {/* Notification List */}
          {visibleNotifications.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <NotificationsIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography color="text.secondary">
                No notifications
              </Typography>
            </Box>
          ) : (
            <List sx={{ py: 0, maxHeight: 480, overflow: 'auto' }}>
              {visibleNotifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <ListItem
                    onClick={(e: React.MouseEvent) => () => !notification.read && handleMarkRead(notification.id)}
                    sx={{
                      bgcolor: notification.read ? 'transparent' : 'action.hover',
                      cursor: notification.read ? 'default' : 'pointer',
                      '&:hover': {
                        bgcolor: notification.read ? 'action.hover' : 'action.selected'
                      }
                    }}
                  >
                    <ListItemIcon>
                      {getNotificationIcon(notification)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography
                            variant="subtitle2"
                            sx={{
                              fontWeight: notification.read ? 'normal' : 'bold'
                            }}
                          >
                            {notification.title}
                          </Typography>
                          {!notification.read && (
                            <Box
                              sx={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                bgcolor: 'primary.main'
                              }}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2" color="text.secondary">
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" color="text.disabled">
                            {formatDistanceToNow(new Date(notification.timestamp), {
                              addSuffix: true
                            })}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                  {index < visibleNotifications.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}

          {/* Footer */}
          {notifications.length > 0 && (
            <Box
              sx={{
                p: 1,
                textAlign: 'center',
                borderTop: 1,
                borderColor: 'divider'
              }}
            >
              {notifications.length > maxNotifications && (
                <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                  Showing {maxNotifications} of {notifications.length} notifications
                </Typography>
              )}
              <Button
                size="small"
                onClick={handleClearAll}
                sx={{ textTransform: 'none' }}
              >
                Clear All
              </Button>
            </Box>
          )}
        </Paper>
      </Popover>
    </>
  );
};

// Notification toast for immediate alerts
export const RealtimeNotificationToast: React.FunctionComponent<Record<string, any>> = () => {
  const notifications = useAppSelector(selectNotifications);
  const [latestNotification, setLatestNotification] = useState<SystemNotification | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Show toast for new unread notifications
    const unreadNotifications = notifications.filter(n => !n.read);
    if (unreadNotifications.length > 0) {
      const latest = unreadNotifications[0];
      if (latest.id !== latestNotification?.id) {
        setLatestNotification(latest);
        setOpen(true);

        // Auto-hide after 5 seconds
        setTimeout(() => setOpen(false), 5000);
      }
    }
  }, [notifications, latestNotification]);

  if (!latestNotification || !open) return null;

  return (
    <Alert
      severity={latestNotification.severity || 'info'}
      onClose={() => setOpen(false)}
      sx={{
        position: 'fixed',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        minWidth: 300,
        maxWidth: 500
      }}
    >
      <Typography variant="subtitle2">{latestNotification.title}</Typography>
      <Typography variant="body2">{latestNotification.message}</Typography>
    </Alert>
  );
};
