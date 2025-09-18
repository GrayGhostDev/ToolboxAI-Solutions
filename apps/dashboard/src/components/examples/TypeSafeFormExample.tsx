/**
 * Type-Safe Form Example Component
 *
 * This component demonstrates the comprehensive type safety implementation
 * with branded types, discriminated unions, Zod validation, and exhaustive checking.
 */

import React from 'react';
import { z } from 'zod';
import {
  // Branded types
  UserId,
  ClassId,
  Email,
  Username,
  DisplayName,
  createUserId,
  createClassId,
  createEmail,
  createUsername,
  createDisplayName,

  // Discriminated unions
  LoadingState,
  FormState,
  createLoadingState,
  createFormState,
  isLoadingState,
  isFormState,

  // Utility types
  ApiResponse,
  WithChildren,
  RequiredBy,

  // Route types
  RoutePath,
  routes,

  // Event types
  FormEvents,
  InputEvents,
  ButtonEvents,

  // Validation
  validateApiResponse,
  assertNever,
  exhaustiveSwitch,
} from '../../types';

import {
  useTypeSafeForm,
  UserRegistrationSchema,
  ClassCreationSchema,
  CommonValidationSchemas,
} from '../../types/form-validation';

import {
  useCreateClassMutation,
  useUpdateUserMutation,
} from '../../store/api/enhanced-endpoints';

// Example 1: Type-safe form with branded types
interface UserRegistrationFormProps {
  onSuccess: (userId: UserId) => void;
  onError: (error: string) => void;
}

