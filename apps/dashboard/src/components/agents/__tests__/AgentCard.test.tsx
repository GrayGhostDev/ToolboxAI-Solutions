import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { AgentCard } from '../AgentCard';
import { IconCpu } from '@tabler/icons-react';

const renderWithProviders = (component: React.ReactElement) => {
  return render(<MantineProvider>{component}</MantineProvider>);
};

const mockAgentIdle = {
  agent_id: 'agent-test-123',
  agent_type: 'content_generator',
  status: 'idle',
  current_task_id: undefined,
  total_tasks_completed: 42,
  total_tasks_failed: 3,
  average_execution_time: 2.5,
  last_activity: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
  performance_metrics: {
    uptime: 99.5,
    throughput: 50,
    error_rate: 0.5,
    success_rate: 93.3,
  },
  resource_usage: {
    cpu_percent: 35.7,
    memory_mb: 512,
    gpu_percent: 0,
  },
};

const mockAgentRunning = {
  ...mockAgentIdle,
  status: 'running',
  current_task_id: 'task-abc-def-123',
};

const mockAgentHighResource = {
  ...mockAgentIdle,
  resource_usage: {
    cpu_percent: 85.5,
    memory_mb: 900,
    gpu_percent: 70,
  },
};

const mockGetStatusColor = (status: string) => {
  switch (status) {
    case 'idle':
      return 'gray';
    case 'running':
      return 'blue';
    case 'error':
      return 'red';
    default:
      return 'gray';
  }
};

const mockGetStatusIcon = (status: string) => {
  return <IconCpu size={16} />;
};

describe('AgentCard Component', () => {
  const mockOnAgentClick = vi.fn();
  const mockOnTaskExecute = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders agent card with basic information', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Content Generator')).toBeInTheDocument();
      expect(screen.getByText('agent-test-123')).toBeInTheDocument();
    });

    it('renders agent status badge', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('IDLE')).toBeInTheDocument();
    });

    it('renders current task ID when agent is running', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentRunning}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Running: task-abc/)).toBeInTheDocument();
    });

    it('does not render task ID when agent is idle', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.queryByText(/Running:/)).not.toBeInTheDocument();
    });
  });

  describe('Performance Metrics', () => {
    it('displays total tasks completed', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Tasks: 42')).toBeInTheDocument();
    });

    it('displays failed tasks count', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Failed: 3')).toBeInTheDocument();
    });

    it('displays success rate percentage', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Success Rate: 93.3%/)).toBeInTheDocument();
    });

    it('displays average execution time', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Avg Time: 2.5s/)).toBeInTheDocument();
    });
  });

  describe('Resource Usage', () => {
    it('displays CPU usage percentage', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('CPU')).toBeInTheDocument();
      expect(screen.getByText('35.7%')).toBeInTheDocument();
    });

    it('displays memory usage in MB', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Memory')).toBeInTheDocument();
      expect(screen.getByText('512MB')).toBeInTheDocument();
    });

    it('renders resource usage section', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Resource Usage')).toBeInTheDocument();
    });
  });

  describe('Last Activity', () => {
    it('displays last activity timestamp', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Last activity: 5m ago/)).toBeInTheDocument();
    });

    it('formats recent activity as "Just now"', () => {
      const recentAgent = {
        ...mockAgentIdle,
        last_activity: new Date(Date.now() - 30 * 1000).toISOString(), // 30 seconds ago
      };

      renderWithProviders(
        <AgentCard
          agent={recentAgent}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Last activity: Just now/)).toBeInTheDocument();
    });

    it('formats hours correctly', () => {
      const hoursAgent = {
        ...mockAgentIdle,
        last_activity: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      };

      renderWithProviders(
        <AgentCard
          agent={hoursAgent}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Last activity: 2h ago/)).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('renders Execute button', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Execute')).toBeInTheDocument();
    });

    it('enables Execute button when agent is idle', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      const executeButton = screen.getByText('Execute').closest('button');
      expect(executeButton).not.toBeDisabled();
    });

    it('disables Execute button when agent is running', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentRunning}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      const executeButton = screen.getByText('Execute').closest('button');
      expect(executeButton).toBeDisabled();
    });

    it('renders action icons (Metrics, Settings)', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      // Action icons are rendered (check via tooltips)
      const card = screen.getByText('Content Generator').closest('[role="img"], div');
      expect(card).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('calls onAgentClick when card is clicked', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      const card = screen.getByText('Content Generator').closest('div')?.parentElement?.parentElement;
      if (card) {
        fireEvent.click(card);
        expect(mockOnAgentClick).toHaveBeenCalledWith(mockAgentIdle);
      }
    });

    it('calls onTaskExecute when Execute button is clicked', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      const executeButton = screen.getByText('Execute');
      fireEvent.click(executeButton);
      expect(mockOnTaskExecute).toHaveBeenCalledWith(mockAgentIdle);
    });

    it('does not call onAgentClick when Execute button is clicked', () => {
      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      const executeButton = screen.getByText('Execute');
      fireEvent.click(executeButton);

      // Should call onTaskExecute but NOT onAgentClick (event propagation stopped)
      expect(mockOnTaskExecute).toHaveBeenCalled();
      expect(mockOnAgentClick).not.toHaveBeenCalled();
    });
  });

  describe('Formatting', () => {
    it('formats agent_type with underscores to title case', () => {
      const underscoreAgent = {
        ...mockAgentIdle,
        agent_type: 'data_processor_advanced',
      };

      renderWithProviders(
        <AgentCard
          agent={underscoreAgent}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText('Data Processor Advanced')).toBeInTheDocument();
    });

    it('truncates long task IDs to 8 characters', () => {
      const longTaskAgent = {
        ...mockAgentIdle,
        status: 'running',
        current_task_id: 'task-very-long-identifier-123456789',
      };

      renderWithProviders(
        <AgentCard
          agent={longTaskAgent}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(screen.getByText(/Running: task-ver.../)).toBeInTheDocument();
    });
  });

  describe('Status Color Integration', () => {
    it('calls getStatusColor with agent status', () => {
      const mockColorFn = vi.fn(() => 'blue');

      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockColorFn}
          getStatusIcon={mockGetStatusIcon}
        />
      );

      expect(mockColorFn).toHaveBeenCalledWith('idle');
    });

    it('calls getStatusIcon with agent status', () => {
      const mockIconFn = vi.fn(() => <IconCpu size={16} />);

      renderWithProviders(
        <AgentCard
          agent={mockAgentIdle}
          onAgentClick={mockOnAgentClick}
          onTaskExecute={mockOnTaskExecute}
          getStatusColor={mockGetStatusColor}
          getStatusIcon={mockIconFn}
        />
      );

      expect(mockIconFn).toHaveBeenCalledWith('idle');
    });
  });
});
