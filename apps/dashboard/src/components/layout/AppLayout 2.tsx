import * as React from 'react';
import { Box } from '@mantine/core';
import Topbar from './Topbar';
import Sidebar from './Sidebar';
import { type UserRole } from '../../types';
import { useAppSelector } from '../../store';
// ParticleEffects removed - deprecated component archived

interface Props {
  role: UserRole;
  children: React.ReactNode;
  isRobloxPage?: boolean;
}

export default function AppLayout({ role, children, isRobloxPage = false }: Props) {
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);
  const drawerWidth = 240;

  return (
    <Box
      style={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: 'var(--mantine-color-dark-7)',
        overflow: 'hidden',
      }}
    >
      <Topbar />
      <Sidebar role={role} />
      <Box
        component="main"
        style={{
          flexGrow: 1,
          padding: 'var(--mantine-spacing-md)',
          width: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%',
          marginLeft: sidebarOpen ? `${drawerWidth}px` : 0,
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0f0f2e 0%, #1a0b2e 50%, #2e0b2e 100%)',
          position: 'relative',
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
        styles={{
          root: {
            '@media (max-width: 768px)': {
              padding: 'var(--mantine-spacing-sm)',
              width: '100%',
              marginLeft: 0,
            },
          },
        }}
      >
        {/* Particle Effects removed - deprecated component */}

        {/* Spacer for Topbar - equivalent to MUI Toolbar */}
        <Box style={{ height: '64px' }} />

        <Box style={{ position: 'relative', zIndex: 1, minHeight: 'calc(100vh - 64px)' }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}