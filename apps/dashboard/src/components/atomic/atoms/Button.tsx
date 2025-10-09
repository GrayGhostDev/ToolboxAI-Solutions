/**
 * Atomic Button Component
 *
 * A polymorphic button component with Roblox theming, proper accessibility,
 * and support for different variants, sizes, and states using Mantine.
 */

import React, { forwardRef } from 'react';
import { Button as MantineButton, type ButtonProps as MantineButtonProps, Loader } from '@mantine/core';
import { IconType } from '@tabler/icons-react';

// Custom props for our Button component
export interface AtomicButtonProps extends Omit<MantineButtonProps, 'variant' | 'size'> {
  variant?: 'primary' | 'secondary' | 'outlined' | 'text' | 'ghost' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  loadingText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  robloxTheme?: boolean;
}

// Map our custom variants to Mantine variants
const variantMap = {
  primary: 'filled',
  secondary: 'light',
  outlined: 'outline',
  text: 'subtle',
  ghost: 'transparent',
  danger: 'filled'
} as const;

// Map our custom colors based on variant
const colorMap = {
  primary: 'roblox-red',
  secondary: 'gray',
  outlined: 'roblox-red',
  text: 'roblox-red',
  ghost: 'gray',
  danger: 'red'
} as const;

const AtomicButton = forwardRef<HTMLButtonElement, AtomicButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      loading = false,
      loadingText,
      icon,
      iconPosition = 'left',
      disabled,
      robloxTheme = true,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    const mantineVariant = variantMap[variant] || 'filled';
    const mantineColor = robloxTheme ? (colorMap[variant] || 'roblox-cyan') : undefined;

    // Handle loading state
    const leftSection = loading && iconPosition === 'left' ? (
      <Loader size={16} />
    ) : iconPosition === 'left' ? icon : undefined;

    const rightSection = loading && iconPosition === 'right' ? (
      <Loader size={16} />
    ) : iconPosition === 'right' ? icon : undefined;

    return (
      <MantineButton
        ref={ref}
        variant={mantineVariant}
        color={mantineColor}
        size={size}
        disabled={isDisabled}
        leftSection={leftSection}
        rightSection={rightSection}
        loading={loading && !loadingText}
        gradient={variant === 'primary' && robloxTheme ? { from: 'roblox-red.6', to: 'roblox-red.8', deg: 135 } : undefined}
        styles={{
          root: {
            transition: 'all 250ms ease',
            ...(variant === 'primary' && robloxTheme && {
              background: 'linear-gradient(135deg, #E2231A, #B71C15)',
              '&:hover': {
                background: 'linear-gradient(135deg, #B71C15, #E2231A)',
                transform: 'translateY(-2px)',
              },
              '&:active': {
                transform: 'translateY(0) scale(0.98)',
              },
            }),
            ...(variant === 'danger' && {
              background: 'linear-gradient(135deg, #EF4444, #DC2626)',
              '&:hover': {
                background: 'linear-gradient(135deg, #DC2626, #B91C1C)',
                transform: 'translateY(-2px)',
              },
            }),
          },
        }}
        {...props}
      >
        {loading && loadingText ? loadingText : children}
      </MantineButton>
    );
  }
);

AtomicButton.displayName = 'AtomicButton';

export default AtomicButton;
export type { AtomicButtonProps as ButtonProps };