/**
 * Atomic Label Component
 *
 * A semantic label component with proper accessibility and form association.
 */

import React, { forwardRef } from 'react';
import { Text, type TextProps } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

export interface LabelProps extends Omit<TextProps, 'size' | 'component'> {
  size?: 'sm' | 'md' | 'lg';
  weight?: 'normal' | 'medium' | 'semibold' | 'bold';
  required?: boolean;
  optional?: boolean;
  robloxTheme?: boolean;
  htmlFor?: string;
}

const AtomicLabel = forwardRef<HTMLLabelElement, LabelProps>(
  (
    {
      children,
      size = 'md',
      weight = 'medium',
      required = false,
      optional = false,
      robloxTheme = true,
      htmlFor,
      style,
      ...props
    },
    ref
  ) => {
    const sizeMap = {
      sm: designTokens.typography.fontSize.sm[0],
      md: designTokens.typography.fontSize.sm[0],
      lg: designTokens.typography.fontSize.base[0]
    };

    const weightMap = {
      normal: designTokens.typography.fontWeight.normal,
      medium: designTokens.typography.fontWeight.medium,
      semibold: designTokens.typography.fontWeight.semibold,
      bold: designTokens.typography.fontWeight.bold
    };

    const renderContent = () => {
      return (
        <>
          {children}
          {required && (
            <span style={{ color: '#EF4444', marginLeft: '2px' }}>*</span>
          )}
          {optional && (
            <span style={{
              color: '#6B7280',
              fontSize: '0.875em',
              marginLeft: '4px',
              fontWeight: 'normal'
            }}>
              (optional)
            </span>
          )}
        </>
      );
    };

    const customStyle: React.CSSProperties = {
      fontSize: sizeMap[size],
      fontWeight: weightMap[weight],
      color: 'var(--mantine-color-text)',
      marginBottom: designTokens.spacing[1],
      display: 'block',
      ...(style as React.CSSProperties)
    };

    return (
      <Text
        ref={ref}
        component="label"
        htmlFor={htmlFor}
        style={customStyle}
        {...props}
      >
        {renderContent()}
      </Text>
    );
  }
);

AtomicLabel.displayName = 'AtomicLabel';

export type { LabelProps };
export default AtomicLabel;