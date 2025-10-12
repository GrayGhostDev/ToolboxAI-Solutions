import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { AgentMetricsPanel } from '../AgentMetricsPanel';

const renderWithProviders = (component: React.ReactElement) => {
  return render(<MantineProvider>{component}</MantineProvider>);
};

const mockSystemMetrics = {
  agents: {
    total: 5,
    idle: 3,
    busy: 1,
    error: 1,
    utilization_rate: 60.0,
  },
  tasks: {
    total: 150,
    completed: 120,
    failed: 10,
    running: 5,
    queued: 15,
    success_rate: 92.3,
  },
  system: {
    status: 'healthy',
    uptime: '99.9%',
    last_updated: '2025-01-15T12:00:00Z',
  },
};

const mockAgents = [
  {
    agent_id: 'agent-abc-def-123-456',
    agent_type: 'content_generator',
    status: 'idle',
    total_tasks_completed: 50,
    total_tasks_failed: 2,
    average_execution_time: 2.5,
    performance_metrics: {
      success_rate: 96.2,
      error_rate: 3.8,
      throughput: 20,
      uptime: 99.5,
    },
    resource_usage: {
      cpu_percent: 25.5,
      memory_mb: 512,
      gpu_percent: 0,
    },
  },
  {
    agent_id: 'agent-xyz-789-012-345',
    agent_type: 'quiz_generator',
    status: 'busy',
    total_tasks_completed: 30,
    total_tasks_failed: 0,
    average_execution_time: 1.8,
    performance_metrics: {
      success_rate: 100.0,
      error_rate: 0.0,
      throughput: 25,
      uptime: 99.9,
    },
    resource_usage: {
      cpu_percent: 85.0,
      memory_mb: 768,
      gpu_percent: 0,
    },
  },
  {
    agent_id: 'agent-err-404-505-606',
    agent_type: 'terrain_generator',
    status: 'error',
    total_tasks_completed: 10,
    total_tasks_failed: 8,
    average_execution_time: 4.2,
    performance_metrics: {
      success_rate: 55.6,
      error_rate: 44.4,
      throughput: 5,
      uptime: 90.0,
    },
    resource_usage: {
      cpu_percent: 10.0,
      memory_mb: 256,
      gpu_percent: 0,
    },
  },
];