export const UserRegistrationForm: React.FC<UserRegistrationFormProps> = ({
  onSuccess,
  onError,
}) => {
  // Use our type-safe form hook with Zod validation
  const form = useTypeSafeForm(UserRegistrationSchema, {
    initialValues: {
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      displayName: '',
      role: 'student' as const,
      schoolId: '',
      agreeToTerms: false,
    },
    validateOnBlur: true,
    onSubmit: async (data) => {
      try {
        // Create branded types from validated form data
        const email = createEmail(data.email);
        const username = createUsername(data.username);
        const displayName = createDisplayName(data.displayName);

        // Simulate API call
        const response = await fetch('/api/v1/users/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...data,
            email,
            username,
            displayName,
          }),
        });

        const result = await response.json();

        // Validate API response at runtime
        const validationResult = validateApiResponse(
          z.object({ userId: z.string() }),
          result
        );

        if (validationResult.success) {
          const userId = createUserId(validationResult.data.userId);
          onSuccess(userId);
        } else {
          onError(validationResult.error);
        }
      } catch (error) {
        onError(error instanceof Error ? error.message : 'Registration failed');
      }
    },
    onError: (errors) => {
      const errorMessages = Object.values(errors).filter(Boolean);
      if (errorMessages.length > 0) {
        onError(errorMessages.join(', '));
      }
    },
  });

  // Type-safe event handlers
  const handleInputChange = React.useCallback<InputEvents['onChange']>((event) => {
    const { name, value, type, checked } = event.target;
    const fieldValue = type === 'checkbox' ? checked : value;

    // TypeScript ensures we can only pass valid field names
    form.handlers.onChange(name as any, fieldValue);
  }, [form.handlers]);

  const handleSubmit = React.useCallback<FormEvents['onSubmit']>((event) => {
    event.preventDefault();
    const formData = form.getFormData();
    form.handlers.onSubmit(formData);
  }, [form]);

  return (
    <form onSubmit={handleSubmit}>
      {/* Email field with branded type validation */}
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          {...form.getFieldProps('email')}
          onChange={handleInputChange}
        />
        {form.errors.email && (
          <span style={{ color: 'red' }}>{form.errors.email}</span>
        )}
      </div>

      {/* Username field with branded type validation */}
      <div>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          name="username"
          type="text"
          {...form.getFieldProps('username')}
          onChange={handleInputChange}
        />
        {form.errors.username && (
          <span style={{ color: 'red' }}>{form.errors.username}</span>
        )}
      </div>

      {/* Password fields with validation */}
      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          {...form.getFieldProps('password')}
          onChange={handleInputChange}
        />
        {form.errors.password && (
          <span style={{ color: 'red' }}>{form.errors.password}</span>
        )}
      </div>

      <div>
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input
          id="confirmPassword"
          name="confirmPassword"
          type="password"
          {...form.getFieldProps('confirmPassword')}
          onChange={handleInputChange}
        />
        {form.errors.confirmPassword && (
          <span style={{ color: 'red' }}>{form.errors.confirmPassword}</span>
        )}
      </div>

      {/* Role selection with exhaustive checking */}
      <div>
        <label htmlFor="role">Role</label>
        <select
          id="role"
          name="role"
          {...form.getFieldProps('role')}
          onChange={handleInputChange}
        >
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
          <option value="parent">Parent</option>
        </select>
      </div>

      {/* Terms checkbox with type-safe validation */}
      <div>
        <label>
          <input
            type="checkbox"
            name="agreeToTerms"
            checked={form.getFieldProps('agreeToTerms').value}
            onChange={handleInputChange}
          />
          I agree to the terms and conditions
        </label>
        {form.errors.agreeToTerms && (
          <span style={{ color: 'red' }}>{form.errors.agreeToTerms}</span>
        )}
      </div>

      <button
        type="submit"
        disabled={!form.isValid || form.isSubmitting}
      >
        {form.isSubmitting ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
};

// Example 2: Component using discriminated unions for state management
interface AsyncDataComponentProps<T> {
  data: LoadingState | FormState<T>;
  onRetry?: () => void;
}

export function AsyncDataComponent<T>({
  data,
  onRetry,
}: AsyncDataComponentProps<T>): React.ReactElement {
  // Exhaustive pattern matching with type guards
  if (isLoadingState(data, 'idle')) {
    return <div>Ready to load data</div>;
  }

  if (isLoadingState(data, 'loading')) {
    return <div>Loading...</div>;
  }

  if (isLoadingState(data, 'succeeded')) {
    return (
      <div>
        Data loaded successfully at {data.lastUpdated}
        {onRetry && <button onClick={onRetry}>Refresh</button>}
      </div>
    );
  }

  if (isLoadingState(data, 'failed')) {
    return (
      <div>
        Error: {data.error}
        <br />
        Last attempt: {data.lastAttempt}
        {onRetry && <button onClick={onRetry}>Retry</button>}
      </div>
    );
  }

  // If we add new states, TypeScript will catch the missing cases
  return exhaustiveSwitch(data);
}

// Example 3: RTK Query integration with type safety
interface ClassManagementProps {
  teacherId: UserId;
}

export const ClassManagement: React.FC<ClassManagementProps> = ({ teacherId }) => {
  const [createClass, { isLoading: isCreating, error: createError }] = useCreateClassMutation();
  const [updateUser] = useUpdateUserMutation();

  // Type-safe form for class creation
  const classForm = useTypeSafeForm(ClassCreationSchema, {
    onSubmit: async (data) => {
      try {
        const result = await createClass(data).unwrap();

        // Type-safe navigation using branded types
        const classId = createClassId(result.id);
        window.location.href = routes.class({ classId });
      } catch (error) {
        console.error('Failed to create class:', error);
      }
    },
  });

  // Exhaustive error handling
  const renderError = (error: unknown) => {
    if (!error) return null;

    // Type-safe error handling with discriminated unions
    if (typeof error === 'object' && error !== null && 'status' in error) {
      const apiError = error as { status: number; data: any };

      switch (apiError.status) {
        case 400:
          return <div style={{ color: 'red' }}>Invalid data provided</div>;
        case 401:
          return <div style={{ color: 'red' }}>Unauthorized</div>;
        case 403:
          return <div style={{ color: 'red' }}>Forbidden</div>;
        case 404:
          return <div style={{ color: 'red' }}>Not found</div>;
        case 500:
          return <div style={{ color: 'red' }}>Server error</div>;
        default:
          return <div style={{ color: 'red' }}>Unknown error occurred</div>;
      }
    }

    return <div style={{ color: 'red' }}>An error occurred</div>;
  };

  return (
    <div>
      <h2>Class Management</h2>

      {renderError(createError)}

      <form onSubmit={(e) => {
        e.preventDefault();
        classForm.handlers.onSubmit(classForm.getFormData());
      }}>
        <div>
          <label htmlFor="className">Class Name</label>
          <input
            id="className"
            type="text"
            {...classForm.getFieldProps('name')}
            onChange={(e) => classForm.handlers.onChange('name', e.target.value)}
          />
          {classForm.errors.name && (
            <span style={{ color: 'red' }}>{classForm.errors.name}</span>
          )}
        </div>

        <div>
          <label htmlFor="grade">Grade Level</label>
          <select
            id="grade"
            {...classForm.getFieldProps('grade')}
            onChange={(e) => classForm.handlers.onChange('grade', parseInt(e.target.value))}
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map(grade => (
              <option key={grade} value={grade}>Grade {grade}</option>
            ))}
          </select>
          {classForm.errors.grade && (
            <span style={{ color: 'red' }}>{classForm.errors.grade}</span>
          )}
        </div>

        <div>
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            {...classForm.getFieldProps('description')}
            onChange={(e) => classForm.handlers.onChange('description', e.target.value)}
          />
          {classForm.errors.description && (
            <span style={{ color: 'red' }}>{classForm.errors.description}</span>
          )}
        </div>

        <button
          type="submit"
          disabled={!classForm.isValid || isCreating}
        >
          {isCreating ? 'Creating...' : 'Create Class'}
        </button>
      </form>
    </div>
  );
};

