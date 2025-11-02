import * as React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Drawer,
  Box,
  Text,
  Progress,
  Divider,
  Stack,
  Group,
  ScrollArea
} from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import {
  IconDashboard,
  IconSchool,
  IconUsers,
  IconClipboardCheck,
  IconTrophy,
  IconAward,
  IconShield,
  IconSettings,
  IconDeviceGamepad,
  IconUser,
  IconMessage,
  IconChartBar,
  IconCode,
  IconFlag,
  IconPuzzle,
  IconRobot
} from '@tabler/icons-react';
import { type UserRole } from '../../types';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleSidebar } from '../../store/slices/uiSlice';

const drawerWidth = 240;

interface Props {
  role: UserRole;
}

const roleMenus: Record<UserRole, { label: string; icon: React.ReactNode; path: string }[]> = {
  admin: [
    { label: 'Overview', icon: <IconDashboard size={20} />, path: '/' },
    { label: 'Schools', icon: <IconSchool size={20} />, path: '/schools' },
    { label: 'Users', icon: <IconUsers size={20} />, path: '/users' },
    { label: 'Compliance', icon: <IconShield size={20} />, path: '/compliance' },
    { label: 'Analytics', icon: <IconTrophy size={20} />, path: '/analytics' },
    { label: 'Agent System', icon: <IconRobot size={20} />, path: '/agents' },
    { label: 'Roblox Studio', icon: <IconPuzzle size={20} />, path: '/roblox' },
    { label: 'Integrations', icon: <IconCode size={20} />, path: '/integrations' },
    { label: 'Settings', icon: <IconSettings size={20} />, path: '/settings' },
  ],
  teacher: [
    { label: 'Overview', icon: <IconDashboard size={20} />, path: '/' },
    { label: 'Classes', icon: <IconUsers size={20} />, path: '/classes' },
    { label: 'Lessons', icon: <IconClipboardCheck size={20} />, path: '/lessons' },
    { label: 'Assessments', icon: <IconChartBar size={20} />, path: '/assessments' },
    { label: 'Roblox Studio', icon: <IconPuzzle size={20} />, path: '/roblox' },
    { label: 'Reports', icon: <IconTrophy size={20} />, path: '/reports' },
    { label: 'Messages', icon: <IconMessage size={20} />, path: '/messages' },
    { label: 'Settings', icon: <IconSettings size={20} />, path: '/settings' },
  ],
  student: [
    { label: 'Overview', icon: <IconDashboard size={20} />, path: '/' },
    { label: 'Missions', icon: <IconFlag size={20} />, path: '/missions' },
    { label: 'Progress', icon: <IconTrophy size={20} />, path: '/progress' },
    { label: 'Rewards', icon: <IconAward size={20} />, path: '/rewards' },
    { label: 'Leaderboard', icon: <IconTrophy size={20} />, path: '/leaderboard' },
    { label: 'Avatar', icon: <IconUser size={20} />, path: '/avatar' },
    { label: 'Play', icon: <IconDeviceGamepad size={20} />, path: '/play' },
    { label: 'Settings', icon: <IconSettings size={20} />, path: '/settings' },
  ],
  parent: [
    { label: 'Overview', icon: <IconDashboard size={20} />, path: '/' },
    { label: 'Progress', icon: <IconTrophy size={20} />, path: '/progress' },
    { label: 'Reports', icon: <IconChartBar size={20} />, path: '/reports' },
    { label: 'Messages', icon: <IconMessage size={20} />, path: '/messages' },
    { label: 'Settings', icon: <IconSettings size={20} />, path: '/settings' },
  ],
};

