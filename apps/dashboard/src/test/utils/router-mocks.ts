/**
 * Router Mocks for Testing
 *
 * Provides consistent React Router mocks that work across all tests
 * and prevent "mockNavigate is not defined" errors.
 */

import React from 'react';
import { vi } from 'vitest';

// Global router mocks that work across all tests
export const mockNavigate = vi.fn();
export const mockLocation = {
  pathname: '/',
  search: '',
  hash: '',
  state: null,
  key: 'default'
};

export const mockParams = {};
export const mockSearchParams = new URLSearchParams();
export const mockSetSearchParams = vi.fn();

// Set up module-level mocks before any component imports
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    // React Router v7 hooks - only override navigation hooks, keep router context
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
    useParams: () => mockParams,
    useSearchParams: () => [mockSearchParams, mockSetSearchParams],

    // Router v7 specific hooks
    useRouteError: () => null,
    useActionData: () => null,
    useLoaderData: () => ({}),
    useMatches: () => [],
    useNavigation: () => ({
      state: 'idle',
      location: undefined,
      formMethod: undefined,
      formAction: undefined,
      formEncType: undefined,
      formData: undefined,
    }),
    useRevalidator: () => ({
      state: 'idle',
      revalidate: vi.fn(),
    }),

    // Legacy hooks for compatibility (may be removed in v7)
    useHistory: () => ({
      push: mockNavigate,
      replace: vi.fn(),
      go: vi.fn(),
      goBack: vi.fn(),
      goForward: vi.fn(),
      listen: vi.fn(),
    }),

    // Keep actual router components for proper context - DON'T override these!
    // MemoryRouter, Router, Routes, Route need to be actual implementations
    // Only override navigation components
    Navigate: () => null,
    Outlet: () => null,
    Link: ({ children, to, ...props }: any) =>
      React.createElement('a', { href: to, ...props }, children),
    NavLink: ({ children, to, ...props }: any) =>
      React.createElement('a', { href: to, ...props }, children),
  };
});

/**
 * Reset all router mocks between tests
 */
export const resetRouterMocks = () => {
  mockNavigate.mockClear();
  mockSetSearchParams.mockClear();

  // Reset location to default
  Object.assign(mockLocation, {
    pathname: '/',
    search: '',
    hash: '',
    state: null,
    key: 'default'
  });

  // Clear params
  Object.keys(mockParams).forEach(key => delete mockParams[key]);

  // Clear search params
  mockSearchParams.forEach((_, key) => mockSearchParams.delete(key));
};

/**
 * Set mock location for testing navigation
 */
export const setMockLocation = (location: Partial<typeof mockLocation>) => {
  Object.assign(mockLocation, location);
};

/**
 * Set mock params for testing
 */
export const setMockParams = (params: Record<string, string>) => {
  Object.keys(mockParams).forEach(key => delete mockParams[key]);
  Object.assign(mockParams, params);
};

/**
 * Set mock search params for testing
 */
export const setMockSearchParams = (params: Record<string, string>) => {
  mockSearchParams.forEach((_, key) => mockSearchParams.delete(key));
  Object.entries(params).forEach(([key, value]) => {
    mockSearchParams.set(key, value);
  });
};

/**
 * Verify navigation was called with expected arguments
 */
export const expectNavigationTo = (path: string, options?: any) => {
  if (options) {
    expect(mockNavigate).toHaveBeenCalledWith(path, options);
  } else {
    expect(mockNavigate).toHaveBeenCalledWith(path);
  }
};

/**
 * Setup router mocks for a specific test scenario
 */
export const setupRouterMocks = (scenario: {
  currentPath?: string;
  params?: Record<string, string>;
  searchParams?: Record<string, string>;
}) => {
  if (scenario.currentPath) {
    setMockLocation({ pathname: scenario.currentPath });
  }

  if (scenario.params) {
    setMockParams(scenario.params);
  }

  if (scenario.searchParams) {
    setMockSearchParams(scenario.searchParams);
  }
};

export default {
  mockNavigate,
  mockLocation,
  mockParams,
  mockSearchParams,
  resetRouterMocks,
  setMockLocation,
  setMockParams,
  setMockSearchParams,
  expectNavigationTo,
  setupRouterMocks,
};