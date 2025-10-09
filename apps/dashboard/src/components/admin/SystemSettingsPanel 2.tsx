/**
 * SystemSettingsPanel Component
 * Comprehensive system configuration interface for administrators
 */

import React, { memo, useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Text,
  Accordion,
  Stack,
  TextInput,
  Switch,
  Select,
  Button,
  Alert,
  Badge,
  Slider,
  Table,
  ActionIcon,
  Modal,
  List,
  Divider,
  Tabs,
  Tooltip,
  Loader,
  Progress,
  useMantineTheme,
  Group,
  Flex,
  Textarea,
  NumberInput,
  TimeInput,
  Notification,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconChevronDown,
  IconSettings,
  IconShield,
  IconMail,
  IconDatabase,
  IconLanguage,
  IconPalette,
  IconBell,
  IconApi,
  IconGauge,
  IconBackup,
  IconRefresh,
  IconLock,
  IconDeviceFloppy,
  IconRotateClockwise2,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCheck,
  IconX,
  IconAlertTriangle,
  IconInfoCircle,
  IconCloud,
  IconClock,
  IconUsers,
  IconSchool,
} from '@tabler/icons-react';
import { api } from '@/services/api';

interface SystemSettings {
  general: {
    siteName: string;
    siteUrl: string;
    timezone: string;
    language: string;
    maintenanceMode: boolean;
    maintenanceMessage: string;
  };
  security: {
    passwordMinLength: number;
    passwordRequireUppercase: boolean;
    passwordRequireLowercase: boolean;
    passwordRequireNumbers: boolean;
    passwordRequireSpecial: boolean;
    sessionTimeout: number;
    maxLoginAttempts: number;
    twoFactorEnabled: boolean;
    ipWhitelist: string[];
    ipBlacklist: string[];
  };
  email: {
    provider: 'smtp' | 'sendgrid' | 'ses';
    smtpHost?: string;
    smtpPort?: number;
    smtpUser?: string;
    smtpSecure?: boolean;
    fromEmail: string;
    fromName: string;
    replyToEmail: string;
  };
  storage: {
    provider: 'local' | 's3' | 'gcs' | 'azure';
    maxFileSize: number;
    allowedFileTypes: string[];
    storageLimit: number;
    currentUsage: number;
    s3Config?: {
      bucket: string;
      region: string;
      accessKeyId: string;
    };
  };
  notifications: {
    emailEnabled: boolean;
    pushEnabled: boolean;
    smsEnabled: boolean;
    defaultNotifications: {
      newUser: boolean;
      newContent: boolean;
      systemAlerts: boolean;
      userReports: boolean;
    };
  };
  performance: {
    cacheEnabled: boolean;
    cacheDuration: number;
    compressionEnabled: boolean;
    lazyLoadingEnabled: boolean;
    cdnEnabled: boolean;
    cdnUrl?: string;
    rateLimitEnabled: boolean;
    rateLimitRequests: number;
    rateLimitWindow: number;
  };
  backup: {
    autoBackupEnabled: boolean;
    backupFrequency: 'daily' | 'weekly' | 'monthly';
    backupTime: string;
    backupRetention: number;
    lastBackup?: string;
    nextBackup?: string;
  };
  api: {
    rateLimit: number;
    timeout: number;
    cors: {
      enabled: boolean;
      origins: string[];
    };
    webhooks: Array<{
      id: string;
      url: string;
      events: string[];
      active: boolean;
    }>;
  };
}

export interface SystemSettingsPanelProps {
  onSettingsChange?: (settings: Partial<SystemSettings>) => void;
  onSettingsSave?: (settings: SystemSettings) => void;
  allowDangerousActions?: boolean;
  readOnly?: boolean;
}

