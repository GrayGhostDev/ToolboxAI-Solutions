import * as React from 'react';
import { Box, AppShell } from '@mantine/core';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { type UserRole } from '../../types';

interface AppLayoutProps {
  children: React.ReactNode;
  role: UserRole;
  isRobloxPage?: boolean;
}

export default function AppLayout({ children, role, isRobloxPage = false }: AppLayoutProps) {
  return (
    <AppShell
      header={{ height: 64 }}
      navbar={{ width: 240, breakpoint: 'sm' }}
      padding="md"
    >
      <AppShell.Header>
        <Topbar />
      </AppShell.Header>

      <AppShell.Navbar>
        <Sidebar role={role} />
      </AppShell.Navbar>

      <AppShell.Main>
        <Box
          style={{
            minHeight: 'calc(100vh - 64px)',
            padding: '1rem',
          }}
        >
          {children}
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}
