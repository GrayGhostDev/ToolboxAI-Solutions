// @ts-nocheck - Temporary fix for Phase 3
/**
 * ActivityFeed Component
 * Displays recent system activities with real-time updates
 */
import React, { memo, useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemText from '@mui/material/ListItemText';
import Avatar from '@mui/material/Avatar';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Divider from '@mui/material/Divider';
import Button from '@mui/material/Button';
import Badge from '@mui/material/Badge';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

import {
  Person as PersonIcon,
  School as SchoolIcon,
  Assessment as AssessmentIcon,
  EmojiEvents as AchievementIcon,
  Message as MessageIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  MoreVert as MoreIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';
import { usePusher } from '@/hooks/usePusher';
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
  metadata?: Record<string, any>;
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
const MotionListItem = motion(ListItem);
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
  const theme = useTheme();
  const [activities, setActivities] = useState<Activity[]>(initialActivities);
  const [filteredType, setFilteredType] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  // Setup Pusher for real-time updates
  const { subscribe, unsubscribe } = usePusher();
  useEffect(() => {
    if (enableRealtime) {
      const channel = 'admin-activities';
      const handleNewActivity = (data: Activity) => {
        setActivities(prev => [data, ...prev].slice(0, maxItems));
      };
      subscribe(channel, 'new-activity', handleNewActivity);
      return () => {
        unsubscribe(channel, 'new-activity', handleNewActivity);
      };
    }
  }, [enableRealtime, maxItems, subscribe, unsubscribe]);
  // Auto-refresh
  useEffect(() => {
    if (autoRefresh && onRefresh) {
      const interval = setInterval(() => {
        onRefresh();
      }, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, onRefresh]);
  // Update activities when prop changes
  useEffect(() => {
    setActivities(initialActivities);
  }, [initialActivities]);
  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'user':
        return <PersonIcon />;
      case 'system':
        return <InfoIcon />;
      case 'education':
        return <SchoolIcon />;
      case 'achievement':
        return <AchievementIcon />;
      case 'message':
        return <MessageIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'error':
        return <ErrorIcon />;
      default:
        return <InfoIcon />;
    }
  };
  const getActivityColor = (type: Activity['type'], importance: Activity['importance']) => {
    if (importance === 'critical') return theme.palette.error.main;
    if (importance === 'high') return theme.palette.warning.main;
    switch (type) {
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'achievement':
        return theme.palette.success.main;
      case 'education':
        return theme.palette.info.main;
      default:
        return theme.palette.text.secondary;
    }
  };
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, activity: Activity) => {
    setAnchorEl(event.currentTarget);
    setSelectedActivity(activity);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
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
      <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }
  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }
  return (
    <Paper
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography variant="h6" fontWeight="bold">
              Recent Activity
            </Typography>
            {unreadCount > 0 && (
              <Badge badgeContent={unreadCount} color="error">
                <Box />
              </Badge>
            )}
          </Stack>
          <Stack direction="row" spacing={1}>
            {showFilters && (
              <IconButton size="small" onClick={(e: React.MouseEvent) => (e) => setAnchorEl(e.currentTarget)}>
                <FilterIcon />
              </IconButton>
            )}
            {onRefresh && (
              <IconButton size="small" onClick={(e: React.MouseEvent) => () => onRefresh()}>
                <RefreshIcon />
              </IconButton>
            )}
          </Stack>
        </Stack>
        {/* Filter chips */}
        {showFilters && (
          <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap', gap: 1 }}>
            <Chip
              label="All"
              size="small"
              variant={!filteredType ? 'filled' : 'outlined'}
              onClick={(e: React.MouseEvent) => () => setFilteredType(null)}
            />
            {['user', 'system', 'education', 'achievement'].map(type => (
              <Chip
                key={type}
                label={type.charAt(0).toUpperCase() + type.slice(1)}
                size="small"
                variant={filteredType === type ? 'filled' : 'outlined'}
                onClick={(e: React.MouseEvent) => () => setFilteredType(type)}
              />
            ))}
          </Stack>
        )}
      </Box>
      {/* Activity list */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <List sx={{ p: 0 }}>
          <AnimatePresence>
            {filteredActivities.length === 0 ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No activities to display
                </Typography>
              </Box>
            ) : (
              filteredActivities.map((activity, index) => (
                <MotionListItem
                  key={activity.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  button
                  onClick={(e: React.MouseEvent) => () => onActivityClick?.(activity)}
                  sx={{
                    opacity: activity.read ? 0.7 : 1,
                    backgroundColor: activity.read
                      ? 'transparent'
                      : alpha(theme.palette.primary.main, 0.05),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                    },
                  }}
                >
                  <ListItemAvatar>
                    <Avatar
                      sx={{
                        backgroundColor: alpha(
                          getActivityColor(activity.type, activity.importance),
                          0.1
                        ),
                        color: getActivityColor(activity.type, activity.importance),
                      }}
                    >
                      {activity.user?.avatar ? (
                        <img src={activity.user.avatar} alt={activity.user.name} />
                      ) : (
                        getActivityIcon(activity.type)
                      )}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Typography variant="body2" fontWeight={500}>
                          {activity.action}
                        </Typography>
                        {activity.importance === 'critical' && (
                          <Chip label="Critical" size="small" color="error" />
                        )}
                        {activity.importance === 'high' && (
                          <Chip label="Important" size="small" color="warning" />
                        )}
                      </Stack>
                    }
                    secondary={
                      <Stack spacing={0.5}>
                        <Typography variant="body2" color="text.secondary">
                          {activity.description}
                        </Typography>
                        <Stack direction="row" spacing={1} alignItems="center">
                          {activity.user && (
                            <Chip
                              label={activity.user.name}
                              size="small"
                              variant="outlined"
                              sx={{ height: 20 }}
                            />
                          )}
                          <Typography variant="caption" color="text.secondary">
                            {formatDistanceToNow(new Date(activity.timestamp), {
                              addSuffix: true,
                            })}
                          </Typography>
                        </Stack>
                      </Stack>
                    }
                  />
                  <IconButton
                    size="small"
                    onClick={(e: React.MouseEvent) => (e) => {
                      e.stopPropagation();
                      handleMenuOpen(e, activity);
                    }}
                  >
                    <MoreIcon fontSize="small" />
                  </IconButton>
                </MotionListItem>
              ))
            )}
          </AnimatePresence>
        </List>
      </Box>
      {/* Context menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={(e: React.MouseEvent) => handleMarkAsRead}>
          {selectedActivity?.read ? 'Mark as unread' : 'Mark as read'}
        </MenuItem>
        <MenuItem onClick={(e: React.MouseEvent) => handleDelete}>Delete</MenuItem>
        <Divider />
        <MenuItem onClick={(e: React.MouseEvent) => handleMenuClose}>View details</MenuItem>
      </Menu>
    </Paper>
  );
});
ActivityFeed.displayName = 'ActivityFeed';
export default ActivityFeed;