/**
 * Test Wrapper Component
 *
 * Provides a simplified wrapper for testing that bypasses MUI styling issues
 */

import React from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { WebSocketProvider } from './websocket-test-provider';
import { EmotionTestProvider } from './emotion-test-setup';
import userSlice from '@/store/slices/userSlice';
import uiSlice from '@/store/slices/uiSlice';
import dashboardSlice from '@/store/slices/dashboardSlice';
import assessmentsSlice from '@/store/slices/assessmentsSlice';
import complianceSlice from '@/store/slices/complianceSlice';
import messagesSlice from '@/store/slices/messagesSlice';
import progressSlice from '@/store/slices/progressSlice';
import gamificationSlice from '@/store/slices/gamificationSlice';
import analyticsSlice from '@/store/slices/analyticsSlice';
import classesSlice from '@/store/slices/classesSlice';
import lessonsSlice from '@/store/slices/lessonsSlice';
import realtimeSlice from '@/store/slices/realtimeSlice';
import robloxSlice from '@/store/slices/robloxSlice';

// Using 2025 best practices for Emotion/MUI testing
// Theme is now handled by EmotionTestProvider

// Create test store
const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: {
      user: userSlice,
      ui: uiSlice,
      dashboard: dashboardSlice,
      assessments: assessmentsSlice,
      compliance: complianceSlice,
      messages: messagesSlice,
      progress: progressSlice,
      gamification: gamificationSlice,
      analytics: analyticsSlice,
      classes: classesSlice,
      lessons: lessonsSlice,
      realtime: realtimeSlice,
      roblox: robloxSlice,
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
}

export const TestWrapper: React.FunctionComponent<TestWrapperProps> = ({ children, initialState = {} }) => {
  const store = createTestStore(initialState);

  return (
    <Provider store={store}>
      <BrowserRouter>
        <WebSocketProvider>
          <EmotionTestProvider>
            {children}
          </EmotionTestProvider>
        </WebSocketProvider>
      </BrowserRouter>
    </Provider>
  );
};

export { createTestStore };