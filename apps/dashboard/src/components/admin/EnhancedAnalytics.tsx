import { useState } from 'react';
import {
  Box,
  Card,
  Text,
  Title,
  Grid,
  Stack,
  Badge,
  Select,
  ActionIcon,
  Button,
  Tabs,
  Alert,
  Group,
} from '@mantine/core';

import {
  IconRefresh as Refresh,
  IconDownload as Download,
  IconTimeline as Timeline,
  IconUsers as People,
  IconClipboard as Assessment,
  IconGauge as Speed,
} from '@tabler/icons-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { usePusherContext } from '../../contexts/PusherContext';

// Import our new analytics components
import UserActivityChart from '../analytics/UserActivityChart';
import ContentMetrics from '../analytics/ContentMetrics';
import PerformanceIndicator from '../analytics/PerformanceIndicator';
import StudentProgress from '../progress/StudentProgress';
import ClassOverview from '../progress/ClassOverview';

interface EnhancedAnalyticsProps {
  initialTab?: number;
  timeRange?: '24h' | '7d' | '30d' | '90d';
}

export function EnhancedAnalytics({ 
  initialTab = 0,
  timeRange: initialTimeRange = '7d' 
}: EnhancedAnalyticsProps) {
  const dispatch = useAppDispatch();
  const { isConnected } = usePusherContext();
  const userRole = useAppSelector((state) => state.user.role);
  
  const [currentTab, setCurrentTab] = useState(initialTab);
  const [timeRange, setTimeRange] = useState(initialTimeRange);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Handle manual refresh
  const handleRefresh = () => {
    setLastRefresh(new Date());
    dispatch(addNotification({
      type: 'info',
      message: 'Analytics data refreshed',
    }));
  };

  // Handle data export
  const handleExport = () => {
    const data = {
      timestamp: new Date().toISOString(),
      timeRange,
      currentTab,
      userRole,
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    dispatch(addNotification({
      type: 'success',
      message: 'Analytics data exported successfully',
    }));
  };

  // Tab configuration based on user role
  const getTabConfig = () => {
    const baseTabs = [
      { label: 'Overview', icon: <Timeline /> },
      { label: 'User Activity', icon: <People /> },
      { label: 'Content Metrics', icon: <Assessment /> },
      { label: 'Performance', icon: <Speed /> },
    ];

    if (userRole === 'admin') {
      return [
        ...baseTabs,
        { label: 'Class Management', icon: <Assessment /> },
      ];
    } else if (userRole === 'teacher') {
      return [
        ...baseTabs,
        { label: 'My Classes', icon: <Assessment /> },
        { label: 'Student Progress', icon: <People /> },
      ];
    }

    return baseTabs;
  };

  const tabs = getTabConfig();

  const renderTabContent = () => {
    switch (currentTab) {
      case 0: // Overview
        return (
          <Grid container spacing={3}>
            {/* Performance Indicators */}
            <Grid item xs={12}>
              <PerformanceIndicator 
                showSystemHealth={userRole === 'admin'}
                autoRefresh={autoRefresh}
                refreshInterval={30}
              />
            </Grid>
            
            {/* Quick Stats Grid */}
            <Grid item xs={12} md={6}>
              <UserActivityChart 
                timeRange={timeRange}
                height={300}
                autoRefresh={autoRefresh}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <ContentMetrics 
                timeRange={timeRange}
                autoRefresh={autoRefresh}
              />
            </Grid>
          </Grid>
        );

      case 1: // User Activity
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <UserActivityChart 
                timeRange={timeRange}
                height={400}
                autoRefresh={autoRefresh}
              />
            </Grid>
          </Grid>
        );

      case 2: // Content Metrics
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <ContentMetrics 
                timeRange={timeRange}
                autoRefresh={autoRefresh}
              />
            </Grid>
          </Grid>
        );

      case 3: // Performance
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <PerformanceIndicator 
                showSystemHealth={userRole === 'admin'}
                autoRefresh={autoRefresh}
                refreshInterval={30}
              />
            </Grid>
          </Grid>
        );

      case 4: // Class Management / My Classes
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <ClassOverview 
                autoRefresh={autoRefresh}
                showStudentList={true}
              />
            </Grid>
          </Grid>
        );

      case 5: // Student Progress (Teacher only)
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <StudentProgress 
                showDetailed={true}
                autoRefresh={autoRefresh}
              />
            </Grid>
          </Grid>
        );

      default:
        return (
          <Alert severity="info">
            Select a tab to view analytics data.
          </Alert>
        );
    }
  };

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Analytics Dashboard
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          {/* Connection Status */}
          {isConnected && autoRefresh && (
            <Chip label="Live Updates" color="success" size="small" />
          )}
          
          {/* Time Range Selector */}
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel size="small">Time Range</InputLabel>
            <Select
              size="small"
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value as any)}
            >
              <MenuItem value="24h">Last 24 hours</MenuItem>
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
            </Select>
          </FormControl>
          
          {/* Auto Refresh Toggle */}
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel size="small">Refresh</InputLabel>
            <Select
              size="small"
              value={autoRefresh ? 'auto' : 'manual'}
              label="Refresh"
              onChange={(e) => setAutoRefresh(e.target.value === 'auto')}
            >
              <MenuItem value="auto">Auto</MenuItem>
              <MenuItem value="manual">Manual</MenuItem>
            </Select>
          </FormControl>
          
          {/* Action Buttons */}
          <IconButton onClick={(e: React.MouseEvent) => handleRefresh} title="Refresh Data">
            <Refresh />
          </IconButton>
          <Button 
            variant="outlined" 
            startIcon={<Download />} 
            onClick={(e: React.MouseEvent) => handleExport}
          >
            Export
          </Button>
        </Stack>
      </Stack>
      
      {/* Last Update Info */}
      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
        Last updated: {lastRefresh.toLocaleString()}
        {autoRefresh && ' • Auto-refresh enabled'}
      </Typography>

      {/* Navigation Tabs */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 0 }}>
          <Tabs 
            value={currentTab} 
            onChange={(_, newValue) => setCurrentTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            {tabs.map((tab, index) => (
              <Tab 
                key={index}
                label={tab.label} 
                icon={tab.icon}
                iconPosition="start"
              />
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Tab Content */}
      <Box>
        {renderTabContent()}
      </Box>
    </Box>
  );
}

export default EnhancedAnalytics;