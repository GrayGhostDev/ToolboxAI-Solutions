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

      notifications.show({
        title: 'Success',
        message: 'Settings saved successfully',
        color: 'green',
        icon: <IconCheck size={16} />,
      });
      onSettingsSave?.(settings);
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: 'Failed to save settings',
        color: 'red',
        icon: <IconX size={16} />,
      });
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
      notifications.show({
        title: 'Success',
        message: 'Backup initiated successfully',
        color: 'green',
        icon: <IconCheck size={16} />,
      });
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: 'Failed to initiate backup',
        color: 'red',
        icon: <IconX size={16} />,
      });
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
    <Stack gap="md">
      <TextInput
        label="Site Name"
        value={settings.general.siteName}
        onChange={(e) => handleSettingChange('general', 'siteName', e.target.value)}
        disabled={readOnly}
      />
      <TextInput
        label="Site URL"
        value={settings.general.siteUrl}
        onChange={(e) => handleSettingChange('general', 'siteUrl', e.target.value)}
        disabled={readOnly}
      />
      <Select
        label="Timezone"
        value={settings.general.timezone}
        onChange={(value) => handleSettingChange('general', 'timezone', value)}
        disabled={readOnly}
        data={[
          { value: 'America/New_York', label: 'Eastern Time' },
          { value: 'America/Chicago', label: 'Central Time' },
          { value: 'America/Denver', label: 'Mountain Time' },
          { value: 'America/Los_Angeles', label: 'Pacific Time' },
          { value: 'UTC', label: 'UTC' },
        ]}
      />
      <Select
        label="Language"
        value={settings.general.language}
        onChange={(value) => handleSettingChange('general', 'language', value)}
        disabled={readOnly}
        data={[
          { value: 'en', label: 'English' },
          { value: 'es', label: 'Spanish' },
          { value: 'fr', label: 'French' },
          { value: 'de', label: 'German' },
          { value: 'zh', label: 'Chinese' },
        ]}
      />
      <Divider />
      <Alert icon={<IconAlertTriangle size={16} />} title="Maintenance Mode" color="yellow">
        <Stack gap="sm">
          <Group>
            <Switch
              checked={settings.general.maintenanceMode}
              onChange={(e) => handleSettingChange('general', 'maintenanceMode', e.currentTarget.checked)}
              disabled={readOnly}
              label="Enable Maintenance Mode"
            />
          </Group>
          {settings.general.maintenanceMode && (
            <Textarea
              label="Maintenance Message"
              value={settings.general.maintenanceMessage}
              onChange={(e) => handleSettingChange('general', 'maintenanceMessage', e.target.value)}
              rows={3}
              disabled={readOnly}
            />
          )}
        </Stack>
      </Alert>
    </Stack>
  );

  const renderSecuritySettings = () => (
    <Stack gap="md">
      <Text size="sm" fw={600}>
        Password Requirements
      </Text>
      <Stack gap="sm">
        <Group>
          <Text size="sm" style={{ width: 200 }}>Minimum Length</Text>
          <Box style={{ flex: 1 }}>
            <Slider
              value={settings.security.passwordMinLength}
              onChange={(value) => handleSettingChange('security', 'passwordMinLength', value)}
              min={6}
              max={20}
              marks
              label={(value) => value}
              disabled={readOnly}
            />
          </Box>
        </Group>
        <Switch
          checked={settings.security.passwordRequireUppercase}
          onChange={(e) => handleSettingChange('security', 'passwordRequireUppercase', e.currentTarget.checked)}
          disabled={readOnly}
          label="Require uppercase letters"
        />
        <Switch
          checked={settings.security.passwordRequireLowercase}
          onChange={(e) => handleSettingChange('security', 'passwordRequireLowercase', e.currentTarget.checked)}
          disabled={readOnly}
          label="Require lowercase letters"
        />
        <Switch
          checked={settings.security.passwordRequireNumbers}
          onChange={(e) => handleSettingChange('security', 'passwordRequireNumbers', e.currentTarget.checked)}
          disabled={readOnly}
          label="Require numbers"
        />
        <Switch
          checked={settings.security.passwordRequireSpecial}
          onChange={(e) => handleSettingChange('security', 'passwordRequireSpecial', e.currentTarget.checked)}
          disabled={readOnly}
          label="Require special characters"
        />
      </Stack>

      <Divider />

      <Text size="sm" fw={600}>
        Session & Login
      </Text>
      <Stack gap="sm">
        <NumberInput
          label="Session Timeout (seconds)"
          value={settings.security.sessionTimeout}
          onChange={(value) => handleSettingChange('security', 'sessionTimeout', value || 0)}
          disabled={readOnly}
        />
        <NumberInput
          label="Max Login Attempts"
          value={settings.security.maxLoginAttempts}
          onChange={(value) => handleSettingChange('security', 'maxLoginAttempts', value || 0)}
          disabled={readOnly}
        />
        <Switch
          checked={settings.security.twoFactorEnabled}
          onChange={(e) => handleSettingChange('security', 'twoFactorEnabled', e.currentTarget.checked)}
          disabled={readOnly}
          label="Enable Two-Factor Authentication"
        />
      </Stack>

      <Divider />

      <Text size="sm" fw={600}>
        IP Access Control
      </Text>
      <Stack gap="sm">
        <Button
          variant="outline"
          leftSection={<IconPlus size={16} />}
          onClick={() => setIpDialogOpen(true)}
          disabled={readOnly}
        >
          Manage IP Whitelist/Blacklist
        </Button>
        <Group>
          <Badge
            variant="outline"
            color="green"
          >
            {settings.security.ipWhitelist.length} Whitelisted IPs
          </Badge>
          <Badge
            variant="outline"
            color="red"
          >
            {settings.security.ipBlacklist.length} Blacklisted IPs
          </Badge>
        </Group>
      </Stack>
    </Stack>
  );

  const renderPerformanceSettings = () => (
    <Stack gap="md">
      <Text size="sm" fw={600}>
        Caching
      </Text>
      <Stack gap="sm">
        <Switch
          checked={settings.performance.cacheEnabled}
          onChange={(e) => handleSettingChange('performance', 'cacheEnabled', e.currentTarget.checked)}
          disabled={readOnly}
          label="Enable Caching"
        />
        {settings.performance.cacheEnabled && (
          <NumberInput
            label="Cache Duration (seconds)"
            value={settings.performance.cacheDuration}
            onChange={(value) => handleSettingChange('performance', 'cacheDuration', value || 0)}
            disabled={readOnly}
          />
        )}
      </Stack>

      <Divider />

      <Text size="sm" fw={600}>
        Optimization
      </Text>
      <Stack gap="sm">
        <Switch
          checked={settings.performance.compressionEnabled}
          onChange={(e) => handleSettingChange('performance', 'compressionEnabled', e.currentTarget.checked)}
          disabled={readOnly}
          label="Enable Compression"
        />
        <Switch
          checked={settings.performance.lazyLoadingEnabled}
          onChange={(e) => handleSettingChange('performance', 'lazyLoadingEnabled', e.currentTarget.checked)}
          disabled={readOnly}
          label="Enable Lazy Loading"
        />
        <Switch
          checked={settings.performance.cdnEnabled}
          onChange={(e) => handleSettingChange('performance', 'cdnEnabled', e.currentTarget.checked)}
          disabled={readOnly}
          label="Enable CDN"
        />
        {settings.performance.cdnEnabled && (
          <TextInput
            label="CDN URL"
            value={settings.performance.cdnUrl || ''}
            onChange={(e) => handleSettingChange('performance', 'cdnUrl', e.target.value)}
            disabled={readOnly}
          />
        )}
      </Stack>

      <Divider />

      <Text size="sm" fw={600}>
        Rate Limiting
      </Text>
      <Stack gap="sm">
        <Switch
          checked={settings.performance.rateLimitEnabled}
          onChange={(e) => handleSettingChange('performance', 'rateLimitEnabled', e.currentTarget.checked)}
          disabled={readOnly}
          label="Enable Rate Limiting"
        />
        {settings.performance.rateLimitEnabled && (
          <>
            <NumberInput
              label="Requests per Window"
              value={settings.performance.rateLimitRequests}
              onChange={(value) => handleSettingChange('performance', 'rateLimitRequests', value || 0)}
              disabled={readOnly}
            />
            <NumberInput
              label="Window Duration (seconds)"
              value={settings.performance.rateLimitWindow}
              onChange={(value) => handleSettingChange('performance', 'rateLimitWindow', value || 0)}
              disabled={readOnly}
            />
          </>
        )}
      </Stack>
    </Stack>
  );

  const renderBackupSettings = () => (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} title="Backup Status" color="blue">
        <Stack gap="xs">
          <Text size="sm">
            Last backup: {settings.backup.lastBackup ? new Date(settings.backup.lastBackup).toLocaleString() : 'Never'}
          </Text>
          <Text size="sm">
            Next scheduled: {settings.backup.nextBackup ? new Date(settings.backup.nextBackup).toLocaleString() : 'Not scheduled'}
          </Text>
        </Stack>
      </Alert>

      <Switch
        checked={settings.backup.autoBackupEnabled}
        onChange={(e) => handleSettingChange('backup', 'autoBackupEnabled', e.currentTarget.checked)}
        disabled={readOnly}
        label="Enable Automatic Backups"
      />

      {settings.backup.autoBackupEnabled && (
        <>
          <Select
            label="Backup Frequency"
            value={settings.backup.backupFrequency}
            onChange={(value) => handleSettingChange('backup', 'backupFrequency', value)}
            disabled={readOnly}
            data={[
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly' },
              { value: 'monthly', label: 'Monthly' },
            ]}
          />

          <TimeInput
            label="Backup Time"
            value={settings.backup.backupTime}
            onChange={(e) => handleSettingChange('backup', 'backupTime', e.target.value)}
            disabled={readOnly}
          />

          <NumberInput
            label="Retention Period (days)"
            value={settings.backup.backupRetention}
            onChange={(value) => handleSettingChange('backup', 'backupRetention', value || 0)}
            disabled={readOnly}
          />
        </>
      )}

      <Button
        variant="filled"
        leftSection={<IconBackup size={16} />}
        onClick={handleRunBackup}
        disabled={readOnly || saving}
        loading={saving}
      >
        Run Manual Backup Now
      </Button>
    </Stack>
  );

  return (
    <Paper style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box p="md" style={{ borderBottom: `1px solid ${theme.colors.gray[3]}` }}>
        <Group justify="space-between" align="center">
          <Text size="lg" fw={600}>
            System Settings
          </Text>
          <Group gap="xs">
            {allowDangerousActions && (
              <Button
                size="sm"
                color="red"
                variant="outline"
                leftSection={<IconRotateClockwise2 size={16} />}
                onClick={handleResetSettings}
                disabled={readOnly}
              >
                Reset to Defaults
              </Button>
            )}
            <Button
              variant="filled"
              size="sm"
              leftSection={<IconDeviceFloppy size={16} />}
              onClick={handleSaveSettings}
              disabled={readOnly || saving}
              loading={saving}
            >
              Save Changes
            </Button>
          </Group>
        </Group>
      </Box>

      {/* Loading */}
      {loading && <Progress size="xs" animated />}

      {/* Content */}
      <Box style={{ flex: 1, overflow: 'auto' }} p="md">
        <Accordion value={expandedPanel} onChange={setExpandedPanel}>
          {/* General Settings */}
          <Accordion.Item value="general">
            <Accordion.Control icon={<IconSettings size={20} />}>
              General Settings
            </Accordion.Control>
            <Accordion.Panel>{renderGeneralSettings()}</Accordion.Panel>
          </Accordion.Item>

          {/* Security Settings */}
          <Accordion.Item value="security">
            <Accordion.Control icon={<IconShield size={20} />}>
              Security Settings
            </Accordion.Control>
            <Accordion.Panel>{renderSecuritySettings()}</Accordion.Panel>
          </Accordion.Item>

          {/* Performance Settings */}
          <Accordion.Item value="performance">
            <Accordion.Control icon={<IconGauge size={20} />}>
              Performance Settings
            </Accordion.Control>
            <Accordion.Panel>{renderPerformanceSettings()}</Accordion.Panel>
          </Accordion.Item>

          {/* Backup Settings */}
          <Accordion.Item value="backup">
            <Accordion.Control icon={<IconBackup size={20} />}>
              Backup Settings
            </Accordion.Control>
            <Accordion.Panel>{renderBackupSettings()}</Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Box>

      {/* Confirmation Modal */}
      <Modal
        opened={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        title="Confirm Action"
        centered
      >
        <Stack gap="md">
          <Text>
            {confirmAction === 'reset'
              ? 'Are you sure you want to reset all settings to defaults? This action cannot be undone.'
              : 'Are you sure you want to proceed with this action?'}
          </Text>
          <Group justify="flex-end" gap="sm">
            <Button variant="outline" onClick={() => setConfirmDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="filled"
              color="red"
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
          </Group>
        </Stack>
      </Modal>
    </Paper>
  );
});

SystemSettingsPanel.displayName = 'SystemSettingsPanel';

export default SystemSettingsPanel;