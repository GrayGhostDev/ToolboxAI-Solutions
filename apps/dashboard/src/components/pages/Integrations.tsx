import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import * as React from "react";

import { useAppSelector } from "../../store";

interface Integration {
  id: string;
  name: string;
  type: "lms" | "gaming" | "cloud" | "analytics" | "communication";
  icon: React.ReactNode;
  status: "connected" | "disconnected" | "error" | "syncing";
  description: string;
  lastSync?: string;
  features: string[];
  apiKey?: string;
  webhookUrl?: string;
  permissions: string[];
}

interface ApiEndpoint {
  id: string;
  name: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  endpoint: string;
  description: string;
  status: "active" | "inactive" | "error";
  lastCall?: string;
  callCount: number;
}

export default function Integrations() {
  const [selectedIntegration, setSelectedIntegration] = React.useState<Integration | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = React.useState(false);
  const [apiDialogOpen, setApiDialogOpen] = React.useState(false);

  const integrations: Integration[] = [
    {
      id: "roblox",
      name: "Roblox Studio",
      type: "gaming",
      icon: <SportsEsportsIcon style={{ color: "#E74C3C" }} />,
      status: "connected",
      description: "Direct integration with Roblox for educational experiences",
      lastSync: "2024-01-29 10:30:00",
      features: ["Experience Publishing", "Player Analytics", "Asset Management", "Badge System"],
      permissions: ["read", "write", "publish"],
    },
    {
      id: "google-classroom",
      name: "Google Classroom",
      type: "lms",
      icon: <IconSchool style={{ color: "#4285F4" }} />,
      status: "connected",
      description: "Sync with Google Classroom for assignments and grades",
      lastSync: "2024-01-29 09:15:00",
      features: ["Assignment Sync", "Grade Import", "Class Roster", "Calendar Integration"],
      permissions: ["read", "write"],
    },
    {
      id: "canvas",
      name: "Canvas LMS",
      type: "lms",
      icon: <IconSchool style={{ color: "#E74C3C" }} />,
      status: "disconnected",
      description: "Integration with Canvas Learning Management System",
      features: ["Course Management", "Grade Book", "Assignment Submission", "Discussion Forums"],
      permissions: [],
    },
    {
      id: "microsoft-teams",
      name: "Microsoft Teams",
      type: "communication",
      icon: <CloudSyncIcon style={{ color: "#5059C9" }} />,
      status: "syncing",
      description: "Collaborate through Microsoft Teams for Education",
      lastSync: "2024-01-29 11:00:00",
      features: ["Video Classes", "Chat Integration", "File Sharing", "Assignment Distribution"],
      permissions: ["read", "write", "meetings"],
    },
    {
      id: "google-drive",
      name: "Google Drive",
      type: "cloud",
      icon: <StorageIcon style={{ color: "#0F9D58" }} />,
      status: "connected",
      description: "Store and share educational content via Google Drive",
      lastSync: "2024-01-29 08:45:00",
      features: ["File Storage", "Document Sharing", "Collaborative Editing", "Backup"],
      permissions: ["read", "write", "share"],
    },
    {
      id: "kahoot",
      name: "Kahoot!",
      type: "gaming",
      icon: <SportsEsportsIcon style={{ color: "#46178F" }} />,
      status: "error",
      description: "Create and play learning games with Kahoot!",
      features: ["Quiz Creation", "Live Games", "Reports", "Student Engagement"],
      permissions: [],
    },
  ];

  const apiEndpoints: ApiEndpoint[] = [
    {
      id: "1",
      name: "Get Student Progress",
      method: "GET",
      endpoint: "/api/v1/students/{id}/progress",
      description: "Retrieve student progress and achievements",
      status: "active",
      lastCall: "2024-01-29 11:30:00",
      callCount: 1547,
    },
    {
      id: "2",
      name: "Submit Assignment",
      method: "POST",
      endpoint: "/api/v1/assignments/submit",
      description: "Submit student assignments",
      status: "active",
      lastCall: "2024-01-29 11:28:00",
      callCount: 892,
    },
    {
      id: "3",
      name: "Update Grades",
      method: "PUT",
      endpoint: "/api/v1/grades/{id}",
      description: "Update student grades",
      status: "active",
      lastCall: "2024-01-29 10:15:00",
      callCount: 456,
    },
    {
      id: "4",
      name: "Sync Roblox Data",
      method: "POST",
      endpoint: "/api/v1/roblox/sync",
      description: "Synchronize data with Roblox platform",
      status: "error",
      lastCall: "2024-01-29 09:00:00",
      callCount: 78,
    },
  ];


  const getStatusChip = (status: string) => {
    const statusConfig = {
      connected: { label: "Connected", color: "success" as const },
      disconnected: { label: "Disconnected", color: "default" as const },
      error: { label: "Error", color: "error" as const },
      syncing: { label: "Syncing", color: "info" as const },
      active: { label: "Active", color: "success" as const },
      inactive: { label: "Inactive", color: "default" as const },
    };
    const config = statusConfig[status as keyof typeof statusConfig];
    return <Chip label={config?.label || status} size="small" color={config?.color || "default"} />;
  };

  const handleConnect = (integration: Integration) => {
    setSelectedIntegration(integration);
    setConfigDialogOpen(true);
  };

  const handleDisconnect = (integration: Integration) => {
    console.log("Disconnecting:", integration.name);
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
              <Stack direction="row" alignItems="center" gap={2}>
                <IntegrationInstructionsIcon style={{ fontSize: 32, color: "primary.main" }} />
                <div>
                  <Typography order={5} style={{ fontWeight: 600 }}>
                    Platform Integrations
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Connect with learning management systems and external platforms
                  </Typography>
                </div>
              </Stack>
              <Stack direction="row" gap={2}>
                <Button variant="outline" startIcon={<ApiIcon />} onClick={(e: React.MouseEvent) => () => setApiDialogOpen(true)}>
                  API Docs
                </Button>
                <Button variant="filled" startIcon={<IconPlus />}>
                  Add Integration
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Stats Cards */}
      <Grid2 xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Active Integrations
              </Typography>
              <Typography order={4} style={{ fontWeight: 700 }}>
                {integrations.filter(i => i.status === "connected").length}
              </Typography>
              <Typography variant="caption" color="success.main">
                {integrations.length} total available
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
                API Calls Today
              </Typography>
              <Typography order={4} style={{ fontWeight: 700 }}>
                {apiEndpoints.reduce((sum, api) => sum + api.callCount, 0).toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Across {apiEndpoints.length} endpoints
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
                Data Synced
              </Typography>
              <Typography order={4} style={{ fontWeight: 700 }}>
                245 GB
              </Typography>
              <Typography variant="caption" color="text.secondary">
                This month
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
                System Health
              </Typography>
              <Typography order={4} style={{ fontWeight: 700, color: "success.main" }}>
                98.5%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Uptime last 30 days
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Roblox Integration Highlight */}
      <Grid2 xs={12}>
        <Alert severity="success" icon={<SportsEsportsIcon />}>
          <AlertTitle>Roblox Integration Active</AlertTitle>
          Your educational experiences are syncing with Roblox. Last sync: 5 minutes ago. 
          <Button 
            size="small" 
            style={{ ml: 2 }}
            onClick={(e: React.MouseEvent) => () => {
              const robloxIntegration = integrations.find(i => i.id === "roblox");
              if (robloxIntegration) {
                setSelectedIntegration(robloxIntegration);
                setApiDialogOpen(true);
              }
            }}
          >
            View Details
          </Button>
        </Alert>
      </Grid2>

      {/* Integration Cards */}
      <Grid2 xs={12}>
        <Typography order={6} style={{ fontWeight: 600, mb: 2 }}>
          Available Integrations
        </Typography>
        <Grid2 container spacing={2}>
          {integrations.map((integration) => (
            <Grid2 key={integration.id} xs={12} md={6} lg={4}>
              <Card style={{
                height: "100%",
                opacity: integration.status === "disconnected" ? 0.7 : 1,
                transition: "all 0.3s",
                "&:hover": {
                  transform: integration.status !== "disconnected" ? "translateY(-4px)" : "none",
                  boxShadow: integration.status !== "disconnected" ? 4 : 1,
                },
              }}>
                <CardContent>
                  <Stack spacing={2}>
                    {/* Header */}
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Stack direction="row" alignItems="center" gap={1}>
                        {integration.icon}
                        <div>
                          <Typography order={6} style={{ fontWeight: 600 }}>
                            {integration.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {integration.type}
                          </Typography>
                        </div>
                      </Stack>
                      {getStatusChip(integration.status)}
                    </Stack>

                    {/* Description */}
                    <Typography size="sm" color="text.secondary">
                      {integration.description}
                    </Typography>

                    {/* Features */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" style={{ mb: 1 }}>
                        Features:
                      </Typography>
                      <Stack direction="row" flexWrap="wrap" gap={0.5}>
                        {integration.features.map((feature, idx) => (
                          <Chip key={idx} label={feature} size="small" variant="outline" />
                        ))}
                      </Stack>
                    </Box>

                    {/* Status Info */}
                    {integration.lastSync && (
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="caption" color="text.secondary">
                          Last sync: {new Date(integration.lastSync).toLocaleString()}
                        </Typography>
                        {integration.status === "syncing" && (
                          <LinearProgress style={{ width: 100, height: 4, borderRadius: 2 }} />
                        )}
                      </Stack>
                    )}

                    {/* Actions */}
                    <Stack direction="row" gap={1}>
                      {integration.status === "disconnected" ? (
                        <Button
                          variant="filled"
                          fullWidth
                          onClick={(e: React.MouseEvent) => () => handleConnect(integration)}
                        >
                          Connect
                        </Button>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            startIcon={<IconSettings />}
                            style={{ flex: 1 }}
                            onClick={(e: React.MouseEvent) => () => handleConnect(integration)}
                          >
                            Configure
                          </Button>
                          <Button
                            variant="outline"
                            color="red"
                            onClick={(e: React.MouseEvent) => () => handleDisconnect(integration)}
                          >
                            Disconnect
                          </Button>
                        </>
                      )}
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>
          ))}
        </Grid2>
      </Grid2>

      {/* API Endpoints */}
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography order={6} style={{ fontWeight: 600 }}>
                API Endpoints
              </Typography>
              <Button variant="outline" startIcon={<CodeIcon />}>
                Generate API Key
              </Button>
            </Stack>
            <List>
              {apiEndpoints.map((endpoint) => (
                <ListItem key={endpoint.id} divider>
                  <ListItemIcon>
                    <Chip
                      label={endpoint.method}
                      size="small"
                      color={
                        endpoint.method === "GET" ? "info" :
                        endpoint.method === "POST" ? "success" :
                        endpoint.method === "PUT" ? "warning" : "error"
                      }
                      style={{ minWidth: 60 }}
                    />
                  </ListItemIcon>
                  <ListItemText
                    primaryTypographyProps={{ component: 'div' }}
                    secondaryTypographyProps={{ component: 'div' }}
                    primary={
                      <Stack direction="row" alignItems="center" gap={1}>
                        <Typography size="sm" style={{ fontWeight: 600 }}>
                          {endpoint.name}
                        </Typography>
                        {getStatusChip(endpoint.status)}
                      </Stack>
                    }
                    secondary={
                      <Stack>
                        <Typography variant="caption" style={{ fontFamily: "monospace" }}>
                          {endpoint.endpoint}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {endpoint.description} • {endpoint.callCount} calls
                          {endpoint.lastCall && ` • Last: ${new Date(endpoint.lastCall).toLocaleTimeString()}`}
                        </Typography>
                      </Stack>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton size="small">
                      <IconEye />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid2>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Configure {selectedIntegration?.name}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} style={{ mt: 2 }}>
            <TextField
              fullWidth
              label="API Key"
              type="password"
              defaultValue={selectedIntegration?.apiKey}
              helperText="Enter your API key for this integration"
            />
            <TextField
              fullWidth
              label="Webhook URL"
              defaultValue={selectedIntegration?.webhookUrl}
              helperText="Optional: Webhook for real-time updates"
            />
            <Box>
              <Typography variant="subtitle2" style={{ mb: 1 }}>
                Permissions
              </Typography>
              <FormGroup>
                <FormControlLabel control={<Checkbox defaultChecked />} label="Read data" />
                <FormControlLabel control={<Checkbox defaultChecked />} label="Write data" />
                <FormControlLabel control={<Checkbox />} label="Delete data" />
                <FormControlLabel control={<Checkbox defaultChecked />} label="Real-time sync" />
              </FormGroup>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="filled" onClick={(e: React.MouseEvent) => () => setConfigDialogOpen(false)}>
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>

      {/* API Documentation Dialog */}
      <Dialog open={apiDialogOpen} onClose={() => setApiDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          API Documentation
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" style={{ mb: 2 }}>
            <AlertTitle>API Base URL</AlertTitle>
            https://api.educationalplatform.com/v1
          </Alert>
          <Typography size="sm" paragraph>
            Use your API key in the Authorization header: Bearer YOUR_API_KEY
          </Typography>
          <Typography size="sm" paragraph>
            Rate limit: 1000 requests per hour
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setApiDialogOpen(false)}>Close</Button>
          <Button variant="filled" startIcon={<FileDownload />}>
            Download Full Documentation
          </Button>
        </DialogActions>
      </Dialog>
    </Grid2>
  );
}