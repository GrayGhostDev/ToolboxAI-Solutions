/**
 * Development Role Switcher Component
 * Only renders in development mode
 * Allows easy switching between roles for testing
 */

import React from 'react';
import { Button, Group, Paper, Text, Stack } from '@mantine/core';
import { IconUser, IconSchool, IconUsers, IconShield } from '@tabler/icons-react';
import { useAppSelector, useAppDispatch } from '../../store';
import { setRole } from '../../store/slices/userSlice';
import type { UserRole } from '../../types/roles';

const roleIcons: Record<UserRole, React.ReactNode> = {
  student: <IconUser size={16} />,
  teacher: <IconSchool size={16} />,
  parent: <IconUsers size={16} />,
  admin: <IconShield size={16} />,
};

const roleColors: Record<UserRole, string> = {
  student: 'blue',
  teacher: 'green',
  parent: 'orange',
  admin: 'red',
};

export function DevRoleSwitcher() {
  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const dispatch = useAppDispatch();
  const currentRole = useAppSelector((s) => s.user.role);
  const [switching, setSwitching] = React.useState(false);

  const handleRoleSwitch = async (role: UserRole) => {
    setSwitching(true);
    try {
      // Update Redux store directly in dev mode
      dispatch(setRole(role));

      // Reload page to apply new role routing
      setTimeout(() => {
        window.location.href = '/';
      }, 500);
    } finally {
      setSwitching(false);
    }
  };

  return (
    <Paper
      p="md"
      withBorder
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 9999,
        background: 'rgba(0, 0, 0, 0.9)',
        borderColor: '#00d9ff',
        boxShadow: '0 0 20px rgba(0, 217, 255, 0.3)',
      }}
    >
      <Stack spacing="xs">
        <Text
          size="sm"
          weight={700}
          style={{
            color: '#00d9ff',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}
        >
          Dev: Role Switcher
        </Text>

        <Text size="xs" style={{ color: '#a0e7ff' }}>
          Current: {currentRole}
        </Text>

        <Group spacing="xs">
          {(['student', 'teacher', 'parent', 'admin'] as UserRole[]).map((role) => (
            <Button
              key={role}
              size="xs"
              color={roleColors[role]}
              variant={currentRole === role ? 'filled' : 'outline'}
              leftSection={roleIcons[role]}
              onClick={() => handleRoleSwitch(role)}
              disabled={switching || currentRole === role}
              style={{
                opacity: currentRole === role ? 0.7 : 1,
              }}
            >
              {role.charAt(0).toUpperCase() + role.slice(1)}
            </Button>
          ))}
        </Group>

        {switching && (
          <Text size="xs" style={{ color: '#ffb347' }}>
            Switching role...
          </Text>
        )}
      </Stack>
    </Paper>
  );
}

