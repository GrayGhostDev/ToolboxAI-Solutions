import {
  Box, Button, Text, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader,
  Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio,
  Switch, Slider, Rating, Skeleton, Table, useMantineTheme
} from '@mantine/core';
import { IconRefresh, IconDeviceFloppy } from '@tabler/icons-react';

// Helper function for color transparency (replaces MUI alpha)
const alpha = (color: string, opacity: number) => {
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
};
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
  const theme = useMantineTheme();
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
      <Group justify="space-between" align="center" mb="lg">
        <Text size="xl" fw={600}>
          System Settings
        </Text>
        <Group gap="md">
          <Button
            variant="outline"
            leftSection={<IconRefresh />}
            onClick={handleReset}
            disabled={!hasChanges || saving}
          >
            Reset
          </Button>
          <Button
            variant="filled"
            leftSection={<IconDeviceFloppy />}
            onClick={handleSave}
            disabled={!hasChanges || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Group>
      </Group>

      {hasChanges && (
        <Alert color="yellow" mb="md">
          You have unsaved changes. Don't forget to save before leaving this page.
        </Alert>
      )}

      <Stack gap="md">
        {/* General Settings */}
        <Card withBorder>
          <Text fw={600} size="lg" mb="md">General Settings</Text>
          <Stack gap="md">
            <TextInput
              label="Site Name"
              value={settings.general.siteName}
              onChange={(e) => handleChange('general', 'siteName', e.target.value)}
            />
            <TextInput
              label="Site URL"
              value={settings.general.siteUrl}
              onChange={(e) => handleChange('general', 'siteUrl', e.target.value)}
            />
            <TextInput
              label="Admin Email"
              type="email"
              value={settings.general.adminEmail}
              onChange={(e) => handleChange('general', 'adminEmail', e.target.value)}
            />
            <Select
              label="Timezone"
              value={settings.general.timezone}
              onChange={(value) => handleChange('general', 'timezone', value)}
              data={[
                { value: 'America/New_York', label: 'Eastern Time' },
                { value: 'America/Chicago', label: 'Central Time' },
                { value: 'America/Denver', label: 'Mountain Time' },
                { value: 'America/Los_Angeles', label: 'Pacific Time' },
                { value: 'UTC', label: 'UTC' }
              ]}
            />
            <Select
              label="Language"
              value={settings.general.language}
              onChange={(value) => handleChange('general', 'language', value)}
              data={[
                { value: 'en', label: 'English' },
                { value: 'es', label: 'Spanish' },
                { value: 'fr', label: 'French' },
                { value: 'de', label: 'German' }
              ]}
            />
            <Group justify="space-between">
              <Text>Maintenance Mode</Text>
              <Group gap="xs">
                <Switch
                  checked={settings.general.maintenanceMode}
                  onChange={(e) => handleChange('general', 'maintenanceMode', e.currentTarget.checked)}
                />
                {settings.general.maintenanceMode && (
                  <Badge color="yellow" size="sm">Active</Badge>
                )}
              </Group>
            </Group>
          </Stack>
        </Card>

        {/* Security Settings */}
        <Card withBorder>
          <Text fw={600} size="lg" mb="md">Security Settings</Text>
          <Stack gap="md">
            <Group justify="space-between">
              <Text>Require Two-Factor Authentication</Text>
              <Switch
                checked={settings.security.twoFactorAuth}
                onChange={(e) => handleChange('security', 'twoFactorAuth', e.currentTarget.checked)}
              />
            </Group>
            <TextInput
              label="Session Timeout (minutes)"
              type="number"
              value={settings.security.sessionTimeout}
              onChange={(e) => handleChange('security', 'sessionTimeout', parseInt(e.target.value))}
            />
            <TextInput
              label="Minimum Password Length"
              type="number"
              value={settings.security.passwordMinLength}
              onChange={(e) => handleChange('security', 'passwordMinLength', parseInt(e.target.value))}
            />
            <Group justify="space-between">
              <Text>Require Special Characters</Text>
              <Switch
                checked={settings.security.passwordRequireSpecial}
                onChange={(e) => handleChange('security', 'passwordRequireSpecial', e.currentTarget.checked)}
              />
            </Group>
            <Group justify="space-between">
              <Text>Require Numbers</Text>
              <Switch
                checked={settings.security.passwordRequireNumbers}
                onChange={(e) => handleChange('security', 'passwordRequireNumbers', e.currentTarget.checked)}
              />
            </Group>
            <TextInput
              label="Max Login Attempts"
              type="number"
              value={settings.security.maxLoginAttempts}
              onChange={(e) => handleChange('security', 'maxLoginAttempts', parseInt(e.target.value))}
            />
          </Stack>
        </Card>

        {/* Email Settings */}
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
          <Card withBorder>
            <Text fw={600} size="lg" mb="md">Email Settings</Text>
            <Stack gap="md">
              <TextInput
                label="SMTP Host"
                value={settings.email.smtpHost}
                onChange={(e) => handleChange('email', 'smtpHost', e.target.value)}
              />
              <TextInput
                label="SMTP Port"
                type="number"
                value={settings.email.smtpPort}
                onChange={(e) => handleChange('email', 'smtpPort', parseInt(e.target.value))}
              />
              <TextInput
                label="SMTP User"
                value={settings.email.smtpUser}
                onChange={(e) => handleChange('email', 'smtpUser', e.target.value)}
              />
              <TextInput
                label="SMTP Password"
                type="password"
                value={settings.email.smtpPassword}
                onChange={(e) => handleChange('email', 'smtpPassword', e.target.value)}
              />
              <Group justify="space-between">
                <Text>Use Secure Connection (TLS)</Text>
                <Switch
                  checked={settings.email.smtpSecure}
                  onChange={(e) => handleChange('email', 'smtpSecure', e.currentTarget.checked)}
                />
              </Group>
              <TextInput
                label="From Email"
                value={settings.email.emailFrom}
                onChange={(e) => handleChange('email', 'emailFrom', e.target.value)}
              />
            </Stack>
          </Card>

          {/* Feature Toggles */}
          <Card withBorder>
            <Text fw={600} size="lg" mb="md">Feature Toggles</Text>
            <Stack gap="md">
              <Group justify="space-between">
                <Text>Enable User Registration</Text>
                <Switch
                  checked={settings.features.enableRegistration}
                  onChange={(e) => handleChange('features', 'enableRegistration', e.currentTarget.checked)}
                />
              </Group>
              <Group justify="space-between">
                <Text>Enable Roblox Integration</Text>
                <Switch
                  checked={settings.features.enableRobloxIntegration}
                  onChange={(e) => handleChange('features', 'enableRobloxIntegration', e.currentTarget.checked)}
                />
              </Group>
              <Group justify="space-between">
                <Text>Enable AI Content Generation</Text>
                <Switch
                  checked={settings.features.enableAIContent}
                  onChange={(e) => handleChange('features', 'enableAIContent', e.currentTarget.checked)}
                />
              </Group>
              <Group justify="space-between">
                <Text>Enable Report Generation</Text>
                <Switch
                  checked={settings.features.enableReports}
                  onChange={(e) => handleChange('features', 'enableReports', e.currentTarget.checked)}
                />
              </Group>
              <Group justify="space-between">
                <Text>Enable Messaging System</Text>
                <Switch
                  checked={settings.features.enableMessaging}
                  onChange={(e) => handleChange('features', 'enableMessaging', e.currentTarget.checked)}
                />
              </Group>
              <Group justify="space-between">
                <Text>Enable Gamification</Text>
                <Switch
                  checked={settings.features.enableGamification}
                  onChange={(e) => handleChange('features', 'enableGamification', e.currentTarget.checked)}
                />
              </Group>
            </Stack>
          </Card>
        </SimpleGrid>

        {/* API Settings */}
        <Card withBorder>
          <Text fw={600} size="lg" mb="md">API Settings</Text>
          <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
            <TextInput
              label="Rate Limit (requests/minute)"
              type="number"
              value={settings.api.rateLimit}
              onChange={(e) => handleChange('api', 'rateLimit', parseInt(e.target.value))}
            />
            <TextInput
              label="API Timeout (seconds)"
              type="number"
              value={settings.api.apiTimeout}
              onChange={(e) => handleChange('api', 'apiTimeout', parseInt(e.target.value))}
            />
            <TextInput
              label="Max Upload Size (MB)"
              type="number"
              value={settings.api.maxUploadSize}
              onChange={(e) => handleChange('api', 'maxUploadSize', parseInt(e.target.value))}
            />
          </SimpleGrid>
          <TextInput
            label="Allowed Origins (comma-separated)"
            value={settings.api.allowedOrigins}
            onChange={(e) => handleChange('api', 'allowedOrigins', e.target.value)}
            mt="md"
          />
        </Card>
      </Stack>
    </Box>
  );
};

export default SystemSettings;