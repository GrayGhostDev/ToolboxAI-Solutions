import { useState, type ReactNode } from 'react';
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Select,
  Stack,
  Tabs,
  Text,
  Grid,
} from '@mantine/core';
import {
  IconDownload,
  IconRefresh,
  IconTimeline,
  IconUsers,
  IconClipboard,
  IconGauge,
} from '@tabler/icons-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { usePusherContext } from '../../contexts/PusherContext';
import UserActivityChart from '../analytics/UserActivityChart';
import ContentMetrics from '../analytics/ContentMetrics';
import PerformanceIndicator from '../analytics/PerformanceIndicator';

const TabsList: any = (Tabs as any).List;
const TabsTab: any = (Tabs as any).Tab;
const TabsPanel: any = (Tabs as any).Panel;
const GridCol: any = (Grid as any).Col;

const TIME_RANGE_OPTIONS = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: '90d', label: 'Last 90 days' },
] as const;

type TimeRangeOption = (typeof TIME_RANGE_OPTIONS)[number]['value'];

type TabDefinition = {
  label: string;
  icon: ReactNode;
  description: string;
};

interface EnhancedAnalyticsProps {
  initialTab?: number;
  timeRange?: TimeRangeOption;
}

export function EnhancedAnalytics({
  initialTab = 0,
  timeRange: initialTimeRange = '7d',
}: EnhancedAnalyticsProps) {
  const dispatch = useAppDispatch();
  const { isConnected } = usePusherContext();
  const role = useAppSelector((state) => state.user.role);

  const [currentTab, setCurrentTab] = useState(initialTab);
  const [timeRange, setTimeRange] = useState<TimeRangeOption>(initialTimeRange);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const tabs: TabDefinition[] = [
    { label: 'Overview', icon: <IconTimeline size={16} />, description: 'System-wide performance and activity' },
    { label: 'User Activity', icon: <IconUsers size={16} />, description: 'Engagement metrics across the platform' },
    { label: 'Content Metrics', icon: <IconClipboard size={16} />, description: 'Moderation queue and content insights' },
  ];

  if (role === 'teacher') {
    tabs.push({ label: 'Class Insights', icon: <IconClipboard size={16} />, description: 'Classroom analytics coming soon' });
  }

  if (role === 'admin') {
    tabs.push({ label: 'System Health', icon: <IconGauge size={16} />, description: 'Infrastructure analytics coming soon' });
  }

  const handleRefresh = () => {
    dispatch(addNotification({ type: 'info', message: 'Analytics data refreshed' }));
  };

  const handleExport = () => {
    const payload = {
      exportedAt: new Date().toISOString(),
      timeRange,
      currentTab,
      role,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `analytics-${new Date().toISOString().split('T')[0]}.json`;
    anchor.click();
    URL.revokeObjectURL(url);

    dispatch(addNotification({ type: 'success', message: 'Analytics export generated' }));
  };

  const renderOverview = () => (
    <Stack gap="md">
      <Grid>
        <GridCol span={12}>
          <PerformanceIndicator
            showSystemHealth={role === 'admin'}
            refreshInterval={30}
            autoRefresh={autoRefresh}
          />
        </GridCol>
        <GridCol span={{ base: 12, md: 6 }}>
          <UserActivityChart timeRange={timeRange} height={320} autoRefresh={autoRefresh} />
        </GridCol>
        <GridCol span={{ base: 12, md: 6 }}>
          <ContentMetrics timeRange={timeRange} autoRefresh={autoRefresh} />
        </GridCol>
      </Grid>
    </Stack>
  );

  const renderUserActivity = () => (
    <UserActivityChart timeRange={timeRange} height={420} autoRefresh={autoRefresh} />
  );

  const renderContentMetrics = () => (
    <ContentMetrics timeRange={timeRange} autoRefresh={autoRefresh} />
  );

  const renderComingSoon = (message: string) => (
    <Alert color="blue" variant="light">
      {message}
    </Alert>
  );

  const renderTabContent = (index: number) => {
    switch (index) {
      case 0:
        return renderOverview();
      case 1:
        return renderUserActivity();
      case 2:
        return renderContentMetrics();
      case 3:
        return renderComingSoon('Classroom analytics will be available in an upcoming update.');
      case 4:
        return renderComingSoon('Advanced system health dashboards will be available soon.');
      default:
        return renderComingSoon('Select a tab to view analytics.');
    }
  };

  return (
    <Card withBorder shadow="sm" radius="md">
      <Stack gap="md">
        <Group justify="space-between" align="center">
          <Stack gap={4}>
            <Text size="lg" fw={600}>
              Analytics Dashboard
            </Text>
            <Text size="sm" c="dimmed">
              Explore engagement, moderation, and performance insights
            </Text>
          </Stack>
          <Group gap="xs" align="center">
            {isConnected && autoRefresh && (
              <Badge color="green" variant="light">
                Live updates
              </Badge>
            )}
            <Select
              size="xs"
              value={timeRange}
              data={TIME_RANGE_OPTIONS}
              onChange={(value: string | null) => setTimeRange((value as TimeRangeOption | null) ?? timeRange)}
              aria-label="Select analytics time range"
            />
            <Select
              size="xs"
              value={autoRefresh ? 'auto' : 'manual'}
              data={[
                { value: 'auto', label: 'Auto refresh' },
                { value: 'manual', label: 'Manual refresh' },
              ]}
              onChange={(value: string | null) => setAutoRefresh(value === 'auto')}
              aria-label="Select refresh mode"
            />
            <Button
              size="xs"
              variant="light"
              leftSection={<IconRefresh size={14} />}
              onClick={handleRefresh}
            >
              Refresh
            </Button>
            <Button
              size="xs"
              variant="outline"
              leftSection={<IconDownload size={14} />}
              onClick={handleExport}
            >
              Export
            </Button>
          </Group>
        </Group>

        <Tabs
          value={currentTab.toString()}
          onChange={(value: string | null) => setCurrentTab(Number(value ?? 0))}
        >
          <TabsList>
            {tabs.map((tab, index) => (
              <TabsTab key={tab.label} value={index.toString()}>
                <Group gap={6} align="center">
                  {tab.icon}
                  <span>{tab.label}</span>
                </Group>
              </TabsTab>
            ))}
          </TabsList>

          {tabs.map((tab, index) => (
            <TabsPanel key={`panel-${tab.label}`} value={index.toString()} p="md">
              <Stack gap="sm">
                <Text size="sm" c="dimmed">
                  {tab.description}
                </Text>
                {renderTabContent(index)}
              </Stack>
            </TabsPanel>
          ))}
        </Tabs>
      </Stack>
    </Card>
  );
}

export default EnhancedAnalytics;
