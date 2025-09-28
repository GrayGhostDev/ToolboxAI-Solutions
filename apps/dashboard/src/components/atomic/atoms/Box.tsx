/**
 * Atomic Box Component
 *
 * A polymorphic layout component with responsive spacing, flexbox utilities,
 * and Roblox theming support using Mantine.
 */

import React, { forwardRef } from 'react';
import { Box as MantineBox, BoxProps as MantineBoxProps, MantineStyleProp } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

// Spacing type
type SpacingValue = keyof typeof designTokens.spacing | 'auto' | number | string;
type ResponsiveSpacing = SpacingValue | { xs?: SpacingValue; sm?: SpacingValue; md?: SpacingValue; lg?: SpacingValue; xl?: SpacingValue };

// Custom props for our Box component
export interface AtomicBoxProps extends Omit<MantineBoxProps, 'w' | 'h'> {
  // Padding (Mantine already has these, we just redefine for consistency)
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

  // Border
  customBorder?: boolean | string;
  borderRadius?: keyof typeof designTokens.borderRadius | string | number;

  // Background
  bg?: string;
  gradient?: boolean;

  // Roblox theming
  robloxTheme?: boolean;
  gameContainer?: boolean;

  // Polymorphic component
  component?: React.ElementType;
}

const AtomicBox = forwardRef<HTMLDivElement, AtomicBoxProps>(
  (
    {
      children,
      component = 'div',
      p, px, py, pt, pr, pb, pl,
      m, mx, my, mt, mr, mb, ml,
      display,
      position,
      flexDirection,
      justifyContent,
      alignItems,
      flexWrap,
      gap,
      w,
      h,
      minW,
      minH,
      maxW,
      maxH,
      customBorder,
      borderRadius,
      bg,
      gradient = false,
      robloxTheme = false,
      gameContainer = false,
      style,
      ...props
    },
    ref
  ) => {
    // Convert spacing values
    const getSpacingValue = (value: SpacingValue): string | number => {
      if (value === 'auto') return 'auto';
      if (typeof value === 'number' || typeof value === 'string') return value;
      return designTokens.spacing[value] || 0;
    };

    const processSpacing = (spacing: ResponsiveSpacing | undefined): any => {
      if (!spacing) return undefined;

      if (typeof spacing === 'object') {
        // For responsive spacing, Mantine expects an object with breakpoint keys
        return spacing;
      }

      return getSpacingValue(spacing);
    };

    // Build styles object
    let customStyles: React.CSSProperties = {};

    // Dimensions
    if (w !== undefined) customStyles.width = typeof w === 'number' ? `${w}px` : w;
    if (h !== undefined) customStyles.height = typeof h === 'number' ? `${h}px` : h;
    if (minW !== undefined) customStyles.minWidth = typeof minW === 'number' ? `${minW}px` : minW;
    if (minH !== undefined) customStyles.minHeight = typeof minH === 'number' ? `${minH}px` : minH;
    if (maxW !== undefined) customStyles.maxWidth = typeof maxW === 'number' ? `${maxW}px` : maxW;
    if (maxH !== undefined) customStyles.maxHeight = typeof maxH === 'number' ? `${maxH}px` : maxH;

    // Layout
    if (display) customStyles.display = display;
    if (position) customStyles.position = position;

    // Flexbox
    if (flexDirection) customStyles.flexDirection = flexDirection;
    if (justifyContent) customStyles.justifyContent = justifyContent;
    if (alignItems) customStyles.alignItems = alignItems;
    if (flexWrap) customStyles.flexWrap = flexWrap;
    if (gap) customStyles.gap = processSpacing(gap);

    // Background
    if (bg) {
      customStyles.backgroundColor = bg;
    } else if (gradient && robloxTheme) {
      customStyles.background = 'linear-gradient(135deg, rgba(226, 35, 26, 0.1), rgba(139, 92, 246, 0.1))';
    }

    // Border
    if (customBorder) {
      if (typeof customBorder === 'string') {
        customStyles.border = customBorder;
      } else {
        customStyles.border = '1px solid var(--mantine-color-gray-4)';
      }
    }

    // Border radius
    if (borderRadius !== undefined) {
      if (typeof borderRadius === 'string' && borderRadius in designTokens.borderRadius) {
        customStyles.borderRadius = designTokens.borderRadius[borderRadius as keyof typeof designTokens.borderRadius];
      } else {
        customStyles.borderRadius = borderRadius;
      }
    }

    // Game container styling for Roblox theme
    if (gameContainer && robloxTheme) {
      customStyles = {
        ...customStyles,
        background: 'radial-gradient(circle at 20% 80%, rgba(226, 35, 26, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)',
        borderRadius: designTokens.borderRadius['3xl'],
        position: 'relative',
        overflow: 'hidden'
      };
    }

    // Build Mantine style prop
    const mantineStyles: MantineStyleProp = {
      ...customStyles,
      ...(style as React.CSSProperties)
    };

    // Add animation for game container
    const animationStyles = gameContainer && robloxTheme ? (
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .game-container::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: conic-gradient(from 0deg, transparent, rgba(226, 35, 26, 0.1), transparent);
          animation: rotate 10s linear infinite;
          pointer-events: none;
        }
      ` }} />
    ) : null;

    return (
      <>
        {animationStyles}
        <MantineBox
          ref={ref}
          component={component}
          p={processSpacing(p)}
          px={processSpacing(px)}
          py={processSpacing(py)}
          pt={processSpacing(pt)}
          pr={processSpacing(pr)}
          pb={processSpacing(pb)}
          pl={processSpacing(pl)}
          m={processSpacing(m)}
          mx={processSpacing(mx)}
          my={processSpacing(my)}
          mt={processSpacing(mt)}
          mr={processSpacing(mr)}
          mb={processSpacing(mb)}
          ml={processSpacing(ml)}
          style={mantineStyles}
          className={gameContainer && robloxTheme ? 'game-container' : undefined}
          {...props}
        >
          {children}
        </MantineBox>
      </>
    );
  }
);

AtomicBox.displayName = 'AtomicBox';

export default AtomicBox;
export type { AtomicBoxProps as BoxProps };