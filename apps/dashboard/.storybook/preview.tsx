import React from 'react';
import type { Preview } from '@storybook/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';

// Import your theme
import { lightTheme } from '../src/theme';

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
  },
  decorators: [
    (Story) => (
      <Provider store={mockStore}>
        <BrowserRouter>
          <ThemeProvider theme={lightTheme}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <CssBaseline />
              <Story />
            </LocalizationProvider>
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    ),
  ],
};

export default preview;