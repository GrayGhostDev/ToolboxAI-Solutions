/**
 * Atomic Avatar Component
 *
 * Avatar component with Roblox gaming features like level badges and online status.
 */

import React, { forwardRef } from 'react';
import { Avatar as MuiAvatar } from '@mui/material';
import { AvatarProps as MuiAvatarProps } from '@mui/material';
import { styled } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import { designTokens } from '../../../theme/designTokens';

export interface AvatarProps extends MuiAvatarProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  level?: number;
  isOnline?: boolean;
  status?: 'online' | 'offline' | 'away' | 'busy';
  border?: boolean;
  robloxTheme?: boolean;
}

const sizeMap = {
  xs: { size: 24, levelSize: 16, statusSize: 6 },
  sm: { size: 32, levelSize: 20, statusSize: 8 },
  md: { size: 40, levelSize: 24, statusSize: 10 },
  lg: { size: 48, levelSize: 28, statusSize: 12 },
  xl: { size: 64, levelSize: 32, statusSize: 16 },
  '2xl': { size: 80, levelSize: 40, statusSize: 20 }
};

const statusColors = {
  online: '#22C55E',
  offline: '#6B7280',
  away: '#F59E0B',
  busy: '#EF4444'
};

const StyledAvatarContainer = styled('div')<AvatarProps>(({
  theme,
  size = 'md',
  level,
  isOnline,
  status = 'online',
  border = true,
  robloxTheme = true
}) => {
  const { size: avatarSize, levelSize, statusSize } = sizeMap[size];
  const robloxRed = '#E2231A';

  return {
    position: 'relative',
    display: 'inline-block',

    '& .MuiAvatar-root': {
      width: avatarSize,
      height: avatarSize,
      ...(border && {
        border: `3px solid ${robloxTheme ? robloxRed : theme.palette.primary.main}`,
        boxShadow: robloxTheme
          ? `0 0 0 2px ${alpha(robloxRed, 0.2)}`
          : `0 0 0 2px ${alpha(theme.palette.primary.main, 0.2)}`
      }),
      transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,

      '&:hover': {
        transform: 'scale(1.05)'
      }
    },

    // Online status indicator
    ...((isOnline || status) && {
      '&::after': {
        content: '""',
        position: 'absolute',
        bottom: size === 'xs' ? -2 : size === 'sm' ? -2 : 0,
        right: size === 'xs' ? -2 : size === 'sm' ? -2 : 0,
        width: statusSize,
        height: statusSize,
        backgroundColor: statusColors[status],
        borderRadius: '50%',
        border: `2px solid ${theme.palette.background.paper}`,
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        ...(status === 'online' && {
          animation: 'pulse 2s infinite'
        })
      }
    }),

    // Level badge
    ...(level && {
      '&::before': {
        content: `"${level}"`,
        position: 'absolute',
        top: size === 'xs' ? -6 : size === 'sm' ? -8 : -8,
        left: size === 'xs' ? -6 : size === 'sm' ? -8 : -8,
        width: levelSize,
        height: levelSize,
        backgroundColor: '#F59E0B',
        color: '#FFFFFF',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size === 'xs' ? '8px' : size === 'sm' ? '10px' : '12px',
        fontWeight: 'bold',
        border: `2px solid ${theme.palette.background.paper}`,
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        zIndex: 1
      }
    }),

    // Animation keyframes
    '@keyframes pulse': {
      '0%, 100%': {
        opacity: 1
      },
      '50%': {
        opacity: 0.5
      }
    }
  };
});

const AtomicAvatar = forwardRef<HTMLDivElement, AvatarProps>(
  (
    {
      children,
      size = 'md',
      level,
      isOnline,
      status = isOnline ? 'online' : 'offline',
      border = true,
      robloxTheme = true,
      src,
      alt,
      ...props
    },
    ref
  ) => {
    return (
      <StyledAvatarContainer
        ref={ref}
        size={size}
        level={level}
        isOnline={isOnline}
        status={status}
        border={border}
        robloxTheme={robloxTheme}
      >
        <MuiAvatar
          src={src}
          alt={alt}
          {...props}
        >
          {children}
        </MuiAvatar>
      </StyledAvatarContainer>
    );
  }
);

AtomicAvatar.displayName = 'AtomicAvatar';

export default AtomicAvatar;