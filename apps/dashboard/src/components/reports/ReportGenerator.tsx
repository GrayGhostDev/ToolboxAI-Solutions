import React, { useState, useEffect } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Paper from '@mui/material/Paper';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import CircularProgress from '@mui/material/CircularProgress';

import {
  Download,
  PictureAsPdf,
  TableChart,
  Assessment,
  School,
  Person,
  CalendarMonth,
  Refresh,
  Email,
  Schedule,
  CheckCircle,
  Warning,
  Description,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format as formatDate, subDays } from 'date-fns';
import { useAppSelector } from '../../store';
import { generateReport } from '../../services/api';

interface ReportConfig {
  type: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  formats: string[];
  parameters: string[];
}

interface GeneratedReport {
  id: string;
  name: string;
  type: string;
  format: string;
  generatedAt: Date;
  size: string;
  status: 'pending' | 'ready' | 'failed';
  url?: string;
}

const reportTypes: ReportConfig[] = [
  {
    type: 'student-progress',
    name: 'Student Progress Report',
    description: 'Comprehensive progress report for individual students or entire class',
    icon: <School />,
    formats: ['pdf', 'excel', 'csv'],
    parameters: ['student', 'dateRange', 'subjects'],
  },
  {
    type: 'assessment-results',
    name: 'Assessment Results',
    description: 'Detailed assessment scores and analytics',
    icon: <Assessment />,
    formats: ['pdf', 'excel'],
    parameters: ['assessment', 'class', 'dateRange'],
  },
  {
    type: 'attendance',
    name: 'Attendance Report',
    description: 'Class attendance records and patterns',
    icon: <Person />,
    formats: ['pdf', 'excel', 'csv'],
    parameters: ['class', 'dateRange'],
  },
  {
    type: 'analytics-summary',
    name: 'Analytics Summary',
    description: 'Overall platform usage and engagement metrics',
    icon: <TableChart />,
    formats: ['pdf', 'pptx'],
    parameters: ['dateRange', 'metrics'],
  },
  {
    type: 'compliance',
    name: 'Compliance Report',
    description: 'FERPA and COPPA compliance documentation',
    icon: <Description />,
    formats: ['pdf'],
    parameters: ['dateRange', 'regulations'],
  },
];