export default function Sidebar({ role }: Props) {
  const location = useLocation();
  const dispatch = useAppDispatch();
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);
  const xp = useAppSelector((s) => s.gamification.xp);
  const level = useAppSelector((s) => s.gamification.level);
  const nextLevelXP = useAppSelector((s) => s.gamification.nextLevelXP);
  const displayName = useAppSelector((s) => s.user.displayName);
  const firstName = useAppSelector((s) => s.user.firstName);
  
  // Mobile detection
  const isMobile = useMediaQuery('(max-width: 768px)');

  const progress = ((xp % 100) / 100) * 100;

  // Roles are already normalized as lowercase strings matching UserRole
  const menuItems = roleMenus[role] || roleMenus.student;
  
  // Auto-close sidebar on mobile when clicking navigation items
  const handleNavigation = () => {
    if (isMobile && sidebarOpen) {
      dispatch(toggleSidebar());
    }
  };

  // On desktop, render as fixed sidebar. On mobile, render as drawer.
  const sidebarContent = (
    <ScrollArea h="100vh">
      {/* Space for toolbar */}
      <Box h={64} />

      {/* User Info Section */}
      <Box
        p="md"
        mx="md"
        mb="xs"
        style={{
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))',
          border: '1px solid rgba(0, 188, 212, 0.3)',
          borderRadius: 'var(--mantine-radius-md)',
        }}
      >
        <Text
          size="lg"
          fw={600}
          mb="xs"
          style={{
            background: 'linear-gradient(135deg, #00bcd4, #e91e63)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
            letterSpacing: '-0.02em',
          }}
        >
          {firstName || displayName || role}
        </Text>

        {/* XP Progress for Students */}
        {role === 'student' && (
          <Stack spacing={4} mt="sm">
            <Group position="apart">
              <Text size="xs" color="dimmed">
                Level {level}
              </Text>
              <Text size="xs" color="dimmed">
                {xp} / {nextLevelXP} XP
              </Text>
            </Group>
            <Progress
              value={progress}
              size="sm"
              radius="xl"
              styles={{
                root: {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                },
                bar: {
                  background: 'linear-gradient(90deg, #9333EA 0%, #14B8A6 100%)',
                },
              }}
            />
          </Stack>
        )}
      </Box>

      <Divider color="rgba(255,255,255,0.1)" />

      {/* Navigation Menu */}
      <Stack spacing={6} p="sm" mt="sm">
        {menuItems.map((item) => {
          // Build full path with role prefix
          const rolePrefix = `/${role}`;
          const fullPath = item.path === '/' ? `${rolePrefix}/overview` : `${rolePrefix}${item.path}`;

          // Improved route matching: exact match or starts with the path for nested routes
          const isActive = location.pathname === fullPath ||
                          (item.path !== '/' && location.pathname.startsWith(fullPath));

          return (
            <Box
              key={item.path}
              component={Link}
              to={fullPath}
              onClick={handleNavigation}
              sx={(theme: any) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '14px 16px',
                borderRadius: theme.radius.md,
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                color: 'white',
                textDecoration: 'none',
                width: '100%',
                border: '1px solid',
                cursor: 'pointer',
                ...(isActive ? {
                  background: 'linear-gradient(135deg, #00d9ff 0%, #ff2d95 100%)',
                  boxShadow: '0 6px 20px rgba(0, 217, 255, 0.5), 0 0 30px rgba(0, 217, 255, 0.2)',
                  borderColor: 'rgba(0, 217, 255, 0.6)',
                  transform: 'translateX(4px)',
                } : {
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderColor: 'rgba(255, 255, 255, 0.08)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, rgba(0, 217, 255, 0.25) 0%, rgba(255, 45, 149, 0.25) 100%)',
                    borderColor: 'rgba(0, 217, 255, 0.5)',
                    boxShadow: '0 4px 12px rgba(0, 217, 255, 0.3)',
                    transform: 'translateX(4px)',
                  },
                }),
              })}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  color: isActive ? '#ffffff' : '#00d9ff',
                  filter: isActive ? 'none' : 'brightness(0.9)',
                  fontSize: '20px',
                }}
              >
                {item.icon}
              </Box>
              <Text
                size="md"
                sx={{
                  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.95rem',
                  color: isActive ? '#ffffff' : '#e0f7ff',
                  letterSpacing: '0.01em',
                  textShadow: isActive ? '0 0 8px rgba(0, 217, 255, 0.4)' : 'none',
                }}
              >
                {item.label}
              </Text>
            </Box>
          );
        })}
      </Stack>

      {/* Quick Stats for Teachers/Admins */}
      {(role === 'teacher' || role === 'admin') && (
        <>
          <Divider color="rgba(255,255,255,0.1)" />
          <Box p="md">
            <Text 
              size="sm" 
              mb="md"
              style={{
                fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
                fontWeight: 700,
                letterSpacing: '0.1em',
                color: '#00d9ff',
                textTransform: 'uppercase',
              }}
            >
              Quick Stats
            </Text>
            <Stack spacing={8}>
              <Group position="apart">
                <Text size="sm" style={{ color: '#a0e7ff', fontFamily: 'Inter, sans-serif' }}>Active Classes</Text>
                <Text size="sm" fw={700} style={{ color: '#00d9ff', fontFamily: 'Inter, sans-serif' }}>
                  4
                </Text>
              </Group>
              <Group position="apart">
                <Text size="sm" style={{ color: '#a0e7ff', fontFamily: 'Inter, sans-serif' }}>Total Students</Text>
                <Text size="sm" fw={700} style={{ color: '#00d9ff', fontFamily: 'Inter, sans-serif' }}>
                  86
                </Text>
              </Group>
              <Group position="apart">
                <Text size="sm" style={{ color: '#a0e7ff', fontFamily: 'Inter, sans-serif' }}>Pending Tasks</Text>
                <Text size="sm" fw={700} style={{ color: '#ff2d95', fontFamily: 'Inter, sans-serif' }}>
                  12
                </Text>
              </Group>
            </Stack>
          </Box>
        </>
      )}
    </ScrollArea>
  );

  // Mobile: Use Drawer
  if (isMobile) {
    return (
      <Drawer
        opened={sidebarOpen}
        onClose={() => dispatch(toggleSidebar())}
        size={drawerWidth}
        position="left"
        withCloseButton={false}
        withOverlay={true}
        zIndex={100}
        transitionProps={{ duration: 300, timingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)' }}
        styles={{
          drawer: {
            background: 'linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%)',
            borderRight: '2px solid var(--mantine-color-cyan-6)',
            boxShadow: '0 0 20px rgba(0, 188, 212, 0.3)',
          },
        }}
      >
        {sidebarContent}
      </Drawer>
    );
  }

  // Desktop: Fixed sidebar
  return (
    <Box
      style={{
        width: drawerWidth,
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        background: 'linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%)',
        borderRight: '2px solid var(--mantine-color-cyan-6)',
        boxShadow: '0 0 20px rgba(0, 188, 212, 0.3)',
        zIndex: 100,
        overflowY: 'auto',
      }}
    >
      {sidebarContent}
    </Box>
  );
}