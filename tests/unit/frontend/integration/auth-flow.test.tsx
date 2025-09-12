import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import MockAdapter from 'axios-mock-adapter';
import axios from 'axios';
import { userSlice } from '../../store/slices/userSlice';
import { uiSlice } from '../../store/slices/uiSlice';
import Login from '../../components/pages/Login';
import DashboardHome from '../../components/pages/DashboardHome';
import { API_BASE_URL } from '../../config';

describe('Authentication Flow Integration', () => {
  let mock: MockAdapter;
  let store: any;

  beforeEach(() => {
    mock = new MockAdapter(axios);
    
    // Clear localStorage
    localStorage.clear();
    
    // Create fresh store
    store = configureStore({
      reducer: {
        user: userSlice.reducer,
        ui: uiSlice.reducer,
      },
    });
  });

  afterEach(() => {
    mock.restore();
    vi.clearAllMocks();
  });

  const TestWrapper = ({ children }: any) => (
    <Provider store={store}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </Provider>
  );

  it('should complete full login flow successfully', async () => {
    const user = userEvent.setup();
    
    // Mock login endpoint
    mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, {
      success: true,
      data: {
        user: {
          id: 'user-123',
          email: 'teacher@example.com',
          name: 'Test Teacher',
          role: 'teacher',
        },
        token: 'jwt-token-123',
        refreshToken: 'refresh-token-123',
      },
    });

    // Mock dashboard data
    mock.onGet(`${API_BASE_URL}/dashboard/overview`).reply(200, {
      success: true,
      data: {
        totalStudents: 45,
        totalClasses: 3,
      },
    });

    // Render login page
    const { rerender } = render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    // Fill in login form
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    await user.type(emailInput, 'teacher@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(loginButton);

    // Wait for login to complete
    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBe('jwt-token-123');
      expect(localStorage.getItem('refresh_token')).toBe('refresh-token-123');
    });

    // Verify user is redirected to dashboard
    rerender(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/Welcome, Test Teacher/i)).toBeInTheDocument();
      expect(screen.getByText(/45/)).toBeInTheDocument(); // Total students
    });
  });

  it('should handle token refresh automatically', async () => {
    // Set expired token
    localStorage.setItem('auth_token', 'expired-token');
    localStorage.setItem('refresh_token', 'valid-refresh-token');

    // First API call returns 401
    mock.onGet(`${API_BASE_URL}/dashboard/overview`).replyOnce(401, {
      success: false,
      message: 'Token expired',
    });

    // Refresh token endpoint
    mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(200, {
      success: true,
      data: {
        token: 'new-jwt-token',
        refreshToken: 'new-refresh-token',
      },
    });

    // Retry with new token succeeds
    mock.onGet(`${API_BASE_URL}/dashboard/overview`).reply(200, {
      success: true,
      data: {
        totalStudents: 30,
      },
    });

    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBe('new-jwt-token');
      expect(screen.getByText(/30/)).toBeInTheDocument();
    });
  });

  it('should handle logout across all services', async () => {
    const user = userEvent.setup();
    
    // Setup authenticated state
    store.dispatch(userSlice.actions.setUser({
      user: { id: '123', email: 'test@example.com', role: 'teacher' },
      token: 'jwt-token',
      refreshToken: 'refresh-token',
    }));
    
    localStorage.setItem('auth_token', 'jwt-token');
    localStorage.setItem('refresh_token', 'refresh-token');

    // Mock logout endpoint
    mock.onPost(`${API_BASE_URL}/auth/logout`).reply(200, {
      success: true,
    });

    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    // Click logout button
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    await user.click(logoutButton);

    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(store.getState().user.isAuthenticated).toBe(false);
    });
  });

  it('should validate role-based access control', async () => {
    // Test student role restrictions
    store.dispatch(userSlice.actions.setUser({
      user: { id: '123', email: 'student@example.com', role: 'student' },
      token: 'jwt-token',
      refreshToken: 'refresh-token',
    }));

    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    // Student should not see teacher-only features
    expect(screen.queryByText(/Create Class/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Generate Content/i)).not.toBeInTheDocument();
    
    // Student should see their features
    expect(screen.getByText(/My Classes/i)).toBeInTheDocument();
    expect(screen.getByText(/My Progress/i)).toBeInTheDocument();
  });

  it('should handle session expiry gracefully', async () => {
    // Set token that will expire
    localStorage.setItem('auth_token', 'soon-to-expire');
    localStorage.setItem('refresh_token', 'expired-refresh');

    // Both token and refresh fail
    mock.onGet(`${API_BASE_URL}/dashboard/overview`).reply(401);
    mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(401);

    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should redirect to login
      expect(screen.getByText(/Session expired/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });
  });

  it('should persist authentication across page refreshes', async () => {
    // Simulate page load with existing tokens
    localStorage.setItem('auth_token', 'valid-token');
    localStorage.setItem('refresh_token', 'valid-refresh');

    // Mock user verification
    mock.onGet(`${API_BASE_URL}/auth/verify`).reply(200, {
      success: true,
      data: {
        user: {
          id: 'user-123',
          email: 'teacher@example.com',
          role: 'teacher',
        },
      },
    });

    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(store.getState().user.isAuthenticated).toBe(true);
      expect(store.getState().user.currentUser.email).toBe('teacher@example.com');
    });
  });

  it('should handle concurrent API calls with authentication', async () => {
    localStorage.setItem('auth_token', 'valid-token');

    // Mock multiple endpoints
    mock.onGet(`${API_BASE_URL}/dashboard/overview`).reply(200, {
      success: true,
      data: { totalStudents: 100 },
    });
    
    mock.onGet(`${API_BASE_URL}/classes`).reply(200, {
      success: true,
      data: [{ id: '1', name: 'Math 101' }],
    });
    
    mock.onGet(`${API_BASE_URL}/assessments`).reply(200, {
      success: true,
      data: [{ id: '1', title: 'Quiz 1' }],
    });

    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    await waitFor(() => {
      // All data should load
      expect(screen.getByText(/100/)).toBeInTheDocument();
      expect(screen.getByText(/Math 101/)).toBeInTheDocument();
      expect(screen.getByText(/Quiz 1/)).toBeInTheDocument();
    });
  });

  it('should handle cross-service authentication (Dashboard → Roblox)', async () => {
    localStorage.setItem('auth_token', 'dashboard-token');

    // Mock Roblox content generation requiring auth
    mock.onPost(`${API_BASE_URL}/roblox/generate`).reply(config => {
      // Verify auth header is present
      expect(config.headers?.Authorization).toBe('Bearer dashboard-token');
      
      return [200, {
        success: true,
        data: {
          worldId: 'world-123',
          status: 'generated',
        },
      }];
    });

    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <DashboardHome />
      </TestWrapper>
    );

    // Click generate content button
    const generateButton = screen.getByRole('button', { name: /Generate Roblox Content/i });
    await user.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText(/Content Generated Successfully/i)).toBeInTheDocument();
    });
  });
});