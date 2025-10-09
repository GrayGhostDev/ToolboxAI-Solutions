/**
 * Atomic Icon Component
 *
 * A versatile icon component supporting Tabler Icons, custom SVGs,
 * and Roblox-themed styling with proper accessibility.
 */

import React, { forwardRef } from 'react';
import { Box, type BoxProps } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

export interface IconProps extends Omit<BoxProps, 'color'> {
  name?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'disabled' | 'inherit' | string;
  variant?: 'filled' | 'outlined' | 'rounded' | 'sharp';
  spin?: boolean;
  pulse?: boolean;
  bounce?: boolean;
  robloxTheme?: boolean;
}

// Icon size mapping
const sizeMap = {
  xs: '12px',
  sm: '16px',
  md: '20px',
  lg: '24px',
  xl: '32px',
  '2xl': '40px'
};

const AtomicIcon = forwardRef<HTMLDivElement, IconProps>(
  (
    {
      children,
      name,
      size = 'md',
      color = 'inherit',
      variant = 'filled',
      spin = false,
      pulse = false,
      bounce = false,
      robloxTheme = true,
      style,
      ...props
    },
    ref
  ) => {
    // Get color value
    const getColor = () => {
      switch (color) {
        case 'primary':
          return robloxTheme ? '#E2231A' : 'var(--mantine-color-blue-6)';
        case 'secondary':
          return 'var(--mantine-color-gray-6)';
        case 'success':
          return 'var(--mantine-color-green-6)';
        case 'error':
          return 'var(--mantine-color-red-6)';
        case 'warning':
          return 'var(--mantine-color-yellow-6)';
        case 'info':
          return 'var(--mantine-color-blue-6)';
        case 'disabled':
          return 'var(--mantine-color-gray-5)';
        case 'inherit':
          return 'inherit';
        default:
          // Custom color
          return color;
      }
    };

    // Generate animation keyframes CSS
    const getAnimationCSS = () => {
      let animationCSS = '';

      if (spin) {
        animationCSS += `
          @keyframes icon-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `;
      }

      if (pulse) {
        animationCSS += `
          @keyframes icon-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `;
      }

      if (bounce) {
        animationCSS += `
          @keyframes icon-bounce {
            0%, 20%, 53%, 80%, 100% { transform: translateY(0); }
            40%, 43% { transform: translateY(-8px); }
            70% { transform: translateY(-4px); }
            90% { transform: translateY(-2px); }
          }
        `;
      }

      return animationCSS;
    };

    const baseStyles: React.CSSProperties = {
      fontSize: sizeMap[size],
      color: getColor(),
      transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      ...(style as React.CSSProperties)
    };

    // Add animation styles
    if (spin) {
      baseStyles.animation = 'icon-spin 1s linear infinite';
    } else if (pulse) {
      baseStyles.animation = 'icon-pulse 2s ease-in-out infinite';
    } else if (bounce) {
      baseStyles.animation = 'icon-bounce 1s ease-in-out infinite';
    }

    // Render SVG with default icon if no children provided
    const renderIcon = () => {
      if (children) {
        return children;
      }

      // Default fallback icon (checkmark)
      return (
        <svg
          width={sizeMap[size]}
          height={sizeMap[size]}
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </svg>
      );
    };

    return (
      <>
        {/* Inject animation CSS */}
        {(spin || pulse || bounce) && (
          <style dangerouslySetInnerHTML={{ __html: getAnimationCSS() }} />
        )}

        <Box
          ref={ref}
          component="span"
          style={baseStyles}
          {...props}
        >
          {renderIcon()}
        </Box>
      </>
    );
  }
);

AtomicIcon.displayName = 'AtomicIcon';

export type { IconProps };
export default AtomicIcon;