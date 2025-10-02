import React from 'react';
import type { Preview } from '@storybook/react';
import { MantineProvider } from '@mantine/core';
import { DatesProvider } from '@mantine/dates';
import { Notifications } from '@mantine/notifications';
import { ModalsProvider } from '@mantine/modals';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';

// Import Mantine styles
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/notifications/styles.css';

// Import your Mantine theme
import { theme } from '../src/theme/mantine-theme';

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
      default: 'light',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#1a1b1e' },
      ],
    },
  },
  decorators: [
    (Story) => (
      <Provider store={mockStore}>
        <BrowserRouter>
          <MantineProvider theme={theme}>
            <DatesProvider settings={{}}>
              <ModalsProvider>
                <Notifications position="top-right" />
                <Story />
              </ModalsProvider>
            </DatesProvider>
          </MantineProvider>
        </BrowserRouter>
      </Provider>
    ),
  ],
};

export default preview;