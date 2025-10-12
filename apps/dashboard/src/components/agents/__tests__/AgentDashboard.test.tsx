import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { AgentDashboard } from '../AgentDashboard';

// Mock hooks
const mockUsePusher = vi.fn();
const mockUseAgentAPI = vi.fn();
const mockUseSupabaseAgent = vi.fn();

vi.mock('../../../hooks/usePusher', () => ({
  usePusher: () => mockUsePusher()
}));

vi.mock('../../../hooks/useAgentAPI', () => ({
  useAgentAPI: () => mockUseAgentAPI()
}));

vi.mock('../../../hooks/useSupabaseAgent', () => ({
  useSupabaseAgent: () => mockUseSupabaseAgent()
}));

// Mock child components
vi.mock('../AgentCard', () => ({
  AgentCard: ({ agent, onAgentClick, onTaskExecute }: any) => (
    <div data-testid={`agent-card-${agent.agent_id}`}>
      <div>{agent.agent_type}</div>
      <button onClick={() => onAgentClick(agent)}>View Agent</button>
      <button onClick={() => onTaskExecute(agent)}>Execute Task</button>
    </div>
  ),
}));

vi.mock('../AgentTaskDialog', () => ({
  AgentTaskDialog: ({ open, onClose }: any) =>
    open ? <div data-testid="task-dialog"><button onClick={onClose}>Close Dialog</button></div> : null,
}));

vi.mock('../AgentMetricsPanel', () => ({
  AgentMetricsPanel: ({ open, onClose }: any) =>
    open ? <div data-testid="metrics-panel"><button onClick={onClose}>Close Panel</button></div> : null,
}));

vi.mock('../SystemHealthIndicator', () => ({
  SystemHealthIndicator: ({ status, isConnected }: any) => (
    <div data-testid="health-indicator">
      Status: {status}, Connected: {isConnected ? 'Yes' : 'No'}
    </div>
  ),
}));

const renderWithProviders = (component: React.ReactElement) => {
  return render(<MantineProvider>{component}</MantineProvider>);
};

const mockAgent = {
  agent_id: 'agent-123',
  agent_type: 'content_generator',
  status: 'idle' as const,
  current_task_id: undefined,
  total_tasks_completed: 50,
  total_tasks_failed: 2,
  average_execution_time: 2.5,
  last_activity: new Date().toISOString(),
  created_at: new Date().toISOString(),
  performance_metrics: {
    uptime: 99.5,
    throughput: 20,
    error_rate: 0.5,
    success_rate: 96.2,
  },
  resource_usage: {
    cpu_percent: 25,
    memory_mb: 512,
    gpu_percent: 0,
  },
};

const mockSystemMetrics = {
  agents: {
    total: 3,
    idle: 2,
    busy: 1,
    error: 0,
    utilization_rate: 33.3,
  },
  tasks: {
    total: 150,
    completed: 140,
    failed: 10,
    running: 5,
    queued: 10,
    success_rate: 93.3,
  },
  system: {
    status: 'healthy' as const,
    uptime: '99.9%',
    last_updated: new Date().toISOString(),
  },
};

