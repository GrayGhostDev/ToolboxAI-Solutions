import React from 'react';
import {
  MantineProvider as BaseMantineProvider,
  createTheme,
  MantineColorsTuple,
  DEFAULT_THEME,
  MantineColorScheme
} from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { useThemeContext } from '../contexts/ThemeContext';
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

function MantineProviderInner({ children }: MantineProviderProps) {
  const { actualMode } = useThemeContext();
  const colorScheme: MantineColorScheme = actualMode;

  return (
    <BaseMantineProvider theme={robloxMantineTheme} defaultColorScheme={colorScheme}>
      <Notifications position="top-right" limit={5} />
      {children}
    </BaseMantineProvider>
  );
}

export function MantineProvider({ children }: MantineProviderProps) {
  // We need to handle cases where ThemeContext might not be available yet
  try {
    return <MantineProviderInner>{children}</MantineProviderInner>;
  } catch (error) {
    // Fallback if theme context is not available
    return (
      <BaseMantineProvider theme={robloxMantineTheme} defaultColorScheme="light">
        <Notifications position="top-right" limit={5} />
        {children}
      </BaseMantineProvider>
    );
  }
}

export { robloxMantineTheme as theme };