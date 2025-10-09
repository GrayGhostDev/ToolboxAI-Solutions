/**
 * Test Wrapper Component
 *
 * Provides a simplified wrapper for testing that bypasses MUI styling issues
 */

import React from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';

// Simple reducer setup to avoid complex dependencies
const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: {
      user: (state = { isAuthenticated: false, user: null, token: null }, action) => {
        switch (action.type) {
          case 'user/signInSuccess':
            return {
              ...state,
              isAuthenticated: true,
              user: (action.payload as any)?.user,
              token: (action.payload as any)?.token
            };
          case 'user/signOut':
            return {
              ...state,
              isAuthenticated: false,
              user: null,
              token: null
            };
          default:
            return state;
        }
      },
      // Minimal reducers for other slices to prevent errors
      ui: (state = {}, action) => state,
      dashboard: (state = {}, action) => state,
      assessments: (state = {}, action) => state,
      compliance: (state = {}, action) => state,
      messages: (state = {}, action) => state,
      progress: (state = {}, action) => state,
      gamification: (state = {}, action) => state,
      analytics: (state = {}, action) => state,
      classes: (state = {}, action) => state,
      lessons: (state = {}, action) => state,
      realtime: (state = {}, action) => state,
      roblox: (state = {}, action) => state,
    },
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }),
  });
};

interface TestWrapperProps {
  children: React.ReactNode;
  initialState?: any;
  authState?: 'authenticated' | 'unauthenticated' | 'loading';
  userRole?: 'admin' | 'teacher' | 'student';
}

export const TestWrapper: React.FunctionComponent<TestWrapperProps> = ({
  children,
  initialState = {},
  authState = 'authenticated',
  userRole = 'student'
}) => {
  // Create initial state with auth information
  const mockUser = authState === 'authenticated' ? {
    id: 'test-user-id',
    email: `${userRole}@test.com`,
    username: `test_${userRole}`,
    displayName: `Test ${userRole}`,
    role: userRole,
    schoolId: 'test-school',
    classIds: userRole === 'teacher' ? ['class-1', 'class-2'] : ['class-1'],
    avatarUrl: null,
  } : null;

  const storeInitialState = {
    user: {
      isAuthenticated: authState === 'authenticated',
      isLoading: authState === 'loading',
      user: mockUser,
      token: authState === 'authenticated' ? 'mock-jwt-token' : null,
      refreshToken: authState === 'authenticated' ? 'mock-refresh-token' : null,
      error: null,
    },
    ...initialState
  };

  const store = createTestStore(storeInitialState);

  return (
    <Provider store={store}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </Provider>
  );
};

export { createTestStore };