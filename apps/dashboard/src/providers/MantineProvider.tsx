import React from 'react';
import {
  MantineProvider as BaseMantineProvider,
  createTheme,
  MantineColorsTuple,
  DEFAULT_THEME,
  MantineColorScheme
} from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/charts/styles.css';
import '@mantine/spotlight/styles.css';
import '@mantine/tiptap/styles.css';

import { robloxMantineTheme } from '../config/mantine-theme';

interface MantineProviderProps {
  children: React.ReactNode;
}

export function MantineProvider({ children }: MantineProviderProps) {
  // Start with a default theme and let the theme context handle changes later
  return (
    <BaseMantineProvider theme={robloxMantineTheme} defaultColorScheme="light">
      <Notifications position="top-right" limit={5} />
      {children}
    </BaseMantineProvider>
  );
}

export { robloxMantineTheme as theme };
