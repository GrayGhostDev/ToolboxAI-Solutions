jest.setTimeout(10000);

/**
 * Simplified Login Component Test
 * Using React 18 compatible testing approach
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '@/test/utils/test-render';
import Login from '@/components/pages/Login';

// Mock the API
vi.mock('@/services/api', () => ({
  login: vi.fn(),
}));

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock websocket
vi.mock('../../services/pusher', () => ({
  connectWebSocket: vi.fn().mockResolvedValue(undefined),
}));

describe('Login Component (Simplified)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should render login form', () => {
    render(<Login />);

    // Check for essential elements
    expect(screen.getByLabelText(/username or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should update input values when typing', async () => {
    const user = userEvent.setup();
    render(<Login />);

    const emailInput = screen.getByLabelText(/username or email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('should handle form submission', async () => {
    const user = userEvent.setup();
    const { login } = await import('@/services/api');

    // Mock successful login
    (login as any).mockResolvedValueOnce({
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh',
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'test',
        displayName: 'Test User',
        role: 'student',
        schoolId: 'school-1',
        classIds: [],
        avatarUrl: null,
      }
    });

    render(<Login />);

    // Fill form
    await user.type(screen.getByLabelText(/username or email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');

    // Submit
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify login was called
    await waitFor(() => {
      expect(login).toHaveBeenCalledWith('test@example.com', 'password123');
    });

    // Verify navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  it('should show error on failed login', async () => {
    const user = userEvent.setup();
    const { login } = await import('@/services/api');

    // Mock failed login
    (login as any).mockRejectedValueOnce(new Error('Invalid credentials'));

    render(<Login />);

    // Fill and submit form
    await user.type(screen.getByLabelText(/username or email/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Check for error message
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    // Should not navigate
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});