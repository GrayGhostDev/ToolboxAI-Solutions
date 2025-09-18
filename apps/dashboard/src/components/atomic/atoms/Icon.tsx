/**
 * Atomic Icon Component
 *
 * A versatile icon component supporting Material Icons, custom SVGs,
 * and Roblox-themed styling with proper accessibility.
 */

import React, { forwardRef } from 'react';
import { SvgIcon, SvgIconProps, styled } from '@mui/material';
import { designTokens } from '../../../theme/designTokens';

export interface IconProps extends Omit<SvgIconProps, 'color'> {
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

const StyledIcon = styled(SvgIcon)<IconProps>(({
  theme,
  size = 'md',
  color = 'inherit',
  spin = false,
  pulse = false,
  bounce = false,
  robloxTheme = true
}) => {
  // Get color value
  const getColor = () => {
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
      case 'disabled':
        return theme.palette.action.disabled;
      case 'inherit':
        return 'inherit';
      default:
        // Custom color
        return color;
    }
  };

  const baseStyles = {
    fontSize: sizeMap[size],
    color: getColor(),
    transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`
  };

  // Animation styles
  const animationStyles: any = {};

  if (spin) {
    animationStyles['@keyframes spin'] = {
      '0%': { transform: 'rotate(0deg)' },
      '100%': { transform: 'rotate(360deg)' }
    };
    animationStyles.animation = 'spin 1s linear infinite';
  }

  if (pulse) {
    animationStyles['@keyframes pulse'] = {
      '0%, 100%': { opacity: 1 },
      '50%': { opacity: 0.5 }
    };
    animationStyles.animation = 'pulse 2s ease-in-out infinite';
  }

  if (bounce) {
    animationStyles['@keyframes bounce'] = {
      '0%, 20%, 53%, 80%, 100%': { transform: 'translateY(0)' },
      '40%, 43%': { transform: 'translateY(-8px)' },
      '70%': { transform: 'translateY(-4px)' },
      '90%': { transform: 'translateY(-2px)' }
    };
    animationStyles.animation = 'bounce 1s ease-in-out infinite';
  }

  return {
    ...baseStyles,
    ...animationStyles
  };
});

const AtomicIcon = forwardRef<SVGSVGElement, IconProps>(
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
      ...props
    },
    ref
  ) => {
    // If children are provided, render as custom icon
    if (children) {
      return (
        <StyledIcon
          ref={ref}
          size={size}
          color={color}
          spin={spin}
          pulse={pulse}
          bounce={bounce}
          robloxTheme={robloxTheme}
          {...props}
        >
          {children}
        </StyledIcon>
      );
    }

    // For named Material Icons, we would typically import them
    // This is a simplified version - in a real implementation,
    // you would have a mapping of icon names to components
    if (name) {
      // Placeholder for named icons
      // In practice, you would import and use actual Material Icon components
      return (
        <StyledIcon
          ref={ref}
          size={size}
          color={color}
          spin={spin}
          pulse={pulse}
          bounce={bounce}
          robloxTheme={robloxTheme}
          {...props}
        >
          {/* This would be replaced with actual icon component */}
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </StyledIcon>
      );
    }

    // Default fallback icon
    return (
      <StyledIcon
        ref={ref}
        size={size}
        color={color}
        spin={spin}
        pulse={pulse}
        bounce={bounce}
        robloxTheme={robloxTheme}
        {...props}
      >
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
      </StyledIcon>
    );
  }
);

AtomicIcon.displayName = 'AtomicIcon';

export type { IconProps };
export default AtomicIcon;