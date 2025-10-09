/**
 * Atomic Input Component
 *
 * A versatile input component with Roblox theming, validation states,
 * and proper accessibility features.
 */

import React, { forwardRef } from 'react';
import { TextInput, type TextInputProps, ActionIcon, Box } from '@mantine/core';
import { IconEye, IconEyeOff, IconX } from '@tabler/icons-react';
import { designTokens } from '../../../theme/designTokens';

export interface InputProps extends Omit<TextInputProps, 'variant' | 'size'> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'unstyled' | 'roblox';
  state?: 'default' | 'error' | 'warning' | 'success';
  clearable?: boolean;
  onClear?: () => void;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  robloxTheme?: boolean;
}

// Roblox brand colors
const ROBLOX_RED = '#E2231A';
const ROBLOX_RED_DARK = '#B71C15';

// Size configurations
const sizeMap = {
  sm: {
    height: '32px',
    fontSize: designTokens.typography.fontSize.sm[0],
    padding: `${designTokens.spacing[1]} ${designTokens.spacing[2]}`
  },
  md: {
    height: '40px',
    fontSize: designTokens.typography.fontSize.sm[0],
    padding: `${designTokens.spacing[2]} ${designTokens.spacing[3]}`
  },
  lg: {
    height: '48px',
    fontSize: designTokens.typography.fontSize.base[0],
    padding: `${designTokens.spacing[2.5]} ${designTokens.spacing[4]}`
  }
};

const AtomicInput = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      size = 'md',
      variant = 'default',
      state = 'default',
      clearable = false,
      onClear,
      leftIcon,
      rightIcon,
      type: initialType = 'text',
      robloxTheme = true,
      value,
      onChange,
      ...props
    },
    ref
  ) => {
    const [type, setType] = React.useState(initialType);
    const [showPassword, setShowPassword] = React.useState(false);

    const isPassword = initialType === 'password';
    const hasValue = Boolean(value && String(value).length > 0);

    const handleTogglePassword = () => {
      setShowPassword(!showPassword);
      setType(showPassword ? 'password' : 'text');
    };

    const handleClear = () => {
      if (onClear) {
        onClear();
      } else if (onChange) {
        onChange({
          target: { value: '' }
        } as React.ChangeEvent<HTMLInputElement>);
      }
    };

    // Build right section with controls
    const getRightSection = () => {
      const controls = [];

      // Clear button
      if (clearable && hasValue) {
        controls.push(
          <ActionIcon
            key="clear"
            variant="transparent"
            color="gray"
            size="sm"
            aria-label="clear input"
            onClick={handleClear}
          >
            <IconX size={16} />
          </ActionIcon>
        );
      }

      // Password visibility toggle
      if (isPassword) {
        controls.push(
          <ActionIcon
            key="password-toggle"
            variant="transparent"
            color="gray"
            size="sm"
            aria-label="toggle password visibility"
            onClick={handleTogglePassword}
          >
            {showPassword ? <IconEyeOff size={16} /> : <IconEye size={16} />}
          </ActionIcon>
        );
      }

      // Custom right icon (if no other controls)
      if (rightIcon && !isPassword && !clearable) {
        controls.push(
          <Box key="right-icon" component="span">
            {rightIcon}
          </Box>
        );
      }

      return controls.length > 0 ? (
        <Box style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          {controls}
        </Box>
      ) : undefined;
    };

    // Get Mantine size
    const getMantineSize = () => {
      switch (size) {
        case 'sm': return 'sm';
        case 'lg': return 'lg';
        default: return 'md';
      }
    };

    // Get error state
    const error = state === 'error';

    // Custom styles for Roblox theme
    const getStyles = () => {
      const currentSize = sizeMap[size];

      if (variant === 'roblox' && robloxTheme) {
        return {
          input: {
            fontSize: currentSize.fontSize,
            minHeight: currentSize.height,
            borderRadius: designTokens.borderRadius.xl,
            border: '2px solid var(--mantine-color-gray-4)',
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
            transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,

            '&:hover': {
              borderColor: `${ROBLOX_RED}80`,
              boxShadow: `0 4px 12px ${ROBLOX_RED}1A`
            },

            '&:focus': {
              borderColor: ROBLOX_RED,
              boxShadow: `0 0 0 3px ${ROBLOX_RED}1A`,
              backgroundColor: 'white'
            },

            '&[data-invalid]': {
              borderColor: 'var(--mantine-color-red-6)',
              boxShadow: '0 0 0 3px var(--mantine-color-red-1)'
            }
          }
        };
      }

      return {
        input: {
          fontSize: currentSize.fontSize,
          minHeight: currentSize.height,
          borderRadius: designTokens.borderRadius.lg
        }
      };
    };

    return (
      <TextInput
        ref={ref}
        type={type}
        size={getMantineSize()}
        variant={variant === 'roblox' ? 'default' : variant}
        error={error}
        value={value}
        onChange={onChange}
        leftSection={leftIcon}
        rightSection={getRightSection()}
        styles={getStyles()}
        {...props}
      />
    );
  }
);

AtomicInput.displayName = 'AtomicInput';

export type { InputProps };
export default AtomicInput;