import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Paper from '@mui/material/Paper';
import Avatar from '@mui/material/Avatar';
import Button from '@mui/material/Button';

import {
  Search,
  FilterList,
  Download,
  Refresh,
  Info,
  Warning,
  Error,
  CheckCircle,
  Security,
  Person,
  School,
  Assessment,
  Login,
  Logout,
  Edit,
  Delete,
  Add,
  Settings,
} from '@mui/icons-material';
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
        return <Login fontSize="small" />;
      case 'user':
        return <Person fontSize="small" />;
      case 'content':
        return <School fontSize="small" />;
      case 'system':
        return <Settings fontSize="small" />;
      case 'security':
        return <Security fontSize="small" />;
      case 'api':
        return <Assessment fontSize="small" />;
      default:
        return <Info fontSize="small" />;
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle color="success" fontSize="small" />;
      case 'warning':
        return <Warning color="warning" fontSize="small" />;
      case 'error':
        return <Error color="error" fontSize="small" />;
      case 'info':
      default:
        return <Info color="info" fontSize="small" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'info':
      default:
        return 'info';
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes('login') || action.includes('Login')) return <Login fontSize="small" />;
    if (action.includes('logout') || action.includes('Logout')) return <Logout fontSize="small" />;
    if (action.includes('create') || action.includes('Create')) return <Add fontSize="small" />;
    if (action.includes('update') || action.includes('Update')) return <Edit fontSize="small" />;
    if (action.includes('delete') || action.includes('Delete')) return <Delete fontSize="small" />;
    return null;
  };

  const filteredLogs = getFilteredLogs();

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>
        Activity Logs
      </Typography>

      {/* Summary Cards */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="caption" color="text.secondary">
              Total Logs
            </Typography>
            <Typography variant="h4">{logs.length}</Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="caption" color="text.secondary">
              Warnings
            </Typography>
            <Typography variant="h4" color="warning.main">
              {logs.filter((l) => l.level === 'warning').length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="caption" color="text.secondary">
              Errors
            </Typography>
            <Typography variant="h4" color="error.main">
              {logs.filter((l) => l.level === 'error').length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="caption" color="text.secondary">
              Security Events
            </Typography>
            <Typography variant="h4" color="primary.main">
              {logs.filter((l) => l.category === 'security').length}
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      {/* Logs Table */}
      <Card>
        <CardHeader
          title="Activity History"
          action={
            <Stack direction="row" spacing={1}>
              <Button
                variant={autoRefresh ? 'contained' : 'outlined'}
                size="small"
                onClick={(e: React.MouseEvent) => () => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
              </Button>
              <Button variant="outlined" startIcon={<Download />} size="small" onClick={(e: React.MouseEvent) => handleExportLogs}>
                Export
              </Button>
              <IconButton onClick={(e: React.MouseEvent) => loadLogs}>
                <Refresh />
              </IconButton>
            </Stack>
          }
        />
        <CardContent>
          {/* Filters */}
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
              sx={{ flexGrow: 1, maxWidth: 400 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="Category"
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="auth">Authentication</MenuItem>
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="content">Content</MenuItem>
                <MenuItem value="system">System</MenuItem>
                <MenuItem value="security">Security</MenuItem>
                <MenuItem value="api">API</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Level</InputLabel>
              <Select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)} label="Level">
                <MenuItem value="all">All Levels</MenuItem>
                <MenuItem value="info">Info</MenuItem>
                <MenuItem value="success">Success</MenuItem>
                <MenuItem value="warning">Warning</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </Select>
            </FormControl>
          </Stack>

          {/* Table */}
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>IP Address</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredLogs
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>
                        <Typography variant="caption">
                          {format(log.timestamp, 'MMM dd, HH:mm:ss')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Avatar sx={{ width: 24, height: 24, fontSize: '0.875rem' }}>
                            {log.user[0].toUpperCase()}
                          </Avatar>
                          <Typography variant="body2">{log.user}</Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} alignItems="center">
                          {getActionIcon(log.action)}
                          <Typography variant="body2">{log.action}</Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getCategoryIcon(log.category)}
                          label={log.category}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getLevelIcon(log.level)}
                          label={log.level}
                          size="small"
                          color={getLevelColor(log.level)}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={log.details}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 300,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {log.details}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                          {log.ipAddress}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                {filteredLogs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No logs found matching your filters
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={filteredLogs.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

export default ActivityLogs;