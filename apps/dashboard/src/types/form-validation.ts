/**
 * Type-Safe Form Validation System
 *
 * This module provides comprehensive form validation with Zod schemas,
 * ensuring type safety at compile time and runtime validation.
 */

import { z } from 'zod';
import React from 'react';
import type {
  FormState,
  createFormState,
  isFormState,
} from './discriminated-unions';
import type {
  Email,
  Username,
  DisplayName,
  createEmail,
  createUsername,
  createDisplayName,
} from './branded';
import type { DeepPartial, RequiredBy } from './utility-types';

// Base validation result
export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
  warnings?: Record<string, string>;
}

// Field validation rule
export interface ValidationRule<T = any> {
  name: string;
  message: string;
  validator: (value: T, formData?: Record<string, any>) => boolean;
}

// Form field configuration
export interface FormFieldConfig<T = any> {
  required?: boolean;
  rules?: ValidationRule<T>[];
  schema?: z.ZodSchema<T>;
  transform?: (value: any) => T;
  defaultValue?: T;
  dependencies?: string[];
}

// Form schema definition
export type FormSchema<T extends Record<string, any>> = {
  [K in keyof T]: FormFieldConfig<T[K]>;
};

// Form errors type
export type FormErrors<T extends Record<string, any>> = {
  [K in keyof T]?: string;
};

// Form warnings type
export type FormWarnings<T extends Record<string, any>> = {
  [K in keyof T]?: string;
};

// Form field state
export interface FormFieldState<T = any> {
  value: T;
  error?: string;
  warning?: string;
  touched: boolean;
  dirty: boolean;
  validating: boolean;
}

// Complete form state
export interface TypeSafeFormState<T extends Record<string, any>> {
  fields: { [K in keyof T]: FormFieldState<T[K]> };
  isValid: boolean;
  isSubmitting: boolean;
  isValidating: boolean;
  submitCount: number;
  errors: FormErrors<T>;
  warnings: FormWarnings<T>;
}

// Form event handlers
export interface FormEventHandlers<T extends Record<string, any>> {
  onChange: <K extends keyof T>(field: K, value: T[K]) => void;
  onBlur: <K extends keyof T>(field: K) => void;
  onFocus: <K extends keyof T>(field: K) => void;
  onSubmit: (data: T) => void | Promise<void>;
  onReset: () => void;
  validate: (field?: keyof T) => Promise<boolean>;
  setFieldError: <K extends keyof T>(field: K, error: string) => void;
  setFieldWarning: <K extends keyof T>(field: K, warning: string) => void;
  setFieldValue: <K extends keyof T>(field: K, value: T[K]) => void;
}

// Built-in validation schemas
export const CommonValidationSchemas = {
  // Text fields
  requiredString: z.string().min(1, 'This field is required'),
  optionalString: z.string().optional(),
  nonEmptyString: z.string().min(1, 'Cannot be empty'),
  maxLengthString: (max: number) => z.string().max(max, `Maximum ${max} characters`),
  minLengthString: (min: number) => z.string().min(min, `Minimum ${min} characters`),

  // Email validation
  email: z.string().email('Invalid email address'),
  optionalEmail: z.string().email('Invalid email address').optional(),

  // Username validation
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(30, 'Username cannot exceed 30 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores, and dashes'),

  // Password validation
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one lowercase letter, one uppercase letter, and one number'),

  // Number fields
  positiveNumber: z.number().positive('Must be a positive number'),
  nonNegativeNumber: z.number().min(0, 'Cannot be negative'),
  percentage: z.number().min(0).max(100, 'Must be between 0 and 100'),
  grade: z.number().int().min(1).max(12, 'Grade must be between 1 and 12'),

  // Boolean fields
  required: z.boolean().refine(val => val === true, 'This field is required'),
  optional: z.boolean().optional(),

  // Date fields
  dateString: z.string().datetime('Invalid date format'),
  futureDate: z.string().datetime().refine(
    date => new Date(date) > new Date(),
    'Date must be in the future'
  ),
  pastDate: z.string().datetime().refine(
    date => new Date(date) < new Date(),
    'Date must be in the past'
  ),

  // Array fields
  nonEmptyArray: <T>(itemSchema: z.ZodSchema<T>) =>
    z.array(itemSchema).min(1, 'At least one item is required'),
  maxItemsArray: <T>(itemSchema: z.ZodSchema<T>, max: number) =>
    z.array(itemSchema).max(max, `Maximum ${max} items allowed`),

  // File validation
  imageFile: z.instanceof(File).refine(
    file => file.type.startsWith('image/'),
    'Must be an image file'
  ),
  maxFileSize: (maxSizeBytes: number) =>
    z.instanceof(File).refine(
      file => file.size <= maxSizeBytes,
      `File size cannot exceed ${Math.round(maxSizeBytes / 1024 / 1024)}MB`
    ),

  // URL validation
  url: z.string().url('Invalid URL format'),
  optionalUrl: z.string().url('Invalid URL format').optional().or(z.literal('')),
} as const;

