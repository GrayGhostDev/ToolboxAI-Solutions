/**
 * Atomic Badge Component
 *
 * A badge component with gaming elements, rarity levels, and notifications.
 */

import React, { forwardRef } from 'react';
import { Badge as MuiBadge, BadgeProps as MuiBadgeProps, styled, alpha } from '@mui/material';
import { designTokens } from '../../../theme/designTokens';

// Custom props for our Badge component
export interface AtomicBadgeProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'standard' | 'dot' | 'achievement' | 'notification';
  rarity?: 'common' | 'rare' | 'epic' | 'legendary';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  pulse?: boolean;
  glow?: boolean;
  robloxTheme?: boolean;
  children?: React.ReactNode;
}

// Combine with MUI badge props, excluding conflicting ones
export type BadgeProps = AtomicBadgeProps & Omit<MuiBadgeProps, keyof AtomicBadgeProps | 'color' | 'variant'>;

const rarityColors = {
  common: '#10B981',
  rare: '#3B82F6',
  epic: '#8B5CF6',
  legendary: '#F59E0B'
};

const StyledBadge = styled(MuiBadge)<AtomicBadgeProps>(({
  theme,
  size = 'md',
  variant = 'standard',
  rarity,
  color = 'primary',
  pulse = false,
  glow = false,
  robloxTheme = true
}) => {
  const sizeMap = {
    sm: { minWidth: 16, height: 16, fontSize: '10px' },
    md: { minWidth: 20, height: 20, fontSize: '12px' },
    lg: { minWidth: 24, height: 24, fontSize: '14px' }
  };

  const currentSize = sizeMap[size];

  const getColor = () => {
    if (rarity) {
      return rarityColors[rarity];
    }

    switch (color) {
      case 'primary':
        return robloxTheme ? '#E2231A' : theme.palette.primary.main;
      case 'secondary':
        return theme.palette.secondary.main;
      case 'success':
        return theme.palette.success.main;
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'info':
        return theme.palette.info.main;
      default:
        return theme.palette.primary.main;
    }
  };

  const badgeColor = getColor();

  const baseStyles = {
    '& .MuiBadge-badge': {
      minWidth: currentSize.minWidth,
      height: currentSize.height,
      fontSize: currentSize.fontSize,
      fontWeight: designTokens.typography.fontWeight.bold,
      padding: variant === 'dot' ? 0 : '0 6px',
      borderRadius: variant === 'dot' ? '50%' : designTokens.borderRadius.full,
      backgroundColor: badgeColor,
      color: '#FFFFFF',
      border: `2px solid ${theme.palette.background.paper}`,
      transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,

      ...(glow && {
        boxShadow: `0 0 10px ${alpha(badgeColor, 0.5)}, 0 0 20px ${alpha(badgeColor, 0.3)}`
      }),

      ...(pulse && {
        animation: 'badgePulse 2s ease-in-out infinite'
      })
    },

    '@keyframes badgePulse': {
      '0%, 100%': {
        opacity: 1,
        transform: 'scale(1)'
      },
      '50%': {
        opacity: 0.8,
        transform: 'scale(1.1)'
      }
    }
  };

  if (variant === 'achievement') {
    return {
      ...baseStyles,
      '& .MuiBadge-badge': {
        ...baseStyles['& .MuiBadge-badge'],
        background: `linear-gradient(135deg, ${badgeColor}, ${alpha(badgeColor, 0.8)})`,
        boxShadow: `0 2px 8px ${alpha(badgeColor, 0.3)}, 0 0 0 2px ${theme.palette.background.paper}`,
        animation: pulse ? 'achievementPulse 3s ease-in-out infinite' : undefined
      },

      '@keyframes achievementPulse': {
        '0%, 100%': {
          opacity: 1,
          transform: 'scale(1)'
        },
        '25%': {
          opacity: 0.9,
          transform: 'scale(1.05)'
        },
        '50%': {
          opacity: 0.8,
          transform: 'scale(1.1)'
        },
        '75%': {
          opacity: 0.9,
          transform: 'scale(1.05)'
        }
      }
    };
  }

  if (variant === 'notification') {
    return {
      ...baseStyles,
      '& .MuiBadge-badge': {
        ...baseStyles['& .MuiBadge-badge'],
        background: '#EF4444',
        animation: 'notificationPulse 1.5s ease-in-out infinite'
      },

      '@keyframes notificationPulse': {
        '0%, 100%': {
          opacity: 1
        },
        '50%': {
          opacity: 0.7
        }
      }
    };
  }

  return baseStyles;
});

const AtomicBadge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      children,
      size = 'md',
      variant = 'standard',
      rarity,
      color = 'primary',
      pulse = false,
      glow = false,
      robloxTheme = true,
      ...props
    },
    ref
  ) => {
    return (
      <StyledBadge
        ref={ref}
        size={size}
        variant={(variant === 'achievement' || variant === 'notification') ? 'standard' : variant}
        rarity={rarity}
        color={color}
        pulse={pulse}
        glow={glow}
        robloxTheme={robloxTheme}
        {...props as any}
      >
        {children}
      </StyledBadge>
    );
  }
);

AtomicBadge.displayName = 'AtomicBadge';

export default AtomicBadge;
export type { BadgeProps };