describe('AgentMetricsPanel Component', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders modal when open', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('Agent System Metrics')).toBeInTheDocument();
    });

    it('does not render modal when closed', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={false}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.queryByText('Agent System Metrics')).not.toBeInTheDocument();
    });

    it('renders last updated timestamp', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });

    it('shows "No metrics data available" when systemMetrics is null', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={null}
          agents={[]}
        />
      );

      expect(screen.getByText('No metrics data available')).toBeInTheDocument();
    });

    it('shows "Never" when last_updated is not provided', () => {
      const metricsWithoutUpdate = {
        ...mockSystemMetrics,
        system: {
          ...mockSystemMetrics.system,
          last_updated: '',
        },
      };

      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={metricsWithoutUpdate}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Last updated: Never/)).toBeInTheDocument();
    });
  });

  describe('System Overview', () => {
    it('displays total agents count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Total Agents')).toBeInTheDocument();
    });

    it('displays utilization rate', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('60.0%')).toBeInTheDocument();
      expect(screen.getByText('Utilization')).toBeInTheDocument();
    });

    it('displays success rate', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('92.3%')).toBeInTheDocument();
      // Success Rate appears in System Overview and as table header
      const successRateElements = screen.getAllByText('Success Rate');
      expect(successRateElements.length).toBeGreaterThan(0);
    });

    it('displays queued tasks count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('Queued Tasks')).toBeInTheDocument();
    });
  });

  describe('Agent Status Breakdown', () => {
    it('displays agent status breakdown section', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('Agent Status Breakdown')).toBeInTheDocument();
    });

    it('displays idle agents count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Idle: 3/)).toBeInTheDocument();
      expect(screen.getByText('Available for tasks')).toBeInTheDocument();
    });

    it('displays busy agents count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Busy: 1/)).toBeInTheDocument();
      expect(screen.getByText('Currently processing tasks')).toBeInTheDocument();
    });

    it('displays error agents count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Error: 1/)).toBeInTheDocument();
      expect(screen.getByText('Agents with errors')).toBeInTheDocument();
    });
  });

  describe('Task Statistics', () => {
    it('displays task statistics section', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('Task Statistics')).toBeInTheDocument();
    });

    it('displays completed tasks count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Completed: 120/)).toBeInTheDocument();
      expect(screen.getByText('Successfully completed tasks')).toBeInTheDocument();
    });

    it('displays failed tasks count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Failed: 10/)).toBeInTheDocument();
      expect(screen.getByText('Failed task executions')).toBeInTheDocument();
    });

    it('displays running tasks count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Running: 5/)).toBeInTheDocument();
      expect(screen.getByText('Currently executing')).toBeInTheDocument();
    });

    it('displays queued tasks count', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText(/Queued: 15/)).toBeInTheDocument();
      expect(screen.getByText('Waiting for execution')).toBeInTheDocument();
    });
  });

  describe('Individual Agent Performance Table', () => {
    it('displays individual agent performance section', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('Individual Agent Performance')).toBeInTheDocument();
    });

    it('displays table headers', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('Agent ID')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Tasks')).toBeInTheDocument();
      // Success Rate appears in System Overview and table header
      const successRateElements = screen.getAllByText('Success Rate');
      expect(successRateElements.length).toBeGreaterThan(0);
      expect(screen.getByText('Avg Time')).toBeInTheDocument();
      expect(screen.getByText('CPU')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
    });

    it('displays all agents in table', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      // Truncated agent IDs (first 12 chars)
      expect(screen.getByText('agent-abc-de...')).toBeInTheDocument();
      expect(screen.getByText('agent-xyz-78...')).toBeInTheDocument();
      expect(screen.getByText('agent-err-40...')).toBeInTheDocument();
    });

    it('displays agent types with underscores replaced', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('content generator')).toBeInTheDocument();
      expect(screen.getByText('quiz generator')).toBeInTheDocument();
      expect(screen.getByText('terrain generator')).toBeInTheDocument();
    });

    it('displays status badges with correct colors', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      // Status badges (multiple with same text, so using getAllByText)
      const idleBadges = screen.getAllByText('idle');
      const busyBadges = screen.getAllByText('busy');
      const errorBadges = screen.getAllByText('error');

      expect(idleBadges.length).toBeGreaterThan(0);
      expect(busyBadges.length).toBeGreaterThan(0);
      expect(errorBadges.length).toBeGreaterThan(0);
    });

    it('displays task completion counts', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('50')).toBeInTheDocument(); // First agent tasks
      expect(screen.getByText('30')).toBeInTheDocument(); // Second agent tasks
      expect(screen.getByText('10')).toBeInTheDocument(); // Third agent tasks
    });

    it('displays failed task counts in parentheses', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('(2 failed)')).toBeInTheDocument();
      expect(screen.getByText('(8 failed)')).toBeInTheDocument();
    });

    it('does not display failed count when zero', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      // Second agent has 0 failed tasks, should not show failed count
      expect(screen.queryByText('(0 failed)')).not.toBeInTheDocument();
    });

    it('displays success rates with correct formatting', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('96.2%')).toBeInTheDocument();
      expect(screen.getByText('100.0%')).toBeInTheDocument();
      expect(screen.getByText('55.6%')).toBeInTheDocument();
    });

    it('displays average execution times', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('2.5s')).toBeInTheDocument();
      expect(screen.getByText('1.8s')).toBeInTheDocument();
      expect(screen.getByText('4.2s')).toBeInTheDocument();
    });

    it('displays CPU usage percentages', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      // CPU percentages in table
      const cpuValues = screen.getAllByText(/\d+%/);
      const cpuTexts = cpuValues.map(el => el.textContent);

      expect(cpuTexts.some(text => text?.includes('25') || text?.includes('26'))).toBe(true);
      expect(cpuTexts.some(text => text?.includes('85'))).toBe(true);
      expect(cpuTexts.some(text => text?.includes('10'))).toBe(true);
    });

    it('displays memory usage in MB', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('512MB')).toBeInTheDocument();
      expect(screen.getByText('768MB')).toBeInTheDocument();
      expect(screen.getByText('256MB')).toBeInTheDocument();
    });
  });

  describe('Data Formatting', () => {
    it('formats duration in seconds', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      // Average execution times < 60s should be in seconds
      expect(screen.getByText('2.5s')).toBeInTheDocument();
      expect(screen.getByText('1.8s')).toBeInTheDocument();
    });

    it('formats duration in minutes for values >= 60s', () => {
      const agentsWithMinutes = [
        {
          ...mockAgents[0],
          average_execution_time: 125.5, // 2.09 minutes
        },
      ];

      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={agentsWithMinutes}
        />
      );

      expect(screen.getByText(/2.1m/)).toBeInTheDocument();
    });

    it('formats duration in hours for values >= 3600s', () => {
      const agentsWithHours = [
        {
          ...mockAgents[0],
          average_execution_time: 7200, // 2 hours
        },
      ];

      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={agentsWithHours}
        />
      );

      expect(screen.getByText('2.0h')).toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    it('renders close button', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      expect(screen.getByText('Close')).toBeInTheDocument();
    });

    it('calls onClose when close button is clicked', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={mockAgents}
        />
      );

      const closeButton = screen.getByText('Close');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Empty States', () => {
    it('handles empty agents array', () => {
      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={mockSystemMetrics}
          agents={[]}
        />
      );

      // Table should be rendered but with no agent rows
      expect(screen.getByText('Individual Agent Performance')).toBeInTheDocument();
      expect(screen.getByText('Agent ID')).toBeInTheDocument();
    });

    it('displays system overview even with no agents', () => {
      const metricsWithNoAgents = {
        ...mockSystemMetrics,
        agents: {
          total: 0,
          idle: 0,
          busy: 0,
          error: 0,
          utilization_rate: 0,
        },
      };

      renderWithProviders(
        <AgentMetricsPanel
          open={true}
          onClose={mockOnClose}
          systemMetrics={metricsWithNoAgents}
          agents={[]}
        />
      );

      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });
  });
});