// Specific form schemas for the application
export const UserRegistrationSchema = z.object({
  email: CommonValidationSchemas.email,
  username: CommonValidationSchemas.username,
  password: CommonValidationSchemas.password,
  confirmPassword: z.string(),
  firstName: CommonValidationSchemas.requiredString,
  lastName: CommonValidationSchemas.requiredString,
  displayName: CommonValidationSchemas.requiredString,
  role: z.enum(['teacher', 'student', 'parent']),
  schoolId: CommonValidationSchemas.optionalString,
  agreeToTerms: CommonValidationSchemas.required,
}).refine(
  data => data.password === data.confirmPassword,
  {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  }
);

export const UserLoginSchema = z.object({
  email: CommonValidationSchemas.email,
  password: CommonValidationSchemas.requiredString,
  rememberMe: CommonValidationSchemas.optional,
});

export const ClassCreationSchema = z.object({
  name: CommonValidationSchemas.requiredString.max(100),
  grade: CommonValidationSchemas.grade,
  description: CommonValidationSchemas.optionalString.max(500),
  schedule: CommonValidationSchemas.optionalString,
  maxStudents: CommonValidationSchemas.positiveNumber.max(50).optional(),
});

export const LessonCreationSchema = z.object({
  title: CommonValidationSchemas.requiredString.max(200),
  description: CommonValidationSchemas.requiredString,
  subject: z.enum([
    'Math',
    'Science',
    'Language',
    'Arts',
    'Technology',
    'Social Studies',
    'Physical Education',
    'Life Skills'
  ]),
  classIds: CommonValidationSchemas.nonEmptyArray(z.string()),
  content: z.any(),
  robloxWorldId: CommonValidationSchemas.optionalString,
  estimatedDuration: CommonValidationSchemas.positiveNumber.optional(),
});

export const AssessmentCreationSchema = z.object({
  title: CommonValidationSchemas.requiredString.max(200),
  description: CommonValidationSchemas.optionalString,
  type: z.enum(['quiz', 'test', 'assignment', 'project']),
  classId: CommonValidationSchemas.requiredString,
  lessonId: CommonValidationSchemas.optionalString,
  dueDate: CommonValidationSchemas.optionalString,
  maxAttempts: CommonValidationSchemas.positiveNumber.max(10).optional(),
  timeLimit: CommonValidationSchemas.positiveNumber.optional(),
  questions: CommonValidationSchemas.nonEmptyArray(z.object({
    type: z.enum(['multiple_choice', 'true_false', 'short_answer', 'essay']),
    question: CommonValidationSchemas.requiredString,
    options: z.array(z.string()).optional(),
    correctAnswer: z.union([z.string(), z.number()]).optional(),
    points: CommonValidationSchemas.positiveNumber,
  })),
});

export const MessageCreationSchema = z.object({
  toUserId: CommonValidationSchemas.requiredString,
  subject: CommonValidationSchemas.requiredString.max(200),
  content: CommonValidationSchemas.requiredString,
  attachments: z.array(z.instanceof(File)).optional(),
  priority: z.enum(['low', 'normal', 'high']).optional(),
  scheduledSend: CommonValidationSchemas.optionalString,
});

export const UserProfileUpdateSchema = z.object({
  firstName: CommonValidationSchemas.optionalString.max(50),
  lastName: CommonValidationSchemas.optionalString.max(50),
  displayName: CommonValidationSchemas.optionalString.max(50),
  bio: CommonValidationSchemas.optionalString.max(500),
  avatarFile: CommonValidationSchemas.imageFile.optional(),
  language: CommonValidationSchemas.optionalString,
  timezone: CommonValidationSchemas.optionalString,
  notificationPreferences: z.object({
    email: CommonValidationSchemas.optional,
    push: CommonValidationSchemas.optional,
    sms: CommonValidationSchemas.optional,
  }).optional(),
});

