import * as React from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Chip,
  LinearProgress,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tab,
  Tabs,
  Paper,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import InfoIcon from "@mui/icons-material/Info";
import SecurityIcon from "@mui/icons-material/Security";
import VerifiedUserIcon from "@mui/icons-material/VerifiedUser";
import PolicyIcon from "@mui/icons-material/Policy";
import GavelIcon from "@mui/icons-material/Gavel";
import AssignmentTurnedInIcon from "@mui/icons-material/AssignmentTurnedIn";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import RefreshIcon from "@mui/icons-material/Refresh";
import SettingsIcon from "@mui/icons-material/Settings";
import PersonIcon from "@mui/icons-material/Person";
import SchoolIcon from "@mui/icons-material/School";
import FamilyRestroomIcon from "@mui/icons-material/FamilyRestroom";
import { useAppSelector } from "../../store";

interface ComplianceItem {
  id: string;
  regulation: string;
  status: "compliant" | "warning" | "violation";
  score: number;
  lastAudit: string;
  nextAudit: string;
  issues: number;
  details: string;
}

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  user: string;
  regulation: string;
  status: string;
  details: string;
}

interface ConsentRecord {
  id: string;
  studentName: string;
  parentName: string;
  dateProvided: string;
  type: string;
  status: "active" | "expired" | "revoked";
  expiryDate: string;
}