describe('AgentDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUsePusher.mockReturnValue({
      service: {
        subscribe: vi.fn(() => 'sub-id'),
        unsubscribe: vi.fn(),
      },
      isConnected: true,
    });

    mockUseAgentAPI.mockReturnValue({
      getAgentsStatus: vi.fn().mockResolvedValue({
        success: true,
        data: [mockAgent],
      }),
      getSystemMetrics: vi.fn().mockResolvedValue({
        success: true,
        data: mockSystemMetrics,
      }),
      executeTask: vi.fn(),
      getAgentStatus: vi.fn(),
      loading: false,
    });

    mockUseSupabaseAgent.mockReturnValue({
      agents: [],
      executions: [],
      metrics: null,
      systemHealth: null,
      healthSummary: null,
      loading: false,
      error: null,
      configured: false,
      actions: {},
    });
  });

  describe('Rendering', () => {
    it('renders dashboard title', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Agent Dashboard')).toBeInTheDocument();
      });
    });

    it('shows loading skeleton when loading and no agents', async () => {
      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockImplementation(() => new Promise(() => {})), // Never resolves
        getSystemMetrics: vi.fn().mockImplementation(() => new Promise(() => {})),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: true,
      });

      const { container } = renderWithProviders(<AgentDashboard />);

      // Loading skeletons should be visible (Mantine Skeleton has data-animate="true")
      await waitFor(() => {
        const skeletons = container.querySelectorAll('[data-animate="true"]');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    it('renders system health indicator', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('health-indicator')).toBeInTheDocument();
      });

      expect(screen.getByText(/Status: healthy/)).toBeInTheDocument();
      expect(screen.getByText(/Connected: Yes/)).toBeInTheDocument();
    });

    it('renders action buttons', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Metrics')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  describe('System Overview Cards', () => {
    it('displays total agents card', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Total Agents')).toBeInTheDocument();
      });

      expect(screen.getByText('3')).toBeInTheDocument();
      // "healthy" appears in both health indicator and total agents card
      const healthyTexts = screen.getAllByText(/healthy/);
      expect(healthyTexts.length).toBeGreaterThan(0);
    });

    it('displays utilization card', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Utilization')).toBeInTheDocument();
      });

      expect(screen.getByText('33.3%')).toBeInTheDocument();
    });

    it('displays success rate card', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Success Rate')).toBeInTheDocument();
      });

      expect(screen.getByText('93.3%')).toBeInTheDocument();
      expect(screen.getByText('140 completed')).toBeInTheDocument();
    });

    it('displays queue card', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Queue')).toBeInTheDocument();
      });

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('5 running')).toBeInTheDocument();
    });
  });

  describe('Agent Display', () => {
    it('renders Active Agents section', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Active Agents')).toBeInTheDocument();
      });
    });

    it('displays agent cards', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('agent-card-agent-123')).toBeInTheDocument();
      });

      expect(screen.getByText('content_generator')).toBeInTheDocument();
    });

    it('shows no agents message when agents array is empty', async () => {
      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: true,
          data: [],
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: true,
          data: mockSystemMetrics,
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/No agents are currently registered/)).toBeInTheDocument();
      });
    });

    it('displays multiple agents', async () => {
      const agents = [
        { ...mockAgent, agent_id: 'agent-1', agent_type: 'content_generator' },
        { ...mockAgent, agent_id: 'agent-2', agent_type: 'quiz_generator' },
        { ...mockAgent, agent_id: 'agent-3', agent_type: 'terrain_generator' },
      ];

      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: true,
          data: agents,
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: true,
          data: mockSystemMetrics,
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('agent-card-agent-1')).toBeInTheDocument();
      });

      expect(screen.getByTestId('agent-card-agent-2')).toBeInTheDocument();
      expect(screen.getByTestId('agent-card-agent-3')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('opens metrics panel when Metrics button clicked', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Metrics')).toBeInTheDocument();
      });

      const metricsButton = screen.getByText('Metrics');
      fireEvent.click(metricsButton);

      await waitFor(() => {
        expect(screen.getByTestId('metrics-panel')).toBeInTheDocument();
      });
    });

    it('closes metrics panel when close button clicked', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Metrics')).toBeInTheDocument();
      });

      // Open panel
      const metricsButton = screen.getByText('Metrics');
      fireEvent.click(metricsButton);

      await waitFor(() => {
        expect(screen.getByTestId('metrics-panel')).toBeInTheDocument();
      });

      // Close panel
      const closeButton = screen.getByText('Close Panel');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('metrics-panel')).not.toBeInTheDocument();
      });
    });

    it('opens task dialog when Execute Task button clicked on agent card', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('agent-card-agent-123')).toBeInTheDocument();
      });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByTestId('task-dialog')).toBeInTheDocument();
      });
    });

    it('closes task dialog when close button clicked', async () => {
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('agent-card-agent-123')).toBeInTheDocument();
      });

      // Open dialog
      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByTestId('task-dialog')).toBeInTheDocument();
      });

      // Close dialog
      const closeButton = screen.getByText('Close Dialog');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('task-dialog')).not.toBeInTheDocument();
      });
    });

    it('calls refresh when Refresh button clicked', async () => {
      const getAgentsStatus = vi.fn().mockResolvedValue({
        success: true,
        data: [mockAgent],
      });

      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus,
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: true,
          data: mockSystemMetrics,
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });

      // Initial load
      expect(getAgentsStatus).toHaveBeenCalledTimes(1);

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      // Should be called again after refresh
      await waitFor(() => {
        expect(getAgentsStatus).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error alert when API fails', async () => {
      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: false,
          message: 'Failed to load agents',
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: false,
          message: 'Failed to load metrics',
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
      });
    });

    it('clears error when close button clicked', async () => {
      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: false,
          message: 'Failed to load agents',
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: false,
          message: 'Failed to load metrics',
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
      });

      // Find and click close button on alert
      const buttons = screen.getAllByRole('button');
      const closeButton = buttons.find(btn => btn.getAttribute('aria-label')?.includes('close'));

      if (closeButton) {
        fireEvent.click(closeButton);

        await waitFor(() => {
          expect(screen.queryByText(/Failed to load/)).not.toBeInTheDocument();
        });
      }
    });
  });

  describe('Supabase Fallback', () => {
    it('uses Supabase data when API fails and Supabase is configured', async () => {
      const supabaseAgent = {
        agent_id: 'supabase-agent-1',
        agent_type: 'content_generator',
        status: 'idle' as const,
        current_task_id: null,
        total_tasks_completed: 10,
        total_tasks_failed: 0,
        average_execution_time: 1.5,
        last_activity: new Date().toISOString(),
        created_at: new Date().toISOString(),
      };

      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: false,
          message: 'API not available',
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: false,
          message: 'API not available',
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      mockUseSupabaseAgent.mockReturnValue({
        agents: [supabaseAgent],
        executions: [],
        metrics: null,
        systemHealth: null,
        healthSummary: {
          total_agents: 1,
          busy_agents: 0,
          error_agents: 0,
          success_rate: 100,
        },
        loading: false,
        error: null,
        configured: true,
        actions: {},
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('agent-card-supabase-agent-1')).toBeInTheDocument();
      });
    });
  });

  describe('Agents by Type Section', () => {
    it('displays Agents by Type section when multiple agent types exist', async () => {
      const agents = [
        { ...mockAgent, agent_id: 'agent-1', agent_type: 'content_generator' },
        { ...mockAgent, agent_id: 'agent-2', agent_type: 'quiz_generator' },
        { ...mockAgent, agent_id: 'agent-3', agent_type: 'content_generator' },
      ];

      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: true,
          data: agents,
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: true,
          data: mockSystemMetrics,
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Agents by Type')).toBeInTheDocument();
      });

      // Should show formatted type names
      expect(screen.getByText('Content Generator')).toBeInTheDocument();
      expect(screen.getByText('Quiz Generator')).toBeInTheDocument();
    });

    it('does not display Agents by Type section when only one type exists', async () => {
      // Single agent type (content_generator)
      const agents = [
        { ...mockAgent, agent_id: 'agent-1', agent_type: 'content_generator' },
        { ...mockAgent, agent_id: 'agent-2', agent_type: 'content_generator' },
      ];

      mockUseAgentAPI.mockReturnValue({
        getAgentsStatus: vi.fn().mockResolvedValue({
          success: true,
          data: agents,
        }),
        getSystemMetrics: vi.fn().mockResolvedValue({
          success: true,
          data: mockSystemMetrics,
        }),
        executeTask: vi.fn(),
        getAgentStatus: vi.fn(),
        loading: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.queryByText('Agents by Type')).not.toBeInTheDocument();
      });
    });
  });

  describe('Pusher Integration', () => {
    it('shows disconnected status when Pusher is not connected', async () => {
      mockUsePusher.mockReturnValue({
        service: {
          subscribe: vi.fn(),
          unsubscribe: vi.fn(),
        },
        isConnected: false,
      });

      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Connected: No/)).toBeInTheDocument();
      });
    });
  });
});
