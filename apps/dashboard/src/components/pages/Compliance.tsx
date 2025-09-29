import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import * as React from "react";

import { useEffect } from "react";
import { useAppSelector, useAppDispatch } from "../../store";
import {
  fetchComplianceStatus,
  fetchAuditLogs,
  fetchConsentRecords,
  recordConsent,
  revokeConsent,
  runComplianceAudit,
  exportComplianceReport,
  clearError,
} from "../../store/slices/complianceSlice";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`compliance-tabpanel-${index}`}
      aria-labelledby={`compliance-tab-${index}`}
      {...other}
    >
      {value === index && <Box style={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Compliance() {
  const dispatch = useAppDispatch();
  const role = useAppSelector((s) => s.user.role);
  const { 
    status, 
    auditLogs, 
    consentRecords, 
    pendingConsents, 
    overallScore, 
    loading, 
    error, 
    lastChecked 
  } = useAppSelector((s) => s.compliance);
  
  const [activeTab, setActiveTab] = React.useState(0);
  const [consentDialogOpen, setConsentDialogOpen] = React.useState(false);
  const [auditDialogOpen, setAuditDialogOpen] = React.useState(false);
  const [selectedRegulation, setSelectedRegulation] = React.useState<string>("");
  const [consentFormData, setConsentFormData] = React.useState({
    studentId: "",
    parentName: "",
    parentEmail: "",
    consentType: "coppa" as "coppa" | "ferpa" | "gdpr",
  });

  // Fetch compliance data on mount
  useEffect(() => {
    dispatch(fetchComplianceStatus());
    dispatch(fetchAuditLogs());
    dispatch(fetchConsentRecords());
  }, [dispatch]);

  // Auto-refresh compliance status every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      dispatch(fetchComplianceStatus());
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [dispatch]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRefresh = () => {
    dispatch(fetchComplianceStatus());
    dispatch(fetchAuditLogs());
    dispatch(fetchConsentRecords());
  };

  const handleRecordConsent = async () => {
    const { studentId, consentType } = consentFormData;
    await dispatch(recordConsent({ 
      type: consentType, 
      userId: studentId,
      signature: "digital_signature_placeholder"
    }));
    setConsentDialogOpen(false);
    setConsentFormData({
      studentId: "",
      parentName: "",
      parentEmail: "",
      consentType: "coppa",
    });
  };

  const handleRevokeConsent = async (consentId: string) => {
    if (window.confirm("Are you sure you want to revoke this consent?")) {
      await dispatch(revokeConsent(consentId));
    }
  };

  const handleRunAudit = async () => {
    const regulation = selectedRegulation || "all";
    await dispatch(runComplianceAudit(regulation as any));
    setAuditDialogOpen(false);
  };

  const handleExportReport = async (format: "pdf" | "csv" | "json") => {
    const result = await dispatch(exportComplianceReport(format));
    if (exportComplianceReport.fulfilled.match(result)) {
      // Download the file
      window.open(result.payload.url, "_blank");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "compliant":
        return <IconCircleCheck color="green" />;
      case "warning":
        return <IconAlertTriangle color="yellow" />;
      case "violation":
        return <IconCircleX color="red" />;
      default:
        return <IconInfoCircle color="cyan" />;
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

  const getScoreColor = (score: number) => {
    if (score >= 90) return "success.main";
    if (score >= 70) return "warning.main";
    return "error.main";
  };

  return (
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
            >
              <Stack direction="row" alignItems="center" spacing={2}>
                <SecurityIcon style={{ fontSize: 32, color: "primary.main" }} />
                <Box>
                  <Typography order={5} style={{ fontWeight: 600 }}>
                    Compliance Dashboard
                  </Typography>
                  <Typography size="sm" color="text.secondary">
                    Last checked: {lastChecked ? new Date(lastChecked).toLocaleString() : "Never"}
                  </Typography>
                </Box>
              </Stack>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outline"
                  startIcon={<IconRefresh />}
                  onClick={(e: React.MouseEvent) => handleRefresh}
                  disabled={loading}
                >
                  Refresh
                </Button>
                {role === "admin" && (
                  <>
                    <Button
                      variant="outline"
                      startIcon={<AssignmentTurnedInIcon />}
                      onClick={(e: React.MouseEvent) => () => setAuditDialogOpen(true)}
                    >
                      Run Audit
                    </Button>
                    <Button
                      variant="filled"
                      startIcon={<FileIconDownload />}
                      onClick={(e: React.MouseEvent) => () => handleExportReport("pdf")}
                    >
                      Export Report
                    </Button>
                  </>
                )}
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Overall Score Card */}
      <Grid2 xs={12} md={4}>
        <Card>
          <CardContent>
            <Stack alignItems="center" spacing={2}>
              <Typography order={6} color="text.secondary">
                Overall Compliance Score
              </Typography>
              <Box position="relative" display="inline-flex">
                <CircularProgress
                  variant="determinate"
                  value={overallScore}
                  size={120}
                  thickness={4}
                  style={{ color: getScoreColor(overallScore) }}
                />
                <Box
                  top={0}
                  left={0}
                  bottom={0}
                  right={0}
                  position="absolute"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  <Typography order={3} component="div" color="text.primary">
                    {overallScore}%
                  </Typography>
                </Box>
              </Box>
              <Chip
                label={overallScore >= 90 ? "Excellent" : overallScore >= 70 ? "Good" : "Needs Improvement"}
                color={overallScore >= 90 ? "success" : overallScore >= 70 ? "warning" : "error"}
              />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Pending Actions Card */}
      <Grid2 xs={12} md={4}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography order={6} color="text.secondary">
                Pending Actions
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <FamilyRestroomIcon color="yellow" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Parent Consents"
                    secondary={`${pendingConsents} pending`}
                  />
                  {pendingConsents > 0 && (
                    <Button size="small" onClick={(e: React.MouseEvent) => () => setConsentDialogOpen(true)}>
                      Review
                    </Button>
                  )}
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <PolicyIcon color="cyan" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Policy Updates"
                    secondary="0 required"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <IconAlertTriangle color="red" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Compliance Issues"
                    secondary={`${pendingConsents} to resolve`}
                  />
                </ListItem>
              </List>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Quick Actions Card */}
      <Grid2 xs={12} md={4}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography order={6} color="text.secondary">
                Quick Actions
              </Typography>
              <Stack spacing={1}>
                <Button
                  fullWidth
                  variant="outline"
                  startIcon={<IconUser />}
                  onClick={(e: React.MouseEvent) => () => setConsentDialogOpen(true)}
                >
                  Record Consent
                </Button>
                <Button
                  fullWidth
                  variant="outline"
                  startIcon={<FileIconDownload />}
                  onClick={(e: React.MouseEvent) => () => handleExportReport("csv")}
                >
                  Download Data
                </Button>
                <Button
                  fullWidth
                  variant="outline"
                  startIcon={<IconSettings />}
                  onClick={(e: React.MouseEvent) => () => setActiveTab(3)}
                >
                  Settings
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Compliance Status Cards */}
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Typography order={6} style={{ mb: 2 }}>
              Regulatory Compliance
            </Typography>
            <Grid2 container spacing={2}>
              {status && Object.entries(status)
                .filter(([key]) => ['coppa', 'ferpa', 'gdpr'].includes(key))
                .map(([regulation, data]) => (
                <Grid2 key={regulation} xs={12} sm={6} md={3}>
                  <Card variant="outline">
                    <CardContent>
                      <Stack spacing={1}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography order={6}>
                            {regulation.toUpperCase()}
                          </Typography>
                          {getStatusIcon(data.status)}
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={data.score}
                          color={getStatusColor(data.status) as any}
                          style={{ height: 8, borderRadius: 1 }}
                        />
                        <Stack direction="row" justifyContent="space-between">
                          <Typography size="sm" color="text.secondary">
                            Score: {data.score}%
                          </Typography>
                          <Chip
                            label={data.status}
                            size="small"
                            color={getStatusColor(data.status) as any}
                          />
                        </Stack>
                        {data.issues.length > 0 && (
                          <Alert severity="warning" style={{ py: 0.5 }}>
                            <AlertTitle style={{ fontSize: "0.875rem", mb: 0 }}>
                              {data.issues.length} Issues
                            </AlertTitle>
                          </Alert>
                        )}
                        <Typography variant="caption" color="text.secondary">
                          Last audit: {new Date(data.lastAudit).toLocaleDateString()}
                        </Typography>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid2>
              ))}
              {loading && !status && (
                [...Array(4)].map((_, i) => (
                  <Grid2 key={i} xs={12} sm={6} md={3}>
                    <Skeleton variant="rectangular" height={200} />
                  </Grid2>
                ))
              )}
            </Grid2>
          </CardContent>
        </Card>
      </Grid2>

      {/* Tabbed Content */}
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Box style={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Audit Logs" />
                <Tab label="Consent Records" />
                <Tab label="Data Retention" />
                <Tab label="Settings" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <TableContainer component={Paper} variant="outline">
                <Table size="small">
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
                      <TableRow key={log.id}>
                        <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                        <TableCell>{log.action}</TableCell>
                        <TableCell>{log.userEmail}</TableCell>
                        <TableCell>
                          <Chip label={log.regulation} size="small" />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={log.status}
                            size="small"
                            color={log.status === "Approved" ? "success" : "default"}
                          />
                        </TableCell>
                        <TableCell>{log.details}</TableCell>
                      </TableRow>
                    ))}
                    {auditLogs.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          No audit logs available
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <TableContainer component={Paper} variant="outline">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Student</TableCell>
                      <TableCell>Parent</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Date Provided</TableCell>
                      <TableCell>Expiry Date</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {consentRecords.map((consent) => (
                      <TableRow key={consent.id}>
                        <TableCell>{consent.studentName}</TableCell>
                        <TableCell>{consent.parentName || "N/A"}</TableCell>
                        <TableCell>
                          <Chip label={consent.consentType.toUpperCase()} size="small" />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={consent.status}
                            size="small"
                            color={
                              consent.status === "active"
                                ? "success"
                                : consent.status === "expired"
                                ? "warning"
                                : "error"
                            }
                          />
                        </TableCell>
                        <TableCell>{new Date(consent.dateProvided).toLocaleDateString()}</TableCell>
                        <TableCell>
                          {consent.expiryDate
                            ? new Date(consent.expiryDate).toLocaleDateString()
                            : "N/A"}
                        </TableCell>
                        <TableCell>
                          {consent.status === "active" && (
                            <IconButton
                              size="small"
                              onClick={(e: React.MouseEvent) => () => handleRevokeConsent(consent.id)}
                            >
                              <IconCircleX fontSize="small" />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {consentRecords.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} align="center">
                          No consent records available
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Stack spacing={2}>
                <Alert severity="info">
                  <AlertTitle>Data Retention Policy</AlertTitle>
                  All student data is retained according to regulatory requirements.
                  Data is automatically purged after the retention period expires.
                </Alert>
                <TableContainer component={Paper} variant="outline">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Data Type</TableCell>
                        <TableCell>Retention Period</TableCell>
                        <TableCell>Next Purge</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Student Records</TableCell>
                        <TableCell>5 years</TableCell>
                        <TableCell>2029-01-01</TableCell>
                        <TableCell>
                          <Chip label="Active" size="small" color="green" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Assessment Data</TableCell>
                        <TableCell>3 years</TableCell>
                        <TableCell>2027-01-01</TableCell>
                        <TableCell>
                          <Chip label="Active" size="small" color="green" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Activity Logs</TableCell>
                        <TableCell>1 year</TableCell>
                        <TableCell>2025-01-01</TableCell>
                        <TableCell>
                          <Chip label="Active" size="small" color="green" />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Stack>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Stack spacing={3}>
                <Alert severity="warning">
                  <AlertTitle>Settings</AlertTitle>
                  Changes to compliance settings require administrator approval.
                </Alert>
                <FormControl fullWidth>
                  <InputLabel>Auto-Audit Frequency</InputLabel>
                  <Select value="monthly" label="Auto-Audit Frequency">
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                    <MenuItem value="quarterly">Quarterly</MenuItem>
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Data Retention Period</InputLabel>
                  <Select value="5years" label="Data Retention Period">
                    <MenuItem value="1year">1 Year</MenuItem>
                    <MenuItem value="3years">3 Years</MenuItem>
                    <MenuItem value="5years">5 Years</MenuItem>
                    <MenuItem value="7years">7 Years</MenuItem>
                  </Select>
                </FormControl>
                <Stack direction="row" spacing={2}>
                  <Button variant="filled" disabled>
                    Save Settings
                  </Button>
                  <Button variant="outline">Cancel</Button>
                </Stack>
              </Stack>
            </TabPanel>
          </CardContent>
        </Card>
      </Grid2>

      {/* Record Consent Dialog */}
      <Dialog open={consentDialogOpen} onClose={() => setConsentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Record Parent Consent</DialogTitle>
        <DialogContent>
          <Stack spacing={2} style={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Student ID"
              value={consentFormData.studentId}
              onChange={(e) => setConsentFormData({ ...consentFormData, studentId: e.target.value })}
            />
            <TextField
              fullWidth
              label="Parent Name"
              value={consentFormData.parentName}
              onChange={(e) => setConsentFormData({ ...consentFormData, parentName: e.target.value })}
            />
            <TextField
              fullWidth
              label="Parent Email"
              type="email"
              value={consentFormData.parentEmail}
              onChange={(e) => setConsentFormData({ ...consentFormData, parentEmail: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Consent Type</InputLabel>
              <Select
                value={consentFormData.consentType}
                label="Consent Type"
                onChange={(e) => setConsentFormData({ ...consentFormData, consentType: e.target.value as any })}
              >
                <MenuItem value="coppa">COPPA</MenuItem>
                <MenuItem value="ferpa">FERPA</MenuItem>
                <MenuItem value="gdpr">GDPR</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setConsentDialogOpen(false)}>Cancel</Button>
          <Button variant="filled" onClick={(e: React.MouseEvent) => handleRecordConsent}>
            Record Consent
          </Button>
        </DialogActions>
      </Dialog>

      {/* Run Audit Dialog */}
      <Dialog open={auditDialogOpen} onClose={() => setAuditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Compliance Audit</DialogTitle>
        <DialogContent>
          <Stack spacing={2} style={{ mt: 2 }}>
            <Alert severity="info">
              Running an audit will check all compliance requirements and update the status.
            </Alert>
            <FormControl fullWidth>
              <InputLabel>Regulation</InputLabel>
              <Select
                value={selectedRegulation}
                label="Regulation"
                onChange={(e) => setSelectedRegulation(e.target.value)}
              >
                <MenuItem value="">All Regulations</MenuItem>
                <MenuItem value="coppa">COPPA</MenuItem>
                <MenuItem value="ferpa">FERPA</MenuItem>
                <MenuItem value="gdpr">GDPR</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setAuditDialogOpen(false)}>Cancel</Button>
          <Button variant="filled" onClick={(e: React.MouseEvent) => handleRunAudit} startIcon={<AssignmentTurnedInIcon />}>
            Run Audit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Error Alert */}
      {error && (
        <Grid2 xs={12}>
          <Alert severity="error" onClose={() => dispatch(clearError())}>
            {error}
          </Alert>
        </Grid2>
      )}
    </Grid2>
  );
}
