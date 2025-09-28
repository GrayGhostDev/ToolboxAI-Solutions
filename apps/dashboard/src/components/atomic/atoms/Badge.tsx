/**
 * Atomic Badge Component
 *
 * A badge component with gaming elements, rarity levels, and notifications.
 * Uses Mantine's Badge and Indicator components for different use cases.
 */

import React, { forwardRef } from 'react';
import { Badge as MantineBadge, Indicator, BadgeProps as MantineBadgeProps, IndicatorProps } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

// Custom props for our Badge component
export interface AtomicBadgeProps {
  // Badge mode - standalone label or notification indicator
  mode?: 'label' | 'indicator';

  // Common properties
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'filled' | 'light' | 'outline' | 'dot' | 'achievement' | 'notification';
  rarity?: 'common' | 'rare' | 'epic' | 'legendary';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  pulse?: boolean;
  glow?: boolean;
  robloxTheme?: boolean;

  // For label mode
  label?: React.ReactNode;
  leftSection?: React.ReactNode;
  rightSection?: React.ReactNode;

  // For indicator mode
  children?: React.ReactNode;
  content?: React.ReactNode;
  position?: IndicatorProps['position'];
  offset?: number;
  inline?: boolean;
  withBorder?: boolean;
  disabled?: boolean;
  processing?: boolean;
}

const rarityColors = {
  common: 'teal',
  rare: 'blue',
  epic: 'violet',
  legendary: 'yellow'
};

const colorMap = {
  primary: 'roblox-red',
  secondary: 'gray',
  success: 'green',
  error: 'red',
  warning: 'orange',
  info: 'cyan'
};

const AtomicBadge = forwardRef<HTMLDivElement, AtomicBadgeProps>(
  (
    {
      mode = 'label',
      size = 'md',
      variant = 'filled',
      rarity,
      color = 'primary',
      pulse = false,
      glow = false,
      robloxTheme = true,
      label,
      leftSection,
      rightSection,
      children,
      content,
      position = 'top-end',
      offset = 7,
      inline = false,
      withBorder = true,
      disabled = false,
      processing = false,
      ...props
    },
    ref
  ) => {
    // Determine the color to use
    const getColor = () => {
      if (rarity) {
        return rarityColors[rarity];
      }
      if (robloxTheme && color) {
        return colorMap[color] || 'gray';
      }
      return color || 'gray';
    };

    const badgeColor = getColor();

    // Map custom variants to Mantine variants
    const getMantineVariant = () => {
      if (variant === 'achievement' || variant === 'notification') {
        return 'filled';
      }
      if (variant === 'dot') {
        return 'dot';
      }
      return variant as 'filled' | 'light' | 'outline' | 'dot';
    };

    // Create animation styles
    const animationStyles = (pulse || glow || variant === 'achievement' || variant === 'notification') ? (
      <style dangerouslySetInnerHTML={{ __html: `
        ${pulse ? `
        @keyframes badgePulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.1); }
        }
        .badge-pulse {
          animation: badgePulse 2s ease-in-out infinite;
        }` : ''}

        ${variant === 'achievement' ? `
        @keyframes achievementPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          25% { opacity: 0.9; transform: scale(1.05); }
          50% { opacity: 0.8; transform: scale(1.1); }
          75% { opacity: 0.9; transform: scale(1.05); }
        }
        .badge-achievement {
          animation: achievementPulse 3s ease-in-out infinite;
          background: linear-gradient(135deg, var(--mantine-color-${badgeColor}-6), var(--mantine-color-${badgeColor}-8));
        }` : ''}

        ${variant === 'notification' ? `
        @keyframes notificationPulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        .badge-notification {
          animation: notificationPulse 1.5s ease-in-out infinite;
          background-color: var(--mantine-color-red-6);
        }` : ''}

        ${glow ? `
        .badge-glow {
          box-shadow: 0 0 10px rgba(226, 35, 26, 0.5), 0 0 20px rgba(226, 35, 26, 0.3);
        }` : ''}
      ` }} />
    ) : null;

    // Build class names
    const getClassName = () => {
      const classes = [];
      if (pulse) classes.push('badge-pulse');
      if (variant === 'achievement') classes.push('badge-achievement');
      if (variant === 'notification') classes.push('badge-notification');
      if (glow) classes.push('badge-glow');
      return classes.join(' ');
    };

    // Build styles
    const customStyles: React.CSSProperties = {};

    // Add gradient for achievement variant
    if (variant === 'achievement' && robloxTheme) {
      customStyles.background = `linear-gradient(135deg, var(--mantine-color-${badgeColor}-6), var(--mantine-color-${badgeColor}-8))`;
      customStyles.border = withBorder ? '2px solid var(--mantine-color-white)' : undefined;
      customStyles.boxShadow = `0 2px 8px rgba(0, 0, 0, 0.15)`;
    }

    // Add notification styles
    if (variant === 'notification') {
      customStyles.backgroundColor = 'var(--mantine-color-red-6)';
      customStyles.color = 'white';
    }

    // Render as label (standalone badge)
    if (mode === 'label') {
      return (
        <>
          {animationStyles}
          <MantineBadge
            ref={ref as any}
            size={size}
            variant={getMantineVariant()}
            color={badgeColor}
            leftSection={leftSection}
            rightSection={rightSection}
            className={getClassName()}
            styles={{
              root: {
                ...customStyles,
                transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
                fontWeight: designTokens.typography.fontWeight.bold
              }
            }}
            {...props as MantineBadgeProps}
          >
            {label || children}
          </MantineBadge>
        </>
      );
    }

    // Render as indicator (notification badge on another element)
    return (
      <>
        {animationStyles}
        <Indicator
          inline={inline}
          label={content}
          size={size === 'xs' ? 8 : size === 'sm' ? 10 : size === 'md' ? 12 : size === 'lg' ? 14 : 16}
          position={position}
          offset={offset}
          withBorder={withBorder}
          disabled={disabled}
          processing={processing}
          color={badgeColor}
          className={getClassName()}
          styles={{
            indicator: {
              ...customStyles,
              transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
              fontWeight: designTokens.typography.fontWeight.bold
            }
          }}
          {...props as Partial<IndicatorProps>}
        >
          {children}
        </Indicator>
      </>
    );
  }
);

AtomicBadge.displayName = 'AtomicBadge';

export default AtomicBadge;
export type { AtomicBadgeProps as BadgeProps };