export default function Compliance() {
  const role = useAppSelector((s) => s.user.role);
  const [activeTab, setActiveTab] = React.useState(0);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [selectedItem, setSelectedItem] = React.useState<ComplianceItem | null>(null);

  const complianceData: ComplianceItem[] = [
    {
      id: "coppa",
      regulation: "COPPA",
      status: "compliant",
      score: 95,
      lastAudit: "2024-01-15",
      nextAudit: "2024-02-15",
      issues: 0,
      details: "Children's Online Privacy Protection Act compliance",
    },
    {
      id: "ferpa",
      regulation: "FERPA",
      status: "compliant",
      score: 92,
      lastAudit: "2024-01-10",
      nextAudit: "2024-02-10",
      issues: 2,
      details: "Family Educational Rights and Privacy Act compliance",
    },
    {
      id: "gdpr",
      regulation: "GDPR",
      status: "warning",
      score: 78,
      lastAudit: "2024-01-08",
      nextAudit: "2024-02-08",
      issues: 5,
      details: "General Data Protection Regulation compliance",
    },
    {
      id: "ccpa",
      regulation: "CCPA",
      status: "compliant",
      score: 88,
      lastAudit: "2024-01-12",
      nextAudit: "2024-02-12",
      issues: 1,
      details: "California Consumer Privacy Act compliance",
    },
  ];

  const auditLogs: AuditLog[] = [
    {
      id: "1",
      timestamp: "2024-01-29 10:30:00",
      action: "Data Access",
      user: "admin@school.edu",
      regulation: "FERPA",
      status: "Approved",
      details: "Accessed student records for report generation",
    },
    {
      id: "2",
      timestamp: "2024-01-29 09:15:00",
      action: "Consent Updated",
      user: "parent@email.com",
      regulation: "COPPA",
      status: "Completed",
      details: "Parental consent renewed for data processing",
    },
    {
      id: "3",
      timestamp: "2024-01-28 16:45:00",
      action: "Data Export",
      user: "teacher@school.edu",
      regulation: "GDPR",
      status: "Pending Review",
      details: "Student data export request under review",
    },
    {
      id: "4",
      timestamp: "2024-01-28 14:20:00",
      action: "Privacy Policy Update",
      user: "legal@school.edu",
      regulation: "All",
      status: "Published",
      details: "Updated privacy policy to version 2.3",
    },
    {
      id: "5",
      timestamp: "2024-01-28 11:00:00",
      action: "Data Deletion",
      user: "admin@school.edu",
      regulation: "GDPR",
      status: "Completed",
      details: "Removed inactive student data per retention policy",
    },
  ];

  const consentRecords: ConsentRecord[] = [
    {
      id: "1",
      studentName: "Alex Johnson",
      parentName: "Sarah Johnson",
      dateProvided: "2024-01-01",
      type: "Data Processing",
      status: "active",
      expiryDate: "2025-01-01",
    },
    {
      id: "2",
      studentName: "Emma Davis",
      parentName: "Michael Davis",
      dateProvided: "2023-12-15",
      type: "Marketing Communications",
      status: "active",
      expiryDate: "2024-12-15",
    },
    {
      id: "3",
      studentName: "James Wilson",
      parentName: "Lisa Wilson",
      dateProvided: "2023-11-20",
      type: "Third-Party Sharing",
      status: "expired",
      expiryDate: "2024-01-20",
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "compliant":
        return <CheckCircleIcon sx={{ color: "success.main" }} />;
      case "warning":
        return <WarningIcon sx={{ color: "warning.main" }} />;
      case "violation":
        return <ErrorIcon sx={{ color: "error.main" }} />;
      default:
        return <InfoIcon sx={{ color: "info.main" }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "compliant":
        return "success";
      case "warning":
        return "warning";
      case "violation":
        return "error";
      default:
        return "default";
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleItemClick = (item: ComplianceItem) => {
    setSelectedItem(item);
    setDialogOpen(true);
  };

  const overallScore = Math.round(
    complianceData.reduce((sum, item) => sum + item.score, 0) / complianceData.length
  );

  return (
    <Grid2 container spacing={3}>
      {/* Header */}
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Stack direction="row" alignItems="center" gap={2}>
                <SecurityIcon sx={{ fontSize: 32, color: "primary.main" }} />
                <div>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    Compliance Dashboard
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Regulatory compliance monitoring and management
                  </Typography>
                </div>
              </Stack>
              <Stack direction="row" gap={2}>
                <Button variant="outlined" startIcon={<RefreshIcon />}>
                  Refresh
                </Button>
                <Button variant="contained" startIcon={<FileDownloadIcon />}>
                  Export Report
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Overall Compliance Score */}
      <Grid2 size={{ xs: 12, md: 4 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent>
            <Stack alignItems="center" spacing={2}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Overall Compliance Score
              </Typography>
              <Box sx={{ position: "relative", display: "inline-flex" }}>
                <Box
                  sx={{
                    width: 120,
                    height: 120,
                    borderRadius: "50%",
                    border: `8px solid`,
                    borderColor: overallScore >= 90 ? "success.main" : overallScore >= 70 ? "warning.main" : "error.main",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {overallScore}%
                  </Typography>
                </Box>
              </Box>
              <Chip
                label={overallScore >= 90 ? "Excellent" : overallScore >= 70 ? "Good" : "Needs Attention"}
                color={overallScore >= 90 ? "success" : overallScore >= 70 ? "warning" : "error"}
                sx={{ fontWeight: 600 }}
              />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Active Issues */}
      <Grid2 size={{ xs: 12, md: 4 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Active Issues
            </Typography>
            <Stack spacing={2}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="text.secondary">
                  Critical
                </Typography>
                <Chip label="0" color="error" size="small" />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="text.secondary">
                  Warning
                </Typography>
                <Chip label="5" color="warning" size="small" />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="text.secondary">
                  Minor
                </Typography>
                <Chip label="3" color="info" size="small" />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="text.secondary">
                  Total
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  8
                </Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Upcoming Audits */}
      <Grid2 size={{ xs: 12, md: 4 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Upcoming Audits
            </Typography>
            <Stack spacing={1}>
              {complianceData.map((item) => (
                <Stack key={item.id} direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">{item.regulation}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(item.nextAudit).toLocaleDateString()}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Compliance Status Cards */}
      <Grid2 size={12}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
          Regulatory Compliance Status
        </Typography>
        <Grid2 container spacing={2}>
          {complianceData.map((item) => (
            <Grid2 key={item.id} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card
                sx={{
                  cursor: "pointer",
                  transition: "all 0.3s",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: 4,
                  },
                }}
                onClick={() => handleItemClick(item)}
              >
                <CardContent>
                  <Stack spacing={2}>
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Stack direction="row" alignItems="center" gap={1}>
                        {getStatusIcon(item.status)}
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {item.regulation}
                        </Typography>
                      </Stack>
                      <Chip
                        label={item.status}
                        size="small"
                        color={getStatusColor(item.status) as any}
                      />
                    </Stack>
                    <Box>
                      <Stack direction="row" justifyContent="space-between" mb={0.5}>
                        <Typography variant="caption" color="text.secondary">
                          Compliance Score
                        </Typography>
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          {item.score}%
                        </Typography>
                      </Stack>
                      <LinearProgress
                        variant="determinate"
                        value={item.score}
                        sx={{ height: 6, borderRadius: 3 }}
                        color={item.score >= 90 ? "success" : item.score >= 70 ? "warning" : "error"}
                      />
                    </Box>
                    <Stack spacing={0.5}>
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="caption" color="text.secondary">
                          Active Issues
                        </Typography>
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          {item.issues}
                        </Typography>
                      </Stack>
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="caption" color="text.secondary">
                          Last Audit
                        </Typography>
                        <Typography variant="caption">
                          {new Date(item.lastAudit).toLocaleDateString()}
                        </Typography>
                      </Stack>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>
          ))}
        </Grid2>
      </Grid2>

      {/* Tabs Section */}
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Tabs value={activeTab} onChange={handleTabChange} aria-label="compliance tabs">
              <Tab label="Audit Trail" />
              <Tab label="Consent Management" />
              <Tab label="Data Retention" />
              <Tab label="Incidents" />
            </Tabs>
            <Box sx={{ mt: 3 }}>
              {/* Audit Trail Tab */}
              {activeTab === 0 && (
                <TableContainer>
                  <Table aria-label="audit trail table">
                    <TableHead>
                      <TableRow>
                        <TableCell>Timestamp</TableCell>
                        <TableCell>Action</TableCell>
                        <TableCell>User</TableCell>
                        <TableCell>Regulation</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Details</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {auditLogs.map((log) => (
                        <TableRow key={log.id} hover>
                          <TableCell>
                            <Typography variant="caption">
                              {new Date(log.timestamp).toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell>{log.action}</TableCell>
                          <TableCell>
                            <Typography variant="caption">{log.user}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={log.regulation} size="small" />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={log.status}
                              size="small"
                              color={
                                log.status === "Approved" || log.status === "Completed"
                                  ? "success"
                                  : log.status === "Pending Review"
                                  ? "warning"
                                  : "default"
                              }
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">{log.details}</Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Consent Management Tab */}
              {activeTab === 1 && (
                <TableContainer>
                  <Table aria-label="consent management table">
                    <TableHead>
                      <TableRow>
                        <TableCell>Student</TableCell>
                        <TableCell>Parent/Guardian</TableCell>
                        <TableCell>Consent Type</TableCell>
                        <TableCell>Date Provided</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Expiry Date</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {consentRecords.map((record) => (
                        <TableRow key={record.id} hover>
                          <TableCell>{record.studentName}</TableCell>
                          <TableCell>{record.parentName}</TableCell>
                          <TableCell>{record.type}</TableCell>
                          <TableCell>
                            {new Date(record.dateProvided).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={record.status}
                              size="small"
                              color={record.status === "active" ? "success" : "error"}
                            />
                          </TableCell>
                          <TableCell>
                            {new Date(record.expiryDate).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Button size="small" variant="outlined">
                              {record.status === "expired" ? "Renew" : "View"}
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Data Retention Tab */}
              {activeTab === 2 && (
                <Stack spacing={3}>
                  <Alert severity="info">
                    <AlertTitle>Data Retention Policy</AlertTitle>
                    Student data is retained for 7 years after graduation. Personal data can be deleted upon request in compliance with GDPR.
                  </Alert>
                  <Grid2 container spacing={2}>
                    <Grid2 size={{ xs: 12, md: 6 }}>
                      <Card variant="outlined">
                        <CardContent>
                          <Stack spacing={2}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                              Active Data
                            </Typography>
                            <Stack spacing={1}>
                              <Stack direction="row" justifyContent="space-between">
                                <Typography variant="body2">Student Records</Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>2,845</Typography>
                              </Stack>
                              <Stack direction="row" justifyContent="space-between">
                                <Typography variant="body2">Parent Accounts</Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>2,102</Typography>
                              </Stack>
                              <Stack direction="row" justifyContent="space-between">
                                <Typography variant="body2">Teacher Accounts</Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>156</Typography>
                              </Stack>
                            </Stack>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid2>
                    <Grid2 size={{ xs: 12, md: 6 }}>
                      <Card variant="outlined">
                        <CardContent>
                          <Stack spacing={2}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                              Scheduled for Deletion
                            </Typography>
                            <Stack spacing={1}>
                              <Stack direction="row" justifyContent="space-between">
                                <Typography variant="body2">Inactive &gt; 1 year</Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>45</Typography>
                              </Stack>
                              <Stack direction="row" justifyContent="space-between">
                                <Typography variant="body2">Graduated &gt; 7 years</Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>128</Typography>
                              </Stack>
                              <Stack direction="row" justifyContent="space-between">
                                <Typography variant="body2">Deletion Requests</Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>8</Typography>
                              </Stack>
                            </Stack>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid2>
                  </Grid2>
                </Stack>
              )}

              {/* Incidents Tab */}
              {activeTab === 3 && (
                <Stack spacing={3}>
                  <Alert severity="warning">
                    <AlertTitle>Recent Incident</AlertTitle>
                    Unauthorized access attempt detected on 2024-01-28. Investigation in progress.
                  </Alert>
                  <List>
                    <ListItem>
                      <ListItemIcon>
                        <WarningIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Unauthorized Access Attempt"
                        secondary="2024-01-28 - Failed login attempts from unknown IP"
                      />
                      <Button size="small" variant="outlined">View Details</Button>
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <InfoIcon color="info" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Data Export Request"
                        secondary="2024-01-25 - Large data export request flagged for review"
                      />
                      <Button size="small" variant="outlined">Review</Button>
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Resolved: Policy Violation"
                        secondary="2024-01-20 - Improper data sharing resolved"
                      />
                      <Button size="small" variant="outlined">View Report</Button>
                    </ListItem>
                  </List>
                </Stack>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid2>

      {/* Compliance Details Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedItem?.regulation} Compliance Details
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Stack spacing={2} sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                {selectedItem.details}
              </Typography>
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Status:</Typography>
                  <Chip
                    label={selectedItem.status}
                    size="small"
                    color={getStatusColor(selectedItem.status) as any}
                  />
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Compliance Score:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {selectedItem.score}%
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Active Issues:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {selectedItem.issues}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Last Audit:</Typography>
                  <Typography variant="body2">
                    {new Date(selectedItem.lastAudit).toLocaleDateString()}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Next Audit:</Typography>
                  <Typography variant="body2">
                    {new Date(selectedItem.nextAudit).toLocaleDateString()}
                  </Typography>
                </Stack>
              </Stack>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<SettingsIcon />}>
            Configure
          </Button>
        </DialogActions>
      </Dialog>
    </Grid2>
  );
}