/**
 * FormField Molecule
 *
 * A complete form field combining label, input, helper text, and error state.
 * This molecule demonstrates atomic design principles by composing atoms.
 */

import React, { forwardRef } from 'react';
import { Box } from '@mantine/core';
import { AtomicLabel, AtomicInput, AtomicText } from '../atoms';
import type { InputProps } from '../atoms/Input';
import type { LabelProps } from '../atoms/Label';
import { designTokens } from '../../../theme/designTokens';

export interface FormFieldProps extends Omit<InputProps, 'id'> {
  id?: string;
  label?: string;
  helperText?: string;
  errorText?: string;
  required?: boolean;
  optional?: boolean;
  labelProps?: Partial<LabelProps>;
  description?: string;
  showCharacterCount?: boolean;
  maxLength?: number;
  robloxTheme?: boolean;
}

const FormField = forwardRef<HTMLDivElement, FormFieldProps>(
  (
    {
      id,
      label,
      helperText,
      errorText,
      required = false,
      optional = false,
      labelProps,
      description,
      showCharacterCount = false,
      maxLength,
      value,
      state = 'default',
      robloxTheme = true,
      ...inputProps
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const fieldId = id || `form-field-${Math.random().toString(36).substr(2, 9)}`;

    // Determine field state
    const currentState = errorText ? 'error' : state;

    // Calculate character count
    const characterCount = value ? String(value).length : 0;
    const isOverLimit = maxLength ? characterCount > maxLength : false;

    // Helper text to display
    const displayHelperText = errorText || helperText;

    return (
      <Box
        ref={ref}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: designTokens.spacing[1],
          width: '100%'
        }}
      >
        {/* Label */}
        {label && (
          <AtomicLabel
            htmlFor={fieldId}
            required={required}
            optional={optional}
            robloxTheme={robloxTheme}
            {...labelProps}
          >
            {label}
          </AtomicLabel>
        )}

        {/* Description */}
        {description && (
          <AtomicText
            variant="sm"
            color="secondary"
            style={{
              marginTop: designTokens.spacing[0.5]
            }}
          >
            {description}
          </AtomicText>
        )}

        {/* Input */}
        <AtomicInput
          id={fieldId}
          value={value}
          state={currentState}
          robloxTheme={robloxTheme}
          error={currentState === 'error'}
          {...(maxLength && { maxLength })}
          {...inputProps}
        />

        {/* Helper text and character count */}
        {(displayHelperText || showCharacterCount) && (
          <Box style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: designTokens.spacing[0.5]
          }}>
            {displayHelperText && (
              <AtomicText
                variant="sm"
                color={errorText ? 'error' : 'secondary'}
              >
                {displayHelperText}
              </AtomicText>
            )}

            {showCharacterCount && (
              <AtomicText
                variant="xs"
                color={isOverLimit ? 'error' : 'disabled'}
              >
                {characterCount}
                {maxLength && `/${maxLength}`}
              </AtomicText>
            )}
          </Box>
        )}
      </Box>
    );
  }
);

FormField.displayName = 'FormField';

export type { FormFieldProps };
export default FormField;