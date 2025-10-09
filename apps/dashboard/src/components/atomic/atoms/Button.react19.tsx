/**
 * Atomic Button Component - React 19 Version
 *
 * Refactored to use React 19 features and Mantine:
 * - Direct ref prop support
 * - Using new Actions API for async operations
 * - Mantine Button as base component
 */

import React from 'react';
import { Button as MantineButton, Loader, useMantineTheme } from '@mantine/core';
import type { ButtonProps as MantineButtonProps } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';
import { useAction } from '../../../config/react19';

// Custom props for our Button component
export interface AtomicButtonProps {
  variant?: 'primary' | 'secondary' | 'outlined' | 'text' | 'ghost' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  loadingText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  robloxTheme?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  // React 19: Support async actions
  action?: (...args: any[]) => Promise<any>;
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
}

// Combine with Mantine button props and React 19 ref support
export type ButtonProps = AtomicButtonProps &
  Omit<MantineButtonProps, keyof AtomicButtonProps | 'variant' | 'size'> & {
    ref?: React.Ref<HTMLButtonElement>;
  };

// Roblox brand colors
const ROBLOX_RED = '#E2231A';
const ROBLOX_RED_DARK = '#B71C15';
const ROBLOX_WHITE = '#FFFFFF';

// Variant mapping for Mantine
const getMantineVariant = (variant?: string) => {
  switch (variant) {
    case 'primary':
      return 'filled';
    case 'secondary':
      return 'light';
    case 'outlined':
      return 'outline';
    case 'text':
    case 'ghost':
      return 'subtle';
    case 'danger':
      return 'filled';
    default:
      return 'filled';
  }
};

// Size mapping for Mantine
const getMantineSize = (size?: string) => {
  switch (size) {
    case 'xs':
      return 'xs';
    case 'sm':
      return 'sm';
    case 'md':
      return 'md';
    case 'lg':
      return 'lg';
    case 'xl':
      return 'xl';
    default:
      return 'md';
  }
};

// Color mapping for Mantine
const getMantineColor = (variant?: string, robloxTheme?: boolean) => {
  if (!robloxTheme) {
    return 'blue';
  }

  switch (variant) {
    case 'danger':
      return 'red';
    case 'secondary':
      return 'gray';
    default:
      return 'red'; // Roblox red
  }
};

/**
 * React 19 Button Component using Mantine
 * Direct ref prop support
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  loadingText,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  robloxTheme = true,
  disabled,
  onClick,
  action,
  onSuccess,
  onError,
  ref,
  ...props
}: ButtonProps) => {
  const theme = useMantineTheme();

  // React 19: Use the Actions API for async operations
  const actionHandler = action ? useAction(action, onSuccess, onError) : null;

  const handleClick = React.useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
    if (actionHandler) {
      // Use the new Actions API
      actionHandler.execute();
    } else if (onClick) {
      onClick(event);
    }
  }, [actionHandler, onClick]);

  const isLoading = loading || (actionHandler?.isPending ?? false);
  const isDisabled = disabled || isLoading;

  // Map our custom props to Mantine props
  const mantineVariant = getMantineVariant(variant);
  const mantineSize = getMantineSize(size);
  const mantineColor = getMantineColor(variant, robloxTheme);

  // Custom styles for Roblox theme
  const customStyles = robloxTheme ? {
    root: {
      backgroundColor: variant === 'primary' ? ROBLOX_RED : undefined,
      '&:hover': {
        backgroundColor: variant === 'primary' ? ROBLOX_RED_DARK : undefined,
        transform: 'translateY(-1px)',
      },
      '&:active': {
        transform: 'translateY(0)',
      },
    }
  } : undefined;

  return (
    <MantineButton
      ref={ref}
      variant={mantineVariant}
      size={mantineSize}
      color={mantineColor}
      fullWidth={fullWidth}
      loading={isLoading}
      disabled={isDisabled}
      onClick={handleClick}
      leftSection={icon && iconPosition === 'left' ? icon : undefined}
      rightSection={icon && iconPosition === 'right' ? icon : undefined}
      styles={customStyles}
      {...props}
    >
      {isLoading && loadingText ? loadingText : children}
    </MantineButton>
  );
};

// Export for convenience
export default Button;