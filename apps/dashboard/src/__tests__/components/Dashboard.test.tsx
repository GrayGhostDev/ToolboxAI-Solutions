import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import DashboardHome from '../../components/pages/DashboardHome';
import { dashboardSlice } from '../../store/slices/dashboardSlice';
import { userSlice } from '../../store/slices/userSlice';
import { uiSlice } from '../../store/slices/uiSlice';
import * as apiService from '../../services/api';

// Mock the API service
vi.mock('../../services/api');

// Helper function to create a test store
const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      dashboard: dashboardSlice.reducer,
      user: userSlice.reducer,
      ui: uiSlice.reducer,
    },
    preloadedState: initialState,
  });
};

// Wrapper component for tests
const TestWrapper = ({ children, store }: any) => (
  <Provider store={store}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </Provider>
);

describe('Dashboard Component', () => {
  let store: any;
  let mockApiClient: any;

  beforeEach(() => {
    // Reset store before each test
    store = createTestStore({
      user: {
        currentUser: {
          id: 'test-user-123',
          name: 'Test Teacher',
          email: 'teacher@test.com',
          role: 'teacher',
        },
        isAuthenticated: true,
        token: 'test-token',
        loading: false,
        error: null,
      },
      dashboard: {
        overview: null,
        loading: false,
        error: null,
      },
    });

    // Setup API mocks
    mockApiClient = {
      getDashboardOverview: vi.fn().mockResolvedValue({
        totalStudents: 45,
        totalClasses: 3,
        activeAssessments: 7,
        recentActivity: [],
      }),
      getClasses: vi.fn().mockResolvedValue([
        { id: '1', name: 'Math 101', students: 15 },
        { id: '2', name: 'Science 202', students: 20 },
      ]),
    };

    (apiService as any).default = mockApiClient;
  });

  it('should render dashboard with loading state initially', () => {
    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
  });

  it('should fetch and display dashboard overview data', async () => {
    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockApiClient.getDashboardOverview).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/45/)).toBeInTheDocument(); // Total students
      expect(screen.getByText(/3/)).toBeInTheDocument(); // Total classes
    });
  });

  it('should handle error states gracefully', async () => {
    mockApiClient.getDashboardOverview.mockRejectedValue(
      new Error('Failed to fetch dashboard data')
    );

    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument();
    });
  });

  it('should navigate to class details when class card is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Math 101')).toBeInTheDocument();
    });

    const classCard = screen.getByText('Math 101');
    await user.click(classCard);

    // Check if navigation occurred (URL change)
    expect(window.location.pathname).toContain('/class');
  });

  it('should display user role-specific content', () => {
    // Test for teacher role
    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    expect(screen.getByText(/Create Class/i)).toBeInTheDocument();
    expect(screen.getByText(/Generate Content/i)).toBeInTheDocument();
  });

  it('should refresh data when refresh button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockApiClient.getDashboardOverview).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);

    expect(mockApiClient.getDashboardOverview).toHaveBeenCalledTimes(2);
  });

  it('should show correct statistics cards', async () => {
    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/Total Students/i)).toBeInTheDocument();
      expect(screen.getByText(/Total Classes/i)).toBeInTheDocument();
      expect(screen.getByText(/Active Assessments/i)).toBeInTheDocument();
    });
  });

  it('should handle WebSocket connection for real-time updates', async () => {
    // Mock WebSocket
    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
    };
    
    global.WebSocket = vi.fn(() => mockWebSocket) as any;

    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    // Verify WebSocket connection established
    expect(global.WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('ws://localhost:8001')
    );
  });

  it('should display empty state when no classes exist', async () => {
    mockApiClient.getClasses.mockResolvedValue([]);

    render(
      <TestWrapper store={store}>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/No classes found/i)).toBeInTheDocument();
      expect(screen.getByText(/Create your first class/i)).toBeInTheDocument();
    });
  });
});