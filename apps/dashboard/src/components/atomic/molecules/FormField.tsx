/**
 * FormField Molecule
 *
 * A complete form field combining label, input, helper text, and error state.
 * This molecule demonstrates atomic design principles by composing atoms.
 */

import React, { forwardRef } from 'react';
import { styled } from '@mui/material/styles';
import { AtomicLabel, AtomicInput, AtomicText, AtomicBox } from '../atoms';
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

const StyledFormField = styled(AtomicBox)<{ robloxTheme?: boolean }>(({
  theme,
  robloxTheme = true
}) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: designTokens.spacing[1],
  width: '100%',

  '& .form-field__description': {
    color: theme.palette.text.secondary,
    fontSize: designTokens.typography.fontSize.sm[0],
    marginTop: designTokens.spacing[0.5]
  },

  '& .form-field__helper': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: designTokens.spacing[0.5]
  },

  '& .form-field__character-count': {
    fontSize: designTokens.typography.fontSize.xs[0],
    color: theme.palette.text.disabled
  }
}));

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
      <StyledFormField ref={ref} robloxTheme={robloxTheme}>
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
            className="form-field__description"
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
          aria-describedby={
            displayHelperText ? `${fieldId}-helper` : undefined
          }
          {...(maxLength && { inputProps: { maxLength } })}
          {...inputProps}
        />

        {/* Helper text and character count */}
        {(displayHelperText || showCharacterCount) && (
          <AtomicBox className="form-field__helper">
            {displayHelperText && (
              <AtomicText
                id={`${fieldId}-helper`}
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
                className="form-field__character-count"
              >
                {characterCount}
                {maxLength && `/${maxLength}`}
              </AtomicText>
            )}
          </AtomicBox>
        )}
      </StyledFormField>
    );
  }
);

FormField.displayName = 'FormField';

export type { FormFieldProps };
export default FormField;