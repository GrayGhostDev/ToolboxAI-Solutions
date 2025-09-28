import React, { useState, useEffect } from 'react';
import { Box, Card, Table, Text, Badge, TextInput, Select, Stack, ActionIcon, Tooltip, Paper, Avatar, Button, Group, Pagination } from '@mantine/core';

import {
  IconSearch,
  IconFilter,
  IconDownload,
  IconRefresh,
  IconInfoCircle,
  IconAlertTriangle,
  IconAlertCircle,
  IconCircleCheck,
  IconShield,
  IconUser,
  IconSchool,
  IconChartBar,
  IconLogin,
  IconLogout,
  IconEdit,
  IconTrash,
  IconPlus,
  IconSettings,
} from '@tabler/icons-react';
import { format } from 'date-fns';
import { useRealTimeData } from '../../../hooks/useRealTimeData';

interface ActivityLog {
  id: string;
  timestamp: Date;
  user: string;
  userId: string;
  action: string;
  category: 'auth' | 'user' | 'content' | 'system' | 'security' | 'api';
  level: 'info' | 'warning' | 'error' | 'success';
  details: string;
  ipAddress: string;
  userAgent?: string;
}

const ActivityLogs: React.FunctionComponent<Record<string, any>> = () => {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Use real-time data hook for live updates
  const { data: realTimeLogs } = useRealTimeData<ActivityLog>('activity-logs', {
    refreshInterval: autoRefresh ? 5000 : 0,
  });

  // Mock data for demonstration
  const mockLogs: ActivityLog[] = [
    {
      id: '1',
      timestamp: new Date(Date.now() - 1000 * 60 * 2),
      user: 'admin',
      userId: '1',
      action: 'User login',
      category: 'auth',
      level: 'success',
      details: 'Successful login from Chrome browser',
      ipAddress: '192.168.1.100',
      userAgent: 'Chrome/120.0.0.0',
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 1000 * 60 * 5),
      user: 'jane.teacher',
      userId: '2',
      action: 'Created new lesson',
      category: 'content',
      level: 'info',
      details: 'Created lesson: Introduction to Physics',
      ipAddress: '192.168.1.101',
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 1000 * 60 * 10),
      user: 'system',
      userId: 'system',
      action: 'Failed login attempt',
      category: 'security',
      level: 'warning',
      details: '5 failed login attempts from IP 192.168.1.200',
      ipAddress: '192.168.1.200',
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 1000 * 60 * 15),
      user: 'alice.student',
      userId: '3',
      action: 'Completed assessment',
      category: 'content',
      level: 'success',
      details: 'Completed Math Quiz with score 95%',
      ipAddress: '192.168.1.102',
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 1000 * 60 * 20),
      user: 'admin',
      userId: '1',
      action: 'Updated system settings',
      category: 'system',
      level: 'info',
      details: 'Modified security settings: enabled 2FA',
      ipAddress: '192.168.1.100',
    },
    {
      id: '6',
      timestamp: new Date(Date.now() - 1000 * 60 * 25),
      user: 'system',
      userId: 'system',
      action: 'API rate limit exceeded',
      category: 'api',
      level: 'warning',
      details: 'Rate limit exceeded for endpoint /api/v1/content',
      ipAddress: '192.168.1.150',
    },
    {
      id: '7',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      user: 'jane.teacher',
      userId: '2',
      action: 'Deleted user',
      category: 'user',
      level: 'warning',
      details: 'Deleted student account: test.student',
      ipAddress: '192.168.1.101',
    },
    {
      id: '8',
      timestamp: new Date(Date.now() - 1000 * 60 * 35),
      user: 'system',
      userId: 'system',
      action: 'Database backup',
      category: 'system',
      level: 'success',
      details: 'Daily database backup completed successfully',
      ipAddress: 'localhost',
    },
    {
      id: '9',
      timestamp: new Date(Date.now() - 1000 * 60 * 40),
      user: 'admin',
      userId: '1',
      action: 'Password reset',
      category: 'security',
      level: 'info',
      details: 'Password reset email sent to user: bob.parent',
      ipAddress: '192.168.1.100',
    },
    {
      id: '10',
      timestamp: new Date(Date.now() - 1000 * 60 * 45),
      user: 'system',
      userId: 'system',
      action: 'Service error',
      category: 'system',
      level: 'error',
      details: 'Failed to connect to email service',
      ipAddress: 'localhost',
    },
  ];

  useEffect(() => {
    // Load initial logs
    loadLogs();
  }, []);

  useEffect(() => {
    // Update logs when real-time data arrives
    if (realTimeLogs) {
      setLogs(realTimeLogs);
    }
  }, [realTimeLogs]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      setLogs(mockLogs);
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportLogs = () => {
    // Export filtered logs as CSV
    const filteredLogs = getFilteredLogs();
    const csv = [
      'Timestamp,User,Action,Category,Level,Details,IP Address',
      ...filteredLogs.map(
        (log) =>
          `"${format(log.timestamp, 'yyyy-MM-dd HH:mm:ss')}","${log.user}","${log.action}","${
            log.category
          }","${log.level}","${log.details}","${log.ipAddress}"`
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity-logs-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
  };

  const getFilteredLogs = () => {
    return logs.filter((log) => {
      const matchesSearch =
        log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = categoryFilter === 'all' || log.category === categoryFilter;
      const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
      return matchesSearch && matchesCategory && matchesLevel;
    });
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'auth':
        return <IconLogin size={14} />;
      case 'user':
        return <IconUser size={14} />;
      case 'content':
        return <IconSchool size={14} />;
      case 'system':
        return <IconSettings size={14} />;
      case 'security':
        return <IconShield size={14} />;
      case 'api':
        return <IconChartBar size={14} />;
      default:
        return <IconInfoCircle size={14} />;
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <IconCircleCheck color="var(--mantine-color-green-6)" size={14} />;
      case 'warning':
        return <IconAlertTriangle color="var(--mantine-color-orange-6)" size={14} />;
      case 'error':
        return <IconAlertCircle color="var(--mantine-color-red-6)" size={14} />;
      case 'info':
      default:
        return <IconInfoCircle color="var(--mantine-color-blue-6)" size={14} />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'green';
      case 'warning':
        return 'orange';
      case 'error':
        return 'red';
      case 'info':
      default:
        return 'blue';
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes('login') || action.includes('Login')) return <IconLogin size={14} />;
    if (action.includes('logout') || action.includes('Logout')) return <IconLogout size={14} />;
    if (action.includes('create') || action.includes('Create')) return <IconPlus size={14} />;
    if (action.includes('update') || action.includes('Update')) return <IconEdit size={14} />;
    if (action.includes('delete') || action.includes('Delete')) return <IconTrash size={14} />;
    return null;
  };

  const filteredLogs = getFilteredLogs();

  return (
    <Box>
      <Text size="lg" fw={600} mb="lg">
        Activity Logs
      </Text>

      {/* Summary Cards */}
      <Group grow mb="lg">
        <Card p="md">
          <Text size="xs" c="dimmed">
            Total Logs
          </Text>
          <Text size="xl" fw={600}>{logs.length}</Text>
        </Card>
        <Card p="md">
          <Text size="xs" c="dimmed">
            Warnings
          </Text>
          <Text size="xl" fw={600} c="orange">
            {logs.filter((l) => l.level === 'warning').length}
          </Text>
        </Card>
        <Card p="md">
          <Text size="xs" c="dimmed">
            Errors
          </Text>
          <Text size="xl" fw={600} c="red">
            {logs.filter((l) => l.level === 'error').length}
          </Text>
        </Card>
        <Card p="md">
          <Text size="xs" c="dimmed">
            Security Events
          </Text>
          <Text size="xl" fw={600} c="blue">
            {logs.filter((l) => l.category === 'security').length}
          </Text>
        </Card>
      </Group>

      {/* Logs Table */}
      <Card>
        <Group justify="space-between" p="md" style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
          <Text fw={500}>Activity History</Text>
          <Group gap="xs">
            <Button
              variant={autoRefresh ? 'filled' : 'outline'}
              size="xs"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
            </Button>
            <Button
              variant="outline"
              leftSection={<IconDownload size={14} />}
              size="xs"
              onClick={handleExportLogs}
            >
              Export
            </Button>
            <ActionIcon onClick={loadLogs} size="sm">
              <IconRefresh size={16} />
            </ActionIcon>
          </Group>
        </Group>

        <Box p="md">
          {/* Filters */}
          <Group mb="md">
            <TextInput
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftSection={<IconSearch size={16} />}
              style={{ flexGrow: 1, maxWidth: 400 }}
            />
            <Select
              placeholder="Category"
              value={categoryFilter}
              onChange={(value) => setCategoryFilter(value || 'all')}
              data={[
                { value: 'all', label: 'All Categories' },
                { value: 'auth', label: 'Authentication' },
                { value: 'user', label: 'User' },
                { value: 'content', label: 'Content' },
                { value: 'system', label: 'System' },
                { value: 'security', label: 'Security' },
                { value: 'api', label: 'API' },
              ]}
              w={150}
            />
            <Select
              placeholder="Level"
              value={levelFilter}
              onChange={(value) => setLevelFilter(value || 'all')}
              data={[
                { value: 'all', label: 'All Levels' },
                { value: 'info', label: 'Info' },
                { value: 'success', label: 'Success' },
                { value: 'warning', label: 'Warning' },
                { value: 'error', label: 'Error' },
              ]}
              w={130}
            />
          </Group>

          {/* Table */}
          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Timestamp</Table.Th>
                  <Table.Th>User</Table.Th>
                  <Table.Th>Action</Table.Th>
                  <Table.Th>Category</Table.Th>
                  <Table.Th>Level</Table.Th>
                  <Table.Th>Details</Table.Th>
                  <Table.Th>IP Address</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredLogs
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((log) => (
                    <Table.Tr key={log.id}>
                      <Table.Td>
                        <Text size="xs">
                          {format(log.timestamp, 'MMM dd, HH:mm:ss')}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Avatar size="sm">
                            {log.user[0].toUpperCase()}
                          </Avatar>
                          <Text size="sm">{log.user}</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          {getActionIcon(log.action)}
                          <Text size="sm">{log.action}</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          leftSection={getCategoryIcon(log.category)}
                          variant="outline"
                          size="sm"
                        >
                          {log.category}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          leftSection={getLevelIcon(log.level)}
                          color={getLevelColor(log.level)}
                          size="sm"
                        >
                          {log.level}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Tooltip label={log.details}>
                          <Text
                            size="sm"
                            style={{
                              maxWidth: 300,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {log.details}
                          </Text>
                        </Tooltip>
                      </Table.Td>
                      <Table.Td>
                        <Text size="xs" ff="monospace">
                          {log.ipAddress}
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                {filteredLogs.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={7} ta="center">
                      <Text size="sm" c="dimmed">
                        No logs found matching your filters
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>

          <Group justify="space-between" mt="md">
            <Text size="sm" c="dimmed">
              Showing {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, filteredLogs.length)} of {filteredLogs.length} logs
            </Text>
            <Group gap="md">
              <Select
                value={rowsPerPage.toString()}
                onChange={(value) => {
                  setRowsPerPage(parseInt(value || '25', 10));
                  setPage(0);
                }}
                data={[
                  { value: '10', label: '10 per page' },
                  { value: '25', label: '25 per page' },
                  { value: '50', label: '50 per page' },
                  { value: '100', label: '100 per page' },
                ]}
                w={140}
              />
              <Pagination
                total={Math.ceil(filteredLogs.length / rowsPerPage)}
                value={page + 1}
                onChange={(newPage) => setPage(newPage - 1)}
                size="sm"
              />
            </Group>
          </Group>
        </Box>
      </Card>
    </Box>
  );
};

export default ActivityLogs;