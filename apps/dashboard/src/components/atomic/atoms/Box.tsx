/**
 * Atomic Box Component
 *
 * A polymorphic layout component with responsive spacing, flexbox utilities,
 * and Roblox theming support.
 */

import React, { forwardRef } from 'react';
import { Box as MuiBox, BoxProps as MuiBoxProps, styled } from '@mui/material';
import { designTokens } from '../../../theme/designTokens';

// Polymorphic component types
type PolymorphicRef<T extends React.ElementType> = React.ComponentPropsWithRef<T>['ref'];

type PolymorphicProps<T extends React.ElementType = 'div'> = {
  as?: T;
  children?: React.ReactNode;
} & Omit<React.ComponentPropsWithoutRef<T>, 'as' | 'children'>;

// Spacing type
type SpacingValue = keyof typeof designTokens.spacing | 'auto';
type ResponsiveSpacing = SpacingValue | { xs?: SpacingValue; sm?: SpacingValue; md?: SpacingValue; lg?: SpacingValue; xl?: SpacingValue };

// Custom props for our Box component
export interface AtomicBoxProps {
  // Padding
  p?: ResponsiveSpacing;
  px?: ResponsiveSpacing;
  py?: ResponsiveSpacing;
  pt?: ResponsiveSpacing;
  pr?: ResponsiveSpacing;
  pb?: ResponsiveSpacing;
  pl?: ResponsiveSpacing;

  // Margin
  m?: ResponsiveSpacing;
  mx?: ResponsiveSpacing;
  my?: ResponsiveSpacing;
  mt?: ResponsiveSpacing;
  mr?: ResponsiveSpacing;
  mb?: ResponsiveSpacing;
  ml?: ResponsiveSpacing;

  // Layout
  display?: 'block' | 'inline' | 'inline-block' | 'flex' | 'inline-flex' | 'grid' | 'none';
  position?: 'static' | 'relative' | 'absolute' | 'fixed' | 'sticky';

  // Flexbox
  flexDirection?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
  flexWrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
  gap?: ResponsiveSpacing;

  // Dimensions
  w?: string | number;
  h?: string | number;
  minW?: string | number;
  minH?: string | number;
  maxW?: string | number;
  maxH?: string | number;

  // Border - use custom name to avoid conflict
  customBorder?: boolean | string;
  borderRadius?: keyof typeof designTokens.borderRadius | string | number;

  // Background
  bg?: string;
  gradient?: boolean;

  // Roblox theming
  robloxTheme?: boolean;
  gameContainer?: boolean;
}

// Combine with MUI box props, excluding conflicting ones
export type BoxProps = AtomicBoxProps & Omit<MuiBoxProps, keyof AtomicBoxProps | 'border'>;

const StyledBox = styled(MuiBox)<AtomicBoxProps>(({
  theme,
  robloxTheme = false,
  gameContainer = false,
  gradient = false,
  bg,
  customBorder,
  borderRadius,
  w,
  h,
  minW,
  minH,
  maxW,
  maxH
}) => {
  const getSpacingValue = (value: SpacingValue): string => {
    if (value === 'auto') return 'auto';
    return designTokens.spacing[value] || '0';
  };

  const getResponsiveSpacing = (spacing: ResponsiveSpacing | undefined): any => {
    if (!spacing) return undefined;

    if (typeof spacing === 'object') {
      return Object.entries(spacing).reduce((acc, [breakpoint, value]) => {
        acc[breakpoint] = getSpacingValue(value);
        return acc;
      }, {} as any);
    }

    return getSpacingValue(spacing);
  };

  // Base styles
  let styles: any = {};

  // Dimensions
  if (w !== undefined) styles.width = typeof w === 'number' ? `${w}px` : w;
  if (h !== undefined) styles.height = typeof h === 'number' ? `${h}px` : h;
  if (minW !== undefined) styles.minWidth = typeof minW === 'number' ? `${minW}px` : minW;
  if (minH !== undefined) styles.minHeight = typeof minH === 'number' ? `${minH}px` : minH;
  if (maxW !== undefined) styles.maxWidth = typeof maxW === 'number' ? `${maxW}px` : maxW;
  if (maxH !== undefined) styles.maxHeight = typeof maxH === 'number' ? `${maxH}px` : maxH;

  // Background
  if (bg) {
    styles.backgroundColor = bg;
  } else if (gradient && robloxTheme) {
    styles.background = 'linear-gradient(135deg, rgba(226, 35, 26, 0.1), rgba(139, 92, 246, 0.1))';
  }

  // Border
  if (customBorder) {
    if (typeof customBorder === 'string') {
      styles.border = customBorder;
    } else {
      styles.border = `1px solid ${theme.palette.divider}`;
    }
  }

  // Border radius
  if (borderRadius !== undefined) {
    if (typeof borderRadius === 'string' && borderRadius in designTokens.borderRadius) {
      styles.borderRadius = designTokens.borderRadius[borderRadius as keyof typeof designTokens.borderRadius];
    } else {
      styles.borderRadius = borderRadius;
    }
  }

  // Game container styling
  if (gameContainer && robloxTheme) {
    styles = {
      ...styles,
      background: theme.palette.mode === 'dark'
        ? 'radial-gradient(circle at 20% 80%, rgba(226, 35, 26, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)'
        : 'radial-gradient(circle at 20% 80%, rgba(226, 35, 26, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.05) 0%, transparent 50%)',
      borderRadius: designTokens.borderRadius['3xl'],
      position: 'relative',
      overflow: 'hidden',

      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'conic-gradient(from 0deg, transparent, rgba(226, 35, 26, 0.1), transparent)',
        animation: 'rotate 10s linear infinite',
        pointerEvents: 'none'
      }
    };
  }

  return styles;
});

const AtomicBox = forwardRef<HTMLDivElement, BoxProps & PolymorphicProps>(
  (
    {
      children,
      as: Component = 'div',
      p, px, py, pt, pr, pb, pl,
      m, mx, my, mt, mr, mb, ml,
      gap,
      robloxTheme = false,
      gameContainer = false,
      ...props
    },
    ref
  ) => {
    // Convert spacing props to Material-UI format
    const spacingProps = {
      ...(p !== undefined && { p: p }),
      ...(px !== undefined && { px: px }),
      ...(py !== undefined && { py: py }),
      ...(pt !== undefined && { pt: pt }),
      ...(pr !== undefined && { pr: pr }),
      ...(pb !== undefined && { pb: pb }),
      ...(pl !== undefined && { pl: pl }),
      ...(m !== undefined && { m: m }),
      ...(mx !== undefined && { mx: mx }),
      ...(my !== undefined && { my: my }),
      ...(mt !== undefined && { mt: mt }),
      ...(mr !== undefined && { mr: mr }),
      ...(mb !== undefined && { mb: mb }),
      ...(ml !== undefined && { ml: ml }),
      ...(gap !== undefined && { gap: gap })
    };

    return (
      <StyledBox
        ref={ref}
        component={Component}
        robloxTheme={robloxTheme}
        gameContainer={gameContainer}
        {...spacingProps}
        {...props}
      >
        {children}
      </StyledBox>
    );
  }
);

AtomicBox.displayName = 'AtomicBox';

export default AtomicBox;
export type { BoxProps };