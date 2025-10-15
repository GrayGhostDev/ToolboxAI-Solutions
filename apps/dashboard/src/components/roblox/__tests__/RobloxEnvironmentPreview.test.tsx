import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 10000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { BrowserRouter } from 'react-router-dom';
import RobloxEnvironmentPreview from '../RobloxEnvironmentPreview';
import { PusherContext } from '../../../contexts/PusherContext';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock Pusher context
const mockPusherContext = {
  send: vi.fn(),
  subscribe: vi.fn(),
  unsubscribe: vi.fn(),
  isConnected: true,
  connectionState: 'connected' as const,
};

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <MantineProvider>
        <PusherContext.Provider value={mockPusherContext}>
          {component}
        </PusherContext.Provider>
      </MantineProvider>
    </BrowserRouter>
  );
};

describe('RobloxEnvironmentPreview Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders environment data', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Algebra Basics Session')).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(screen.getByText('Interactive 3D classroom for mathematics learning')).toBeInTheDocument();
    });

    it('renders with custom environmentId prop', async () => {
      renderWithProviders(<RobloxEnvironmentPreview environmentId="custom_env_123" />);

      await waitFor(() => {
        expect(screen.getByText('Algebra Basics Session')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('renders environment status badge', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('active')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('View Modes', () => {
    it('defaults to preview mode with iframe', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByTitle('Environment Preview')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('switches to editor mode', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Algebra Basics Session')).toBeInTheDocument();
      }, { timeout: 5000 });

      const editorButton = screen.getByText('Editor');
      fireEvent.click(editorButton);

      await waitFor(() => {
        expect(screen.getByText('Environment Settings')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('switches to stats mode', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Algebra Basics Session')).toBeInTheDocument();
      }, { timeout: 5000 });

      const statsButton = screen.getByText('Stats');
      fireEvent.click(statsButton);

      await waitFor(() => {
        expect(screen.getByText('Performance Statistics')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Controls', () => {
    it('toggles play/pause state', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Paused')).toBeInTheDocument();
      }, { timeout: 5000 });

      const playButton = screen.getByLabelText(/play/i);
      fireEvent.click(playButton);

      await waitFor(() => {
        expect(screen.getByText('Playing')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('renders zoom controls', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByLabelText('Zoom In')).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(screen.getByLabelText('Zoom Out')).toBeInTheDocument();
      expect(screen.getByLabelText('Center View')).toBeInTheDocument();
      expect(screen.getByLabelText('Reset View')).toBeInTheDocument();
    });
  });

  describe('Editor Mode Features', () => {
    it('displays environment information in editor mode', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Editor')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Editor'));

      await waitFor(() => {
        expect(screen.getByText('Environment Information')).toBeInTheDocument();
        expect(screen.getByText('classroom')).toBeInTheDocument();
        expect(screen.getByText('Mathematics')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays layer controls', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Editor')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Editor'));

      await waitFor(() => {
        expect(screen.getByText('Layers')).toBeInTheDocument();
        expect(screen.getByText('Terrain')).toBeInTheDocument();
        expect(screen.getByText('Buildings')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays lighting controls', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Editor')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Editor'));

      await waitFor(() => {
        expect(screen.getByText('Lighting')).toBeInTheDocument();
        expect(screen.getByText('Ambient Light')).toBeInTheDocument();
        expect(screen.getByText('Brightness')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays assets list', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Editor')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Editor'));

      await waitFor(() => {
        expect(screen.getByText('Assets (3)')).toBeInTheDocument();
        expect(screen.getByText('Classroom Model')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Stats Mode Features', () => {
    it('displays performance statistics', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Stats'));

      await waitFor(() => {
        expect(screen.getByText('Performance Statistics')).toBeInTheDocument();
        expect(screen.getByText('Frame Rate')).toBeInTheDocument();
        expect(screen.getByText('60 FPS')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays polygon count', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Stats'));

      await waitFor(() => {
        expect(screen.getByText('Polygon Count')).toBeInTheDocument();
        expect(screen.getByText('15,000')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays performance rating', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument();
      }, { timeout: 5000 });

      fireEvent.click(screen.getByText('Stats'));

      await waitFor(() => {
        expect(screen.getByText('Performance Rating:')).toBeInTheDocument();
        expect(screen.getByText(/Excellent/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Session Objectives', () => {
    it('displays session objectives overlay', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Session Objectives')).toBeInTheDocument();
        expect(screen.getByText('Duration: 45 minutes')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays learning objectives', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Objectives:')).toBeInTheDocument();
        expect(screen.getByText('Understand linear equations')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Preview Content', () => {
    it('renders iframe with correct source', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        const iframe = screen.getByTitle('Environment Preview');
        expect(iframe).toHaveAttribute('src', '/api/environments/env_001/preview');
      }, { timeout: 5000 });
    });
  });

  describe('Accessibility', () => {
    it('has accessible tooltips for controls', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByLabelText('Zoom In')).toBeInTheDocument();
        expect(screen.getByLabelText('Zoom Out')).toBeInTheDocument();
        expect(screen.getByLabelText('Center View')).toBeInTheDocument();
        expect(screen.getByLabelText('Reset View')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('has semantic iframe title', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByTitle('Environment Preview')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Integration', () => {
    it('uses Pusher context', () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      expect(mockPusherContext.send).toBeDefined();
    });

    it('maintains state across view mode changes', async () => {
      renderWithProviders(<RobloxEnvironmentPreview />);

      await waitFor(() => {
        expect(screen.getByText('Algebra Basics Session')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Switch to editor
      fireEvent.click(screen.getByText('Editor'));

      await waitFor(() => {
        expect(screen.getByText('Environment Settings')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Switch back to preview
      fireEvent.click(screen.getByText('Preview'));

      await waitFor(() => {
        expect(screen.getByTitle('Environment Preview')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });
});
