import { vi } from 'vitest';

// Configure test timeout
vi.setConfig({ testTimeout: 30000 });

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import LoadingSpinner from '../LoadingSpinner';
import NotFoundPage from '../NotFoundPage';
import SettingsPage from '../SettingsPage';
import ProfilePage from '../ProfilePage';

const renderWithProviders = (component: React.ReactElement) => {
  return render(<MantineProvider>{component}</MantineProvider>);
};

describe('Shared Components (Stubs)', () => {
  describe('LoadingSpinner', () => {
    it('renders without crashing', () => {
      const { container } = renderWithProviders(<LoadingSpinner />);
      expect(container).toBeTruthy();
    });

    it('renders with fullScreen prop', () => {
      const { container } = renderWithProviders(<LoadingSpinner fullScreen={true} />);
      expect(container).toBeTruthy();
    });

    it('renders with message prop', () => {
      const { container } = renderWithProviders(<LoadingSpinner message="Loading..." />);
      expect(container).toBeTruthy();
    });
  });

  describe('NotFoundPage', () => {
    it('renders without crashing', () => {
      const { container } = renderWithProviders(<NotFoundPage />);
      expect(container).toBeTruthy();
    });
  });

  describe('SettingsPage', () => {
    it('renders without crashing', () => {
      const { container } = renderWithProviders(<SettingsPage />);
      expect(container).toBeTruthy();
    });
  });

  describe('ProfilePage', () => {
    it('renders without crashing', () => {
      const { container } = renderWithProviders(<ProfilePage />);
      expect(container).toBeTruthy();
    });
  });
});
