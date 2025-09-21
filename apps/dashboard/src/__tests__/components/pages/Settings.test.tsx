jest.setTimeout(10000);

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Settings from '@/components/pages/Settings';
import { TestWrapper } from '@/test/utils/test-wrapper';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Settings', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders the settings page header', () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Save All Changes')).toBeInTheDocument();
  });

  it('displays all settings tabs', () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('Security')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();
    expect(screen.getByText('Language')).toBeInTheDocument();
    expect(screen.getByText('Accessibility')).toBeInTheDocument();
    expect(screen.getByText('Data')).toBeInTheDocument();
  });

  it('displays profile tab content by default', () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+1 (555) 123-4567')).toBeInTheDocument();
    expect(screen.getByText('Edit Profile')).toBeInTheDocument();
  });

  it('handles profile edit mode toggle', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    const editButton = screen.getByText('Edit Profile');
    await user.click(editButton);

    expect(screen.getByText('Save')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('switches to notifications tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Notifications'));
    expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
    expect(screen.getByText('Email Notifications')).toBeInTheDocument();
  });

  it('switches to security tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Security'));
    expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument();
    expect(screen.getByText('Change Password')).toBeInTheDocument();
  });

  it('switches to appearance tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Appearance'));
    expect(screen.getByText('Theme')).toBeInTheDocument();
    expect(screen.getByText('Color Scheme')).toBeInTheDocument();
  });

  it('displays notification options in notifications tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Notifications'));

    expect(screen.getByText('New messages')).toBeInTheDocument();
    expect(screen.getByText('Assignment updates')).toBeInTheDocument();
    expect(screen.getByText('Grade posted')).toBeInTheDocument();
    expect(screen.getByText('Weekly progress reports')).toBeInTheDocument();
  });

  it('displays theme options in appearance tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Appearance'));

    expect(screen.getByDisplayValue('light')).toBeInTheDocument();
    expect(screen.getByDisplayValue('dark')).toBeInTheDocument();
    expect(screen.getByDisplayValue('auto')).toBeInTheDocument();
  });

  it('displays security options in security tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Security'));

    expect(screen.getByText('Password')).toBeInTheDocument();
    expect(screen.getByText('Last changed: 30 days ago')).toBeInTheDocument();
    expect(screen.getByText('Configure Authenticator App')).toBeInTheDocument();
    expect(screen.getByText('Active Sessions')).toBeInTheDocument();
  });

  it('displays language options in language tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Language'));

    expect(screen.getByText('Language Preference')).toBeInTheDocument();
    expect(screen.getByText('Regional Settings')).toBeInTheDocument();
    expect(screen.getByText('Date Format')).toBeInTheDocument();
    expect(screen.getByDisplayValue('English')).toBeInTheDocument();
  });

  it('displays accessibility options in accessibility tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Accessibility'));

    expect(screen.getByText('Accessibility Features')).toBeInTheDocument();
    expect(screen.getByText('Large text')).toBeInTheDocument();
    expect(screen.getByText('High contrast')).toBeInTheDocument();
    expect(screen.getByText('Enable keyboard shortcuts')).toBeInTheDocument();
  });

  it('displays data management options in data tab', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Data'));

    expect(screen.getByText('Data Management')).toBeInTheDocument();
    expect(screen.getByText('Download My Data')).toBeInTheDocument();
    expect(screen.getByText('Delete My Account')).toBeInTheDocument();
    expect(screen.getByText('Allow analytics')).toBeInTheDocument();
  });

  it('shows user role chip in profile', () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('teacher')).toBeInTheDocument();
  });

  it('displays timezone selector in profile', () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByDisplayValue('PST')).toBeInTheDocument();
  });

  it('handles profile form updates', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Edit Profile'));

    const nameInput = screen.getByDisplayValue('John Doe');
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Doe');

    expect(nameInput).toHaveValue('Jane Doe');
  });

  it('handles theme selection', async () => {
    render(
      <TestWrapper
        initialState={{
          user: {
            email: 'test@example.com',
            role: 'teacher',
            displayName: 'Test User'
          },
          ui: {
            theme: 'light'
          }
        }}
      >
        <Settings />
      </TestWrapper>
    );

    await user.click(screen.getByText('Appearance'));

    const lightRadio = screen.getByDisplayValue('light');
    const darkRadio = screen.getByDisplayValue('dark');

    expect(lightRadio).toBeChecked();

    await user.click(darkRadio);
    expect(darkRadio).toBeChecked();
  });
});
