/**
 * Atomic Button Component
 *
 * A polymorphic button component with Roblox theming, proper accessibility,
 * and support for different variants, sizes, and states.
 */

import React, { forwardRef } from 'react';
import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  CircularProgress,
  styled,
  alpha
} from '@mui/material';
import { designTokens } from '../../../theme/designTokens';

// Polymorphic component types
type PolymorphicRef<T extends React.ElementType> = React.ComponentPropsWithRef<T>['ref'];

type PolymorphicProps<T extends React.ElementType = 'button'> = {
  as?: T;
  children?: React.ReactNode;
} & Omit<React.ComponentPropsWithoutRef<T>, 'as' | 'children'>;

export interface ButtonProps extends Omit<MuiButtonProps, 'variant' | 'size'> {
  variant?: 'primary' | 'secondary' | 'outlined' | 'text' | 'ghost' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  loadingText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  robloxTheme?: boolean;
}

// Roblox brand colors
const ROBLOX_RED = '#E2231A';
const ROBLOX_RED_DARK = '#B71C15';
const ROBLOX_WHITE = '#FFFFFF';

const StyledButton = styled(MuiButton)<ButtonProps>(({
  theme,
  variant = 'primary',
  size = 'md',
  robloxTheme = true,
  loading
}) => {
  // Size configurations
  const sizeMap = {
    xs: {
      padding: `${designTokens.spacing[1]} ${designTokens.spacing[2]}`,
      fontSize: designTokens.typography.fontSize.xs[0],
      minHeight: '24px'
    },
    sm: {
      padding: `${designTokens.spacing[1.5]} ${designTokens.spacing[3]}`,
      fontSize: designTokens.typography.fontSize.sm[0],
      minHeight: '32px'
    },
    md: {
      padding: `${designTokens.spacing[2]} ${designTokens.spacing[4]}`,
      fontSize: designTokens.typography.fontSize.sm[0],
      minHeight: '40px'
    },
    lg: {
      padding: `${designTokens.spacing[2.5]} ${designTokens.spacing[6]}`,
      fontSize: designTokens.typography.fontSize.base[0],
      minHeight: '48px'
    },
    xl: {
      padding: `${designTokens.spacing[3]} ${designTokens.spacing[8]}`,
      fontSize: designTokens.typography.fontSize.lg[0],
      minHeight: '56px'
    }
  };

  // Variant configurations
  const getVariantStyles = () => {
    const baseStyles = {
      borderRadius: designTokens.borderRadius.lg,
      fontWeight: designTokens.typography.fontWeight.semibold,
      textTransform: 'none' as const,
      position: 'relative' as const,
      overflow: 'hidden' as const,
      transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
      ...sizeMap[size]
    };

    if (!robloxTheme) {
      return baseStyles;
    }

    switch (variant) {
      case 'primary':
        return {
          ...baseStyles,
          background: `linear-gradient(135deg, ${ROBLOX_RED}, ${ROBLOX_RED_DARK})`,
          color: ROBLOX_WHITE,
          border: 'none',
          boxShadow: `0 2px 8px ${alpha(ROBLOX_RED, 0.2)}`,

          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: '-100%',
            width: '100%',
            height: '100%',
            background: `linear-gradient(90deg, transparent, ${alpha(ROBLOX_WHITE, 0.2)}, transparent)`,
            transition: `left ${designTokens.animation.duration.slow} ${designTokens.animation.easing.inOut}`
          },

          '&:hover:not(:disabled)': {
            background: `linear-gradient(135deg, ${ROBLOX_RED_DARK}, ${ROBLOX_RED})`,
            transform: 'translateY(-2px) scale(1.02)',
            boxShadow: `0 8px 25px ${alpha(ROBLOX_RED, 0.4)}`,

            '&::before': {
              left: '100%'
            }
          },

          '&:active:not(:disabled)': {
            transform: 'translateY(0) scale(0.98)'
          },

          '&:disabled': {
            background: alpha(theme.palette.action.disabled, 0.12),
            color: theme.palette.action.disabled,
            boxShadow: 'none',
            cursor: 'not-allowed'
          }
        };

      case 'secondary':
        return {
          ...baseStyles,
          background: theme.palette.grey[100],
          color: theme.palette.text.primary,
          border: `1px solid ${theme.palette.divider}`,

          '&:hover:not(:disabled)': {
            background: theme.palette.grey[200],
            transform: 'translateY(-1px)',
            boxShadow: `0 4px 12px ${alpha(theme.palette.common.black, 0.1)}`
          }
        };

      case 'outlined':
        return {
          ...baseStyles,
          background: 'transparent',
          color: ROBLOX_RED,
          border: `2px solid ${ROBLOX_RED}`,

          '&:hover:not(:disabled)': {
            background: alpha(ROBLOX_RED, 0.1),
            borderColor: ROBLOX_RED_DARK,
            transform: 'translateY(-1px)'
          }
        };

      case 'text':
        return {
          ...baseStyles,
          background: 'transparent',
          color: ROBLOX_RED,
          border: 'none',
          padding: `${designTokens.spacing[1]} ${designTokens.spacing[2]}`,

          '&:hover:not(:disabled)': {
            background: alpha(ROBLOX_RED, 0.1)
          }
        };

      case 'ghost':
        return {
          ...baseStyles,
          background: 'transparent',
          color: theme.palette.text.secondary,
          border: 'none',

          '&:hover:not(:disabled)': {
            background: alpha(theme.palette.action.hover, 0.08),
            color: theme.palette.text.primary
          }
        };

      case 'danger':
        return {
          ...baseStyles,
          background: `linear-gradient(135deg, #EF4444, #DC2626)`,
          color: ROBLOX_WHITE,
          border: 'none',
          boxShadow: `0 2px 8px ${alpha('#EF4444', 0.2)}`,

          '&:hover:not(:disabled)': {
            background: `linear-gradient(135deg, #DC2626, #B91C1C)`,
            transform: 'translateY(-2px) scale(1.02)',
            boxShadow: `0 8px 25px ${alpha('#EF4444', 0.4)}`
          }
        };

      default:
        return baseStyles;
    }
  };

  return {
    ...getVariantStyles(),
    ...(loading && {
      pointerEvents: 'none' as const,
      cursor: 'default'
    })
  };
});

const AtomicButton = forwardRef<HTMLButtonElement, ButtonProps & PolymorphicProps>(
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
      as: Component = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    const renderContent = () => {
      if (loading) {
        return (
          <>
            <CircularProgress
              size={16}
              color="inherit"
              sx={{ mr: loadingText ? 1 : 0 }}
            />
            {loadingText || children}
          </>
        );
      }

      if (icon) {
        return iconPosition === 'left' ? (
          <>
            {React.cloneElement(icon as React.ReactElement, {
              sx: { mr: 1, fontSize: 'inherit' }
            })}
            {children}
          </>
        ) : (
          <>
            {children}
            {React.cloneElement(icon as React.ReactElement, {
              sx: { ml: 1, fontSize: 'inherit' }
            })}
          </>
        );
      }

      return children;
    };

    return (
      <StyledButton
        ref={ref}
        component={Component}
        variant={variant}
        size={size}
        disabled={isDisabled}
        loading={loading}
        robloxTheme={robloxTheme}
        {...props}
      >
        {renderContent()}
      </StyledButton>
    );
  }
);

AtomicButton.displayName = 'AtomicButton';

export type { ButtonProps };
export default AtomicButton;