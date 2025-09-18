/**
 * Atomic Input Component
 *
 * A versatile input component with Roblox theming, validation states,
 * and proper accessibility features.
 */

import React, { forwardRef } from 'react';
import {
  TextField,
  TextFieldProps,
  InputAdornment,
  IconButton,
  styled,
  alpha
} from '@mui/material';
import { Visibility, VisibilityOff, Clear } from '@mui/icons-material';
import { designTokens } from '../../../theme/designTokens';

export interface InputProps extends Omit<TextFieldProps, 'variant' | 'size'> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'outlined' | 'filled' | 'standard' | 'roblox';
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

const StyledTextField = styled(TextField)<InputProps>(({
  theme,
  size = 'md',
  variant = 'outlined',
  state = 'default',
  robloxTheme = true
}) => {
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

  // State color configurations
  const stateColors = {
    default: theme.palette.primary.main,
    error: theme.palette.error.main,
    warning: theme.palette.warning.main,
    success: theme.palette.success.main
  };

  const currentSize = sizeMap[size];
  const focusColor = robloxTheme ? ROBLOX_RED : stateColors[state];

  const baseStyles = {
    '& .MuiInputLabel-root': {
      fontSize: currentSize.fontSize,
      color: theme.palette.text.secondary,
      fontWeight: designTokens.typography.fontWeight.medium,

      '&.Mui-focused': {
        color: focusColor
      },

      '&.Mui-error': {
        color: theme.palette.error.main
      }
    },

    '& .MuiInputBase-root': {
      fontSize: currentSize.fontSize,
      minHeight: currentSize.height,
      borderRadius: designTokens.borderRadius.lg,
      transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,

      '& .MuiInputBase-input': {
        padding: currentSize.padding,
        '&::placeholder': {
          color: theme.palette.text.disabled,
          opacity: 1
        }
      }
    },

    '& .MuiFormHelperText-root': {
      fontSize: designTokens.typography.fontSize.xs[0],
      marginTop: designTokens.spacing[1],
      marginLeft: 0
    }
  };

  if (variant === 'roblox' && robloxTheme) {
    return {
      ...baseStyles,

      '& .MuiOutlinedInput-root': {
        backgroundColor: alpha(theme.palette.background.paper, 0.8),
        border: `2px solid ${theme.palette.divider}`,
        borderRadius: designTokens.borderRadius.xl,
        boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.05)}`,

        '&:hover:not(.Mui-disabled)': {
          borderColor: alpha(ROBLOX_RED, 0.5),
          boxShadow: `0 4px 12px ${alpha(ROBLOX_RED, 0.1)}`
        },

        '&.Mui-focused': {
          borderColor: ROBLOX_RED,
          boxShadow: `0 0 0 3px ${alpha(ROBLOX_RED, 0.1)}`,
          backgroundColor: theme.palette.background.paper
        },

        '&.Mui-error': {
          borderColor: theme.palette.error.main,
          boxShadow: `0 0 0 3px ${alpha(theme.palette.error.main, 0.1)}`
        },

        '& .MuiOutlinedInput-notchedOutline': {
          border: 'none'
        }
      }
    };
  }

  // Standard Material-UI variants with enhancements
  return {
    ...baseStyles,

    '& .MuiOutlinedInput-root': {
      '&:hover:not(.Mui-disabled) .MuiOutlinedInput-notchedOutline': {
        borderColor: alpha(focusColor, 0.5)
      },

      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
        borderColor: focusColor,
        borderWidth: '2px'
      },

      '&.Mui-error .MuiOutlinedInput-notchedOutline': {
        borderColor: theme.palette.error.main
      }
    },

    '& .MuiFilledInput-root': {
      backgroundColor: alpha(theme.palette.action.hover, 0.1),

      '&:hover:not(.Mui-disabled)': {
        backgroundColor: alpha(theme.palette.action.hover, 0.2)
      },

      '&.Mui-focused': {
        backgroundColor: alpha(focusColor, 0.1)
      }
    }
  };
});

const AtomicInput = forwardRef<HTMLDivElement, InputProps>(
  (
    {
      size = 'md',
      variant = 'outlined',
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

    const getStartAdornment = () => {
      if (leftIcon) {
        return (
          <InputAdornment position="start">
            {leftIcon}
          </InputAdornment>
        );
      }
      return undefined;
    };

    const getEndAdornment = () => {
      const adornments = [];

      // Clear button
      if (clearable && hasValue) {
        adornments.push(
          <IconButton
            key="clear"
            aria-label="clear input"
            onClick={handleClear}
            edge="end"
            size="small"
            sx={{ mr: 0.5 }}
          >
            <Clear fontSize="small" />
          </IconButton>
        );
      }

      // Password visibility toggle
      if (isPassword) {
        adornments.push(
          <IconButton
            key="password-toggle"
            aria-label="toggle password visibility"
            onClick={handleTogglePassword}
            edge="end"
            size="small"
          >
            {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
          </IconButton>
        );
      }

      // Custom right icon
      if (rightIcon && !isPassword && !clearable) {
        adornments.push(
          <InputAdornment key="right-icon" position="end">
            {rightIcon}
          </InputAdornment>
        );
      }

      return adornments.length > 0 ? (
        <InputAdornment position="end">
          {adornments}
        </InputAdornment>
      ) : undefined;
    };

    // Map state to error prop for Material-UI
    const error = state === 'error';
    const color = state === 'warning' ? 'warning' : state === 'success' ? 'success' : 'primary';

    return (
      <StyledTextField
        ref={ref}
        type={type}
        size={size}
        variant={variant === 'roblox' ? 'outlined' : variant}
        state={state}
        robloxTheme={robloxTheme}
        error={error}
        color={color}
        value={value}
        onChange={onChange}
        InputProps={{
          startAdornment: getStartAdornment(),
          endAdornment: getEndAdornment()
        }}
        {...props}
      />
    );
  }
);

AtomicInput.displayName = 'AtomicInput';

export type { InputProps };
export default AtomicInput;