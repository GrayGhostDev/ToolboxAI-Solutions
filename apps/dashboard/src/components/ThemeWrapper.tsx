import React from 'react';
import { RobloxThemeProvider } from '../contexts/ThemeContext';
import { MantineProvider } from '../providers/MantineProvider';

interface ThemeWrapperProps {
  children: React.ReactNode;
}

export const ThemeWrapper: React.FunctionComponent<ThemeWrapperProps> = ({ children }) => {
  return (
    <RobloxThemeProvider>
      <MantineProvider>
        <style dangerouslySetInnerHTML={{ __html: `
          /* Custom global styles for Roblox theme */
          * {
            box-sizing: border-box;
          }

          *, *::before, *::after {
            box-sizing: inherit;
          }

          #root {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
          }

          /* Custom scrollbar for Roblox theme */
          ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }

          ::-webkit-scrollbar-track {
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: 9999px;
          }

          ::-webkit-scrollbar-thumb {
            background-color: rgba(226, 35, 26, 0.6);
            border-radius: 9999px;
          }

          ::-webkit-scrollbar-thumb:hover {
            background-color: rgba(226, 35, 26, 0.8);
          }

          /* Focus styles */
          *:focus-visible {
            outline: 2px solid var(--mantine-color-roblox-cyan-6);
            outline-offset: 2px;
          }

          /* Selection styles */
          ::selection {
            background-color: rgba(226, 35, 26, 0.2);
            color: inherit;
          }

          /* Disable text selection on UI elements */
          button, [role="button"] {
            user-select: none;
          }

          /* Smooth scrolling */
          @media (prefers-reduced-motion: no-preference) {
            html {
              scroll-behavior: smooth;
            }
          }
        ` }} />
        {children}
      </MantineProvider>
    </RobloxThemeProvider>
  );
};

export default ThemeWrapper;