export const SystemSettingsPanel = memo<SystemSettingsPanelProps>(({
  onSettingsChange,
  onSettingsSave,
  allowDangerousActions = false,
  readOnly = false,
}) => {
  const theme = useMantineTheme();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [expandedPanel, setExpandedPanel] = useState<string | null>('general');

  // Settings state
  const [settings, setSettings] = useState<SystemSettings>({
    general: {
      siteName: 'ToolboxAI Educational Platform',
      siteUrl: 'https://toolboxai.com',
      timezone: 'America/New_York',
      language: 'en',
      maintenanceMode: false,
      maintenanceMessage: 'We are performing scheduled maintenance. We\'ll be back soon!',
    },
    security: {
      passwordMinLength: 8,
      passwordRequireUppercase: true,
      passwordRequireLowercase: true,
      passwordRequireNumbers: true,
      passwordRequireSpecial: true,
      sessionTimeout: 3600,
      maxLoginAttempts: 5,
      twoFactorEnabled: false,
      ipWhitelist: [],
      ipBlacklist: [],
    },
    email: {
      provider: 'smtp',
      smtpHost: 'smtp.gmail.com',
      smtpPort: 587,
      smtpUser: 'noreply@toolboxai.com',
      smtpSecure: true,
      fromEmail: 'noreply@toolboxai.com',
      fromName: 'ToolboxAI',
      replyToEmail: 'support@toolboxai.com',
    },
    storage: {
      provider: 'local',
      maxFileSize: 100 * 1024 * 1024, // 100MB
      allowedFileTypes: ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'mp4', 'mp3'],
      storageLimit: 10 * 1024 * 1024 * 1024, // 10GB
      currentUsage: 2.5 * 1024 * 1024 * 1024, // 2.5GB
    },
    notifications: {
      emailEnabled: true,
      pushEnabled: true,
      smsEnabled: false,
      defaultNotifications: {
        newUser: true,
        newContent: true,
        systemAlerts: true,
        userReports: false,
      },
    },
    performance: {
      cacheEnabled: true,
      cacheDuration: 3600,
      compressionEnabled: true,
      lazyLoadingEnabled: true,
      cdnEnabled: false,
      rateLimitEnabled: true,
      rateLimitRequests: 100,
      rateLimitWindow: 60,
    },
    backup: {
      autoBackupEnabled: true,
      backupFrequency: 'daily',
      backupTime: '02:00',
      backupRetention: 30,
      lastBackup: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      nextBackup: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
    },
    api: {
      rateLimit: 1000,
      timeout: 30000,
      cors: {
        enabled: true,
        origins: ['http://localhost:3000', 'https://toolboxai.com'],
      },
      webhooks: [],
    },
  });

  // Dialog states
  const [webhookDialogOpen, setWebhookDialogOpen] = useState(false);
  const [ipDialogOpen, setIpDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<string>('');

  // Fetch settings
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      // In a real app, fetch from API
      // const response = await api.get('/admin/settings');
      // setSettings(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load settings');
      setLoading(false);
    }
  };

  const handleSettingChange = (category: keyof SystemSettings, field: string, value: any) => {
    const newSettings = {
      ...settings,
      [category]: {
        ...settings[category],
        [field]: value,
      },
    };
    setSettings(newSettings);
    onSettingsChange?.({ [category]: { [field]: value } });
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // In a real app, save to API
      // await api.post('/admin/settings', settings);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      setSuccess('Settings saved successfully');
      onSettingsSave?.(settings);
    } catch (err) {
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleResetSettings = () => {
    setConfirmAction('reset');
    setConfirmDialogOpen(true);
  };

  const handleRunBackup = async () => {
    setSaving(true);
    try {
      // Trigger manual backup
      await new Promise(resolve => setTimeout(resolve, 2000));
      setSuccess('Backup initiated successfully');
    } catch (err) {
      setError('Failed to initiate backup');
    } finally {
      setSaving(false);
    }
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const renderGeneralSettings = () => (
    <Stack spacing={3}>
      <TextField
        label="Site Name"
        value={settings.general.siteName}
        onChange={(e) => handleSettingChange('general', 'siteName', e.target.value)}
        fullWidth
        disabled={readOnly}
      />
      <TextField
        label="Site URL"
        value={settings.general.siteUrl}
        onChange={(e) => handleSettingChange('general', 'siteUrl', e.target.value)}
        fullWidth
        disabled={readOnly}
      />
      <FormControl fullWidth disabled={readOnly}>
        <InputLabel>Timezone</InputLabel>
        <Select
          value={settings.general.timezone}
          label="Timezone"
          onChange={(e) => handleSettingChange('general', 'timezone', e.target.value)}
        >
          <MenuItem value="America/New_York">Eastern Time</MenuItem>
          <MenuItem value="America/Chicago">Central Time</MenuItem>
          <MenuItem value="America/Denver">Mountain Time</MenuItem>
          <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
          <MenuItem value="UTC">UTC</MenuItem>
        </Select>
      </FormControl>
      <FormControl fullWidth disabled={readOnly}>
        <InputLabel>Language</InputLabel>
        <Select
          value={settings.general.language}
          label="Language"
          onChange={(e) => handleSettingChange('general', 'language', e.target.value)}
        >
          <MenuItem value="en">English</MenuItem>
          <MenuItem value="es">Spanish</MenuItem>
          <MenuItem value="fr">French</MenuItem>
          <MenuItem value="de">German</MenuItem>
          <MenuItem value="zh">Chinese</MenuItem>
        </Select>
      </FormControl>
      <Divider />
      <Alert severity="warning">
        <AlertTitle>Maintenance Mode</AlertTitle>
        <Stack spacing={2}>
          <FormControlLabel
            control={
              <Switch
                checked={settings.general.maintenanceMode}
                onChange={(e) => handleSettingChange('general', 'maintenanceMode', e.target.checked)}
                disabled={readOnly}
              />
            }
            label="Enable Maintenance Mode"
          />
          {settings.general.maintenanceMode && (
            <TextField
              label="Maintenance Message"
              value={settings.general.maintenanceMessage}
              onChange={(e) => handleSettingChange('general', 'maintenanceMessage', e.target.value)}
              multiline
              rows={3}
              fullWidth
              disabled={readOnly}
            />
          )}
        </Stack>
      </Alert>
    </Stack>
  );

  const renderSecuritySettings = () => (
    <Stack spacing={3}>
      <Typography variant="subtitle1" fontWeight="bold">
        Password Requirements
      </Typography>
      <Stack spacing={2}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Typography sx={{ width: 200 }}>Minimum Length</Typography>
          <Slider
            value={settings.security.passwordMinLength}
            onChange={(_, value) => handleSettingChange('security', 'passwordMinLength', value)}
            min={6}
            max={20}
            marks
            valueLabelDisplay="on"
            disabled={readOnly}
            sx={{ flex: 1 }}
          />
        </Stack>
        <FormControlLabel
          control={
            <Switch
              checked={settings.security.passwordRequireUppercase}
              onChange={(e) => handleSettingChange('security', 'passwordRequireUppercase', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Require uppercase letters"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.security.passwordRequireLowercase}
              onChange={(e) => handleSettingChange('security', 'passwordRequireLowercase', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Require lowercase letters"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.security.passwordRequireNumbers}
              onChange={(e) => handleSettingChange('security', 'passwordRequireNumbers', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Require numbers"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.security.passwordRequireSpecial}
              onChange={(e) => handleSettingChange('security', 'passwordRequireSpecial', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Require special characters"
        />
      </Stack>

      <Divider />

      <Typography variant="subtitle1" fontWeight="bold">
        Session & Login
      </Typography>
      <Stack spacing={2}>
        <TextField
          label="Session Timeout (seconds)"
          type="number"
          value={settings.security.sessionTimeout}
          onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
          fullWidth
          disabled={readOnly}
        />
        <TextField
          label="Max Login Attempts"
          type="number"
          value={settings.security.maxLoginAttempts}
          onChange={(e) => handleSettingChange('security', 'maxLoginAttempts', parseInt(e.target.value))}
          fullWidth
          disabled={readOnly}
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.security.twoFactorEnabled}
              onChange={(e) => handleSettingChange('security', 'twoFactorEnabled', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Enable Two-Factor Authentication"
        />
      </Stack>

      <Divider />

      <Typography variant="subtitle1" fontWeight="bold">
        IP Access Control
      </Typography>
      <Stack spacing={2}>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={() => setIpDialogOpen(true)}
          disabled={readOnly}
        >
          Manage IP Whitelist/Blacklist
        </Button>
        <Stack direction="row" spacing={2}>
          <Chip
            label={`${settings.security.ipWhitelist.length} Whitelisted IPs`}
            variant="outlined"
            color="success"
          />
          <Chip
            label={`${settings.security.ipBlacklist.length} Blacklisted IPs`}
            variant="outlined"
            color="error"
          />
        </Stack>
      </Stack>
    </Stack>
  );

  const renderPerformanceSettings = () => (
    <Stack spacing={3}>
      <Typography variant="subtitle1" fontWeight="bold">
        Caching
      </Typography>
      <Stack spacing={2}>
        <FormControlLabel
          control={
            <Switch
              checked={settings.performance.cacheEnabled}
              onChange={(e) => handleSettingChange('performance', 'cacheEnabled', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Enable Caching"
        />
        {settings.performance.cacheEnabled && (
          <TextField
            label="Cache Duration (seconds)"
            type="number"
            value={settings.performance.cacheDuration}
            onChange={(e) => handleSettingChange('performance', 'cacheDuration', parseInt(e.target.value))}
            fullWidth
            disabled={readOnly}
          />
        )}
      </Stack>

      <Divider />

      <Typography variant="subtitle1" fontWeight="bold">
        Optimization
      </Typography>
      <Stack spacing={2}>
        <FormControlLabel
          control={
            <Switch
              checked={settings.performance.compressionEnabled}
              onChange={(e) => handleSettingChange('performance', 'compressionEnabled', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Enable Compression"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.performance.lazyLoadingEnabled}
              onChange={(e) => handleSettingChange('performance', 'lazyLoadingEnabled', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Enable Lazy Loading"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.performance.cdnEnabled}
              onChange={(e) => handleSettingChange('performance', 'cdnEnabled', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Enable CDN"
        />
        {settings.performance.cdnEnabled && (
          <TextField
            label="CDN URL"
            value={settings.performance.cdnUrl || ''}
            onChange={(e) => handleSettingChange('performance', 'cdnUrl', e.target.value)}
            fullWidth
            disabled={readOnly}
          />
        )}
      </Stack>

      <Divider />

      <Typography variant="subtitle1" fontWeight="bold">
        Rate Limiting
      </Typography>
      <Stack spacing={2}>
        <FormControlLabel
          control={
            <Switch
              checked={settings.performance.rateLimitEnabled}
              onChange={(e) => handleSettingChange('performance', 'rateLimitEnabled', e.target.checked)}
              disabled={readOnly}
            />
          }
          label="Enable Rate Limiting"
        />
        {settings.performance.rateLimitEnabled && (
          <>
            <TextField
              label="Requests per Window"
              type="number"
              value={settings.performance.rateLimitRequests}
              onChange={(e) => handleSettingChange('performance', 'rateLimitRequests', parseInt(e.target.value))}
              fullWidth
              disabled={readOnly}
            />
            <TextField
              label="Window Duration (seconds)"
              type="number"
              value={settings.performance.rateLimitWindow}
              onChange={(e) => handleSettingChange('performance', 'rateLimitWindow', parseInt(e.target.value))}
              fullWidth
              disabled={readOnly}
            />
          </>
        )}
      </Stack>
    </Stack>
  );

  const renderBackupSettings = () => (
    <Stack spacing={3}>
      <Alert severity="info">
        <AlertTitle>Backup Status</AlertTitle>
        <Stack spacing={1}>
          <Typography variant="body2">
            Last backup: {settings.backup.lastBackup ? new Date(settings.backup.lastBackup).toLocaleString() : 'Never'}
          </Typography>
          <Typography variant="body2">
            Next scheduled: {settings.backup.nextBackup ? new Date(settings.backup.nextBackup).toLocaleString() : 'Not scheduled'}
          </Typography>
        </Stack>
      </Alert>

      <FormControlLabel
        control={
          <Switch
            checked={settings.backup.autoBackupEnabled}
            onChange={(e) => handleSettingChange('backup', 'autoBackupEnabled', e.target.checked)}
            disabled={readOnly}
          />
        }
        label="Enable Automatic Backups"
      />

      {settings.backup.autoBackupEnabled && (
        <>
          <FormControl fullWidth disabled={readOnly}>
            <InputLabel>Backup Frequency</InputLabel>
            <Select
              value={settings.backup.backupFrequency}
              label="Backup Frequency"
              onChange={(e) => handleSettingChange('backup', 'backupFrequency', e.target.value)}
            >
              <MenuItem value="daily">Daily</MenuItem>
              <MenuItem value="weekly">Weekly</MenuItem>
              <MenuItem value="monthly">Monthly</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Backup Time"
            type="time"
            value={settings.backup.backupTime}
            onChange={(e) => handleSettingChange('backup', 'backupTime', e.target.value)}
            fullWidth
            disabled={readOnly}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            label="Retention Period (days)"
            type="number"
            value={settings.backup.backupRetention}
            onChange={(e) => handleSettingChange('backup', 'backupRetention', parseInt(e.target.value))}
            fullWidth
            disabled={readOnly}
          />
        </>
      )}

      <Button
        variant="contained"
        startIcon={<BackupIcon />}
        onClick={handleRunBackup}
        disabled={readOnly || saving}
      >
        Run Manual Backup Now
      </Button>
    </Stack>
  );

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" fontWeight="bold">
            System Settings
          </Typography>
          <Stack direction="row" spacing={1}>
            {allowDangerousActions && (
              <Button
                size="small"
                color="error"
                startIcon={<ResetIcon />}
                onClick={handleResetSettings}
                disabled={readOnly}
              >
                Reset to Defaults
              </Button>
            )}
            <Button
              variant="contained"
              size="small"
              startIcon={<SaveIcon />}
              onClick={handleSaveSettings}
              disabled={readOnly || saving}
            >
              Save Changes
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Loading */}
      {loading && <LinearProgress />}

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ m: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ m: 2 }}>
          {success}
        </Alert>
      )}

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {/* General Settings */}
        <Accordion
          expanded={expandedPanel === 'general'}
          onChange={(_, isExpanded) => setExpandedPanel(isExpanded ? 'general' : false)}
        >
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Stack direction="row" spacing={2} alignItems="center">
              <SettingsIcon />
              <Typography>General Settings</Typography>
            </Stack>
          </AccordionSummary>
          <AccordionDetails>{renderGeneralSettings()}</AccordionDetails>
        </Accordion>

        {/* Security Settings */}
        <Accordion
          expanded={expandedPanel === 'security'}
          onChange={(_, isExpanded) => setExpandedPanel(isExpanded ? 'security' : false)}
        >
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Stack direction="row" spacing={2} alignItems="center">
              <SecurityIcon />
              <Typography>Security Settings</Typography>
            </Stack>
          </AccordionSummary>
          <AccordionDetails>{renderSecuritySettings()}</AccordionDetails>
        </Accordion>

        {/* Performance Settings */}
        <Accordion
          expanded={expandedPanel === 'performance'}
          onChange={(_, isExpanded) => setExpandedPanel(isExpanded ? 'performance' : false)}
        >
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Stack direction="row" spacing={2} alignItems="center">
              <PerformanceIcon />
              <Typography>Performance Settings</Typography>
            </Stack>
          </AccordionSummary>
          <AccordionDetails>{renderPerformanceSettings()}</AccordionDetails>
        </Accordion>

        {/* Backup Settings */}
        <Accordion
          expanded={expandedPanel === 'backup'}
          onChange={(_, isExpanded) => setExpandedPanel(isExpanded ? 'backup' : false)}
        >
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Stack direction="row" spacing={2} alignItems="center">
              <BackupIcon />
              <Typography>Backup Settings</Typography>
            </Stack>
          </AccordionSummary>
          <AccordionDetails>{renderBackupSettings()}</AccordionDetails>
        </Accordion>
      </Box>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
        <DialogTitle>Confirm Action</DialogTitle>
        <DialogContent>
          <Typography>
            {confirmAction === 'reset'
              ? 'Are you sure you want to reset all settings to defaults? This action cannot be undone.'
              : 'Are you sure you want to proceed with this action?'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => {
              if (confirmAction === 'reset') {
                // Reset settings to defaults
                fetchSettings();
              }
              setConfirmDialogOpen(false);
            }}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
});

SystemSettingsPanel.displayName = 'SystemSettingsPanel';

export default SystemSettingsPanel;