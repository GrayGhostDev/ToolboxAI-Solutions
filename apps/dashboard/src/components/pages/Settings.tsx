import * as React from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Switch,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  FormGroup,
  Checkbox,
  Radio,
  RadioGroup,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  AlertTitle,
  Box,
  Tabs,
  Tab,
  Avatar,
  Badge,
  Chip,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import NotificationsIcon from "@mui/icons-material/Notifications";
import SecurityIcon from "@mui/icons-material/Security";
import PaletteIcon from "@mui/icons-material/Palette";
import LanguageIcon from "@mui/icons-material/Language";
import AccessibilityIcon from "@mui/icons-material/Accessibility";
import StorageIcon from "@mui/icons-material/Storage";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Save";
import CancelIcon from "@mui/icons-material/Cancel";
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import VpnKeyIcon from "@mui/icons-material/VpnKey";
import EmailIcon from "@mui/icons-material/Email";
import SmartphoneIcon from "@mui/icons-material/Smartphone";
import { useAppSelector, useAppDispatch } from "../../store";
import { setTheme } from "../../store/slices/uiSlice";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Settings() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.user);
  const theme = useAppSelector((s) => s.ui.theme);
  const [activeTab, setActiveTab] = React.useState(0);
  const [editMode, setEditMode] = React.useState(false);
  const [adminSettings, setAdminSettings] = React.useState({
    agentDashboard: {
      teacherAccess: false,
      autoRefreshInterval: 30,
      maxConcurrentTasks: 10,
      enableResourceMonitoring: true,
      enableWorktreeCoordination: true,
    },
    systemLimits: {
      maxAgentsPerType: 5,
      taskQueueSize: 1000,
      enableAutoScaling: false,
      minAgents: 1,
      maxAgents: 10,
    },
  });
  const [profileData, setProfileData] = React.useState({
    displayName: (user as any).displayName || "John Doe",
    email: user.email || "john@example.com",
    phone: "+1 (555) 123-4567",
    bio: "Passionate educator dedicated to innovative learning",
    location: "San Francisco, CA",
    timezone: "PST",
  });

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleSaveProfile = () => {
    setEditMode(false);
    console.log("Saving profile:", profileData);
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
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Settings
              </Typography>
              <Button variant="contained" startIcon={<SaveIcon />}>
                Save All Changes
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Settings Tabs */}
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Tabs value={activeTab} onChange={handleTabChange} aria-label="settings tabs">
              <Tab icon={<AccountCircleIcon />} label="Profile" />
              <Tab icon={<NotificationsIcon />} label="Notifications" />
              <Tab icon={<SecurityIcon />} label="Security" />
              <Tab icon={<PaletteIcon />} label="Appearance" />
              <Tab icon={<LanguageIcon />} label="Language" />
              <Tab icon={<AccessibilityIcon />} label="Accessibility" />
              <Tab icon={<StorageIcon />} label="Data" />
              {user.role === "admin" && <Tab icon={<AdminPanelSettingsIcon />} label="Admin" />}
            </Tabs>

            {/* Profile Tab */}
            <TabPanel value={activeTab} index={0}>
              <Grid2 container spacing={3}>
                <Grid2 xs={12} md={4}>
                  <Stack alignItems="center" spacing={2}>
                    <Badge
                      overlap="circular"
                      anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
                      badgeContent={
                        <IconButton
                          size="small"
                          sx={{
                            bgcolor: "primary.main",
                            color: "white",
                            "&:hover": { bgcolor: "primary.dark" },
                          }}
                        >
                          <PhotoCameraIcon fontSize="small" />
                        </IconButton>
                      }
                    >
                      <Avatar
                        src={(user as any).avatarUrl}
                        sx={{ width: 120, height: 120 }}
                      >
                        {(user as any).displayName?.[0]}
                      </Avatar>
                    </Badge>
                    <Typography variant="h6">{profileData.displayName}</Typography>
                    <Chip label={user.role} color="primary" />
                    <Stack direction="row" gap={1}>
                      {!editMode ? (
                        <Button
                          variant="outlined"
                          startIcon={<EditIcon />}
                          onClick={() => setEditMode(true)}
                        >
                          Edit Profile
                        </Button>
                      ) : (
                        <>
                          <Button
                            variant="contained"
                            startIcon={<SaveIcon />}
                            onClick={handleSaveProfile}
                          >
                            Save
                          </Button>
                          <Button
                            variant="outlined"
                            startIcon={<CancelIcon />}
                            onClick={() => setEditMode(false)}
                          >
                            Cancel
                          </Button>
                        </>
                      )}
                    </Stack>
                  </Stack>
                </Grid2>
                <Grid2 xs={12} md={8}>
                  <Stack spacing={2}>
                    <TextField
                      fullWidth
                      label="Display Name"
                      value={profileData.displayName}
                      onChange={(e) => setProfileData({ ...profileData, displayName: e.target.value })}
                      disabled={!editMode}
                    />
                    <TextField
                      fullWidth
                      label="Email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      disabled={!editMode}
                    />
                    <TextField
                      fullWidth
                      label="Phone"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      disabled={!editMode}
                    />
                    <TextField
                      fullWidth
                      label="Bio"
                      multiline
                      rows={3}
                      value={profileData.bio}
                      onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                      disabled={!editMode}
                    />
                    <Grid2 container spacing={2}>
                      <Grid2 xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Location"
                          value={profileData.location}
                          onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
                          disabled={!editMode}
                        />
                      </Grid2>
                      <Grid2 xs={12} md={6}>
                        <FormControl fullWidth disabled={!editMode}>
                          <InputLabel>Timezone</InputLabel>
                          <Select
                            value={profileData.timezone}
                            label="Timezone"
                            onChange={(e) => setProfileData({ ...profileData, timezone: e.target.value })}
                          >
                            <MenuItem value="PST">PST</MenuItem>
                            <MenuItem value="EST">EST</MenuItem>
                            <MenuItem value="CST">CST</MenuItem>
                            <MenuItem value="MST">MST</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid2>
                    </Grid2>
                  </Stack>
                </Grid2>
              </Grid2>
            </TabPanel>

            {/* Notifications Tab */}
            <TabPanel value={activeTab} index={1}>
              <Stack spacing={3}>
                <Alert severity="info">
                  <AlertTitle>Notification Preferences</AlertTitle>
                  Choose how you want to receive notifications about important updates and activities.
                </Alert>
                
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Email Notifications
                    </Typography>
                    <FormGroup>
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="New messages"
                      />
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Assignment updates"
                      />
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Grade posted"
                      />
                      <FormControlLabel
                        control={<Checkbox />}
                        label="Weekly progress reports"
                      />
                      <FormControlLabel
                        control={<Checkbox />}
                        label="System updates"
                      />
                    </FormGroup>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Push Notifications
                    </Typography>
                    <FormGroup>
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Direct messages"
                      />
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Class announcements"
                      />
                      <FormControlLabel
                        control={<Checkbox />}
                        label="Achievement unlocked"
                      />
                      <FormControlLabel
                        control={<Checkbox />}
                        label="Reminder for assignments"
                      />
                    </FormGroup>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Notification Schedule
                    </Typography>
                    <RadioGroup defaultValue="immediate">
                      <FormControlLabel value="immediate" control={<Radio />} label="Immediately" />
                      <FormControlLabel value="hourly" control={<Radio />} label="Hourly digest" />
                      <FormControlLabel value="daily" control={<Radio />} label="Daily digest" />
                      <FormControlLabel value="weekly" control={<Radio />} label="Weekly digest" />
                    </RadioGroup>
                  </CardContent>
                </Card>
              </Stack>
            </TabPanel>

            {/* Security Tab */}
            <TabPanel value={activeTab} index={2}>
              <Stack spacing={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Password
                    </Typography>
                    <Stack spacing={2}>
                      <Typography variant="body2" color="text.secondary">
                        Last changed: 30 days ago
                      </Typography>
                      <Button variant="outlined" startIcon={<VpnKeyIcon />}>
                        Change Password
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Two-Factor Authentication
                    </Typography>
                    <Stack spacing={2}>
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="Enable two-factor authentication"
                      />
                      <Stack direction="row" gap={2}>
                        <Button variant="outlined" startIcon={<SmartphoneIcon />}>
                          Configure Authenticator App
                        </Button>
                        <Button variant="outlined" startIcon={<EmailIcon />}>
                          Configure Email 2FA
                        </Button>
                      </Stack>
                    </Stack>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Active Sessions
                    </Typography>
                    <List>
                      <ListItem>
                        <ListItemText
                          primary="Chrome on Windows"
                          secondary="San Francisco, CA • Active now"
                        />
                        <ListItemSecondaryAction>
                          <Chip label="Current" color="success" size="small" />
                        </ListItemSecondaryAction>
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Safari on iPhone"
                          secondary="San Francisco, CA • 2 hours ago"
                        />
                        <ListItemSecondaryAction>
                          <Button size="small" color="error">
                            Revoke
                          </Button>
                        </ListItemSecondaryAction>
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Stack>
            </TabPanel>

            {/* Appearance Tab */}
            <TabPanel value={activeTab} index={3}>
              <Stack spacing={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Theme
                    </Typography>
                    <RadioGroup
                      value={theme}
                      onChange={(e) => dispatch(setTheme(e.target.value as any))}
                    >
                      <FormControlLabel value="light" control={<Radio />} label="Light" />
                      <FormControlLabel value="dark" control={<Radio />} label="Dark" />
                      <FormControlLabel value="auto" control={<Radio />} label="System default" />
                    </RadioGroup>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Color Scheme
                    </Typography>
                    <Stack direction="row" gap={2}>
                      {["#2563EB", "#9333EA", "#22C55E", "#EF4444", "#F59E0B"].map((color) => (
                        <Box
                          key={color}
                          sx={{
                            width: 40,
                            height: 40,
                            bgcolor: color,
                            borderRadius: 2,
                            cursor: "pointer",
                            border: "2px solid transparent",
                            "&:hover": {
                              border: "2px solid",
                              borderColor: "primary.main",
                            },
                          }}
                        />
                      ))}
                    </Stack>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Display Options
                    </Typography>
                    <FormGroup>
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="Show animations"
                      />
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="Compact mode"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="High contrast"
                      />
                    </FormGroup>
                  </CardContent>
                </Card>
              </Stack>
            </TabPanel>

            {/* Language Tab */}
            <TabPanel value={activeTab} index={4}>
              <Stack spacing={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Language Preference
                    </Typography>
                    <FormControl fullWidth>
                      <InputLabel>Language</InputLabel>
                      <Select defaultValue="en" label="Language">
                        <MenuItem value="en">English</MenuItem>
                        <MenuItem value="es">Español</MenuItem>
                        <MenuItem value="fr">Français</MenuItem>
                        <MenuItem value="de">Deutsch</MenuItem>
                        <MenuItem value="zh">中文</MenuItem>
                        <MenuItem value="ja">日本語</MenuItem>
                      </Select>
                    </FormControl>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Regional Settings
                    </Typography>
                    <Stack spacing={2}>
                      <FormControl fullWidth>
                        <InputLabel>Date Format</InputLabel>
                        <Select defaultValue="mm/dd/yyyy" label="Date Format">
                          <MenuItem value="mm/dd/yyyy">MM/DD/YYYY</MenuItem>
                          <MenuItem value="dd/mm/yyyy">DD/MM/YYYY</MenuItem>
                          <MenuItem value="yyyy-mm-dd">YYYY-MM-DD</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl fullWidth>
                        <InputLabel>Time Format</InputLabel>
                        <Select defaultValue="12h" label="Time Format">
                          <MenuItem value="12h">12-hour</MenuItem>
                          <MenuItem value="24h">24-hour</MenuItem>
                        </Select>
                      </FormControl>
                    </Stack>
                  </CardContent>
                </Card>
              </Stack>
            </TabPanel>

            {/* Accessibility Tab */}
            <TabPanel value={activeTab} index={5}>
              <Stack spacing={3}>
                <Alert severity="info">
                  <AlertTitle>Accessibility Features</AlertTitle>
                  Customize the platform to meet your accessibility needs.
                </Alert>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Visual
                    </Typography>
                    <FormGroup>
                      <FormControlLabel
                        control={<Switch />}
                        label="Large text"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="High contrast"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="Reduce motion"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="Screen reader optimization"
                      />
                    </FormGroup>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Keyboard Navigation
                    </Typography>
                    <FormGroup>
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="Enable keyboard shortcuts"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="Show focus indicators"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="Tab navigation hints"
                      />
                    </FormGroup>
                  </CardContent>
                </Card>
              </Stack>
            </TabPanel>

            {/* Data Tab */}
            <TabPanel value={activeTab} index={6}>
              <Stack spacing={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Data Management
                    </Typography>
                    <Stack spacing={2}>
                      <Button variant="outlined" startIcon={<DownloadIcon />}>
                        Download My Data
                      </Button>
                      <Button variant="outlined" color="error" startIcon={<DeleteIcon />}>
                        Delete My Account
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Privacy Settings
                    </Typography>
                    <FormGroup>
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="Allow analytics"
                      />
                      <FormControlLabel
                        control={<Switch />}
                        label="Share progress with parents"
                      />
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="Show on leaderboards"
                      />
                    </FormGroup>
                  </CardContent>
                </Card>
              </Stack>
            </TabPanel>

            {/* Admin Settings Tab - Only visible to admins */}
            {user.role === "admin" && (
              <TabPanel value={activeTab} index={7}>
                <Stack spacing={3}>
                  <Alert severity="warning">
                    <AlertTitle>Administrator Settings</AlertTitle>
                    These settings affect system-wide behavior and should be changed carefully.
                  </Alert>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                        Agent Dashboard Access
                      </Typography>
                      <FormGroup>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={adminSettings.agentDashboard.teacherAccess}
                              onChange={(e) =>
                                setAdminSettings({
                                  ...adminSettings,
                                  agentDashboard: {
                                    ...adminSettings.agentDashboard,
                                    teacherAccess: e.target.checked,
                                  },
                                })
                              }
                            />
                          }
                          label="Allow teachers to access Agent Dashboard"
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 4.5, mt: 0.5 }}>
                          When enabled, teachers will see the Agent System option in their navigation menu
                        </Typography>
                      </FormGroup>

                      <Divider sx={{ my: 2 }} />

                      <Typography variant="subtitle2" sx={{ mb: 2 }}>
                        Agent Dashboard Configuration
                      </Typography>
                      <Stack spacing={2}>
                        <TextField
                          fullWidth
                          type="number"
                          label="Auto-refresh Interval (seconds)"
                          value={adminSettings.agentDashboard.autoRefreshInterval}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              agentDashboard: {
                                ...adminSettings.agentDashboard,
                                autoRefreshInterval: parseInt(e.target.value) || 30,
                              },
                            })
                          }
                          InputProps={{ inputProps: { min: 5, max: 300 } }}
                          helperText="How often the dashboard should refresh data"
                        />
                        <TextField
                          fullWidth
                          type="number"
                          label="Max Concurrent Tasks"
                          value={adminSettings.agentDashboard.maxConcurrentTasks}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              agentDashboard: {
                                ...adminSettings.agentDashboard,
                                maxConcurrentTasks: parseInt(e.target.value) || 10,
                              },
                            })
                          }
                          InputProps={{ inputProps: { min: 1, max: 50 } }}
                          helperText="Maximum number of tasks that can run simultaneously"
                        />
                        <FormControlLabel
                          control={
                            <Switch
                              checked={adminSettings.agentDashboard.enableResourceMonitoring}
                              onChange={(e) =>
                                setAdminSettings({
                                  ...adminSettings,
                                  agentDashboard: {
                                    ...adminSettings.agentDashboard,
                                    enableResourceMonitoring: e.target.checked,
                                  },
                                })
                              }
                            />
                          }
                          label="Enable Resource Monitoring"
                        />
                        <FormControlLabel
                          control={
                            <Switch
                              checked={adminSettings.agentDashboard.enableWorktreeCoordination}
                              onChange={(e) =>
                                setAdminSettings({
                                  ...adminSettings,
                                  agentDashboard: {
                                    ...adminSettings.agentDashboard,
                                    enableWorktreeCoordination: e.target.checked,
                                  },
                                })
                              }
                            />
                          }
                          label="Enable Worktree Coordination"
                        />
                      </Stack>
                    </CardContent>
                  </Card>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                        System Limits
                      </Typography>
                      <Stack spacing={2}>
                        <TextField
                          fullWidth
                          type="number"
                          label="Max Agents Per Type"
                          value={adminSettings.systemLimits.maxAgentsPerType}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              systemLimits: {
                                ...adminSettings.systemLimits,
                                maxAgentsPerType: parseInt(e.target.value) || 5,
                              },
                            })
                          }
                          InputProps={{ inputProps: { min: 1, max: 20 } }}
                          helperText="Maximum number of agents of each type that can be created"
                        />
                        <TextField
                          fullWidth
                          type="number"
                          label="Task Queue Size"
                          value={adminSettings.systemLimits.taskQueueSize}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              systemLimits: {
                                ...adminSettings.systemLimits,
                                taskQueueSize: parseInt(e.target.value) || 1000,
                              },
                            })
                          }
                          InputProps={{ inputProps: { min: 100, max: 10000 } }}
                          helperText="Maximum number of tasks that can be queued"
                        />

                        <Divider />

                        <Typography variant="subtitle2">Auto-scaling</Typography>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={adminSettings.systemLimits.enableAutoScaling}
                              onChange={(e) =>
                                setAdminSettings({
                                  ...adminSettings,
                                  systemLimits: {
                                    ...adminSettings.systemLimits,
                                    enableAutoScaling: e.target.checked,
                                  },
                                })
                              }
                            />
                          }
                          label="Enable Auto-scaling"
                        />
                        {adminSettings.systemLimits.enableAutoScaling && (
                          <Grid2 container spacing={2}>
                            <Grid2 xs={6}>
                              <TextField
                                fullWidth
                                type="number"
                                label="Min Agents"
                                value={adminSettings.systemLimits.minAgents}
                                onChange={(e) =>
                                  setAdminSettings({
                                    ...adminSettings,
                                    systemLimits: {
                                      ...adminSettings.systemLimits,
                                      minAgents: parseInt(e.target.value) || 1,
                                    },
                                  })
                                }
                                InputProps={{ inputProps: { min: 1, max: 10 } }}
                              />
                            </Grid2>
                            <Grid2 xs={6}>
                              <TextField
                                fullWidth
                                type="number"
                                label="Max Agents"
                                value={adminSettings.systemLimits.maxAgents}
                                onChange={(e) =>
                                  setAdminSettings({
                                    ...adminSettings,
                                    systemLimits: {
                                      ...adminSettings.systemLimits,
                                      maxAgents: parseInt(e.target.value) || 10,
                                    },
                                  })
                                }
                                InputProps={{ inputProps: { min: 1, max: 50 } }}
                              />
                            </Grid2>
                          </Grid2>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>

                  <Stack direction="row" gap={2} justifyContent="flex-end">
                    <Button variant="outlined" onClick={() => window.location.reload()}>
                      Reset to Defaults
                    </Button>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<SaveIcon />}
                      onClick={() => {
                        // Save admin settings to backend
                        console.log("Saving admin settings:", adminSettings);
                        // TODO: Call API to save settings
                      }}
                    >
                      Save Admin Settings
                    </Button>
                  </Stack>
                </Stack>
              </TabPanel>
            )}
          </CardContent>
        </Card>
      </Grid2>
    </Grid2>
  );
}