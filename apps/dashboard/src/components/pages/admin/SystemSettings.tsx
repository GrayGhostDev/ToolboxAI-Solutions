import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../../utils/mui-imports';
import React, { useState } from 'react';

import { useAppDispatch } from '../../../store';
import { addNotification } from '../../../store/slices/uiSlice';

interface Settings {
  general: {
    siteName: string;
    siteUrl: string;
    adminEmail: string;
    timezone: string;
    language: string;
    maintenanceMode: boolean;
  };
  security: {
    twoFactorAuth: boolean;
    sessionTimeout: number;
    passwordMinLength: number;
    passwordRequireSpecial: boolean;
    passwordRequireNumbers: boolean;
    maxLoginAttempts: number;
  };
  email: {
    smtpHost: string;
    smtpPort: number;
    smtpUser: string;
    smtpPassword: string;
    smtpSecure: boolean;
    emailFrom: string;
  };
  features: {
    enableRegistration: boolean;
    enableRobloxIntegration: boolean;
    enableAIContent: boolean;
    enableReports: boolean;
    enableMessaging: boolean;
    enableGamification: boolean;
  };
  api: {
    rateLimit: number;
    apiTimeout: number;
    maxUploadSize: number;
    allowedOrigins: string;
  };
}

const SystemSettings: React.FunctionComponent<Record<string, any>> = () => {
  const dispatch = useAppDispatch();
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  const [settings, setSettings] = useState<Settings>({
    general: {
      siteName: 'ToolBoxAI Educational Platform',
      siteUrl: 'https://toolboxai.com',
      adminEmail: 'admin@toolboxai.com',
      timezone: 'America/New_York',
      language: 'en',
      maintenanceMode: false,
    },
    security: {
      twoFactorAuth: true,
      sessionTimeout: 30,
      passwordMinLength: 8,
      passwordRequireSpecial: true,
      passwordRequireNumbers: true,
      maxLoginAttempts: 5,
    },
    email: {
      smtpHost: 'smtp.gmail.com',
      smtpPort: 587,
      smtpUser: 'noreply@toolboxai.com',
      smtpPassword: '********',
      smtpSecure: true,
      emailFrom: 'ToolBoxAI <noreply@toolboxai.com>',
    },
    features: {
      enableRegistration: true,
      enableRobloxIntegration: true,
      enableAIContent: true,
      enableReports: true,
      enableMessaging: true,
      enableGamification: true,
    },
    api: {
      rateLimit: 100,
      apiTimeout: 30,
      maxUploadSize: 10,
      allowedOrigins: 'http://localhost:3000,http://localhost:5179',
    },
  });

  const handleChange = (section: keyof Settings, field: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      dispatch(
        addNotification({
          type: 'success',
          message: 'Settings saved successfully',
        })
      );
      setHasChanges(false);
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to save settings',
        })
      );
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    // Reset to defaults
    setSettings({
      general: {
        siteName: 'ToolBoxAI Educational Platform',
        siteUrl: 'https://toolboxai.com',
        adminEmail: 'admin@toolboxai.com',
        timezone: 'America/New_York',
        language: 'en',
        maintenanceMode: false,
      },
      security: {
        twoFactorAuth: true,
        sessionTimeout: 30,
        passwordMinLength: 8,
        passwordRequireSpecial: true,
        passwordRequireNumbers: true,
        maxLoginAttempts: 5,
      },
      email: {
        smtpHost: 'smtp.gmail.com',
        smtpPort: 587,
        smtpUser: 'noreply@toolboxai.com',
        smtpPassword: '********',
        smtpSecure: true,
        emailFrom: 'ToolBoxAI <noreply@toolboxai.com>',
      },
      features: {
        enableRegistration: true,
        enableRobloxIntegration: true,
        enableAIContent: true,
        enableReports: true,
        enableMessaging: true,
        enableGamification: true,
      },
      api: {
        rateLimit: 100,
        apiTimeout: 30,
        maxUploadSize: 10,
        allowedOrigins: 'http://localhost:3000,http://localhost:5179',
      },
    });
    setHasChanges(false);
    dispatch(
      addNotification({
        type: 'info',
        message: 'Settings reset to defaults',
      })
    );
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" style={{ mb: 3 }}>
        <Typography order={5} fontWeight={600}>
          System Settings
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outline"
            startIcon={<RestartAlt />}
            onClick={(e: React.MouseEvent) => handleReset}
            disabled={!hasChanges || saving}
          >
            Reset
          </Button>
          <Button
            variant="filled"
            startIcon={<Save />}
            onClick={(e: React.MouseEvent) => handleSave}
            disabled={!hasChanges || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Stack>
      </Stack>

      {hasChanges && (
        <Alert severity="warning" style={{ mb: 2 }}>
          You have unsaved changes. Don't forget to save before leaving this page.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="General Settings" />
            <CardContent>
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="Site Name"
                  value={settings.general.siteName}
                  onChange={(e) => handleChange('general', 'siteName', e.target.value)}
                />
                <TextField
                  fullWidth
                  label="Site URL"
                  value={settings.general.siteUrl}
                  onChange={(e) => handleChange('general', 'siteUrl', e.target.value)}
                />
                <TextField
                  fullWidth
                  label="Admin Email"
                  type="email"
                  value={settings.general.adminEmail}
                  onChange={(e) => handleChange('general', 'adminEmail', e.target.value)}
                />
                <FormControl fullWidth>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={settings.general.timezone}
                    onChange={(e) => handleChange('general', 'timezone', e.target.value)}
                    label="Timezone"
                  >
                    <MenuItem value="America/New_York">Eastern Time</MenuItem>
                    <MenuItem value="America/Chicago">Central Time</MenuItem>
                    <MenuItem value="America/Denver">Mountain Time</MenuItem>
                    <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                    <MenuItem value="UTC">UTC</MenuItem>
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={settings.general.language}
                    onChange={(e) => handleChange('general', 'language', e.target.value)}
                    label="Language"
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                    <MenuItem value="de">German</MenuItem>
                  </Select>
                </FormControl>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.general.maintenanceMode}
                      onChange={(e) => handleChange('general', 'maintenanceMode', e.target.checked)}
                    />
                  }
                  label={
                    <Box>
                      Maintenance Mode
                      {settings.general.maintenanceMode && (
                        <Chip label="Active" color="yellow" size="small" style={{ ml: 1 }} />
                      )}
                    </Box>
                  }
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Security Settings" />
            <CardContent>
              <Stack spacing={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.twoFactorAuth}
                      onChange={(e) => handleChange('security', 'twoFactorAuth', e.target.checked)}
                    />
                  }
                  label="Require Two-Factor Authentication"
                />
                <TextField
                  fullWidth
                  label="Session Timeout (minutes)"
                  type="number"
                  value={settings.security.sessionTimeout}
                  onChange={(e) => handleChange('security', 'sessionTimeout', parseInt(e.target.value))}
                />
                <TextField
                  fullWidth
                  label="Minimum Password Length"
                  type="number"
                  value={settings.security.passwordMinLength}
                  onChange={(e) => handleChange('security', 'passwordMinLength', parseInt(e.target.value))}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.passwordRequireSpecial}
                      onChange={(e) => handleChange('security', 'passwordRequireSpecial', e.target.checked)}
                    />
                  }
                  label="Require Special Characters"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.passwordRequireNumbers}
                      onChange={(e) => handleChange('security', 'passwordRequireNumbers', e.target.checked)}
                    />
                  }
                  label="Require Numbers"
                />
                <TextField
                  fullWidth
                  label="Max Login Attempts"
                  type="number"
                  value={settings.security.maxLoginAttempts}
                  onChange={(e) => handleChange('security', 'maxLoginAttempts', parseInt(e.target.value))}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Email Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Email Settings" />
            <CardContent>
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="SMTP Host"
                  value={settings.email.smtpHost}
                  onChange={(e) => handleChange('email', 'smtpHost', e.target.value)}
                />
                <TextField
                  fullWidth
                  label="SMTP Port"
                  type="number"
                  value={settings.email.smtpPort}
                  onChange={(e) => handleChange('email', 'smtpPort', parseInt(e.target.value))}
                />
                <TextField
                  fullWidth
                  label="SMTP User"
                  value={settings.email.smtpUser}
                  onChange={(e) => handleChange('email', 'smtpUser', e.target.value)}
                />
                <TextField
                  fullWidth
                  label="SMTP Password"
                  type="password"
                  value={settings.email.smtpPassword}
                  onChange={(e) => handleChange('email', 'smtpPassword', e.target.value)}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.email.smtpSecure}
                      onChange={(e) => handleChange('email', 'smtpSecure', e.target.checked)}
                    />
                  }
                  label="Use Secure Connection (TLS)"
                />
                <TextField
                  fullWidth
                  label="From Email"
                  value={settings.email.emailFrom}
                  onChange={(e) => handleChange('email', 'emailFrom', e.target.value)}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Feature Toggles */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Feature Toggles" />
            <CardContent>
              <Stack spacing={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.features.enableRegistration}
                      onChange={(e) => handleChange('features', 'enableRegistration', e.target.checked)}
                    />
                  }
                  label="Enable User Registration"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.features.enableRobloxIntegration}
                      onChange={(e) => handleChange('features', 'enableRobloxIntegration', e.target.checked)}
                    />
                  }
                  label="Enable Roblox Integration"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.features.enableAIContent}
                      onChange={(e) => handleChange('features', 'enableAIContent', e.target.checked)}
                    />
                  }
                  label="Enable AI Content Generation"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.features.enableReports}
                      onChange={(e) => handleChange('features', 'enableReports', e.target.checked)}
                    />
                  }
                  label="Enable Report Generation"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.features.enableMessaging}
                      onChange={(e) => handleChange('features', 'enableMessaging', e.target.checked)}
                    />
                  }
                  label="Enable Messaging System"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.features.enableGamification}
                      onChange={(e) => handleChange('features', 'enableGamification', e.target.checked)}
                    />
                  }
                  label="Enable Gamification"
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* API Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="API Settings" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="Rate Limit (requests/minute)"
                    type="number"
                    value={settings.api.rateLimit}
                    onChange={(e) => handleChange('api', 'rateLimit', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="API Timeout (seconds)"
                    type="number"
                    value={settings.api.apiTimeout}
                    onChange={(e) => handleChange('api', 'apiTimeout', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="Max Upload Size (MB)"
                    type="number"
                    value={settings.api.maxUploadSize}
                    onChange={(e) => handleChange('api', 'maxUploadSize', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12} md={12}>
                  <TextField
                    fullWidth
                    label="Allowed Origins (comma-separated)"
                    value={settings.api.allowedOrigins}
                    onChange={(e) => handleChange('api', 'allowedOrigins', e.target.value)}
                    multiline
                    rows={2}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SystemSettings;