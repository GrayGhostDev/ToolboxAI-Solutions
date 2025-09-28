/**
 * Atomic Avatar Component
 *
 * Avatar component with Roblox gaming features like level badges and online status.
 * Uses Mantine's Avatar and Indicator components.
 */

import React, { forwardRef } from 'react';
import { Avatar as MantineAvatar, AvatarProps as MantineAvatarProps, Indicator, Box } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

export interface AtomicAvatarProps extends Omit<MantineAvatarProps, 'size'> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  level?: number;
  isOnline?: boolean;
  status?: 'online' | 'offline' | 'away' | 'busy';
  border?: boolean;
  robloxTheme?: boolean;
  name?: string;
  initials?: string;
}

const sizeMap = {
  xs: { size: 24, levelSize: 16, statusSize: 8, fontSize: '8px' },
  sm: { size: 32, levelSize: 20, statusSize: 10, fontSize: '10px' },
  md: { size: 40, levelSize: 24, statusSize: 12, fontSize: '12px' },
  lg: { size: 48, levelSize: 28, statusSize: 14, fontSize: '14px' },
  xl: { size: 64, levelSize: 32, statusSize: 16, fontSize: '16px' }
};

const statusColorMap = {
  online: 'green',
  offline: 'gray',
  away: 'yellow',
  busy: 'red'
};

const AtomicAvatar = forwardRef<HTMLDivElement, AtomicAvatarProps>(
  (
    {
      children,
      size = 'md',
      level,
      isOnline,
      status = isOnline ? 'online' : undefined,
      border = true,
      robloxTheme = true,
      src,
      alt,
      name,
      initials,
      color,
      ...props
    },
    ref
  ) => {
    const { size: avatarSize, levelSize, statusSize, fontSize } = sizeMap[size];

    // Get initials from name if not provided
    const getInitials = () => {
      if (initials) return initials;
      if (name) {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
      }
      return children as string;
    };

    // Build avatar styles
    const avatarStyles: React.CSSProperties = {
      width: avatarSize,
      height: avatarSize,
      fontSize: fontSize,
      transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
      cursor: 'pointer',
      ...(border && robloxTheme && {
        border: '3px solid var(--mantine-color-roblox-red-6)',
        boxShadow: '0 0 0 2px rgba(226, 35, 26, 0.2)'
      })
    };

    // Animation styles for status
    const animationStyles = status === 'online' ? (
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes statusPulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .status-online {
          animation: statusPulse 2s infinite;
        }
      ` }} />
    ) : null;

    // Build the avatar component
    const avatarComponent = (
      <MantineAvatar
        ref={ref}
        src={src}
        alt={alt || name}
        color={robloxTheme ? 'roblox-cyan' : color}
        style={avatarStyles}
        {...props}
      >
        {!src && getInitials()}
      </MantineAvatar>
    );

    // Wrap with status indicator if needed
    let wrappedAvatar = avatarComponent;
    if (status) {
      wrappedAvatar = (
        <>
          {animationStyles}
          <Indicator
            position="bottom-end"
            offset={2}
            size={statusSize}
            color={statusColorMap[status]}
            withBorder
            processing={status === 'online'}
            className={status === 'online' ? 'status-online' : undefined}
            styles={{
              indicator: {
                border: '2px solid var(--mantine-color-white)',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
              }
            }}
          >
            {avatarComponent}
          </Indicator>
        </>
      );
    }

    // Wrap with level badge if needed
    if (level) {
      return (
        <Box
          style={{
            position: 'relative',
            display: 'inline-block',
            '&:hover .mantine-Avatar-root': {
              transform: 'scale(1.05)'
            }
          }}
        >
          {wrappedAvatar}
          <Box
            component="span"
            style={{
              position: 'absolute',
              top: -8,
              left: -8,
              width: levelSize,
              height: levelSize,
              backgroundColor: 'var(--mantine-color-yellow-6)',
              color: 'white',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: fontSize,
              fontWeight: 'bold',
              border: '2px solid var(--mantine-color-white)',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
              zIndex: 1
            }}
          >
            {level}
          </Box>
        </Box>
      );
    }

    return wrappedAvatar;
  }
);

AtomicAvatar.displayName = 'AtomicAvatar';

export default AtomicAvatar;
export type { AtomicAvatarProps as AvatarProps };