// Form validation hook
export function useTypeSafeForm<T extends Record<string, any>>(
  schema: z.ZodSchema<T>,
  options: {
    initialValues?: DeepPartial<T>;
    validateOnChange?: boolean;
    validateOnBlur?: boolean;
    onSubmit?: (data: T) => void | Promise<void>;
    onError?: (errors: FormErrors<T>) => void;
  } = {}
) {
  const {
    initialValues = {} as DeepPartial<T>,
    validateOnChange = false,
    validateOnBlur = true,
    onSubmit,
    onError,
  } = options;

  // Form state
  const [formState, setFormState] = React.useState<TypeSafeFormState<T>>(() => {
    const fields = {} as { [K in keyof T]: FormFieldState<T[K]> };

    // Initialize fields from schema and initial values
    const schemaShape = (schema as any)._def?.shape || {};
    Object.keys(schemaShape).forEach(key => {
      const typedKey = key as keyof T;
      fields[typedKey] = {
        value: (initialValues as any)[key] ?? '',
        touched: false,
        dirty: false,
        validating: false,
      };
    });

    return {
      fields,
      isValid: false,
      isSubmitting: false,
      isValidating: false,
      submitCount: 0,
      errors: {} as FormErrors<T>,
      warnings: {} as FormWarnings<T>,
    };
  });

  // Validate a single field
  const validateField = React.useCallback(
    async (field: keyof T): Promise<boolean> => {
      const fieldSchema = (schema as any).shape?.[field];
      if (!fieldSchema) return true;

      try {
        setFormState(prev => ({
          ...prev,
          fields: {
            ...prev.fields,
            [field]: { ...prev.fields[field], validating: true },
          },
        }));

        await fieldSchema.parseAsync(formState.fields[field].value);

        setFormState(prev => ({
          ...prev,
          fields: {
            ...prev.fields,
            [field]: { ...prev.fields[field], validating: false },
          },
          errors: { ...prev.errors, [field]: undefined },
        }));

        return true;
      } catch (error) {
        if (error instanceof z.ZodError) {
          const errorMessage = error.errors[0]?.message || 'Invalid value';

          setFormState(prev => ({
            ...prev,
            fields: {
              ...prev.fields,
              [field]: { ...prev.fields[field], validating: false },
            },
            errors: { ...prev.errors, [field]: errorMessage },
          }));
        }

        return false;
      }
    },
    [schema, formState.fields]
  );

  // Validate entire form
  const validateForm = React.useCallback(async (): Promise<boolean> => {
    setFormState(prev => ({ ...prev, isValidating: true }));

    try {
      const formData = {} as T;
      Object.keys(formState.fields).forEach(key => {
        const typedKey = key as keyof T;
        formData[typedKey] = formState.fields[typedKey].value;
      });

      await schema.parseAsync(formData);

      setFormState(prev => ({
        ...prev,
        isValidating: false,
        isValid: true,
        errors: {} as FormErrors<T>,
      }));

      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors = {} as FormErrors<T>;
        error.errors.forEach(err => {
          if (err.path.length > 0) {
            const field = err.path[0] as keyof T;
            errors[field] = err.message;
          }
        });

        setFormState(prev => ({
          ...prev,
          isValidating: false,
          isValid: false,
          errors,
        }));

        onError?.(errors);
      }

      return false;
    }
  }, [schema, formState.fields, onError]);

  // Event handlers
  const handlers: FormEventHandlers<T> = {
    onChange: React.useCallback(<K extends keyof T>(field: K, value: T[K]) => {
      setFormState(prev => ({
        ...prev,
        fields: {
          ...prev.fields,
          [field]: {
            ...prev.fields[field],
            value,
            dirty: true,
          },
        },
      }));

      if (validateOnChange) {
        validateField(field);
      }
    }, [validateOnChange, validateField]),

    onBlur: React.useCallback(<K extends keyof T>(field: K) => {
      setFormState(prev => ({
        ...prev,
        fields: {
          ...prev.fields,
          [field]: {
            ...prev.fields[field],
            touched: true,
          },
        },
      }));

      if (validateOnBlur) {
        validateField(field);
      }
    }, [validateOnBlur, validateField]),

    onFocus: React.useCallback(<K extends keyof T>(field: K) => {
      setFormState(prev => ({
        ...prev,
        errors: {
          ...prev.errors,
          [field]: undefined,
        },
      }));
    }, []),

    onSubmit: React.useCallback(async (data: T) => {
      setFormState(prev => ({
        ...prev,
        isSubmitting: true,
        submitCount: prev.submitCount + 1,
      }));

      const isValid = await validateForm();

      if (isValid && onSubmit) {
        try {
          await onSubmit(data);
        } catch (error) {
          console.error('Form submission error:', error);
        }
      }

      setFormState(prev => ({ ...prev, isSubmitting: false }));
    }, [validateForm, onSubmit]),

    onReset: React.useCallback(() => {
      setFormState(prev => {
        const resetFields = {} as { [K in keyof T]: FormFieldState<T[K]> };
        Object.keys(prev.fields).forEach(key => {
          const typedKey = key as keyof T;
          resetFields[typedKey] = {
            value: (initialValues as any)[key] ?? '',
            touched: false,
            dirty: false,
            validating: false,
          };
        });

        return {
          ...prev,
          fields: resetFields,
          isValid: false,
          errors: {} as FormErrors<T>,
          warnings: {} as FormWarnings<T>,
        };
      });
    }, [initialValues]),

    validate: validateForm,

    setFieldError: React.useCallback(<K extends keyof T>(field: K, error: string) => {
      setFormState(prev => ({
        ...prev,
        errors: { ...prev.errors, [field]: error },
      }));
    }, []),

    setFieldWarning: React.useCallback(<K extends keyof T>(field: K, warning: string) => {
      setFormState(prev => ({
        ...prev,
        warnings: { ...prev.warnings, [field]: warning },
      }));
    }, []),

    setFieldValue: React.useCallback(<K extends keyof T>(field: K, value: T[K]) => {
      setFormState(prev => ({
        ...prev,
        fields: {
          ...prev.fields,
          [field]: {
            ...prev.fields[field],
            value,
            dirty: true,
          },
        },
      }));
    }, []),
  };

  // Get form data
  const getFormData = React.useCallback((): T => {
    const data = {} as T;
    Object.keys(formState.fields).forEach(key => {
      const typedKey = key as keyof T;
      data[typedKey] = formState.fields[typedKey].value;
    });
    return data;
  }, [formState.fields]);

  // Get field helpers
  const getFieldProps = React.useCallback(<K extends keyof T>(field: K) => ({
    value: formState.fields[field]?.value ?? '',
    error: formState.errors[field],
    warning: formState.warnings[field],
    touched: formState.fields[field]?.touched ?? false,
    dirty: formState.fields[field]?.dirty ?? false,
    validating: formState.fields[field]?.validating ?? false,
    onChange: (value: T[K]) => handlers.onChange(field, value),
    onBlur: () => handlers.onBlur(field),
    onFocus: () => handlers.onFocus(field),
  }), [formState, handlers]);

  return {
    formState,
    handlers,
    getFormData,
    getFieldProps,
    isValid: formState.isValid,
    isSubmitting: formState.isSubmitting,
    isValidating: formState.isValidating,
    errors: formState.errors,
    warnings: formState.warnings,
  };
}

