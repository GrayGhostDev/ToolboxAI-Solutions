/**
 * Atomic Label Component
 *
 * A semantic label component with proper accessibility and form association.
 */

import React, { forwardRef } from 'react';
import { FormLabel, FormLabelProps, styled } from '@mui/material';
import { designTokens } from '../../../theme/designTokens';

export interface LabelProps extends FormLabelProps {
  size?: 'sm' | 'md' | 'lg';
  weight?: 'normal' | 'medium' | 'semibold' | 'bold';
  required?: boolean;
  optional?: boolean;
  robloxTheme?: boolean;
}

const StyledLabel = styled(FormLabel)<LabelProps>(({
  theme,
  size = 'md',
  weight = 'medium',
  robloxTheme = true
}) => {
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

  return {
    fontSize: sizeMap[size],
    fontWeight: weightMap[weight],
    color: theme.palette.text.primary,
    marginBottom: designTokens.spacing[1],
    display: 'block',

    '&.Mui-focused': {
      color: robloxTheme ? '#E2231A' : theme.palette.primary.main
    },

    '&.Mui-error': {
      color: theme.palette.error.main
    }
  };
});

const AtomicLabel = forwardRef<HTMLLabelElement, LabelProps>(
  (
    {
      children,
      required = false,
      optional = false,
      robloxTheme = true,
      ...props
    },
    ref
  ) => {
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

    return (
      <StyledLabel
        ref={ref}
        required={required}
        robloxTheme={robloxTheme}
        {...props}
      >
        {renderContent()}
      </StyledLabel>
    );
  }
);

AtomicLabel.displayName = 'AtomicLabel';

export type { LabelProps };
export default AtomicLabel;