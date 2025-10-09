import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../../utils/mui-imports';
/**
 * Atomic Button Component - React 19 Version
 *
 * Refactored to use React 19 features:
 * - Noneeded (components can accept ref prop directly)
 * - Using new Actions API for async operations
 * - Improved TypeScript types
 */

import React from 'react';
import { designTokens } from '../../../theme/designTokens';
import { useAction } from '../../../config/react19.ts';

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
  // React 19: Support async actions
  action?: (...args: any[]) => Promise<any>;
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
}

// Combine with MUI button props and React 19 ref support
export type ButtonProps = AtomicButtonProps &
  Omit<MuiButtonProps, keyof AtomicButtonProps | 'variant' | 'size'> & {
    ref?: React.Ref<HTMLButtonElement>;
  };

// Roblox brand colors
const ROBLOX_RED = '#E2231A';
const ROBLOX_RED_DARK = '#B71C15';
const ROBLOX_WHITE = '#FFFFFF';

const StyledButton = styled(MuiButton)<AtomicButtonProps>(({
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
      ...sizeMap[size as keyof typeof sizeMap]
    };

    if (!robloxTheme) {
      return baseStyles;
    }

    switch (variant) {
      case 'primary':
        return {
          ...baseStyles,
          backgroundColor: ROBLOX_RED,
          color: ROBLOX_WHITE,
          '&:hover': {
            backgroundColor: ROBLOX_RED_DARK,
            transform: 'translateY(-1px)',
            boxShadow: designTokens.shadows.lg,
          },
          '&:active': {
            transform: 'translateY(0)',
          },
          '&:disabled': {
            backgroundColor: alpha(ROBLOX_RED, 0.4),
            color: alpha(ROBLOX_WHITE, 0.6),
          },
        };

      case 'secondary':
        return {
          ...baseStyles,
          backgroundColor: designTokens.colors.gray[100],
          color: designTokens.colors.gray[900],
          '&:hover': {
            backgroundColor: designTokens.colors.gray[200],
            transform: 'translateY(-1px)',
          },
        };

      case 'outlined':
        return {
          ...baseStyles,
          backgroundColor: 'transparent',
          border: `2px solid ${ROBLOX_RED}`,
          color: ROBLOX_RED,
          '&:hover': {
            backgroundColor: alpha(ROBLOX_RED, 0.1),
            borderColor: ROBLOX_RED_DARK,
          },
        };

      case 'ghost':
        return {
          ...baseStyles,
          backgroundColor: 'transparent',
          color: designTokens.colors.gray[700],
          '&:hover': {
            backgroundColor: alpha(designTokens.colors.gray[500], 0.1),
          },
        };

      case 'danger':
        return {
          ...baseStyles,
          backgroundColor: designTokens.colors.red[600],
          color: ROBLOX_WHITE,
          '&:hover': {
            backgroundColor: designTokens.colors.red[700],
          },
        };

      default:
        return baseStyles;
    }
  };

  return {
    ...getVariantStyles(),
    ...(loading && {
      pointerEvents: 'none',
      opacity: 0.7,
    }),
  };
});

/**
 * React 19 Button Component
 * Noneeded - ref is handled as a regular prop
 */
export const Button = ({
  children,
  loading = false,
  loadingText,
  icon,
  iconPosition = 'left',
  disabled,
  onClick,
  action,
  onSuccess,
  onError,
  ref,
  ...props
}: ButtonProps) => {
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

  const content = (
    <>
      {isLoading ? (
        <>
          <CircularProgress
            size={16}
            style={{
              color: 'inherit',
              marginRight: loadingText ? 1 : 0,
            }}
          />
          {loadingText && <span>{loadingText}</span>}
        </>
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <span style={{ marginRight: '8px', display: 'inline-flex' }}>
              {icon}
            </span>
          )}
          {children}
          {icon && iconPosition === 'right' && (
            <span style={{ marginLeft: '8px', display: 'inline-flex' }}>
              {icon}
            </span>
          )}
        </>
      )}
    </>
  );

  return (
    <StyledButton
      ref={ref}
      disabled={isDisabled}
      onClick={handleClick}
      {...props}
    >
      {content}
    </StyledButton>
  );
};

// Export for convenience
export default Button;