// Form field component props
export interface FormFieldProps<T = any> {
  value: T;
  error?: string;
  warning?: string;
  touched: boolean;
  dirty: boolean;
  validating: boolean;
  onChange: (value: T) => void;
  onBlur: () => void;
  onFocus: () => void;
}

// Type-safe form component props
export interface TypeSafeFormProps<T extends Record<string, any>> {
  schema: z.ZodSchema<T>;
  initialValues?: DeepPartial<T>;
  onSubmit: (data: T) => void | Promise<void>;
  children: (props: {
    formState: TypeSafeFormState<T>;
    handlers: FormEventHandlers<T>;
    getFieldProps: <K extends keyof T>(field: K) => FormFieldProps<T[K]>;
    isValid: boolean;
  }) => React.ReactNode;
}

// Export form type inferences
export type UserRegistration = z.infer<typeof UserRegistrationSchema>;
export type UserLogin = z.infer<typeof UserLoginSchema>;
export type ClassCreation = z.infer<typeof ClassCreationSchema>;
export type LessonCreation = z.infer<typeof LessonCreationSchema>;
export type AssessmentCreation = z.infer<typeof AssessmentCreationSchema>;
export type MessageCreation = z.infer<typeof MessageCreationSchema>;
export type UserProfileUpdate = z.infer<typeof UserProfileUpdateSchema>;