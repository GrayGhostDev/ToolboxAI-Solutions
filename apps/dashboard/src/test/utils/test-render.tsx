import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
/**
 * Custom render function for React 18 compatibility
 *
 * This render function wraps components with necessary providers
 * and handles React 18 concurrent features properly
 */

import React from 'react';
import { render as rtlRender, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
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

// Create a simple theme for testing
const testTheme = createTheme({
  palette: {
    mode: 'light',
  },
});

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
        immutableCheck: false,
      }),
  });
};

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialState?: any;
  store?: any;
}

/**
 * Custom render function that includes all providers
 */
export function renderWithProviders(
  ui: React.ReactElement,
  {
    initialState = {},
    store = createTestStore(initialState),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <BrowserRouter>
          <ThemeProvider theme={testTheme}>
            <CssBaseline />
            {children}
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    );
  }

  // Use RTL's render with our wrapper
  const result = rtlRender(ui, { wrapper: Wrapper, ...renderOptions });

  // Return render result with store for testing
  return {
    ...result,
    store,
  };
}

// Re-export everything from testing library
export * from '@testing-library/react';
export { renderWithProviders as render };