/**
 * Utility Types for ToolboxAI Dashboard
 * 
 * Leverages type-fest for comprehensive TypeScript utility types
 * and adds project-specific types for better type safety.
 * 
 * @version 2025
 */

import React from 'react';

// Import comprehensive utility types from type-fest
export type {
  // Basic utilities
  Simplify,
  Merge,
  MergeDeep,
  RequireExactlyOne,
  RequireAtLeastOne,
  RequireAllOrNone,
  
  // Object utilities
  PartialDeep,
  RequiredDeep,
  ReadonlyDeep,
  WritableDeep,
  PickDeep,
  OmitDeep,
  SetOptional,
  SetRequired,
  SetReadonly,
  SetWritable,
  
  // String utilities
  CamelCase,
  PascalCase,
  KebabCase,
  SnakeCase,
  ScreamingSnakeCase,
  DelimiterCase,
  Split,
  Join,
  Trim,
  Replace,
  
  // Array utilities
  ArrayElement,
  FirstArrayElement,
  LastArrayElement,
  FixedLengthArray,
  MultidimensionalArray,
  MultidimensionalReadonlyArray,
  
  // Function utilities
  AsyncReturnType,
  
  // Conditional utilities
  IsEqual,
  IsNever,
  IsAny,
  IsUnknown,
  
  // Literal utilities
  LiteralUnion,
  UnionToIntersection,
  
  // Object path utilities
  Get,
  Paths,
  
  // Branded types
  Tagged,
  
  // JSON types
  JsonValue,
  JsonObject,
  JsonArray,
  JsonPrimitive,
  
  // Utilities for TypeScript
  TsConfigJson,
  PackageJson,
  
  // Entry utilities
  Entries,
  
  // Exact type
  Exact,
  
  // Opaque type
  Opaque
} from 'type-fest';

// Project-specific utility types not covered by type-fest

// Event handler types
export type EventHandler<T = Event> = (event: T) => void;
export type AsyncEventHandler<T = Event> = (event: T) => Promise<void>;

// React-specific types
export type PropsWithChildren<P = Record<string, unknown>> = P & { 
  children?: React.ReactNode;
};

export type ComponentPropsWithoutRef<T extends keyof JSX.IntrinsicElements | React.JSXElementConstructor<any>> =
  T extends React.JSXElementConstructor<infer P>
    ? Omit<P, 'ref'>
    : T extends keyof JSX.IntrinsicElements
    ? Omit<JSX.IntrinsicElements[T], 'ref'>
    : Record<string, unknown>;

// Redux/State management types
export type Action<T = unknown> = {
  type: string;
  payload?: T;
};

export type Reducer<S, A extends Action> = (state: S, action: A) => S;

export type AsyncAction<T = unknown> = (
  dispatch: Dispatch<Action>, 
  getState: () => unknown
) => Promise<T>;

export type Dispatch<A extends Action = Action> = (action: A) => void;

// API response types
export type ApiResponse<T = unknown> = {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
};

export type PaginatedResponse<T = unknown> = ApiResponse<T[]> & {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
};

// Form types
export type FormFieldValue = string | number | boolean | Date | null | undefined;

export type FormData = Record<string, FormFieldValue>;

export type FormErrors = Record<string, string | undefined>;

export type FormTouched = Record<string, boolean | undefined>;

export type FormState<T extends FormData = FormData> = {
  values: T;
  errors: FormErrors;
  touched: FormTouched;
  isSubmitting: boolean;
  isValid: boolean;
};

// Validation types
export type ValidationRule<T = unknown> = (value: T) => string | undefined;

export type ValidationSchema<T extends FormData> = {
  [K in keyof T]?: ValidationRule<T[K]>[];
};

// Theme types
export type ColorScheme = 'light' | 'dark' | 'auto';
export type ThemeSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ThemeSpacing = 0 | 4 | 8 | 12 | 16 | 20 | 24 | 32 | 40 | 48 | 56 | 64;

// Route types
export type RouteParams = Record<string, string>;
export type QueryParams = Record<string, string | string[] | undefined>;
export type NavigateOptions = {
  replace?: boolean;
  state?: unknown;
};

// WebSocket types
export type WebSocketEventType = 'open' | 'close' | 'error' | 'message';
export type WebSocketEventHandler<T = unknown> = (data: T) => void;

// Error handling types
export type ErrorBoundaryState = {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
};

export type ErrorHandler = (error: Error, errorInfo: React.ErrorInfo) => void;

// Performance monitoring types
export type PerformanceMetric = {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
};

export type PerformanceEntry = {
  name: string;
  entryType: string;
  startTime: number;
  duration: number;
};

// Commonly used type combinations
export type ID = string;
export type Timestamp = number;
export type ISO8601String = string;

// Type checking utility functions
export const isString = (value: unknown): value is string => typeof value === 'string';
export const isNumber = (value: unknown): value is number => typeof value === 'number' && !isNaN(value);
export const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';
export const isObject = (value: unknown): value is Record<string, unknown> => 
  value !== null && typeof value === 'object' && !Array.isArray(value);
export const isArray = (value: unknown): value is unknown[] => Array.isArray(value);
export const isFunction = (value: unknown): value is (...args: unknown[]) => unknown => typeof value === 'function';
export const isDefined = <T>(value: T | undefined | null): value is T => value !== undefined && value !== null;
export const isEmpty = (value: unknown): boolean => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (isObject(value)) return Object.keys(value).length === 0;
  return false;
};

// Type assertion utilities
export const assertIsString = (value: unknown): asserts value is string => {
  if (!isString(value)) {
    throw new Error(`Expected string, got ${typeof value}`);
  }
};

export const assertIsNumber = (value: unknown): asserts value is number => {
  if (!isNumber(value)) {
    throw new Error(`Expected number, got ${typeof value}`);
  }
};

export const assertIsObject = (value: unknown): asserts value is Record<string, unknown> => {
  if (!isObject(value)) {
    throw new Error(`Expected object, got ${typeof value}`);
  }
};