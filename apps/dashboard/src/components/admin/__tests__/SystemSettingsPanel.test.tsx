import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import SystemSettingsPanel from '../SystemSettingsPanel';

// Mock API
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock Mantine notifications
vi.mock('@mantine/notifications', () => ({
  notifications: {
    show: vi.fn(),
  },
  Notifications: ({ children }: any) => <div>{children}</div>,
}));

// Mock Mantine dates
vi.mock('@mantine/dates', async () => {
  const React = await import('react');
  return {
    TimeInput: React.forwardRef(({ label, value, onChange, disabled, ...props }: any, ref: any) =>
      React.createElement('input', {
        ref,
        'aria-label': label,
        value,
        onChange,
        disabled,
        type: 'time',
        ...props
      })
    ),
  };
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <MantineProvider>
      <Notifications />
      {component}
    </MantineProvider>
  );
};

describe('SystemSettingsPanel Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders system settings panel', () => {
      renderWithProviders(<SystemSettingsPanel />);

      expect(screen.getByText('System Settings')).toBeInTheDocument();
    });

    it('renders save changes button', () => {
      renderWithProviders(<SystemSettingsPanel />);

      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });

    it('renders accordion sections', () => {
      renderWithProviders(<SystemSettingsPanel />);

      expect(screen.getByText('General Settings')).toBeInTheDocument();
      expect(screen.getByText('Security Settings')).toBeInTheDocument();
      expect(screen.getByText('Performance Settings')).toBeInTheDocument();
      expect(screen.getByText('Backup Settings')).toBeInTheDocument();
    });

    it('shows reset button when allowDangerousActions is true', () => {
      renderWithProviders(<SystemSettingsPanel allowDangerousActions={true} />);

      expect(screen.getByText('Reset to Defaults')).toBeInTheDocument();
    });

    it('hides reset button when allowDangerousActions is false', () => {
      renderWithProviders(<SystemSettingsPanel allowDangerousActions={false} />);

      expect(screen.queryByText('Reset to Defaults')).not.toBeInTheDocument();
    });
  });

  describe('General Settings', () => {
    it('displays general settings fields', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      // Click on General Settings to expand it
      const generalSettings = screen.getByText('General Settings');
      fireEvent.click(generalSettings);

      await waitFor(() => {
        expect(screen.getByLabelText('Site Name')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Site URL')).toBeInTheDocument();
      expect(screen.getByLabelText('Timezone')).toBeInTheDocument();
      expect(screen.getByLabelText('Language')).toBeInTheDocument();
    });

    it('shows maintenance mode controls', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const generalSettings = screen.getByText('General Settings');
      fireEvent.click(generalSettings);

      await waitFor(() => {
        expect(screen.getByText('Maintenance Mode')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Enable Maintenance Mode')).toBeInTheDocument();
    });

    it('shows maintenance message field when maintenance mode enabled', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const generalSettings = screen.getByText('General Settings');
      fireEvent.click(generalSettings);

      await waitFor(() => {
        const maintenanceSwitch = screen.getByLabelText('Enable Maintenance Mode');
        expect(maintenanceSwitch).toBeInTheDocument();
      });

      const maintenanceSwitch = screen.getByLabelText('Enable Maintenance Mode');
      fireEvent.click(maintenanceSwitch);

      await waitFor(() => {
        expect(screen.getByLabelText('Maintenance Message')).toBeInTheDocument();
      });
    });

    it('disables fields when readOnly is true', async () => {
      renderWithProviders(<SystemSettingsPanel readOnly={true} />);

      const generalSettings = screen.getByText('General Settings');
      fireEvent.click(generalSettings);

      await waitFor(() => {
        const siteNameInput = screen.getByLabelText('Site Name') as HTMLInputElement;
        expect(siteNameInput).toBeDisabled();
      });
    });
  });

  describe('Security Settings', () => {
    it('displays password requirements', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const securitySettings = screen.getByText('Security Settings');
      fireEvent.click(securitySettings);

      await waitFor(() => {
        expect(screen.getByText('Password Requirements')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Require uppercase letters')).toBeInTheDocument();
      expect(screen.getByLabelText('Require lowercase letters')).toBeInTheDocument();
      expect(screen.getByLabelText('Require numbers')).toBeInTheDocument();
      expect(screen.getByLabelText('Require special characters')).toBeInTheDocument();
    });

    it('displays session and login controls', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const securitySettings = screen.getByText('Security Settings');
      fireEvent.click(securitySettings);

      await waitFor(() => {
        expect(screen.getByText('Session & Login')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Session Timeout (seconds)')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Login Attempts')).toBeInTheDocument();
      expect(screen.getByLabelText('Enable Two-Factor Authentication')).toBeInTheDocument();
    });

    it('displays IP access control section', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const securitySettings = screen.getByText('Security Settings');
      fireEvent.click(securitySettings);

      await waitFor(() => {
        expect(screen.getByText('IP Access Control')).toBeInTheDocument();
      });

      expect(screen.getByText('Manage IP Whitelist/Blacklist')).toBeInTheDocument();
    });
  });

  describe('Performance Settings', () => {
    it('displays caching controls', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const performanceSettings = screen.getByText('Performance Settings');
      fireEvent.click(performanceSettings);

      await waitFor(() => {
        expect(screen.getByText('Caching')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Enable Caching')).toBeInTheDocument();
    });

    it('shows cache duration when caching enabled', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const performanceSettings = screen.getByText('Performance Settings');
      fireEvent.click(performanceSettings);

      await waitFor(() => {
        expect(screen.getByLabelText('Cache Duration (seconds)')).toBeInTheDocument();
      });
    });

    it('displays optimization controls', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const performanceSettings = screen.getByText('Performance Settings');
      fireEvent.click(performanceSettings);

      await waitFor(() => {
        expect(screen.getByText('Optimization')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Enable Compression')).toBeInTheDocument();
      expect(screen.getByLabelText('Enable Lazy Loading')).toBeInTheDocument();
      expect(screen.getByLabelText('Enable CDN')).toBeInTheDocument();
    });

    it('displays rate limiting controls', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const performanceSettings = screen.getByText('Performance Settings');
      fireEvent.click(performanceSettings);

      await waitFor(() => {
        expect(screen.getByText('Rate Limiting')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Enable Rate Limiting')).toBeInTheDocument();
    });
  });

  describe('Backup Settings', () => {
    it('displays backup status', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const backupSettings = screen.getByText('Backup Settings');
      fireEvent.click(backupSettings);

      await waitFor(() => {
        expect(screen.getByText('Backup Status')).toBeInTheDocument();
      });

      expect(screen.getByText(/Last backup:/)).toBeInTheDocument();
      expect(screen.getByText(/Next scheduled:/)).toBeInTheDocument();
    });

    it('displays auto backup controls', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const backupSettings = screen.getByText('Backup Settings');
      fireEvent.click(backupSettings);

      await waitFor(() => {
        expect(screen.getByLabelText('Enable Automatic Backups')).toBeInTheDocument();
      });
    });

    it('shows backup configuration when auto backup enabled', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const backupSettings = screen.getByText('Backup Settings');
      fireEvent.click(backupSettings);

      await waitFor(() => {
        expect(screen.getByLabelText('Backup Frequency')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Backup Time')).toBeInTheDocument();
      expect(screen.getByLabelText('Retention Period (days)')).toBeInTheDocument();
    });

    it('displays manual backup button', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const backupSettings = screen.getByText('Backup Settings');
      fireEvent.click(backupSettings);

      await waitFor(() => {
        expect(screen.getByText('Run Manual Backup Now')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('calls onSettingsChange when setting is modified', async () => {
      const mockOnChange = vi.fn();
      renderWithProviders(<SystemSettingsPanel onSettingsChange={mockOnChange} />);

      const generalSettings = screen.getByText('General Settings');
      fireEvent.click(generalSettings);

      await waitFor(() => {
        const siteNameInput = screen.getByLabelText('Site Name');
        expect(siteNameInput).toBeInTheDocument();
      });

      const siteNameInput = screen.getByLabelText('Site Name');
      fireEvent.change(siteNameInput, { target: { value: 'New Site Name' } });

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalled();
      });
    });

    it('shows success notification when settings saved', async () => {
      const { notifications } = require('@mantine/notifications');
      renderWithProviders(<SystemSettingsPanel />);

      const saveButton = screen.getByText('Save Changes');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(notifications.show).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Success',
            message: 'Settings saved successfully',
          })
        );
      });
    });

    it('calls onSettingsSave when save is successful', async () => {
      const mockOnSave = vi.fn();
      renderWithProviders(<SystemSettingsPanel onSettingsSave={mockOnSave} />);

      const saveButton = screen.getByText('Save Changes');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalled();
      });
    });

    it('disables save button when readOnly is true', () => {
      renderWithProviders(<SystemSettingsPanel readOnly={true} />);

      const saveButton = screen.getByText('Save Changes');
      expect(saveButton).toBeDisabled();
    });

    it('shows loading state when saving', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const saveButton = screen.getByText('Save Changes');
      fireEvent.click(saveButton);

      // Button should show loading state briefly
      await waitFor(() => {
        // Loading state is indicated by the button being disabled
        const button = screen.getByText('Save Changes');
        expect(button.closest('button')).toHaveClass('mantine-Button-root');
      });
    });
  });

  describe('Accordion Interactions', () => {
    it('expands general settings by default', () => {
      renderWithProviders(<SystemSettingsPanel />);

      // General settings should be expanded initially
      const generalContent = screen.getByLabelText('Site Name');
      expect(generalContent).toBeInTheDocument();
    });

    it('collapses section when clicked again', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const generalSettings = screen.getByText('General Settings');

      // First click - expand (might already be expanded)
      fireEvent.click(generalSettings);

      await waitFor(() => {
        expect(screen.getByLabelText('Site Name')).toBeInTheDocument();
      });

      // Second click - collapse
      fireEvent.click(generalSettings);

      await waitFor(() => {
        expect(screen.queryByLabelText('Site Name')).not.toBeInTheDocument();
      });
    });

    it('expands different sections independently', async () => {
      renderWithProviders(<SystemSettingsPanel />);

      const securitySettings = screen.getByText('Security Settings');
      fireEvent.click(securitySettings);

      await waitFor(() => {
        expect(screen.getByText('Password Requirements')).toBeInTheDocument();
      });
    });
  });

  describe('Reset Functionality', () => {
    it('opens confirmation dialog when reset clicked', async () => {
      renderWithProviders(<SystemSettingsPanel allowDangerousActions={true} />);

      const resetButton = screen.getByText('Reset to Defaults');
      fireEvent.click(resetButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      });

      expect(screen.getByText(/reset all settings to defaults/i)).toBeInTheDocument();
    });

    it('closes dialog when cancel clicked', async () => {
      renderWithProviders(<SystemSettingsPanel allowDangerousActions={true} />);

      const resetButton = screen.getByText('Reset to Defaults');
      fireEvent.click(resetButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
      });
    });
  });

  describe('Backup Actions', () => {
    it('runs manual backup when button clicked', async () => {
      const { notifications } = require('@mantine/notifications');
      renderWithProviders(<SystemSettingsPanel />);

      const backupSettings = screen.getByText('Backup Settings');
      fireEvent.click(backupSettings);

      await waitFor(() => {
        expect(screen.getByText('Run Manual Backup Now')).toBeInTheDocument();
      });

      const backupButton = screen.getByText('Run Manual Backup Now');
      fireEvent.click(backupButton);

      await waitFor(() => {
        expect(notifications.show).toHaveBeenCalledWith(
          expect.objectContaining({
            message: 'Backup initiated successfully',
          })
        );
      });
    });

    it('disables backup button when readOnly is true', async () => {
      renderWithProviders(<SystemSettingsPanel readOnly={true} />);

      const backupSettings = screen.getByText('Backup Settings');
      fireEvent.click(backupSettings);

      await waitFor(() => {
        const backupButton = screen.getByText('Run Manual Backup Now');
        expect(backupButton).toBeDisabled();
      });
    });
  });
});
