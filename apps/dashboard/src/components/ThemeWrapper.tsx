import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { useAppSelector } from '../store';
import { robloxLightTheme, robloxDarkTheme } from '../theme/robloxTheme';

interface ThemeWrapperProps {
  children: React.ReactNode;
}

export const ThemeWrapper: React.FC<ThemeWrapperProps> = ({ children }) => {
  const themeMode = useAppSelector((state) => state.ui.theme);

  // Use Roblox themes for the fun, energetic feel
  const selectedTheme = React.useMemo(() => {
    return themeMode === 'dark' ? robloxDarkTheme : robloxLightTheme;
  }, [themeMode]);

  return (
    <ThemeProvider theme={selectedTheme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};

export default ThemeWrapper;