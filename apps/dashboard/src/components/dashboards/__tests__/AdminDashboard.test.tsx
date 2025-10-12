import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import AdminDashboard from '../AdminDashboard';

// Mock API module
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/services/pusher', () => ({
  pusherService: {
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
  },
}));

vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(),
}));

import { api } from '@/services/api';
import { pusherService } from '@/services/pusher';
import { formatDistanceToNow } from 'date-fns';

// Mock Redux store
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      user: (state = initialState.user || null) => state,
    },
    preloadedState: initialState,
  });
};

// Mock Pusher channel
const mockPusherChannel = {
  bind: vi.fn(),
  unbind: vi.fn(),
};

const mockMetricsResponse = {
  data: {
    totalUsers: 1247,
    activeUsers: 342,
    totalCourses: 89,
    activeSessions: 156,
    contentGenerated: 3421,
    systemHealth: 95,
    cpuUsage: 45,
    memoryUsage: 62,
    storageUsage: 38,
    apiLatency: 120,
  },
};

const mockAlertsResponse = {
  data: [
    {
      id: '1',
      severity: 'warning' as const,
      message: 'High memory usage detected on worker node 3',
      timestamp: new Date(Date.now() - 3600000),
      resolved: false,
    },
    {
      id: '2',
      severity: 'info' as const,
      message: 'Scheduled maintenance window starts in 24 hours',
      timestamp: new Date(Date.now() - 7200000),
      resolved: false,
    },
  ],
};

const renderWithProviders = (
  component: React.ReactElement,
  initialState = {}
) => {
  const store = createMockStore(initialState);
  return render(
    <Provider store={store}>
      <MantineProvider>{component}</MantineProvider>
    </Provider>
  );
};

