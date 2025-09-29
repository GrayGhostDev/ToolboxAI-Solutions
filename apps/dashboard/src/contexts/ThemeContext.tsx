import React, { createContext, useContext, useEffect, useState } from 'react';
import { getRobloxTheme } from '../theme/robloxTheme';
import { useAppDispatch, useAppSelector } from '../store';
import { setTheme } from '../store/slices/uiSlice';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  mode: ThemeMode;
  actualMode: 'light' | 'dark';
  theme: typeof import('../theme/robloxTheme').robloxTheme;
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
  isDark: boolean;
  isSystem: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

// Detect system theme preference
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

// Get stored theme preference
const getStoredTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'system';
  const stored = localStorage.getItem('roblox-theme-mode');
  if (stored && ['light', 'dark', 'system'].includes(stored)) {
    return stored as ThemeMode;
  }
  return 'system';
};

// Store theme preference
const storeTheme = (mode: ThemeMode) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('roblox-theme-mode', mode);
  }
};

export const RobloxThemeProvider: React.FunctionComponent<ThemeProviderProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const reduxTheme = useAppSelector((state) => state.ui.theme);
  
  const [mode, setMode] = useState<ThemeMode>(() => {
    const stored = getStoredTheme();
    // Sync with Redux on initial load
    if (stored === 'system') {
      const systemTheme = getSystemTheme();
      dispatch(setTheme(systemTheme));
      return 'system';
    } else {
      dispatch(setTheme(stored));
      return stored;
    }
  });
  
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>(getSystemTheme);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      const newSystemTheme = e.matches ? 'dark' : 'light';
      setSystemTheme(newSystemTheme);
      
      // If in system mode, update the actual theme
      if (mode === 'system') {
        dispatch(setTheme(newSystemTheme));
      }
    };

    mediaQuery.addEventListener("change", handleChange as EventListener);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mode, dispatch]);

  // Calculate actual theme mode
  const actualMode: 'light' | 'dark' = mode === 'system' ? systemTheme : mode;
  
  // Get the theme object
  const theme = getRobloxTheme(actualMode);

  // Theme control functions
  const toggleTheme = () => {
    const newMode = actualMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
  };

  const setThemeMode = (newMode: ThemeMode) => {
    setMode(newMode);
    storeTheme(newMode);
    
    // Update Redux store
    const newActualMode = newMode === 'system' ? systemTheme : newMode;
    dispatch(setTheme(newActualMode));
  };

  // Sync with Redux changes (for backward compatibility)
  useEffect(() => {
    if (mode !== 'system' && reduxTheme !== actualMode) {
      setMode(reduxTheme);
      storeTheme(reduxTheme);
    }
  }, [reduxTheme, actualMode, mode]);

  const contextValue: ThemeContextType = {
    mode,
    actualMode,
    theme,
    toggleTheme,
    setThemeMode,
    isDark: actualMode === 'dark',
    isSystem: mode === 'system'
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export default RobloxThemeProvider;