// Example 4: Type-safe event handling with branded types
interface StudentProgressProps {
  studentId: UserId;
  classId: ClassId;
}

export const StudentProgress: React.FC<StudentProgressProps> = ({
  studentId,
  classId,
}) => {
  // State using discriminated unions
  const [progressState, setProgressState] = React.useState<LoadingState>(
    createLoadingState.idle()
  );

  // Type-safe event handlers
  const handleLoadProgress = React.useCallback<ButtonEvents['onClick']>(async (event) => {
    event.preventDefault();

    setProgressState(createLoadingState.loading());

    try {
      const response = await fetch(`/api/v1/students/${studentId}/progress?classId=${classId}`);
      const data = await response.json();

      // Runtime validation with Zod
      const progressSchema = z.object({
        studentId: z.string(),
        overallMastery: z.number().min(0).max(100),
        subjects: z.array(z.object({
          subject: z.string(),
          mastery: z.number().min(0).max(100),
        })),
      });

      const validationResult = validateApiResponse(progressSchema, data);

      if (validationResult.success) {
        setProgressState(createLoadingState.succeeded());
      } else {
        setProgressState(createLoadingState.failed(validationResult.error));
      }
    } catch (error) {
      setProgressState(createLoadingState.failed(
        error instanceof Error ? error.message : 'Failed to load progress'
      ));
    }
  }, [studentId, classId]);

  // Exhaustive state rendering
  const renderProgressState = () => {
    switch (progressState.status) {
      case 'idle':
        return (
          <button onClick={handleLoadProgress}>
            Load Student Progress
          </button>
        );

      case 'loading':
        return <div>Loading student progress...</div>;

      case 'succeeded':
        return (
          <div>
            Progress loaded successfully!
            <br />
            Last updated: {progressState.lastUpdated}
            <button onClick={handleLoadProgress}>Refresh</button>
          </div>
        );

      case 'failed':
        return (
          <div>
            Failed to load progress: {progressState.error}
            <br />
            <button onClick={handleLoadProgress}>Try Again</button>
          </div>
        );

      default:
        // TypeScript will catch if we miss any cases
        return assertNever(progressState);
    }
  };

  return (
    <div>
      <h3>Student Progress</h3>
      <p>Student ID: {studentId}</p>
      <p>Class ID: {classId}</p>
      {renderProgressState()}
    </div>
  );
};

// Example 5: Higher-order component with strict typing
export function withTypeValidation<P extends object>(
  Component: React.ComponentType<P>,
  schema: z.ZodSchema<P>
): React.ComponentType<P> {
  return function ValidatedComponent(props: P) {
    // Runtime prop validation in development
    if (process.env.NODE_ENV === 'development') {
      try {
        schema.parse(props);
      } catch (error) {
        if (error instanceof z.ZodError) {
          console.error(`Props validation failed for ${Component.name}:`, error.errors);

          return (
            <div style={{ color: 'red', border: '1px solid red', padding: '10px' }}>
              <strong>Props Validation Error in {Component.name}</strong>
              <pre>{JSON.stringify(error.errors, null, 2)}</pre>
            </div>
          );
        }
      }
    }

    return <Component {...props} />;
  };
}

// Usage example of HOC
const ValidatedUserRegistrationForm = withTypeValidation(
  UserRegistrationForm,
  z.object({
    onSuccess: z.function(),
    onError: z.function(),
  })
);

export default {
  UserRegistrationForm,
  AsyncDataComponent,
  ClassManagement,
  StudentProgress,
  ValidatedUserRegistrationForm,
};