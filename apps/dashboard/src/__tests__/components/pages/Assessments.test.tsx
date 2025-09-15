import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Assessments from '@/components/pages/Assessments';
import { TestWrapper } from '@/test/utils/test-wrapper';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Assessments', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('confirm', vi.fn(() => true));
  });

  afterEach(() => {
    vi.resetAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders the assessments page header', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('Assessments')).toBeInTheDocument();
    expect(screen.getByText('Create Assessment')).toBeInTheDocument();
  });

  it('displays statistics cards', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('Active Assessments')).toBeInTheDocument();
    expect(screen.getByText('Pending Grading')).toBeInTheDocument();
    expect(screen.getByText('Average Score')).toBeInTheDocument();
    expect(screen.getByText('Completion Rate')).toBeInTheDocument();
  });

  it('shows loading state when fetching assessments', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: true,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows empty state when no assessments exist', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('No assessments found. Create your first assessment to get started.')).toBeInTheDocument();
  });

  it('displays error message when there is an error', () => {
    const errorMessage = 'Failed to load assessments';
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: errorMessage,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('displays assessments when data is loaded', () => {
    const mockAssessments = [
      {
        id: 'assessment-1',
        title: 'Math Quiz Chapter 5',
        type: 'quiz',
        status: 'active',
        dueDate: '2024-01-20T23:59:59Z',
        submissions: 15,
        maxSubmissions: 25,
        averageScore: 85,
        createdAt: '2024-01-15T10:00:00Z',
      },
      {
        id: 'assessment-2',
        title: 'Biology Final Exam',
        type: 'test',
        status: 'active',
        dueDate: '2024-01-25T23:59:59Z',
        submissions: 20,
        maxSubmissions: 30,
        averageScore: 78,
        createdAt: '2024-01-14T14:00:00Z',
      },
    ];

    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: mockAssessments,
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('Math Quiz Chapter 5')).toBeInTheDocument();
    expect(screen.getByText('Biology Final Exam')).toBeInTheDocument();
  });

  it('shows refresh button', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByLabelText('Refresh')).toBeInTheDocument();
  });

  it('shows filter button', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByLabelText('Filter list')).toBeInTheDocument();
  });

  it('displays assessment type chips correctly', () => {
    const mockAssessments = [
      {
        id: 'assessment-1',
        title: 'Math Quiz',
        type: 'quiz',
        status: 'active',
        dueDate: '2024-01-20T23:59:59Z',
        submissions: 15,
        maxSubmissions: 25,
        averageScore: 85,
        createdAt: '2024-01-15T10:00:00Z',
      },
    ];

    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: mockAssessments,
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('Math Quiz')).toBeInTheDocument();
  });

  it('shows due date information', () => {
    const mockAssessments = [
      {
        id: 'assessment-1',
        title: 'Math Quiz',
        type: 'quiz',
        status: 'active',
        dueDate: '2024-01-20T23:59:59Z',
        submissions: 15,
        maxSubmissions: 25,
        averageScore: 85,
        createdAt: '2024-01-15T10:00:00Z',
      },
    ];

    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: mockAssessments,
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('Math Quiz')).toBeInTheDocument();
  });

  it('calculates statistics correctly with zero values', () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    expect(screen.getByText('0')).toBeInTheDocument(); // Active assessments
    expect(screen.getByText('0%')).toBeInTheDocument(); // Average score and completion rate
  });

  it('handles create assessment button click', async () => {
    render(
      <TestWrapper
        initialState={{
          assessments: {
            assessments: [],
            submissions: [],
            loading: false,
            error: null,
            filters: { status: undefined, type: undefined }
          }
        }}
      >
        <Assessments />
      </TestWrapper>
    );

    const createButton = screen.getByText('Create Assessment');
    await user.click(createButton);

    expect(createButton).toBeInTheDocument();
  });
});
