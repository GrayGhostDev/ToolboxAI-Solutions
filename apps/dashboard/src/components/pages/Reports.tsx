import * as React from 'react';
import {
  Card,
  Text,
  Button,
  Stack,
  Select,
  TextInput,
  Badge,
  Box,
  Table,
  ActionIcon,
  Alert,
  Progress,
  List,
  Tabs,
  Grid,
  Group,
  Title,
  Container,
  Paper,
  Center
} from '@mantine/core';

import { DateInput } from '@mantine/dates';
import {
  IconDownload,
  IconPrinter,
  IconMail,
  IconCalendarTime,
  IconClipboardCheck,
  IconTrendingUp,
  IconUsers,
  IconSchool,
  IconTrophy,
  IconFile,
  IconFileText,
  IconRefresh,
  IconDots,
  IconChartLine,
} from '@tabler/icons-react';
import { useAppSelector, useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import {
  generateReport,
  scheduleReport,
  emailReport,
  listReportTemplates,
  listReports,
  getReportStatistics,
  downloadReport,
  type ReportTemplate as ApiReportTemplate,
  type Report as ApiReport,
  type ReportGenerateRequest,
  apiClient,
  listUsers,
  listClasses,
} from '../../services/api';

// Import our new analytics components
import UserActivityChart from '../analytics/UserActivityChart';
import ContentMetrics from '../analytics/ContentMetrics';
import PerformanceIndicator from '../analytics/PerformanceIndicator';

interface Report {
  id: string;
  name: string;
  type: 'progress' | 'attendance' | 'grades' | 'behavior' | 'custom';
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  lastGenerated: string;
  nextScheduled?: string;
  status: 'ready' | 'generating' | 'scheduled' | 'error';
  size?: string;
  recipients?: number;
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: string;
  fields: string[];
  popular?: boolean;
  type?: 'progress' | 'attendance' | 'grades' | 'behavior' | 'custom';
}

const performanceData = [
  { month: 'Jan', students: 85, average: 78 },
  { month: 'Feb', students: 88, average: 80 },
  { month: 'Mar', students: 92, average: 82 },
  { month: 'Apr', students: 90, average: 85 },
  { month: 'May', students: 94, average: 87 },
  { month: 'Jun', students: 96, average: 89 },
];

const subjectDistribution = [
  { name: 'Math', value: 30, color: '#2563EB' },
  { name: 'Science', value: 25, color: '#22C55E' },
  { name: 'Language', value: 20, color: '#FACC15' },
  { name: 'Arts', value: 15, color: '#9333EA' },
  { name: 'Tech', value: 10, color: '#EF4444' },
];

export default function Reports() {
  const dispatch = useAppDispatch();
  const role = useAppSelector((s) => s.user.role);
  const [reportType, setReportType] = React.useState('progress');
  const [dateRange, setDateRange] = React.useState<[Date | null, Date | null]>([null, null]);
  const [selectedTemplate, setSelectedTemplate] = React.useState<ApiReportTemplate | null>(null);
  const [reportTemplates, setReportTemplates] = React.useState<ApiReportTemplate[]>([]);
  const [reports, setReports] = React.useState<ApiReport[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [selectedClass, setSelectedClass] = React.useState('all');
  const [stats, setStats] = React.useState<any>(null);
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = React.useState(false);
  const [classes, setClasses] = React.useState<any[]>([]);
  const [students, setStudents] = React.useState<any[]>([]);
  const [isEmailDialogOpen, setIsEmailDialogOpen] = React.useState(false);
  const [selectedReportForEmail, setSelectedReportForEmail] = React.useState<string | null>(null);
  const [currentTab, setCurrentTab] = React.useState(0);

  // Load data on component mount
  React.useEffect(() => {
    fetchReportData();
    loadClasses();
    loadStudents();
  }, []);

  const loadClasses = async () => {
    // Check if in bypass mode
    const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (bypassAuth || useMockData) {
      // Use fallback data directly in bypass mode
      setClasses([
        { id: 'math5a', name: 'Mathematics Grade 5A', subject: 'Mathematics', students: 28 },
        { id: 'science6b', name: 'Science Grade 6B', subject: 'Science', students: 25 },
        { id: 'history7a', name: 'History Grade 7A', subject: 'History', students: 30 },
        { id: 'english5b', name: 'English Grade 5B', subject: 'English', students: 27 },
        { id: 'physics8a', name: 'Physics Grade 8A', subject: 'Physics', students: 24 },
      ]);
      return;
    }

    // Only make API call if not in bypass mode
    try {
      const classes = await listClasses();
      setClasses(classes || []);
    } catch (error) {
      console.error('Error loading classes:', error);
      // Use fallback data if API fails
      setClasses([
        { id: 'math5a', name: 'Mathematics Grade 5A', subject: 'Mathematics', students: 28 },
        { id: 'science6b', name: 'Science Grade 6B', subject: 'Science', students: 25 },
        { id: 'history7a', name: 'History Grade 7A', subject: 'History', students: 30 },
        { id: 'english5b', name: 'English Grade 5B', subject: 'English', students: 27 },
        { id: 'physics8a', name: 'Physics Grade 8A', subject: 'Physics', students: 24 },
      ]);
    }
  };

  const loadStudents = async () => {
    // Check if in bypass mode
    const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (bypassAuth || useMockData) {
      // Use fallback data directly in bypass mode
      setStudents([
        { id: 'student1', name: 'Emma Wilson', grade: 5, class: 'math5a' },
        { id: 'student2', name: 'Michael Chen', grade: 6, class: 'science6b' },
        { id: 'student3', name: 'Sarah Johnson', grade: 7, class: 'history7a' },
        { id: 'student4', name: 'Alex Brown', grade: 5, class: 'english5b' },
        { id: 'student5', name: 'Lisa Martinez', grade: 8, class: 'physics8a' },
      ]);
      return;
    }

    // Only make API call if not in bypass mode
    try {
      const users = await listUsers({ role: 'student' });
      const usersArray = Array.isArray(users) ? users : [];
      const students = usersArray.map((user: any) => ({
        id: user.id,
        name: user.displayName || `${user.firstName} ${user.lastName}`,
        grade: user.gradeLevel || 5,
        class: user.classIds?.[0] || 'unassigned'
      }));
      setStudents(students);
    } catch (error) {
      console.error('Error loading students:', error);
      // Use fallback data if API fails
      setStudents([
        { id: 'student1', name: 'Emma Wilson', grade: 5, class: 'math5a' },
        { id: 'student2', name: 'Michael Chen', grade: 6, class: 'science6b' },
        { id: 'student3', name: 'Sarah Johnson', grade: 7, class: 'history7a' },
        { id: 'student4', name: 'Alex Brown', grade: 5, class: 'english5b' },
        { id: 'student5', name: 'Lisa Martinez', grade: 8, class: 'physics8a' },
      ]);
    }
  };

  const fetchReportData = async () => {
    // Check if in bypass mode
    const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (bypassAuth || useMockData) {
      // Use mock data directly in bypass mode
      setReportTemplates([]);  // Will fallback to mockTemplates
      setReports(mockReports);
      setStats({
        reports_generated: 157,
        reports_this_month: 23,
        scheduled_reports: 5,
        total_recipients: 450,
        storage_used_gb: 3.2,
      });
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      // Fetch templates, reports, and statistics in parallel
      const [templatesData, reportsData, statsData] = await Promise.all([
        listReportTemplates({ popular_only: true }),
        listReports({ limit: 10 }),
        getReportStatistics(),
      ]);
      setReportTemplates(Array.isArray(templatesData) ? templatesData : []);
      setReports(Array.isArray(reportsData) ? reportsData : []);
      setStats(statsData || {});
    } catch (error) {
      console.error('Failed to load report data:', error);
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to load report data',
        })
      );
    } finally {
      setLoading(false);
    }
  };

  const mockReports: Report[] = [
    {
      id: '1',
      name: 'Weekly Progress Report',
      type: 'progress',
      frequency: 'weekly',
      lastGenerated: '2024-01-29 10:00',
      nextScheduled: '2024-02-05 10:00',
      status: 'ready',
      size: '2.4 MB',
      recipients: 45,
    },
    {
      id: '2',
      name: 'Monthly Attendance Summary',
      type: 'attendance',
      frequency: 'monthly',
      lastGenerated: '2024-01-01 08:00',
      nextScheduled: '2024-02-01 08:00',
      status: 'scheduled',
      size: '1.8 MB',
      recipients: 12,
    },
    {
      id: '3',
      name: 'Q4 Grade Report',
      type: 'grades',
      frequency: 'quarterly',
      lastGenerated: '2024-01-15 14:00',
      status: 'ready',
      size: '5.2 MB',
      recipients: 156,
    },
    {
      id: '4',
      name: 'Student Behavior Analysis',
      type: 'behavior',
      frequency: 'monthly',
      lastGenerated: '2024-01-20 09:30',
      status: 'generating',
      recipients: 8,
    },
    {
      id: '5',
      name: 'Custom Analytics Report',
      type: 'custom',
      frequency: 'daily',
      lastGenerated: '2024-01-28 16:00',
      nextScheduled: '2024-01-30 16:00',
      status: 'error',
      recipients: 3,
    },
  ];

  const mockTemplates: ReportTemplate[] = [
    {
      id: '1',
      name: 'Student Progress Report',
      description: 'Comprehensive progress tracking including XP, levels, and achievements',
      icon: <IconTrendingUp />,
      category: 'Academic',
      fields: ['Student Name', 'Class', 'XP Earned', 'Level', 'Badges', 'Completion Rate'],
      popular: true,
    },
    {
      id: '2',
      name: 'Class Performance Summary',
      description: 'Overall class performance metrics and comparisons',
      icon: <IconSchool />,
      category: 'Academic',
      fields: ['Class Name', 'Average Score', 'Top Performers', 'Areas for Improvement'],
      popular: true,
    },
    {
      id: '3',
      name: 'Individual Student Report Card',
      description: 'Traditional report card with grades and teacher comments',
      icon: <IconFileText />,
      category: 'Grades',
      fields: ['Subject', 'Grade', 'Teacher Comments', 'Attendance', 'Behavior'],
    },
    {
      id: '4',
      name: 'Roblox Activity Report',
      description: 'Gaming platform engagement and educational game progress',
      icon: <IconTrophy />,
      category: 'Gamification',
      fields: ['Game Sessions', 'Time Played', 'Achievements', 'Skills Developed'],
      popular: true,
    },
    {
      id: '5',
      name: 'Parent Communication Log',
      description: 'Record of parent-teacher communications and meetings',
      icon: <IconUsers />,
      category: 'Communication',
      fields: ['Date', 'Parent Name', 'Discussion Topics', 'Action Items', 'Follow-up'],
    },
    {
      id: '6',
      name: 'Compliance Audit Report',
      description: 'COPPA, FERPA, and GDPR compliance status',
      icon: <IconChartLine />,
      category: 'Compliance',
      fields: ['Regulation', 'Status', 'Issues', 'Remediation', 'Audit Date'],
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'success';
      case 'generating':
        return 'info';
      case 'scheduled':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedTemplate && !reportType) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Please select a report type or template',
        })
      );
      return;
    }

    const reportData: ReportGenerateRequest = {
      name: `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report - ${new Date().toLocaleDateString()}`,
      type: reportType.toLowerCase() as any, // Ensure lowercase for backend
      format: 'pdf', // This will be converted to lowercase in the API function
      template_id: selectedTemplate?.id,
      filters: {
        date_range: dateRange,
        class_id: selectedClass !== 'all' ? selectedClass : undefined,
      },
    };

    try {
      setLoading(true);
      const newReport = await generateReport(reportData);
      dispatch(
        addNotification({
          type: 'success',
          message: 'Report generation started successfully',
        })
      );
      // Refresh reports list
      const updatedReports = await listReports({ limit: 10 });
      setReports(updatedReports);
    } catch (error) {
      console.error('Failed to generate report:', error);
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to generate report',
        })
      );
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleReport = async () => {
    setIsScheduleDialogOpen(true);
  };

  const handleEmailReport = (reportId: string) => {
    setSelectedReportForEmail(reportId);
    setIsEmailDialogOpen(true);
  };

  const handleUseTemplate = (templateId: string) => {
    const template = Array.isArray(reportTemplates) && reportTemplates.length > 0
      ? reportTemplates.find(t => t.id === templateId)
      : mockTemplates.find(t => t.id === templateId) as any;
    if (template) {
      setSelectedTemplate(template);
      setReportType(template.type || 'custom');
      setCurrentTab(0); // Switch to Generate Report tab
      dispatch(
        addNotification({
          type: 'info',
          message: `Template "${template.name}" selected`,
          severity: 'info',
        })
      );
    }
  };

  const handlePrintReport = (reportId: string) => {
    const report = reports.find(r => r.id === reportId);
    if (report) {
      window.print();
      dispatch(
        addNotification({
          type: 'info',
          message: `Printing ${report.name}`,
          severity: 'info',
        })
      );
    }
  };

  const handleReportActions = (reportId: string, action: string) => {
    switch (action) {
      case 'duplicate':
        // Duplicate report logic
        dispatch(
          addNotification({
            type: 'success',
            message: 'Report duplicated',
            severity: 'success',
          })
        );
        break;
      case 'share':
        // Share report logic
        navigator.clipboard.writeText(`${window.location.origin}/reports/${reportId}`);
        dispatch(
          addNotification({
            type: 'success',
            message: 'Report link copied to clipboard',
            severity: 'success',
          })
        );
        break;
      case 'delete':
        // Delete report logic
        setReports(reports.filter(r => r.id !== reportId));
        dispatch(
          addNotification({
            type: 'success',
            message: 'Report deleted',
            severity: 'success',
          })
        );
        break;
      default:
        break;
    }
  };

  const handleDownloadReport = async (reportId: string) => {
    try {
      await downloadReport(reportId);
      dispatch(
        addNotification({
          type: 'info',
          message: 'Report download started',
        })
      );
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to download report',
        })
      );
    }
  };

  const handleViewAllTemplates = async () => {
    try {
      const allTemplates = await listReportTemplates();
      setReportTemplates(allTemplates);
      dispatch(
        addNotification({
          type: 'success',
          message: `Loaded ${allTemplates.length} templates`,
        })
      );
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to load templates',
        })
      );
    }
  };

  const renderTabContent = () => {
    switch (currentTab) {
      case 0: // Reports Generation
        return (
          <Tabs.Panel value="0">
            {/* Quick Stats */}
            <Grid>
              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Card padding="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Reports Generated
                    </Text>
                    <Title order={2} fw={700}>
                      {stats?.reports_generated || 0}
                    </Title>
                    <Text size="xs" c="green">
                      {stats?.reports_this_month || 0} this month
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Card padding="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Scheduled Reports
                    </Text>
                    <Title order={2} fw={700}>
                      {stats?.scheduled_reports || 0}
                    </Title>
                    <Text size="xs" c="dimmed">
                      {stats?.next_scheduled_time
                        ? `Next: ${new Date(stats.next_scheduled_time).toLocaleString()}`
                        : 'No scheduled reports'}
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Card padding="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Recipients
                    </Text>
                    <Title order={2} fw={700}>
                      {stats?.total_recipients || 0}
                    </Title>
                    <Text size="xs" c="dimmed">
                      Across all reports
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Card padding="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Storage Used
                    </Text>
                    <Title order={2} fw={700}>
                      {stats?.storage_used_gb || 0} GB
                    </Title>
                    <Progress
                      value={Math.min((stats?.storage_used_gb || 0) * 10, 100)}
                      mt="xs"
                    />
                  </Stack>
                </Card>
              </Grid.Col>

              {/* Report Generator */}
              <Grid.Col span={{ base: 12, lg: 8 }}>
                <Card padding="md">
                  <Title order={4} fw={600} mb="lg">
                    Generate New Report
                  </Title>
                  <Grid>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Select
                        label="Report Type"
                        value={reportType}
                        onChange={(value) => setReportType(value || 'progress')}
                        data={[
                          { value: 'progress', label: 'Progress Report' },
                          { value: 'attendance', label: 'Attendance Report' },
                          { value: 'grades', label: 'Grade Report' },
                          { value: 'behavior', label: 'Behavior Report' },
                          { value: 'custom', label: 'Custom Report' },
                        ]}
                      />
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Select
                        label="Class/Student"
                        value={selectedClass}
                        onChange={(value) => setSelectedClass(value || 'all')}
                        data={[
                          { value: 'all', label: 'All Classes' },
                          ...classes.map((cls) => ({
                            value: cls.id,
                            label: `${cls.name} (${cls.students} students)`,
                          })),
                          { value: 'individual', label: 'Individual Student' },
                        ]}
                      />
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <DateInput
                        label="Start Date"
                        value={dateRange[0]}
                        onChange={(newValue) => setDateRange([newValue, dateRange[1]])}
                      />
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <DateInput
                        label="End Date"
                        value={dateRange[1]}
                        onChange={(newValue) => setDateRange([dateRange[0], newValue])}
                      />
                    </Grid.Col>
                    <Grid.Col span={12}>
                      <Group gap="md">
                        <Button
                          leftSection={<IconDownload />}
                          onClick={handleGenerateReport}
                          style={{ flex: 1 }}
                        >
                          Generate Report
                        </Button>
                        <Button
                          variant="outline"
                          leftSection={<IconCalendarTime />}
                          onClick={handleScheduleReport}
                        >
                          Schedule
                        </Button>
                        <Button
                          variant="outline"
                          leftSection={<IconMail />}
                          disabled={reports.length === 0}
                          onClick={() => reports.length > 0 && handleEmailReport(reports[0].id)}
                        >
                          Email
                        </Button>
                        <Button variant="outline" leftSection={<IconPrinter />}>
                          Print
                        </Button>
                      </Group>
                    </Grid.Col>
                  </Grid>
                </Card>
              </Grid.Col>

            {/* Report Templates */}
            <Grid.Col span={{ base: 12, lg: 4 }}>
              <Card h="100%">
                <Title order={6} fw={600} mb="md">
                  Popular Templates
                </Title>
                <List size="sm">
                  {(Array.isArray(reportTemplates) && reportTemplates.length > 0
                    ? reportTemplates.filter(t => t.is_popular)
                    : mockTemplates.filter(t => t.popular)
                  ).map((template) => (
                    <List.Item
                      key={template.id}
                      icon={template.icon}
                      onClick={() => setSelectedTemplate(template)}
                      style={{ cursor: 'pointer' }}
                    >
                      <Group justify="space-between">
                        <Stack gap="xs">
                          <Text size="sm" fw={500}>{template.name}</Text>
                          <Text size="xs" c="dimmed">{template.description}</Text>
                        </Stack>
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleUseTemplate(template.id);
                          }}
                        >
                          Use
                        </Button>
                      </Group>
                    </List.Item>
                  ))}
                </List>
                <Button
                  fullWidth
                  variant="outline"
                  mt="md"
                  onClick={handleViewAllTemplates}
                  loading={loading}
                >
                  View All Templates
                </Button>
              </Card>
            </Grid.Col>

            {/* Recent Reports */}
            <Grid.Col span={12}>
              <Card>
                <Title order={6} fw={600} mb="md">
                  Recent Reports
                </Title>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Report Name</Table.Th>
                        <Table.Th>Type</Table.Th>
                        <Table.Th>Frequency</Table.Th>
                        <Table.Th>Generated</Table.Th>
                        <Table.Th>Status</Table.Th>
                        <Table.Th>Size</Table.Th>
                        <Table.Th>Recipients</Table.Th>
                        <Table.Th>Actions</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {((reports.length > 0 ? (reports as any[]) : (mockReports as any[]))).slice(0, 5).map((report: any) => (
                        <Table.Tr key={report.id}>
                          <Table.Td>
                            <Group gap="xs">
                              <IconFile size={16} />
                              <Text size="sm">{report.name}</Text>
                            </Group>
                          </Table.Td>
                          <Table.Td>
                            <Badge size="sm">{report.type}</Badge>
                          </Table.Td>
                          <Table.Td>{report.frequency}</Table.Td>
                          <Table.Td>
                            <Text size="xs">
                              {new Date(report.lastGenerated).toLocaleString()}
                            </Text>
                          </Table.Td>
                          <Table.Td>
                            <Badge
                              size="sm"
                              color={getStatusColor(report.status) as any}
                            >
                              {report.status}
                            </Badge>
                          </Table.Td>
                          <Table.Td>{report.size || '—'}</Table.Td>
                          <Table.Td>{report.recipients}</Table.Td>
                          <Table.Td>
                            <Group gap="xs">
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                disabled={report.status !== 'ready'}
                                onClick={() => handleDownloadReport(report.id)}
                              >
                                <IconDownload size={16} />
                              </ActionIcon>
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                onClick={() => handleEmailReport(report.id)}
                                title="Email Report"
                              >
                                <IconMail size={16} />
                              </ActionIcon>
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                onClick={() => handlePrintReport(report.id)}
                                title="Print Report"
                              >
                                <IconPrinter size={16} />
                              </ActionIcon>
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                onClick={() => handleReportActions(report.id, 'share')}
                                title="Share Report"
                              >
                                <IconDots size={16} />
                              </ActionIcon>
                            </Group>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>
      );

      case 1: // Analytics Dashboard
        return (
          <Tabs.Panel value="1">
            <Grid>
              <Grid.Col span={12}>
                <UserActivityChart timeRange="30d" height={350} autoRefresh={true} />
              </Grid.Col>
              <Grid.Col span={12}>
                <ContentMetrics timeRange="30d" autoRefresh={true} />
              </Grid.Col>
            </Grid>
          </Tabs.Panel>
        );

      case 2: // Performance Metrics
        return (
          <Tabs.Panel value="2">
            <Grid>
              <Grid.Col span={12}>
                <PerformanceIndicator showSystemHealth={role === 'admin'} autoRefresh={true} />
              </Grid.Col>
            </Grid>
          </Tabs.Panel>
        );

      default:
        return (
          <Tabs.Panel value="0">
            <Alert color="blue">
              Select a tab to view reports and analytics.
            </Alert>
          </Tabs.Panel>
        );
    }
  };

  return (
    <Container size="xl">
      <Grid>
        {/* Header */}
        <Grid.Col span={12}>
          <Card padding="md">
            <Group
              justify="space-between"
              align="center"
              mb="md"
            >
              <Group gap="md">
                <IconClipboardCheck size={32} color="blue" />
                <Box>
                  <Title order={3} fw={600}>
                    Reports & Analytics
                  </Title>
                  <Text size="xs" c="dimmed">
                    Generate reports and view real-time analytics
                  </Text>
                </Box>
              </Group>
              <Group gap="md">
                <Button variant="outline" leftSection={<IconRefresh />} onClick={fetchReportData}>
                  Refresh
                </Button>
                <Button leftSection={<IconDownload />}>
                  Export All
                </Button>
              </Group>
            </Group>

            {/* Navigation Tabs */}
            <Tabs value={currentTab.toString()} onChange={(value) => setCurrentTab(Number(value))}>
              <Tabs.List>
                <Tabs.Tab
                  value="0"
                  leftSection={<IconFileText />}
                >
                  Reports
                </Tabs.Tab>
                <Tabs.Tab
                  value="1"
                  leftSection={<IconChartLine />}
                >
                  Analytics
                </Tabs.Tab>
                <Tabs.Tab
                  value="2"
                  leftSection={<IconTrendingUp />}
                >
                  Performance
                </Tabs.Tab>
              </Tabs.List>

              {/* Tab Content */}
              {renderTabContent()}
            </Tabs>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  );
}