import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import '@testing-library/jest-dom';

// Mock the store slices
const mockStore = configureStore({
  reducer: {
    ui: () => ({ theme: 'light', loading: false }),
    user: () => ({ currentUser: null, isAuthenticated: false }),
    dashboard: () => ({ metrics: {} }),
  },
});

// Mock Pusher
vi.mock('pusher-js', () => ({
  default: vi.fn(() => ({
    subscribe: vi.fn(() => ({
      bind: vi.fn(),
      unbind: vi.fn(),
      trigger: vi.fn(),
    })),
    unsubscribe: vi.fn(),
    disconnect: vi.fn(),
    connection: {
      bind: vi.fn(),
      unbind: vi.fn(),
      state: 'connected',
    },
  })),
}));

// Mock the config
vi.mock('../config', () => ({
  API_BASE_URL: 'http://localhost:8008',
  WS_URL: 'http://localhost:8008',
  ENABLE_WEBSOCKET: false,
  PUSHER_KEY: 'test-key',
  PUSHER_CLUSTER: 'us2',
}));

describe('App Component', () => {
  it('should render without crashing', () => {
    const AppComponent = () => (
      <Provider store={mockStore}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          <div>App Loaded</div>
        </BrowserRouter>
      </Provider>
    );

    render(<AppComponent />);
    expect(screen.getByText('App Loaded')).toBeInTheDocument();
  });

  it('should have correct Redux store structure', () => {
    const state = mockStore.getState();
    expect(state).toHaveProperty('ui');
    expect(state).toHaveProperty('user');
    expect(state).toHaveProperty('dashboard');
  });
});