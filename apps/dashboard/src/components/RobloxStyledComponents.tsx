/**
 * Roblox-Styled Components
 *
 * Pre-built components with Roblox theming and gamification elements.
 * 🎯 100% PURE MANTINE v8 IMPLEMENTATION - ZERO MUI/EMOTION DEPENDENCIES
 */
import React from 'react';
import {
  Box,
  Card,
  Button,
  Text,
  Paper,
  Stack,
  Group,
  Container,
  ActionIcon,
  Avatar,
  Divider,
  TextInput,
  Badge,
  Alert,
  Loader,
  Progress,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Select,
  Skeleton
} from '@mantine/core';

// Roblox brand colors
const ROBLOX_RED = '#E2231A';
const ROBLOX_RED_DARK = '#B71C15';
const ROBLOX_GRAY = '#393B3D';
const ROBLOX_WHITE = '#FFFFFF';

// Pure CSS animations (no emotion/styled-components)
const injectRobloxAnimations = () => {
  if (typeof document !== 'undefined' && !document.getElementById('roblox-animations')) {
    const style = document.createElement('style');
    style.id = 'roblox-animations';
    style.textContent = `
      @keyframes robloxPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.9; }
      }
      @keyframes robloxGlow {
        0%, 100% { box-shadow: 0 0 5px rgba(226, 35, 26, 0.25); }
        50% { box-shadow: 0 0 20px rgba(226, 35, 26, 0.5); }
      }
      @keyframes robloxShimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
      }
      @keyframes robloxFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
      }
    `;
    document.head.appendChild(style);
  }
};

// Initialize animations
injectRobloxAnimations();
// Enhanced Card with Roblox styling - Pure Mantine
export const RobloxCard: React.FC<any> = ({ children, ...props }) => (
  <Card
    {...props}
    style={{
      borderRadius: 'var(--mantine-radius-xl)',
      border: '2px solid var(--mantine-color-gray-3)',
      background: 'var(--mantine-color-white)',
      boxShadow: '0 4px 12px rgba(226, 35, 26, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1)',
      transition: 'all 300ms ease-in-out',
      position: 'relative',
      overflow: 'hidden',
      ...props.style
    }}
    styles={{
      root: {
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: `linear-gradient(135deg, ${ROBLOX_RED}, ${ROBLOX_RED_DARK})`,
          borderRadius: 'var(--mantine-radius-xl) var(--mantine-radius-xl) 0 0'
        },
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
          borderColor: `${ROBLOX_RED}80`
        }
      }
    }}
  >
    {children}
  </Card>
);

// Gaming-style button - Pure Mantine
export const RobloxButton: React.FC<any> = ({ children, ...props }) => (
  <Button
    {...props}
    variant="filled"
    color={ROBLOX_RED}
    style={{
      borderRadius: 'var(--mantine-radius-md)',
      fontWeight: 700,
      fontSize: 'var(--mantine-font-size-sm)',
      textTransform: 'none',
      position: 'relative',
      overflow: 'hidden',
      transition: 'all 300ms ease-in-out',
      ...props.style
    }}
    styles={{
      root: {
        '&:hover': {
          transform: 'translateY(-2px) scale(1.02)',
          boxShadow: `0 8px 25px ${ROBLOX_RED}66`
        }
      }
    }}
  >
    {children}
  </Button>
);

// Gamification chip - Pure Mantine
export const RobloxChip: React.FC<any> = ({ children, achievement = 'common', ...props }) => {
  const colorMap = {
    common: '#6B7280',
    uncommon: '#10B981',
    rare: '#3B82F6',
    epic: '#8B5CF6',
    legendary: '#F59E0B'
  };
  const color = colorMap[achievement] || colorMap.common;

  return (
    <Badge
      {...props}
      variant="filled"
      style={{
        background: `linear-gradient(135deg, ${color}, ${color}CC)`,
        color: ROBLOX_WHITE,
        border: `1px solid ${color}4D`,
        borderRadius: 'var(--mantine-radius-md)',
        transition: 'all 300ms ease-in-out',
        ...props.style
      }}
      styles={{
        root: {
          '&:hover': {
            transform: 'scale(1.05)',
            boxShadow: `0 4px 15px ${color}80`,
            animation: 'robloxGlow 1s ease-in-out'
          }
        }
      }}
    >
      {children}
    </Badge>
  );
};

// XP Progress bar - Pure Mantine
export const XPProgressBar: React.FC<any> = ({ level = 1, ...props }) => (
  <Progress
    {...props}
    radius="xl"
    size="md"
    color={ROBLOX_RED}
    style={{
      backgroundColor: `${ROBLOX_GRAY}26`,
      position: 'relative',
      ...props.style
    }}
    styles={{
      bar: {
        background: `linear-gradient(90deg, ${ROBLOX_RED_DARK}, ${ROBLOX_RED})`,
        position: 'relative',
        overflow: 'hidden',
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `linear-gradient(90deg, transparent, ${ROBLOX_WHITE}4D, transparent)`,
          backgroundSize: '200% 100%',
          animation: 'robloxShimmer 2s infinite'
        }
      }
    }}
  />
);

