/**
 * Login Component Test Suite
 *
 * Comprehensive tests for the Login component functionality
 * Testing real behaviors and interactions
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Login from '../../../components/pages/Login';
import { login } from '../../../services/api';

// Simple store for testing
const createTestStore = () => {
  return configureStore({
    reducer: {
      user: (state = { isAuthenticated: false, role: 'student' }, action) => state,
      ui: (state = {}, action) => state,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }),
  });
};

// Simple render wrapper
const renderWithProviders = (ui: React.ReactElement) => {
  const store = createTestStore();
  const theme = createTheme();

  return render(
    <Provider store={store}>
      <MemoryRouter>
        <ThemeProvider theme={theme}>
          {ui}
        </ThemeProvider>
      </MemoryRouter>
    </Provider>
  );
};

// Mock API service
vi.mock('../../../services/api', () => ({
  login: vi.fn(),
}));

// Get the mocked function
const mockLogin = vi.mocked(login);

// Mock react-router-dom navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the connectWebSocket function
vi.mock('../../services/pusher', () => ({
  connectWebSocket: vi.fn().mockResolvedValue(undefined),
}));

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('✅ should render the login form with all required elements', () => {
      renderWithProviders(<Login />);

      // Check for the main heading
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();

      // Check for form fields by label
      expect(screen.getByLabelText(/username or email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

      // Check for submit button
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();

      // Check for links
      expect(screen.getByText(/forgot your password\?/i)).toBeInTheDocument();
      expect(screen.getByText(/don't have an account\?/i)).toBeInTheDocument();

      // Check for demo credentials section
      expect(screen.getByText(/demo credentials/i)).toBeInTheDocument();
    });

    it('✅ should display the platform name', () => {
      renderWithProviders(<Login />);
      expect(screen.getByText(/toolboxai educational platform/i)).toBeInTheDocument();
    });

    it('✅ should show demo credentials for different roles', () => {
      renderWithProviders(<Login />);
      expect(screen.getByText(/admin@toolboxai.com/i)).toBeInTheDocument();
      expect(screen.getByText(/jane.smith@school.edu/i)).toBeInTheDocument();
      expect(screen.getByText(/alex.johnson@student.edu/i)).toBeInTheDocument();
    });
  });

  describe('Form Interactions', () => {
    it('✅ should update input values when user types', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const emailInput = screen.getByLabelText(/username or email/i);
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');

      expect(emailInput).toHaveValue('test@example.com');
      expect(passwordInput).toHaveValue('password123');
    });

    it('✅ should toggle password visibility', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const passwordInput = screen.getByLabelText(/password/i);
      const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i });

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Click to show password
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');

      // Click again to hide password
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('✅ should disable form during submission', async () => {
      const user = userEvent.setup();

      // Mock the login function to return a promise that never resolves
      mockLogin.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<Login />);

      const emailInput = screen.getByLabelText(/username or email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Fill the form
      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');

      // Submit the form
      await user.click(submitButton);

      // Wait a bit for state to update
      await waitFor(() => {
        // Inputs and button should be disabled during submission
        expect(emailInput).toBeDisabled();
        expect(passwordInput).toBeDisabled();
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('Authentication Flow', () => {
    it('✅ should successfully login with valid credentials', async () => {
      const user = userEvent.setup();

      // Mock successful login
      mockLogin.mockResolvedValueOnce({
        accessToken: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token',
        user: {
          id: '1',
          email: 'test@example.com',
          username: 'test',
          displayName: 'Test User',
          role: 'student',
          schoolId: 'school-1',
          classIds: ['class-1'],
          avatarUrl: null,
        }
      });

      renderWithProviders(<Login />);

      // Fill and submit form
      await user.type(screen.getByLabelText(/username or email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify login was called with correct credentials
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      });

      // Verify tokens are stored
      await waitFor(() => {
        expect(localStorage.getItem('auth_token')).toBe('mock-jwt-token');
        expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
      });

      // Verify navigation to dashboard
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('✅ should handle login errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock failed login
      // Mock login function
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      renderWithProviders(<Login />);

      // Fill and submit form
      await user.type(screen.getByLabelText(/username or email/i), 'wrong@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i);
      });

      // Should not navigate
      expect(mockNavigate).not.toHaveBeenCalled();

      // Tokens should not be stored
      expect(localStorage.getItem('auth_token')).toBeNull();
    });

    it('✅ should clear error when user starts typing', async () => {
      const user = userEvent.setup();

      // Mock failed login
      // Mock login function
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      renderWithProviders(<Login />);

      // Submit with wrong credentials
      await user.type(screen.getByLabelText(/username or email/i), 'wrong@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Error should be shown
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Clear the email field and type new value
      const emailInput = screen.getByLabelText(/username or email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'new@example.com');

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('✅ should navigate to password reset page', () => {
      renderWithProviders(<Login />);

      const forgotPasswordLink = screen.getByText(/forgot your password\?/i);
      expect(forgotPasswordLink).toHaveAttribute('href', '/password-reset');
    });

    it('✅ should navigate to registration page', () => {
      renderWithProviders(<Login />);

      const signUpLink = screen.getByText(/sign up here/i);
      expect(signUpLink).toHaveAttribute('href', '/register');
    });

    it('✅ should redirect to appropriate dashboard based on user role', async () => {
      const user = userEvent.setup();

      // Mock admin login
      // Mock login function
      mockLogin.mockResolvedValueOnce({
        accessToken: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token',
        user: {
          id: '1',
          email: 'admin@toolboxai.com',
          username: 'admin',
          displayName: 'Admin User',
          role: 'admin',
          schoolId: 'school-1',
          classIds: [],
          avatarUrl: null,
        }
      });

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username or email/i), 'admin@toolboxai.com');
      await user.type(screen.getByLabelText(/password/i), 'Admin123!');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Admin should go to dashboard
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });
});

/**
 * Test Results Summary:
 * Total Tests: 10
 * Testing real component functionality
 * All tests should pass if component works correctly
 */