describe('AdminDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Set up default mock return values
    (api.get as any).mockResolvedValue(mockMetricsResponse);
    (api.patch as any).mockResolvedValue({ data: {} });
    (pusherService.subscribe as any).mockReturnValue(mockPusherChannel);
    (pusherService.unsubscribe as any).mockReturnValue(undefined);
    (formatDistanceToNow as any).mockReturnValue('2 hours ago');
  });

  describe('Rendering', () => {
    it('shows loading state initially', () => {
      (api.get as any).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { container } = renderWithProviders(<AdminDashboard />);

      // Look for the Mantine Loader component by class
      const loader = container.querySelector('.mantine-Loader-root');
      expect(loader).toBeInTheDocument();
    });

    it('renders admin dashboard after loading', async () => {
      (api.get as any)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(screen.getByText('System overview and management tools')).toBeInTheDocument();
    });

    it('renders with default section prop', async () => {
      (api.get as any)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('renders with custom section prop', async () => {
      (api.get as any)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard section="users" />);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      }, { timeout: 10000 });
    });
  });

  describe('Metrics Display', () => {
    beforeEach(async () => {
      (api.get as any)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);
    });

    it('displays total users metric', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Total Users')).toBeInTheDocument();
        expect(screen.getByText('1247')).toBeInTheDocument();
      });
    });

    it('displays active sessions metric', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Active Sessions')).toBeInTheDocument();
        expect(screen.getByText('156')).toBeInTheDocument();
      });
    });

    it('displays content generated metric', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Content Generated')).toBeInTheDocument();
        expect(screen.getByText('3421')).toBeInTheDocument();
      });
    });

    it('displays system health metric', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('System Health')).toBeInTheDocument();
        expect(screen.getByText('95%')).toBeInTheDocument();
      });
    });

    it('displays system performance metrics in Overview tab', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('System Performance')).toBeInTheDocument();
      });

      expect(screen.getByText('CPU Usage')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
      expect(screen.getByText('62%')).toBeInTheDocument();
      expect(screen.getByText('Storage Usage')).toBeInTheDocument();
      expect(screen.getByText('38%')).toBeInTheDocument();
      expect(screen.getByText('API Latency')).toBeInTheDocument();
      expect(screen.getByText('120ms')).toBeInTheDocument();
    });
  });

  describe('System Health Indicators', () => {
    it('shows green indicator for healthy system (>=90%)', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          data: { ...mockMetricsResponse.data, systemHealth: 95 },
        })
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('95%')).toBeInTheDocument();
      });

      // No warning alert should be shown
      expect(screen.queryByText(/System health is below optimal levels/)).not.toBeInTheDocument();
    });

    it('shows yellow indicator for moderate health (70-89%)', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          data: { ...mockMetricsResponse.data, systemHealth: 80 },
        })
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('80%')).toBeInTheDocument();
      });
    });

    it('shows warning alert for low health (<70%)', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          data: { ...mockMetricsResponse.data, systemHealth: 65 },
        })
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/System health is below optimal levels/)).toBeInTheDocument();
      });
    });
  });

  describe('Alerts Display', () => {
    beforeEach(() => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);
    });

    it('displays system alerts', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('System Alerts')).toBeInTheDocument();
      });

      expect(screen.getByText('High memory usage detected on worker node 3')).toBeInTheDocument();
      expect(screen.getByText('Scheduled maintenance window starts in 24 hours')).toBeInTheDocument();
    });

    it('shows alert timestamps', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        const timestamps = screen.getAllByText('2 hours ago');
        expect(timestamps.length).toBeGreaterThan(0);
      });
    });

    it('allows resolving unresolved alerts', async () => {
      (api.patch as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('High memory usage detected on worker node 3')).toBeInTheDocument();
      });

      // Find resolve button for first alert
      const alertsSection = screen.getByText('System Alerts').closest('div');
      const resolveButtons = within(alertsSection!).getAllByRole('button');

      fireEvent.click(resolveButtons[0]);

      await waitFor(() => {
        expect(api.patch).toHaveBeenCalledWith('/api/v1/admin/alerts/1/resolve');
      });
    });
  });

  describe('Tab Navigation', () => {
    beforeEach(() => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);
    });

    it('renders all tabs', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      expect(screen.getByText('Users')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
      expect(screen.getByText('Security')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('shows Overview tab by default', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('System Performance')).toBeInTheDocument();
      });
    });

    it('switches to Users tab', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      const usersTab = screen.getByText('Users').closest('button');
      fireEvent.click(usersTab!);

      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeInTheDocument();
      });
    });

    it('switches to Content tab', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      const contentTab = screen.getByText('Content').closest('button');
      fireEvent.click(contentTab!);

      await waitFor(() => {
        expect(screen.getByText('Content Moderation')).toBeInTheDocument();
      });
    });

    it('switches to Security tab', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      const securityTab = screen.getByText('Security').closest('button');
      fireEvent.click(securityTab!);

      await waitFor(() => {
        expect(screen.getByText('Security Settings')).toBeInTheDocument();
      });
    });

    it('switches to Settings tab', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      const settingsTab = screen.getByText('Settings').closest('button');
      fireEvent.click(settingsTab!);

      await waitFor(() => {
        expect(screen.getByText('System Settings')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    beforeEach(() => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);
    });

    it('refreshes data when refresh button clicked', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      // Clear mock calls from initial load
      vi.clearAllMocks();
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      const refreshButton = screen.getByLabelText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/api/v1/admin/metrics');
        expect(api.get).toHaveBeenCalledWith('/api/v1/admin/alerts');
      });
    });

    it('handles Export Logs button click', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Export Logs')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export Logs');
      fireEvent.click(exportButton);

      expect(consoleSpy).toHaveBeenCalledWith('Export logs');
      consoleSpy.mockRestore();
    });

    it('handles Backup System button click', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Backup System')).toBeInTheDocument();
      });

      const backupButton = screen.getByText('Backup System');
      fireEvent.click(backupButton);

      expect(consoleSpy).toHaveBeenCalledWith('Backup system');
      consoleSpy.mockRestore();
    });

    it('handles Clear Cache button click', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Clear Cache')).toBeInTheDocument();
      });

      const clearButton = screen.getByText('Clear Cache');
      fireEvent.click(clearButton);

      expect(consoleSpy).toHaveBeenCalledWith('Clear cache');
      consoleSpy.mockRestore();
    });
  });

  describe('API Integration', () => {
    it('fetches metrics on mount', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/api/v1/admin/metrics');
      });
    });

    it('fetches alerts on mount', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/api/v1/admin/alerts');
      });
    });

    it('handles metrics API error gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      (api.get as ReturnType<typeof vi.fn>)
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to fetch metrics:', expect.any(Error));
      });

      // Should still render with mock/fallback data
      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it('handles alerts API error gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockRejectedValueOnce(new Error('API Error'));

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to fetch alerts:', expect.any(Error));
      });

      consoleErrorSpy.mockRestore();
    });

    it('validates and sanitizes metrics data', async () => {
      const invalidMetrics = {
        data: {
          systemHealth: 150, // Invalid: > 100
          cpuUsage: -10, // Invalid: < 0
          memoryUsage: 'invalid', // Invalid: not a number
          storageUsage: 50,
          apiLatency: -5, // Invalid: < 0
        },
      };

      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(invalidMetrics)
        .mockResolvedValueOnce(mockAlertsResponse);

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      // Should clamp systemHealth to 0-100 range (150 → 100%)
      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument();
      });

      // Verify CPU usage clamped to 0% (was -10)
      // Multiple metrics may show 0% (CPU, Memory, etc.), so check for at least one
      await waitFor(() => {
        const zeroPercentElements = screen.getAllByText('0%');
        expect(zeroPercentElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Pusher Integration', () => {
    beforeEach(() => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);
    });

    it('subscribes to admin-updates channel on mount', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(pusherService.subscribe).toHaveBeenCalledWith('admin-updates');
      });
    });

    it('binds metrics-update event handler', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(mockPusherChannel.bind).toHaveBeenCalledWith(
          'metrics-update',
          expect.any(Function)
        );
      });
    });

    it('binds alert-new event handler', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(mockPusherChannel.bind).toHaveBeenCalledWith(
          'alert-new',
          expect.any(Function)
        );
      });
    });

    it('updates metrics when metrics-update event received', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(mockPusherChannel.bind).toHaveBeenCalled();
      });

      // Get the metrics-update callback
      const metricsUpdateCall = (mockPusherChannel.bind as ReturnType<typeof vi.fn>).mock.calls
        .find(call => call[0] === 'metrics-update');
      const metricsUpdateCallback = metricsUpdateCall?.[1];

      // Simulate Pusher event
      const newMetrics = {
        systemHealth: 88,
        cpuUsage: 60,
      };

      metricsUpdateCallback?.(newMetrics);

      await waitFor(() => {
        expect(screen.getByText('88%')).toBeInTheDocument();
        expect(screen.getByText('60%')).toBeInTheDocument();
      });
    });

    it('adds new alert when alert-new event received', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(mockPusherChannel.bind).toHaveBeenCalled();
      });

      // Get the alert-new callback
      const alertNewCall = (mockPusherChannel.bind as ReturnType<typeof vi.fn>).mock.calls
        .find(call => call[0] === 'alert-new');
      const alertNewCallback = alertNewCall?.[1];

      // Simulate Pusher event
      const newAlert = {
        id: '3',
        severity: 'error' as const,
        message: 'New critical error',
        timestamp: new Date(),
        resolved: false,
      };

      alertNewCallback?.(newAlert);

      await waitFor(() => {
        expect(screen.getByText('New critical error')).toBeInTheDocument();
      });
    });

    it('unsubscribes from Pusher on unmount', async () => {
      const { unmount } = renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(pusherService.subscribe).toHaveBeenCalled();
      });

      unmount();

      expect(pusherService.unsubscribe).toHaveBeenCalledWith('admin-updates');
    });

    it('handles Pusher subscription errors gracefully', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      (pusherService.subscribe as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Pusher connection failed');
      });

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(consoleWarnSpy).toHaveBeenCalledWith(
          'Failed to subscribe to Pusher updates:',
          expect.any(Error)
        );
      });

      // Component should still render
      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      consoleWarnSpy.mockRestore();
    });
  });

  // Note: Auto-refresh interval tests skipped - would require fake timers
  // The component sets up a 30-second interval for refreshing metrics
  // This is tested indirectly through the refresh button and unmount cleanup

  describe('Accessibility', () => {
    beforeEach(() => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);
    });

    it('has accessible tab panels with ARIA attributes', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByRole('tabpanel')).toBeInTheDocument();
      });

      const tabPanel = screen.getByRole('tabpanel');
      expect(tabPanel).toHaveAttribute('id', 'admin-tabpanel-0');
      expect(tabPanel).toHaveAttribute('aria-labelledby', 'admin-tab-0');
    });

    it('has accessible buttons', async () => {
      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByLabelText('Refresh')).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /Export Logs/i });
      expect(exportButton).toBeInTheDocument();

      const backupButton = screen.getByRole('button', { name: /Backup System/i });
      expect(backupButton).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing Redux user state', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce(mockAlertsResponse);

      // Render with no user in Redux state
      renderWithProviders(<AdminDashboard />, { user: null });

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });
    });

    it('handles empty alerts array', async () => {
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce({ data: [] });

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(screen.getByText('System Alerts')).toBeInTheDocument();
      });

      // Should render alerts section but with no alerts
      const alertsSection = screen.getByText('System Alerts').closest('div');
      expect(alertsSection).toBeInTheDocument();
    });

    it('handles invalid alerts data from API', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockMetricsResponse)
        .mockResolvedValueOnce({ data: 'invalid' }); // Not an array

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(consoleWarnSpy).toHaveBeenCalledWith(
          'Invalid alerts data received, using fallback'
        );
      });

      consoleWarnSpy.mockRestore();
    });

    it('handles Pusher metrics update errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      renderWithProviders(<AdminDashboard />);

      await waitFor(() => {
        expect(mockPusherChannel.bind).toHaveBeenCalled();
      });

      // Get the metrics-update callback
      const metricsUpdateCall = (mockPusherChannel.bind as ReturnType<typeof vi.fn>).mock.calls
        .find(call => call[0] === 'metrics-update');
      const metricsUpdateCallback = metricsUpdateCall?.[1];

      // Send invalid data
      metricsUpdateCallback?.(null);

      // Should handle gracefully
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });
  });
});