const ReportGenerator: React.FunctionComponent<Record<string, any>> = () => {
  const userRole = useAppSelector((state) => state.user.role);
  const [selectedReport, setSelectedReport] = useState<ReportConfig | null>(null);
  const [exportFormat, setExportFormat] = useState<string>('pdf');
  const [dateRange, setDateRange] = useState({
    start: subDays(new Date(), 30),
    end: new Date(),
  });
  const [selectedStudent, setSelectedStudent] = useState<string>('all');
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentReports, setRecentReports] = useState<GeneratedReport[]>([]);
  const [emailRecipient, setEmailRecipient] = useState('');
  const [scheduleTime, setScheduleTime] = useState<'now' | 'daily' | 'weekly' | 'monthly'>('now');

  // Mock data for demonstration
  const students = [
    { id: 'all', name: 'All Students' },
    { id: '1', name: 'Alice Johnson' },
    { id: '2', name: 'Bob Smith' },
    { id: '3', name: 'Charlie Brown' },
  ];

  const classes = [
    { id: 'all', name: 'All Classes' },
    { id: 'math-8', name: 'Math Grade 8' },
    { id: 'science-7', name: 'Science Grade 7' },
    { id: 'english-9', name: 'English Grade 9' },
  ];

  const subjects = ['Math', 'Science', 'English', 'History', 'Art', 'Physical Education'];

  useEffect(() => {
    // Load recent reports
    loadRecentReports();
  }, []);

  const loadRecentReports = async () => {
    // Mock recent reports - replace with actual API call
    setRecentReports([
      {
        id: '1',
        name: 'Weekly Progress Report',
        type: 'student-progress',
        format: 'pdf',
        generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
        size: '2.4 MB',
        status: 'ready',
        url: '/reports/weekly-progress.pdf',
      },
      {
        id: '2',
        name: 'Math Assessment Results',
        type: 'assessment-results',
        format: 'excel',
        generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
        size: '1.8 MB',
        status: 'ready',
        url: '/reports/math-assessment.xlsx',
      },
      {
        id: '3',
        name: 'Monthly Attendance',
        type: 'attendance',
        format: 'csv',
        generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
        size: '560 KB',
        status: 'ready',
        url: '/reports/attendance.csv',
      },
    ]);
  };

  const handleGenerateReport = async () => {
    if (!selectedReport) return;

    setGenerating(true);
    setError(null);

    try {
      // Prepare report parameters
      const params = {
        type: selectedReport.type,
        format: exportFormat,
        dateRange: {
          start: formatDate(dateRange.start, 'yyyy-MM-dd'),
          end: formatDate(dateRange.end, 'yyyy-MM-dd'),
        },
        filters: {
          student: selectedStudent,
          class: selectedClass,
          subjects: selectedSubjects,
        },
        email: emailRecipient || undefined,
        schedule: scheduleTime,
      };

// Call API to generate report using the typed API helper
      const typeMap: Record<string, 'progress' | 'attendance' | 'grades' | 'behavior' | 'assessment' | 'compliance' | 'gamification' | 'custom'> = {
        'student-progress': 'progress',
        'assessment-results': 'assessment',
        'attendance': 'attendance',
        'analytics-summary': 'custom',
        'compliance': 'compliance',
      };

      const response = await generateReport({
        name: selectedReport.name,
        type: typeMap[selectedReport.type] || 'custom',
        format: exportFormat as any,
        parameters: params,
      });
      
      // Add to recent reports
      const newReport: GeneratedReport = {
        id: response.id,
        name: response.name,
        type: selectedReport.type,
        format: exportFormat,
        generatedAt: new Date(),
        size: response.file_size ? `${Math.round(response.file_size / (1024 * 1024))} MB` : 'Processing...',
        status: response.status === 'completed' ? 'ready' : 'pending',
        url: response.file_path,
      };

      setRecentReports([newReport, ...recentReports]);

      // Simulate processing delay
      setTimeout(() => {
        setRecentReports((prev) =>
          prev.map((r) =>
            r.id === newReport.id ? { ...r, status: 'ready', size: '1.5 MB' } : r
          )
        );
      }, 3000);

      // Reset form
      if (scheduleTime === 'now') {
        setSelectedReport(null);
setExportFormat('pdf');
        setSelectedStudent('all');
        setSelectedClass('all');
        setSelectedSubjects([]);
        setEmailRecipient('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadReport = (report: GeneratedReport) => {
    if (report.url) {
      // Trigger download
      const link = document.createElement('a');
      link.href = report.url;
      link.download = `${report.name}.${report.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <PictureAsPdf color="error" />;
      case 'excel':
      case 'csv':
        return <TableChart color="success" />;
      case 'pptx':
        return <Assessment color="primary" />;
      default:
        return <Description />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
          Report Generator
        </Typography>

        <Grid container spacing={3}>
          {/* Report Type Selection */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title="Select Report Type" />
              <CardContent>
                <Grid container spacing={2}>
                  {reportTypes.map((report) => (
                    <Grid item xs={12} sm={6} key={report.type}>
                      <Paper
                        sx={{
                          p: 2,
                          cursor: 'pointer',
                          border: selectedReport?.type === report.type ? 2 : 1,
                          borderColor: selectedReport?.type === report.type ? 'primary.main' : 'divider',
                          '&:hover': {
                            bgcolor: 'action.hover',
                          },
                        }}
                        onClick={(e: React.MouseEvent) => () => setSelectedReport(report)}
                      >
                        <Stack direction="row" spacing={2} alignItems="center">
                          {report.icon}
                          <Box flex={1}>
                            <Typography variant="subtitle1" fontWeight={600}>
                              {report.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {report.description}
                            </Typography>
                          </Box>
                          {selectedReport?.type === report.type && (
                            <CheckCircle color="primary" />
                          )}
                        </Stack>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>

                {selectedReport && (
                  <>
                    <Divider sx={{ my: 3 }} />
                    
                    {/* Report Parameters */}
                    <Typography variant="h6" gutterBottom>
                      Report Parameters
                    </Typography>
                    
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                      {/* Format Selection */}
                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel>Export Format</InputLabel>
                          <Select
                            value={exportFormat}
                            onChange={(e) => setExportFormat(String(e.target.value))}
                            label="Export Format"
                          >
                            {selectedReport.formats.map((fmt) => (
                              <MenuItem key={fmt} value={fmt}>
                                <Stack direction="row" spacing={1} alignItems="center">
                                  {getFormatIcon(fmt)}
                                  <span>{fmt.toUpperCase()}</span>
                                </Stack>
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>

                      {/* Date Range */}
                      {selectedReport.parameters.includes('dateRange') && (
                        <>
                          <Grid item xs={12} sm={3}>
                            <DatePicker
                              label="Start Date"
                              value={dateRange.start}
                              onChange={(date) => date && setDateRange({ ...dateRange, start: date })}
                              slotProps={{
                                textField: { fullWidth: true },
                              }}
                            />
                          </Grid>
                          <Grid item xs={12} sm={3}>
                            <DatePicker
                              label="End Date"
                              value={dateRange.end}
                              onChange={(date) => date && setDateRange({ ...dateRange, end: date })}
                              slotProps={{
                                textField: { fullWidth: true },
                              }}
                            />
                          </Grid>
                        </>
                      )}

                      {/* Student Selection */}
                      {selectedReport.parameters.includes('student') && (
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth>
                            <InputLabel>Student</InputLabel>
                            <Select
                              value={selectedStudent}
                              onChange={(e) => setSelectedStudent(e.target.value)}
                              label="Student"
                            >
                              {students.map((student) => (
                                <MenuItem key={student.id} value={student.id}>
                                  {student.name}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                      )}

                      {/* Class Selection */}
                      {selectedReport.parameters.includes('class') && (
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth>
                            <InputLabel>Class</InputLabel>
                            <Select
                              value={selectedClass}
                              onChange={(e) => setSelectedClass(e.target.value)}
                              label="Class"
                            >
                              {classes.map((cls) => (
                                <MenuItem key={cls.id} value={cls.id}>
                                  {cls.name}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                      )}

                      {/* Subject Selection */}
                      {selectedReport.parameters.includes('subjects') && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" gutterBottom>
                            Select Subjects
                          </Typography>
                          <Stack direction="row" spacing={1} flexWrap="wrap">
                            {subjects.map((subject) => (
                              <Chip
                                key={subject}
                                label={subject}
                                onClick={(e: React.MouseEvent) => () => {
                                  if (selectedSubjects.includes(subject)) {
                                    setSelectedSubjects(selectedSubjects.filter((s) => s !== subject));
                                  } else {
                                    setSelectedSubjects([...selectedSubjects, subject]);
                                  }
                                }}
                                color={selectedSubjects.includes(subject) ? 'primary' : 'default'}
                                sx={{ mb: 1 }}
                              />
                            ))}
                          </Stack>
                        </Grid>
                      )}

                      {/* Delivery Options */}
                      <Grid item xs={12}>
                        <Divider sx={{ my: 2 }} />
                        <Typography variant="h6" gutterBottom>
                          Delivery Options
                        </Typography>
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Email Report To (Optional)"
                          value={emailRecipient}
                          onChange={(e) => setEmailRecipient(e.target.value)}
                          placeholder="email@example.com"
                          InputProps={{
                            startAdornment: <Email sx={{ mr: 1, color: 'action.active' }} />,
                          }}
                        />
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel>Schedule</InputLabel>
                          <Select
                            value={scheduleTime}
                            onChange={(e) => setScheduleTime(e.target.value as any)}
                            label="Schedule"
                          >
                            <MenuItem value="now">Generate Now</MenuItem>
                            <MenuItem value="daily">Daily</MenuItem>
                            <MenuItem value="weekly">Weekly</MenuItem>
                            <MenuItem value="monthly">Monthly</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      {/* Generate Button */}
                      <Grid item xs={12}>
                        <Box display="flex" justifyContent="flex-end" gap={2}>
                          <Button
                            variant="outlined"
                            onClick={(e: React.MouseEvent) => () => {
                              setSelectedReport(null);
                              setExportFormat('pdf');
                              setSelectedStudent('all');
                              setSelectedClass('all');
                              setSelectedSubjects([]);
                            }}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="contained"
                            startIcon={<Download />}
                            onClick={(e: React.MouseEvent) => handleGenerateReport}
                            disabled={generating}
                          >
                            {generating ? 'Generating...' : 'Generate Report'}
                          </Button>
                        </Box>
                      </Grid>
                    </Grid>
                  </>
                )}

                {generating && <LinearProgress sx={{ mt: 2 }} />}
                {error && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {error}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Reports */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader
                title="Recent Reports"
                action={
                  <IconButton onClick={(e: React.MouseEvent) => loadRecentReports}>
                    <Refresh />
                  </IconButton>
                }
              />
              <CardContent>
                <List>
                  {recentReports.map((report) => (
                    <ListItem key={report.id} divider>
                      <ListItemIcon>{getFormatIcon(report.format)}</ListItemIcon>
                      <ListItemText
                        primary={report.name}
                        secondary={
                          <Stack spacing={0.5}>
                            <Typography variant="caption">
{formatDate(report.generatedAt, 'MMM dd, yyyy HH:mm')}
                            </Typography>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Chip
                                label={report.status}
                                size="small"
                                color={getStatusColor(report.status)}
                              />
                              <Typography variant="caption">{report.size}</Typography>
                            </Stack>
                          </Stack>
                        }
                      />
                      <ListItemSecondaryAction>
                        {report.status === 'ready' && (
                          <Tooltip title="Download">
                            <IconButton onClick={(e: React.MouseEvent) => () => handleDownloadReport(report)}>
                              <Download />
                            </IconButton>
                          </Tooltip>
                        )}
                        {report.status === 'pending' && <CircularProgress size={20} />}
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>

                {recentReports.length === 0 && (
                  <Typography variant="body2" color="text.secondary" align="center">
                    No reports generated yet
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
};

export default ReportGenerator;