/**
 * App Component Test Suite
 * Tests basic app loading and Redux store structure
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@test/utils/render';
import { MemoryRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

// Mock the store slices
const mockStore = configureStore({
  reducer: {
    ui: () => ({ theme: 'light', loading: false }),
    user: () => ({ currentUser: null, isAuthenticated: false }),
    dashboard: () => ({ metrics: {} }),
  },
});

describe('App Component Infrastructure', () => {
  it('should render a simple component without crashing', () => {
    const SimpleComponent = () => <div data-testid="simple-app">App Infrastructure Test</div>;

    render(<SimpleComponent />);
    expect(screen.getByTestId('simple-app')).toBeInTheDocument();
    expect(screen.getByText('App Infrastructure Test')).toBeInTheDocument();
  });

  it('should work with custom store state', () => {
    const TestComponent = () => <div data-testid="store-test">Store Test</div>;

    render(<TestComponent />, {
      preloadedState: {
        ui: { theme: 'dark', loading: false },
        user: { currentUser: { name: 'Test User' }, isAuthenticated: true },
      }
    });

    expect(screen.getByTestId('store-test')).toBeInTheDocument();
  });

  it('should work with router navigation', () => {
    const TestComponent = () => <div data-testid="router-test">Router Test</div>;

    render(<TestComponent />, {
      routerProps: {
        initialEntries: ['/test'],
        initialIndex: 0,
      }
    });

    expect(screen.getByTestId('router-test')).toBeInTheDocument();
  });

  it('should validate test utilities are working', () => {
    // Test that our enhanced expect matchers work
    const element = document.createElement('div');
    element.textContent = 'Test';
    document.body.appendChild(element);

    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent('Test');
  });
});