/**
 * Atomic Text Component
 *
 * A polymorphic text component with consistent typography, theming,
 * and semantic HTML rendering.
 */

import React, { forwardRef } from 'react';
import Typography from '@mui/material/Typography';
import TypographyProps from '@mui/material/TypographyProps';
import { styled } from '@mui/material/styles';
import { designTokens } from '../../../theme/designTokens';

// Polymorphic component types
type PolymorphicRef<T extends React.ElementType> = React.ComponentPropsWithRef<T>['ref'];

type PolymorphicProps<T extends React.ElementType = 'p'> = {
  as?: T;
  children?: React.ReactNode;
} & Omit<React.ComponentPropsWithoutRef<T>, 'as' | 'children'>;

export interface TextProps extends Omit<TypographyProps, 'variant'> {
  variant?:
    | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
    | 'body1' | 'body2' | 'caption' | 'overline'
    | 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl';
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold' | 'extrabold';
  align?: 'left' | 'center' | 'right' | 'justify';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'text' | 'disabled';
  truncate?: boolean;
  gradient?: boolean;
  glow?: boolean;
  robloxTheme?: boolean;
}

const StyledTypography = styled(Typography)<TextProps>(({
  theme,
  variant = 'base',
  weight = 'normal',
  color = 'text',
  truncate = false,
  gradient = false,
  glow = false,
  robloxTheme = true
}) => {
  // Font size mapping
  const sizeMap = {
    // Semantic variants
    h1: designTokens.typography.fontSize['5xl'],
    h2: designTokens.typography.fontSize['4xl'],
    h3: designTokens.typography.fontSize['3xl'],
    h4: designTokens.typography.fontSize['2xl'],
    h5: designTokens.typography.fontSize.xl,
    h6: designTokens.typography.fontSize.lg,
    body1: designTokens.typography.fontSize.base,
    body2: designTokens.typography.fontSize.sm,
    caption: designTokens.typography.fontSize.xs,
    overline: designTokens.typography.fontSize.xs,

    // Size variants
    xs: designTokens.typography.fontSize.xs,
    sm: designTokens.typography.fontSize.sm,
    base: designTokens.typography.fontSize.base,
    lg: designTokens.typography.fontSize.lg,
    xl: designTokens.typography.fontSize.xl,
    '2xl': designTokens.typography.fontSize['2xl'],
    '3xl': designTokens.typography.fontSize['3xl'],
    '4xl': designTokens.typography.fontSize['4xl'],
    '5xl': designTokens.typography.fontSize['5xl']
  };

  // Font weight mapping
  const weightMap = {
    light: designTokens.typography.fontWeight.light,
    normal: designTokens.typography.fontWeight.normal,
    medium: designTokens.typography.fontWeight.medium,
    semibold: designTokens.typography.fontWeight.semibold,
    bold: designTokens.typography.fontWeight.bold,
    extrabold: designTokens.typography.fontWeight.extrabold
  };

  // Color mapping
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
        return theme.palette.text.disabled;
      case 'text':
      default:
        return theme.palette.text.primary;
    }
  };

  const fontSize = sizeMap[variant];
  const fontWeight = weightMap[weight];
  const textColor = getColor();

  const baseStyles = {
    fontSize: fontSize[0],
    lineHeight: fontSize[1],
    fontWeight,
    color: textColor,
    fontFamily: theme.typography.fontFamily,
    margin: 0
  };

  // Truncation styles
  const truncateStyles = truncate ? {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const
  } : {};

  // Gradient text effect
  const gradientStyles = gradient && robloxTheme ? {
    background: 'linear-gradient(135deg, #E2231A, #8B5CF6, #F59E0B)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text'
  } : {};

  // Glow effect
  const glowStyles = glow && robloxTheme ? {
    textShadow: `0 0 10px ${textColor}, 0 0 20px ${textColor}, 0 0 30px ${textColor}`,
    animation: 'pulse 2s ease-in-out infinite alternate'
  } : {};

  return {
    ...baseStyles,
    ...truncateStyles,
    ...gradientStyles,
    ...glowStyles
  };
});

const AtomicText = forwardRef<HTMLElement, TextProps & PolymorphicProps>(
  (
    {
      children,
      variant = 'base',
      weight = 'normal',
      align = 'left',
      color = 'text',
      truncate = false,
      gradient = false,
      glow = false,
      robloxTheme = true,
      as,
      ...props
    },
    ref
  ) => {
    // Determine the semantic HTML element based on variant
    const getComponent = () => {
      if (as) return as;

      // Map text variants to semantic HTML elements
      const componentMap = {
        h1: 'h1',
        h2: 'h2',
        h3: 'h3',
        h4: 'h4',
        h5: 'h5',
        h6: 'h6',
        body1: 'p',
        body2: 'p',
        caption: 'span',
        overline: 'span'
      } as const;

      return componentMap[variant as keyof typeof componentMap] || 'p';
    };

    // Map our variants to Material-UI typography variants where appropriate
    const getMuiVariant = () => {
      const muiVariants = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'body1', 'body2', 'caption', 'overline'];
      return muiVariants.includes(variant) ? variant as TypographyProps['variant'] : 'body1';
    };

    return (
      <StyledTypography
        ref={ref}
        component={getComponent()}
        variant={getMuiVariant()}
        align={align}
        weight={weight}
        color={color}
        truncate={truncate}
        gradient={gradient}
        glow={glow}
        robloxTheme={robloxTheme}
        {...props}
      >
        {children}
      </StyledTypography>
    );
  }
);

AtomicText.displayName = 'AtomicText';

export type { TextProps };
export default AtomicText;