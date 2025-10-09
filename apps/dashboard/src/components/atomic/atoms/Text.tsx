/**
 * Atomic Text Component
 *
 * A polymorphic text component with consistent typography, theming,
 * and semantic HTML rendering.
 */

import React, { forwardRef } from 'react';
import { Text as MantineText, type TextProps as MantineTextProps } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

// Polymorphic component types
type PolymorphicRef<T extends React.ElementType> = React.ComponentPropsWithRef<T>['ref'];

type PolymorphicProps<T extends React.ElementType = 'p'> = {
  component?: T;
  children?: React.ReactNode;
} & Omit<React.ComponentPropsWithoutRef<T>, 'component' | 'children'>;

export interface TextProps extends Omit<MantineTextProps, 'size' | 'component'> {
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
  component?: React.ElementType;
}

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
      component,
      style,
      ...props
    },
    ref
  ) => {
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
          return robloxTheme ? '#E2231A' : 'var(--mantine-color-blue-6)';
        case 'secondary':
          return 'var(--mantine-color-gray-6)';
        case 'success':
          return 'var(--mantine-color-green-6)';
        case 'error':
          return 'var(--mantine-color-red-6)';
        case 'warning':
          return 'var(--mantine-color-yellow-6)';
        case 'info':
          return 'var(--mantine-color-blue-6)';
        case 'disabled':
          return 'var(--mantine-color-gray-5)';
        case 'text':
        default:
          return 'var(--mantine-color-text)';
      }
    };

    // Determine the semantic HTML element based on variant
    const getComponent = () => {
      if (component) return component;

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

    const fontSize = sizeMap[variant];
    const fontWeight = weightMap[weight];
    const textColor = getColor();

    // Build custom styles
    let customStyles: React.CSSProperties = {
      fontSize: fontSize[0],
      lineHeight: fontSize[1],
      fontWeight,
      color: textColor,
      textAlign: align,
      margin: 0,
      ...(style as React.CSSProperties)
    };

    // Truncation styles
    if (truncate) {
      customStyles = {
        ...customStyles,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      };
    }

    // Gradient text effect
    if (gradient && robloxTheme) {
      customStyles = {
        ...customStyles,
        background: 'linear-gradient(135deg, #E2231A, #8B5CF6, #F59E0B)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text'
      };
    }

    // Glow effect
    if (glow && robloxTheme) {
      customStyles = {
        ...customStyles,
        textShadow: `0 0 10px ${textColor}, 0 0 20px ${textColor}, 0 0 30px ${textColor}`,
        animation: 'pulse 2s ease-in-out infinite alternate'
      };
    }

    return (
      <MantineText
        ref={ref}
        component={getComponent()}
        style={customStyles}
        {...props}
      >
        {children}
      </MantineText>
    );
  }
);

AtomicText.displayName = 'AtomicText';

export type { TextProps };
export default AtomicText;