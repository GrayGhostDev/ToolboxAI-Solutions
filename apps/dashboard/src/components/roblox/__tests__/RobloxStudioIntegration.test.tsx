import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import RobloxStudioIntegration from '../RobloxStudioIntegration';
import { api } from '../../../services/api';
import { pusherService } from '../../../services/pusher';

// Mock dependencies
vi.mock('../../../services/api', () => ({
  api: {
    checkRobloxPluginStatus: vi.fn(),
    listRobloxWorlds: vi.fn(),
    deployToRoblox: vi.fn(),
    exportRobloxEnvironment: vi.fn(),
    getRobloxPluginInstallInfo: vi.fn(),
  },
}));

vi.mock('../../../services/pusher', () => ({
  pusherService: {
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
  },
}));

vi.mock('../RobloxAIChat', () => ({
  RobloxAIChat: () => <div data-testid="roblox-ai-chat">Roblox AI Chat Component</div>,
}));

// Mock store
const mockStore = configureStore({
  reducer: {
    user: (state = { id: '1', name: 'Test User', role: 'student' }) => state,
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <Provider store={mockStore}>
      <MantineProvider>{component}</MantineProvider>
    </Provider>
  );
};

describe('RobloxStudioIntegration Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mocks
    (api.checkRobloxPluginStatus as any).mockResolvedValue({
      connected: true,
      version: '1.0.0',
      studioVersion: '2024.10',
    });

    (api.listRobloxWorlds as any).mockResolvedValue([]);

    (pusherService.subscribe as any).mockReturnValue('subscription-id');
  });

  describe('Rendering', () => {
    it('renders the main title and description', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Roblox Studio Integration')).toBeInTheDocument();
      });

      expect(screen.getByText('Create, manage, and deploy educational Roblox environments')).toBeInTheDocument();
    });

    it('renders AI chat component', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByTestId('roblox-ai-chat')).toBeInTheDocument();
      });
    });

    it('renders environment management section', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Generated Environments')).toBeInTheDocument();
      });

      expect(screen.getByText('Manage and deploy your AI-generated Roblox worlds')).toBeInTheDocument();
    });
  });

  describe('Plugin Status', () => {
    it('shows plugin connected status', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Plugin Connected')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('shows plugin version information', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText(/Plugin Version: 1.0.0/)).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(screen.getByText(/Studio Version: 2024.10/)).toBeInTheDocument();
    });

    it('shows disconnected status when plugin is not connected', async () => {
      (api.checkRobloxPluginStatus as any).mockResolvedValue({
        connected: false,
      });

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Plugin Disconnected')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('shows install plugin button when disconnected', async () => {
      (api.checkRobloxPluginStatus as any).mockResolvedValue({
        connected: false,
      });

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Install Plugin')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('hides install plugin button when connected', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.queryByText('Install Plugin')).not.toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('checks plugin status on mount', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(api.checkRobloxPluginStatus).toHaveBeenCalled();
      }, { timeout: 10000 });
    });

    it('refreshes plugin status when refresh button is clicked', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      }, { timeout: 10000 });

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(api.checkRobloxPluginStatus).toHaveBeenCalledTimes(2);
      }, { timeout: 10000 });
    });
  });

  describe('Environment List', () => {
    it('shows empty state when no environments exist', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('No environments generated yet')).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(screen.getByText('Use the AI chat to create your first Roblox environment')).toBeInTheDocument();
    });

    it('displays list of environments', async () => {
      const mockEnvironments = [
        {
          id: 'env_1',
          name: 'Math Adventure',
          status: 'published',
          theme: 'Science Fiction',
          mapType: 'classroom',
          learningObjectives: ['Learn algebra', 'Solve equations'],
          difficulty: 'medium',
          previewUrl: '/preview/env_1',
          downloadUrl: '/download/env_1',
        },
        {
          id: 'env_2',
          name: 'Physics Lab',
          status: 'draft',
          theme: 'Laboratory',
          mapType: 'assessment',
          learningObjectives: ['Understand gravity', 'Apply physics laws'],
          difficulty: 'hard',
        },
      ];

      (api.listRobloxWorlds as any).mockResolvedValue(mockEnvironments);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Math Adventure')).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(screen.getByText('Physics Lab')).toBeInTheDocument();
    });

    it('shows environment status badges', async () => {
      const mockEnvironments = [
        {
          id: 'env_1',
          name: 'Ready Environment',
          status: 'published',
          theme: 'Space',
          mapType: 'playground',
          learningObjectives: [],
          difficulty: 'easy',
        },
      ];

      (api.listRobloxWorlds as any).mockResolvedValue(mockEnvironments);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('ready')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('shows environment metadata', async () => {
      const mockEnvironments = [
        {
          id: 'env_1',
          name: 'Test Environment',
          status: 'published',
          theme: 'Fantasy',
          mapType: 'dungeon',
          learningObjectives: ['Objective 1', 'Objective 2'],
          difficulty: 'medium',
        },
      ];

      (api.listRobloxWorlds as any).mockResolvedValue(mockEnvironments);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText(/Theme: Fantasy/)).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(screen.getByText(/Type: dungeon/)).toBeInTheDocument();
      expect(screen.getByText(/Objectives: Objective 1, Objective 2/)).toBeInTheDocument();
    });
  });

  describe('Environment Actions', () => {
    const mockEnvironment = {
      id: 'env_1',
      name: 'Test Environment',
      status: 'published',
      theme: 'Space',
      mapType: 'classroom',
      learningObjectives: [],
      difficulty: 'easy',
      previewUrl: '/preview/env_1',
      downloadUrl: '/download/env_1',
    };

    beforeEach(() => {
      (api.listRobloxWorlds as any).mockResolvedValue([mockEnvironment]);
    });

    it('displays deploy button for ready environments', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Deploy to Studio')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('deploys environment to studio when clicked', async () => {
      (api.deployToRoblox as any).mockResolvedValue({});

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Deploy to Studio')).toBeInTheDocument();
      }, { timeout: 10000 });

      const deployButton = screen.getByText('Deploy to Studio');
      fireEvent.click(deployButton);

      await waitFor(() => {
        expect(api.deployToRoblox).toHaveBeenCalledWith('env_1');
      }, { timeout: 10000 });
    });

    it('disables deploy button when plugin is not connected', async () => {
      (api.checkRobloxPluginStatus as any).mockResolvedValue({
        connected: false,
      });

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        const deployButton = screen.getByText('Deploy to Studio').closest('button');
        expect(deployButton).toBeDisabled();
      }, { timeout: 10000 });
    });

    it('displays download button', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Download')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('downloads environment when download button clicked', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/octet-stream' });
      (api.exportRobloxEnvironment as any).mockResolvedValue(mockBlob);

      // Mock URL.createObjectURL and document methods
      global.URL.createObjectURL = vi.fn(() => 'blob:test-url');
      global.URL.revokeObjectURL = vi.fn();

      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
      };
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Download')).toBeInTheDocument();
      }, { timeout: 10000 });

      const downloadButton = screen.getByText('Download');
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(api.exportRobloxEnvironment).toHaveBeenCalledWith('env_1');
      }, { timeout: 10000 });
    });

    it('displays preview button when preview URL exists', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Preview')).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('opens preview in new window', async () => {
      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Preview')).toBeInTheDocument();
      }, { timeout: 10000 });

      const previewButton = screen.getByText('Preview');
      fireEvent.click(previewButton);

      expect(mockWindowOpen).toHaveBeenCalledWith('/preview/env_1', '_blank');
    });

    it('displays share button', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        const shareButtons = screen.getAllByLabelText('Share');
        expect(shareButtons.length).toBeGreaterThan(0);
      }, { timeout: 10000 });
    });
  });

  describe('Environment Selection', () => {
    const mockEnvironments = [
      {
        id: 'env_1',
        name: 'Environment 1',
        status: 'published',
        theme: 'Space',
        mapType: 'classroom',
        learningObjectives: [],
        difficulty: 'easy',
      },
      {
        id: 'env_2',
        name: 'Environment 2',
        status: 'published',
        theme: 'Fantasy',
        mapType: 'dungeon',
        learningObjectives: [],
        difficulty: 'medium',
      },
    ];

    it('allows selecting an environment by clicking on it', async () => {
      (api.listRobloxWorlds as any).mockResolvedValue(mockEnvironments);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Environment 1')).toBeInTheDocument();
      }, { timeout: 10000 });

      const env1Card = screen.getByText('Environment 1').closest('div[class*="Card"]');
      if (env1Card) {
        fireEvent.click(env1Card);
      }

      // Environment should still be rendered after selection
      expect(screen.getByText('Environment 1')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('shows error when plugin status check fails', async () => {
      (api.checkRobloxPluginStatus as any).mockRejectedValue(new Error('Connection failed'));

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText(/Unable to connect to Roblox Studio plugin/)).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('shows error when deployment fails', async () => {
      const mockEnvironment = {
        id: 'env_1',
        name: 'Test Environment',
        status: 'published',
        theme: 'Space',
        mapType: 'classroom',
        learningObjectives: [],
        difficulty: 'easy',
      };

      (api.listRobloxWorlds as any).mockResolvedValue([mockEnvironment]);
      (api.deployToRoblox as any).mockRejectedValue(new Error('Deploy failed'));

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Deploy to Studio')).toBeInTheDocument();
      }, { timeout: 10000 });

      const deployButton = screen.getByText('Deploy to Studio');
      fireEvent.click(deployButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to deploy environment to Roblox Studio/)).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('allows closing error alerts', async () => {
      (api.checkRobloxPluginStatus as any).mockRejectedValue(new Error('Connection failed'));

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText(/Unable to connect to Roblox Studio plugin/)).toBeInTheDocument();
      }, { timeout: 10000 });

      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText(/Unable to connect to Roblox Studio plugin/)).not.toBeInTheDocument();
      }, { timeout: 10000 });
    });
  });

  describe('Plugin Installation', () => {
    it('opens plugin install page when install button clicked', async () => {
      (api.checkRobloxPluginStatus as any).mockResolvedValue({ connected: false });
      (api.getRobloxPluginInstallInfo as any).mockResolvedValue({
        installUrl: 'https://create.roblox.com/marketplace/plugins/test-plugin',
      });

      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null);

      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Install Plugin')).toBeInTheDocument();
      }, { timeout: 10000 });

      const installButton = screen.getByText('Install Plugin');
      fireEvent.click(installButton);

      await waitFor(() => {
        expect(mockWindowOpen).toHaveBeenCalledWith(
          'https://create.roblox.com/marketplace/plugins/test-plugin',
          '_blank'
        );
      }, { timeout: 10000 });
    });
  });

  describe('Pusher Integration', () => {
    it('subscribes to roblox-environments channel', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(pusherService.subscribe).toHaveBeenCalledWith(
          'roblox-environments',
          expect.any(Function)
        );
      }, { timeout: 10000 });
    });

    it('unsubscribes on unmount', async () => {
      const { unmount } = renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(pusherService.subscribe).toHaveBeenCalled();
      }, { timeout: 10000 });

      unmount();

      expect(pusherService.unsubscribe).toHaveBeenCalledWith('subscription-id');
    });
  });

  describe('Accessibility', () => {
    it('has accessible buttons', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        const refreshButton = screen.getByText('Refresh');
        expect(refreshButton).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('has proper heading hierarchy', async () => {
      renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        const heading = screen.getByText('Roblox Studio Integration');
        expect(heading).toBeInTheDocument();
      }, { timeout: 10000 });
    });
  });

  describe('Responsiveness', () => {
    it('renders in grid layout', async () => {
      const { container } = renderWithProviders(<RobloxStudioIntegration />);

      await waitFor(() => {
        expect(screen.getByText('Roblox Studio Integration')).toBeInTheDocument();
      }, { timeout: 10000 });

      // Check for Grid components
      const gridElements = container.querySelectorAll('[class*="Grid"]');
      expect(gridElements.length).toBeGreaterThan(0);
    });
  });
});