// Floating action button with game-like effects - Pure Mantine
export const RobloxFAB: React.FC<any> = ({ children, ...props }) => (
  <ActionIcon
    {...props}
    size="xl"
    radius="xl"
    variant="filled"
    color={ROBLOX_RED}
    style={{
      background: `linear-gradient(135deg, ${ROBLOX_RED_DARK}, ${ROBLOX_RED})`,
      boxShadow: `0 4px 20px ${ROBLOX_RED}4D`,
      transition: 'all 300ms ease-in-out',
      ...props.style
    }}
    styles={{
      root: {
        '&:hover': {
          transform: 'scale(1.1)',
          boxShadow: `0 8px 25px ${ROBLOX_RED}66`,
          animation: 'robloxFloat 2s ease-in-out infinite'
        }
      }
    }}
  >
    {children}
  </ActionIcon>
);

// Gaming avatar with level badge - Pure Mantine
export const RobloxAvatar: React.FC<any> = ({ level, isOnline, children, ...props }) => (
  <Box style={{ position: 'relative', display: 'inline-block' }}>
    <Avatar
      {...props}
      style={{
        border: `3px solid ${ROBLOX_RED}`,
        boxShadow: `0 0 0 2px ${ROBLOX_RED}33`,
        transition: 'all 300ms ease-in-out',
        ...props.style
      }}
    >
      {children}
    </Avatar>
    {level && (
      <Badge
        size="sm"
        variant="filled"
        color={ROBLOX_RED}
        style={{
          position: 'absolute',
          bottom: -4,
          right: -4,
          zIndex: 1,
          minWidth: 20,
          height: 20,
          borderRadius: '50%',
          border: '2px solid var(--mantine-color-white)',
          boxShadow: `0 0 10px ${ROBLOX_RED}80`,
          animation: 'robloxPulse 3s infinite'
        }}
      >
        {level}
      </Badge>
    )}
    {isOnline && (
      <Box
        style={{
          position: 'absolute',
          top: 2,
          right: 2,
          width: 12,
          height: 12,
          backgroundColor: '#10B981',
          borderRadius: '50%',
          border: '2px solid var(--mantine-color-white)',
          boxShadow: '0 0 0 2px #10B98133'
        }}
      />
    )}
  </Box>
);

// Achievement badge - Pure Mantine
export const AchievementBadge: React.FC<any> = ({ achievement = 'bronze', children, ...props }) => {
  const colors = {
    bronze: '#CD7F32',
    silver: '#C0C0C0',
    gold: '#FFD700',
    diamond: '#B9F2FF'
  };
  const color = colors[achievement] || colors.bronze;

  return (
    <Badge
      {...props}
      variant="filled"
      style={{
        background: `linear-gradient(135deg, ${color}, ${color}CC)`,
        position: 'relative',
        overflow: 'hidden',
        ...props.style
      }}
      styles={{
        root: {
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            borderRadius: '50%',
            border: '2px solid var(--mantine-color-white)',
            boxShadow: `0 0 10px ${color}80`,
            animation: 'robloxPulse 3s infinite'
          }
        }
      }}
    >
      {children}
    </Badge>
  );
};

// Notification card with Roblox styling - Pure Mantine
export const RobloxNotificationCard: React.FC<any> = ({ severity = 'info', children, ...props }) => {
  const colors = {
    info: '#3B82F6',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444'
  };
  const color = colors[severity];

  return (
    <RobloxCard
      {...props}
      style={{
        backgroundColor: `${color}1A`,
        borderColor: `${color}4D`,
        ...props.style
      }}
      styles={{
        root: {
          '&::before': {
            background: color
          }
        }
      }}
    >
      {children}
    </RobloxCard>
  );
};

// Loading skeleton with Roblox theme - Pure Mantine
export const RobloxSkeleton: React.FC<any> = ({ width = '100%', height = 20, ...props }) => (
  <Box
    {...props}
    style={{
      width,
      height,
      borderRadius: 'var(--mantine-radius-md)',
      background: `linear-gradient(90deg, ${ROBLOX_GRAY}33 25%, ${ROBLOX_GRAY}4D 50%, ${ROBLOX_GRAY}33 75%)`,
      backgroundSize: '200% 100%',
      animation: 'robloxShimmer 1.5s infinite',
      ...props.style
    }}
  />
);

// Gamified container - Pure Mantine
export const GameContainer: React.FC<any> = ({ children, ...props }) => (
  <Box
    {...props}
    style={{
      background: `radial-gradient(circle at 20% 80%, ${ROBLOX_RED}1A 0%, transparent 50%), radial-gradient(circle at 80% 20%, #8B5CF61A 0%, transparent 50%)`,
      borderRadius: 'var(--mantine-radius-xl)',
      padding: 'var(--mantine-spacing-xl)',
      position: 'relative',
      overflow: 'hidden',
      ...props.style
    }}
    styles={{
      root: {
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `conic-gradient(from 0deg, transparent, ${ROBLOX_RED}1A, transparent)`,
          animation: 'robloxFloat 10s linear infinite',
          pointerEvents: 'none'
        }
      }
    }}
  >
    {children}
  </Box>
);
export default {
  RobloxCard,
  RobloxButton,
  RobloxChip,
  XPProgressBar,
  RobloxFAB,
  RobloxAvatar,
  AchievementBadge,
  RobloxNotificationCard,
  RobloxSkeleton,
  GameContainer
};