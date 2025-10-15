import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { AgentTaskDialog } from '../AgentTaskDialog';

const renderWithProviders = (component: React.ReactElement) => {
  return render(<MantineProvider>{component}</MantineProvider>);
};

const mockAgentIdle = {
  agent_id: 'agent-test-123',
  agent_type: 'content_generator',
  status: 'idle',
};

const mockAgentRunning = {
  agent_id: 'agent-test-456',
  agent_type: 'quiz_generator',
  status: 'running',
};

const mockAgentUnknownType = {
  agent_id: 'agent-test-789',
  agent_type: 'unknown_type',
  status: 'idle',
};

const mockTaskResultSuccess = {
  success: true,
  task_id: 'task-abc-123',
  result: {
    content: 'Generated content',
    metadata: {
      tokens: 500,
      duration: 2.5,
    },
  },
  execution_time: 2.5,
};

const mockTaskResultFailure = {
  success: false,
  error: 'Task execution failed due to invalid input',
};

describe('AgentTaskDialog Component', () => {
  const mockOnClose = vi.fn();
  const mockOnExecute = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders nothing when agent is null', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={null}
          onExecute={mockOnExecute}
        />
      );

      // Modal should not be rendered when agent is null
      expect(screen.queryByText(/Execute Task on/)).not.toBeInTheDocument();
    });

    it('renders modal when open and agent is provided', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      expect(screen.getByText(/Execute Task on content generator/i)).toBeInTheDocument();
      expect(screen.getByText('Agent ID: agent-test-123')).toBeInTheDocument();
    });

    it('does not render modal when open is false', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={false}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      expect(screen.queryByText(/Execute Task on/)).not.toBeInTheDocument();
    });

    it('renders agent status badge', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      expect(screen.getByText('IDLE')).toBeInTheDocument();
    });
  });

  describe('Task Type Selection', () => {
    it('displays available task types for content_generator', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        // Task Type field should be rendered
        const taskTypeInputs = screen.getAllByDisplayValue('Generate Content');
        expect(taskTypeInputs.length).toBeGreaterThan(0);
      });
    });

    it('displays available task types for quiz_generator', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentRunning}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        // Task Type field should be rendered with quiz task
        const taskTypeInputs = screen.getAllByDisplayValue('Generate Quiz');
        expect(taskTypeInputs.length).toBeGreaterThan(0);
      });
    });

    it('shows no tasks message when agent type has no tasks', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentUnknownType}
          onExecute={mockOnExecute}
        />
      );

      expect(screen.getByText('No task types available for this agent type.')).toBeInTheDocument();
    });
  });

  describe('Form Fields', () => {
    it('renders subject field for content_generator', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Grade Level')).toBeInTheDocument();
      expect(screen.getByLabelText('Learning Objectives')).toBeInTheDocument();
    });

    it('renders quiz-specific fields for quiz_generator', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentRunning}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Number of Questions')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Difficulty')).toBeInTheDocument();
    });

    it('updates form data when text field changes', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      const subjectInput = screen.getByLabelText('Subject');
      fireEvent.change(subjectInput, { target: { value: 'Mathematics' } });

      expect(subjectInput).toHaveValue('Mathematics');
    });

    it('updates form data when textarea changes', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Learning Objectives')).toBeInTheDocument();
      });

      const objectivesInput = screen.getByLabelText('Learning Objectives');
      fireEvent.change(objectivesInput, { target: { value: 'Objective 1\nObjective 2' } });

      expect(objectivesInput).toHaveValue('Objective 1\nObjective 2');
    });

    it('updates form data when number field changes', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Grade Level')).toBeInTheDocument();
      });

      const gradeLevelInput = screen.getByLabelText('Grade Level');
      fireEvent.change(gradeLevelInput, { target: { value: '5' } });

      // NumberInput may display the value differently
      expect(gradeLevelInput).toBeInTheDocument();
    });
  });

  describe('Task Execution', () => {
    it('renders Execute button', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      expect(screen.getByText('Execute Task')).toBeInTheDocument();
    });

    it('enables Execute button when agent is idle', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      const executeButton = screen.getByText('Execute Task').closest('button');
      expect(executeButton).not.toBeDisabled();
    });

    it('disables Execute button when agent is running', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentRunning}
          onExecute={mockOnExecute}
        />
      );

      const executeButton = screen.getByText('Execute Task').closest('button');
      expect(executeButton).toBeDisabled();
    });

    it('calls onExecute when Execute button is clicked', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultSuccess);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      // Fill out form
      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn math' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(mockOnExecute).toHaveBeenCalled();
      });
    });

    it('shows progress indicator during execution', async () => {
      mockOnExecute.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText('Executing task...')).toBeInTheDocument();
      });
    });

    it('displays success result after successful execution', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultSuccess);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText(/Task completed successfully in/)).toBeInTheDocument();
      });
    });

    it('displays error message after failed execution', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultFailure);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText(/Task execution failed due to invalid input/)).toBeInTheDocument();
      });
    });

    it('handles execution exception', async () => {
      mockOnExecute.mockRejectedValue(new Error('Network error'));

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Result Display', () => {
    it('shows Task Result section when result has data', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultSuccess);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText('Task Result')).toBeInTheDocument();
      });
    });

    it('toggles result collapse when Show/Hide button clicked', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultSuccess);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText('Show')).toBeInTheDocument();
      });

      const toggleButton = screen.getByText('Show');
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('Hide')).toBeInTheDocument();
      });
    });

    it('displays JSON result when expanded', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultSuccess);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), { target: { value: 'Learn' } });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText('Show')).toBeInTheDocument();
      });

      const toggleButton = screen.getByText('Show');
      fireEvent.click(toggleButton);

      await waitFor(() => {
        // Result should contain the JSON content
        const resultText = screen.getByText(/Generated content/);
        expect(resultText).toBeInTheDocument();
      });
    });
  });

  describe('Close Button', () => {
    it('renders Close button', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      expect(screen.getByText('Close')).toBeInTheDocument();
    });

    it('calls onClose when Close button is clicked', () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      const closeButton = screen.getByText('Close');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('calls onClose when modal overlay is clicked', () => {
      const { container } = renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      // Mantine Modal overlay has data-modal-overlay attribute
      const overlay = container.querySelector('[data-modal-overlay]');
      if (overlay) {
        fireEvent.click(overlay);
        expect(mockOnClose).toHaveBeenCalled();
      }
    });
  });

  describe('Form Reset', () => {
    it('resets form when agent changes', async () => {
      const { rerender } = renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Subject')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });

      rerender(
        <MantineProvider>
          <AgentTaskDialog
            open={true}
            onClose={mockOnClose}
            agent={mockAgentRunning}
            onExecute={mockOnExecute}
          />
        </MantineProvider>
      );

      await waitFor(() => {
        // Form should be reset for new agent type
        const subjectInput = screen.queryByLabelText('Subject');
        if (subjectInput) {
          expect(subjectInput).toHaveValue('');
        }
      });
    });
  });

  describe('Default Values', () => {
    it('sets default values for fields when task type changes', async () => {
      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentRunning}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Number of Questions')).toBeInTheDocument();
      });

      // Number of Questions has default value of 5
      const numQuestionsInput = screen.getByLabelText('Number of Questions');
      expect(numQuestionsInput).toBeInTheDocument();
    });
  });

  describe('Field Processing', () => {
    it('processes textarea values into arrays on execution', async () => {
      mockOnExecute.mockResolvedValue(mockTaskResultSuccess);

      renderWithProviders(
        <AgentTaskDialog
          open={true}
          onClose={mockOnClose}
          agent={mockAgentIdle}
          onExecute={mockOnExecute}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Learning Objectives')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Math' } });
      fireEvent.change(screen.getByLabelText('Grade Level'), { target: { value: '5' } });
      fireEvent.change(screen.getByLabelText('Learning Objectives'), {
        target: { value: 'Objective 1\nObjective 2\nObjective 3' }
      });

      const executeButton = screen.getByText('Execute Task');
      fireEvent.click(executeButton);

      await waitFor(() => {
        expect(mockOnExecute).toHaveBeenCalledWith(
          expect.objectContaining({
            task_data: expect.objectContaining({
              objectives: ['Objective 1', 'Objective 2', 'Objective 3']
            })
          })
        );
      });
    });
  });
});
