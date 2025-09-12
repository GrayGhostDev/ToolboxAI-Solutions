import * as React from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Chip,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  AlertTitle,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Tabs,
  Tab,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import PrintIcon from "@mui/icons-material/Print";
import EmailIcon from "@mui/icons-material/Email";
import ScheduleIcon from "@mui/icons-material/Schedule";
import AssessmentIcon from "@mui/icons-material/Assessment";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import PeopleIcon from "@mui/icons-material/People";
import SchoolIcon from "@mui/icons-material/School";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import DescriptionIcon from "@mui/icons-material/Description";
import RefreshIcon from "@mui/icons-material/Refresh";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import TimelineIcon from "@mui/icons-material/Timeline";
import { useAppSelector, useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";
import {
  generateReport,
  scheduleReport,
  emailReport,
  listReportTemplates,
  listReports,
  getReportStatistics,
  downloadReport,
  ReportTemplate as ApiReportTemplate,
  Report as ApiReport,
  ReportGenerateRequest,
} from "../../services/api";

// Import our new analytics components
import UserActivityChart from "../analytics/UserActivityChart";
import ContentMetrics from "../analytics/ContentMetrics";
import PerformanceIndicator from "../analytics/PerformanceIndicator";

interface Report {
  id: string;
  name: string;
  type: "progress" | "attendance" | "grades" | "behavior" | "custom";
  frequency: "daily" | "weekly" | "monthly" | "quarterly" | "yearly";
  lastGenerated: string;
  nextScheduled?: string;
  status: "ready" | "generating" | "scheduled" | "error";
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
}

const performanceData = [
  { month: "Jan", students: 85, average: 78 },
  { month: "Feb", students: 88, average: 80 },
  { month: "Mar", students: 92, average: 82 },
  { month: "Apr", students: 90, average: 85 },
  { month: "May", students: 94, average: 87 },
  { month: "Jun", students: 96, average: 89 },
];

const subjectDistribution = [
  { name: "Math", value: 30, color: "#2563EB" },
  { name: "Science", value: 25, color: "#22C55E" },
  { name: "Language", value: 20, color: "#FACC15" },
  { name: "Arts", value: 15, color: "#9333EA" },
  { name: "Tech", value: 10, color: "#EF4444" },
];

export default function Reports() {
  const dispatch = useAppDispatch();
  const role = useAppSelector((s) => s.user.role);
  const [reportType, setReportType] = React.useState("progress");
  const [dateRange, setDateRange] = React.useState<[Date | null, Date | null]>([null, null]);
  const [selectedTemplate, setSelectedTemplate] = React.useState<ApiReportTemplate | null>(null);
  const [reportTemplates, setReportTemplates] = React.useState<ApiReportTemplate[]>([]);
  const [reports, setReports] = React.useState<ApiReport[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [selectedClass, setSelectedClass] = React.useState("all");
  const [stats, setStats] = React.useState<any>(null);
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = React.useState(false);
  const [isEmailDialogOpen, setIsEmailDialogOpen] = React.useState(false);
  const [selectedReportForEmail, setSelectedReportForEmail] = React.useState<string | null>(null);
  const [currentTab, setCurrentTab] = React.useState(0);

  // Load data on component mount
  React.useEffect(() => {
    fetchReportData();
  }, []);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      // Fetch templates, reports, and statistics in parallel
      const [templatesData, reportsData, statsData] = await Promise.all([
        listReportTemplates({ popular_only: true }),
        listReports({ limit: 10 }),
        getReportStatistics(),
      ]);
      setReportTemplates(templatesData);
      setReports(reportsData);
      setStats(statsData);
    } catch (error) {
      console.error("Failed to load report data:", error);
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to load report data",
        })
      );
    } finally {
      setLoading(false);
    }
  };

  const mockReports: Report[] = [
    {
      id: "1",
      name: "Weekly Progress Report",
      type: "progress",
      frequency: "weekly",
      lastGenerated: "2024-01-29 10:00",
      nextScheduled: "2024-02-05 10:00",
      status: "ready",
      size: "2.4 MB",
      recipients: 45,
    },
    {
      id: "2",
      name: "Monthly Attendance Summary",
      type: "attendance",
      frequency: "monthly",
      lastGenerated: "2024-01-01 08:00",
      nextScheduled: "2024-02-01 08:00",
      status: "scheduled",
      size: "1.8 MB",
      recipients: 12,
    },
    {
      id: "3",
      name: "Q4 Grade Report",
      type: "grades",
      frequency: "quarterly",
      lastGenerated: "2024-01-15 14:00",
      status: "ready",
      size: "5.2 MB",
      recipients: 156,
    },
    {
      id: "4",
      name: "Student Behavior Analysis",
      type: "behavior",
      frequency: "monthly",
      lastGenerated: "2024-01-20 09:30",
      status: "generating",
      recipients: 8,
    },
    {
      id: "5",
      name: "Custom Analytics Report",
      type: "custom",
      frequency: "daily",
      lastGenerated: "2024-01-28 16:00",
      nextScheduled: "2024-01-30 16:00",
      status: "error",
      recipients: 3,
    },
  ];

  const mockTemplates: ReportTemplate[] = [
    {
      id: "1",
      name: "Student Progress Report",
      description: "Comprehensive progress tracking including XP, levels, and achievements",
      icon: <TrendingUpIcon />,
      category: "Academic",
      fields: ["Student Name", "Class", "XP Earned", "Level", "Badges", "Completion Rate"],
      popular: true,
    },
    {
      id: "2",
      name: "Class Performance Summary",
      description: "Overall class performance metrics and comparisons",
      icon: <SchoolIcon />,
      category: "Academic",
      fields: ["Class Name", "Average Score", "Top Performers", "Areas for Improvement"],
      popular: true,
    },
    {
      id: "3",
      name: "Individual Student Report Card",
      description: "Traditional report card with grades and teacher comments",
      icon: <DescriptionIcon />,
      category: "Grades",
      fields: ["Subject", "Grade", "Teacher Comments", "Attendance", "Behavior"],
    },
    {
      id: "4",
      name: "Roblox Activity Report",
      description: "Gaming platform engagement and educational game progress",
      icon: <EmojiEventsIcon />,
      category: "Gamification",
      fields: ["Game Sessions", "Time Played", "Achievements", "Skills Developed"],
      popular: true,
    },
    {
      id: "5",
      name: "Parent Communication Log",
      description: "Record of parent-teacher communications and meetings",
      icon: <PeopleIcon />,
      category: "Communication",
      fields: ["Date", "Parent Name", "Discussion Topics", "Action Items", "Follow-up"],
    },
    {
      id: "6",
      name: "Compliance Audit Report",
      description: "COPPA, FERPA, and GDPR compliance status",
      icon: <AssessmentIcon />,
      category: "Compliance",
      fields: ["Regulation", "Status", "Issues", "Remediation", "Audit Date"],
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ready":
        return "success";
      case "generating":
        return "info";
      case "scheduled":
        return "warning";
      case "error":
        return "error";
      default:
        return "default";
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedTemplate && !reportType) {
      dispatch(
        addNotification({
          type: "error",
          message: "Please select a report type or template",
        })
      );
      return;
    }

    const reportData: ReportGenerateRequest = {
      name: `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report - ${new Date().toLocaleDateString()}`,
      type: reportType.toLowerCase() as any, // Ensure lowercase for backend
      format: "pdf", // This will be converted to lowercase in the API function
      template_id: selectedTemplate?.id,
      filters: {
        date_range: dateRange,
        class_id: selectedClass !== "all" ? selectedClass : undefined,
      },
    };

    try {
      setLoading(true);
      const newReport = await generateReport(reportData);
      dispatch(
        addNotification({
          type: "success",
          message: "Report generation started successfully",
        })
      );
      // Refresh reports list
      const updatedReports = await listReports({ limit: 10 });
      setReports(updatedReports);
    } catch (error) {
      console.error("Failed to generate report:", error);
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to generate report",
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

  const handleDownloadReport = async (reportId: string) => {
    try {
      await downloadReport(reportId);
      dispatch(
        addNotification({
          type: "info",
          message: "Report download started",
        })
      );
    } catch (error) {
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to download report",
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
          type: "success",
          message: `Loaded ${allTemplates.length} templates`,
        })
      );
    } catch (error) {
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to load templates",
        })
      );
    }
  };

  const renderTabContent = () => {
    switch (currentTab) {
      case 0: // Reports Generation
        return (
          <>
            {/* Quick Stats */}
            <Grid2 xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      Reports Generated
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {stats?.reports_generated || 0}
                    </Typography>
                    <Typography variant="caption" color="success.main">
                      {stats?.reports_this_month || 0} this month
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            <Grid2 xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      Scheduled Reports
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {stats?.scheduled_reports || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {stats?.next_scheduled_time 
                        ? `Next: ${new Date(stats.next_scheduled_time).toLocaleString()}`
                        : "No scheduled reports"}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            <Grid2 xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      Recipients
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {stats?.total_recipients || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Across all reports
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            <Grid2 xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      Storage Used
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {stats?.storage_used_gb || 0} GB
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min((stats?.storage_used_gb || 0) * 10, 100)} 
                      sx={{ mt: 1 }} 
                    />
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            {/* Report Generator */}
            <Grid2 xs={12} lg={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                    Generate New Report
                  </Typography>
                  <Grid2 container spacing={2}>
                    <Grid2 xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Report Type</InputLabel>
                        <Select
                          value={reportType}
                          label="Report Type"
                          onChange={(e) => setReportType(e.target.value)}
                        >
                          <MenuItem value="progress">Progress Report</MenuItem>
                          <MenuItem value="attendance">Attendance Report</MenuItem>
                          <MenuItem value="grades">Grade Report</MenuItem>
                          <MenuItem value="behavior">Behavior Report</MenuItem>
                          <MenuItem value="custom">Custom Report</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid2>
                    <Grid2 xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Class/Student</InputLabel>
                        <Select defaultValue="all" label="Class/Student">
                          <MenuItem value="all">All Classes</MenuItem>
                          <MenuItem value="math5a">Math Grade 5A</MenuItem>
                          <MenuItem value="science6b">Science Grade 6B</MenuItem>
                          <MenuItem value="individual">Individual Student</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid2>
                    <Grid2 xs={12} md={6}>
                      <DatePicker
                        label="Start Date"
                        value={dateRange[0]}
                        onChange={(newValue) => setDateRange([newValue, dateRange[1]])}
                        slotProps={{ textField: { fullWidth: true } }}
                      />
                    </Grid2>
                    <Grid2 xs={12} md={6}>
                      <DatePicker
                        label="End Date"
                        value={dateRange[1]}
                        onChange={(newValue) => setDateRange([dateRange[0], newValue])}
                        slotProps={{ textField: { fullWidth: true } }}
                      />
                    </Grid2>
                    <Grid2 xs={12}>
                      <Stack direction="row" gap={2}>
                        <Button
                          variant="contained"
                          startIcon={<FileDownloadIcon />}
                          onClick={handleGenerateReport}
                          sx={{ flex: 1 }}
                        >
                          Generate Report
                        </Button>
                        <Button 
                          variant="outlined" 
                          startIcon={<ScheduleIcon />}
                          onClick={handleScheduleReport}
                        >
                          Schedule
                        </Button>
                        <Button 
                          variant="outlined" 
                          startIcon={<EmailIcon />}
                          disabled={reports.length === 0}
                          onClick={() => reports.length > 0 && handleEmailReport(reports[0].id)}
                        >
                          Email
                        </Button>
                        <Button variant="outlined" startIcon={<PrintIcon />}>
                          Print
                        </Button>
                      </Stack>
                    </Grid2>
                  </Grid2>
                </CardContent>
              </Card>
            </Grid2>

            {/* Report Templates */}
            <Grid2 xs={12} lg={4}>
              <Card sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    Popular Templates
                  </Typography>
                  <List dense>
                    {reportTemplates.filter(t => t.is_popular).map((template) => (
                      <ListItem key={template.id} button onClick={() => setSelectedTemplate(template)}>
                        <ListItemIcon>{template.icon}</ListItemIcon>
                        <ListItemText
                          primary={template.name}
                          secondary={template.description}
                        />
                        <ListItemSecondaryAction>
                          <IconButton edge="end" size="small">
                            <MoreVertIcon />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                  <Button 
                    fullWidth 
                    variant="outlined" 
                    sx={{ mt: 2 }}
                    onClick={handleViewAllTemplates}
                    disabled={loading}
                  >
                    View All Templates
                  </Button>
                </CardContent>
              </Card>
            </Grid2>

            {/* Recent Reports */}
            <Grid2 xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    Recent Reports
                  </Typography>
                  <TableContainer>
                    <Table aria-label="recent reports table">
                      <TableHead>
                        <TableRow>
                          <TableCell>Report Name</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Frequency</TableCell>
                          <TableCell>Generated</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Size</TableCell>
                          <TableCell>Recipients</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {((reports.length > 0 ? (reports as any[]) : (mockReports as any[]))).slice(0, 5).map((report: any) => (
                          <TableRow key={report.id} hover>
                            <TableCell>
                              <Stack direction="row" alignItems="center" gap={1}>
                                <InsertDriveFileIcon fontSize="small" />
                                <Typography variant="body2">{report.name}</Typography>
                              </Stack>
                            </TableCell>
                            <TableCell>
                              <Chip label={report.type} size="small" />
                            </TableCell>
                            <TableCell>{report.frequency}</TableCell>
                            <TableCell>
                              <Typography variant="caption">
                                {new Date(report.lastGenerated).toLocaleString()}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={report.status}
                                size="small"
                                color={getStatusColor(report.status) as any}
                              />
                            </TableCell>
                            <TableCell>{report.size || "—"}</TableCell>
                            <TableCell>{report.recipients}</TableCell>
                            <TableCell>
                              <Stack direction="row" gap={0.5}>
                                <IconButton 
                                  size="small" 
                                  disabled={report.status !== "ready"}
                                  onClick={() => handleDownloadReport(report.id)}
                                >
                                  <FileDownloadIcon />
                                </IconButton>
                                <IconButton 
                                  size="small"
                                  onClick={() => handleEmailReport(report.id)}
                                >
                                  <EmailIcon />
                                </IconButton>
                                <IconButton size="small">
                                  <MoreVertIcon />
                                </IconButton>
                              </Stack>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid2>
          </>
        );
      
      case 1: // Analytics Dashboard
        return (
          <>
            <Grid2 xs={12}>
              <UserActivityChart timeRange="30d" height={350} autoRefresh={true} />
            </Grid2>
            <Grid2 xs={12}>
              <ContentMetrics timeRange="30d" autoRefresh={true} />
            </Grid2>
          </>
        );
      
      case 2: // Performance Metrics
        return (
          <>
            <Grid2 xs={12}>
              <PerformanceIndicator showSystemHealth={role === "admin"} autoRefresh={true} />
            </Grid2>
          </>
        );
      
      default:
        return (
          <Grid2 xs={12}>
            <Alert severity="info">
              Select a tab to view reports and analytics.
            </Alert>
          </Grid2>
        );
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Grid2 container spacing={3}>
        {/* Header */}
        <Grid2 xs={12}>
          <Card>
            <CardContent>
              <Stack
                direction={{ xs: "column", md: "row" }}
                justifyContent="space-between"
                alignItems={{ xs: "flex-start", md: "center" }}
                gap={2}
                mb={2}
              >
                <Stack direction="row" alignItems="center" gap={2}>
                  <AssessmentIcon sx={{ fontSize: 32, color: "primary.main" }} />
                  <div>
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>
                      Reports & Analytics
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Generate reports and view real-time analytics
                    </Typography>
                  </div>
                </Stack>
                <Stack direction="row" gap={2}>
                  <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchReportData}>
                    Refresh
                  </Button>
                  <Button variant="contained" startIcon={<FileDownloadIcon />}>
                    Export All
                  </Button>
                </Stack>
              </Stack>
              
              {/* Navigation Tabs */}
              <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
                <Tab 
                  label="Reports" 
                  icon={<DescriptionIcon />}
                  iconPosition="start"
                />
                <Tab 
                  label="Analytics" 
                  icon={<TimelineIcon />}
                  iconPosition="start"
                />
                <Tab 
                  label="Performance" 
                  icon={<TrendingUpIcon />}
                  iconPosition="start"
                />
              </Tabs>
            </CardContent>
          </Card>
        </Grid2>

        {/* Tab Content */}
        {renderTabContent()}
      </Grid2>
    </LocalizationProvider>
  );
}