/**
 * Storybook Preview Configuration
 * Updated for Mantine v8 and Roblox Theme
 *
 * @version 2.0.0
 * @since 2025-10-01
 */

import React from 'react';
import type { Preview } from '@storybook/react';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';

// Import Mantine theme
import { mantineTheme } from '../src/theme/mantine-theme';

// Import store slices for mock store
import uiReducer from '../src/store/slices/uiSlice';
import userReducer from '../src/store/slices/userSlice';
import dashboardReducer from '../src/store/slices/dashboardSlice';
import gamificationReducer from '../src/store/slices/gamificationSlice';
import messagesReducer from '../src/store/slices/messagesSlice';
import progressReducer from '../src/store/slices/progressSlice';
import assessmentsReducer from '../src/store/slices/assessmentsSlice';
import complianceReducer from '../src/store/slices/complianceSlice';
import analyticsReducer from '../src/store/slices/analyticsSlice';
import classesReducer from '../src/store/slices/classesSlice';
import lessonsReducer from '../src/store/slices/lessonsSlice';
import realtimeReducer from '../src/store/slices/realtimeSlice';
import robloxReducer from '../src/store/slices/robloxSlice';

// Import Mantine styles
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

// Create a mock store for Storybook
const mockStore = configureStore({
  reducer: {
    ui: uiReducer,
    user: userReducer,
    dashboard: dashboardReducer,
    gamification: gamificationReducer,
    messages: messagesReducer,
    progress: progressReducer,
    assessments: assessmentsReducer,
    compliance: complianceReducer,
    analytics: analyticsReducer,
    classes: classesReducer,
    lessons: lessonsReducer,
    realtime: realtimeReducer,
    roblox: robloxReducer,
  },
});

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        { name: 'dark', value: '#0f0f2e' },
        { name: 'light', value: '#f0f2ff' },
      ],
    },
  },
  decorators: [
    (Story) => (
      <Provider store={mockStore}>
        <BrowserRouter>
          <MantineProvider theme={mantineTheme}>
            <Notifications position="top-right" />
            <Story />
          </MantineProvider>
        </BrowserRouter>
      </Provider>
    ),
  ],
};

export default preview;