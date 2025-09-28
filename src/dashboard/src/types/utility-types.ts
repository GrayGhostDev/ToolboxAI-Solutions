/**
 * Utility Types for ToolboxAI Dashboard
 * 
 * Advanced TypeScript utility types for better type safety and inference
 * across the ToolboxAI Dashboard application.
 * 
 * @version 2025
 */

// Basic utility types
export type Prettify<T> = {
  [K in keyof T]: T[K];
} & Record<string, never>;

export type UnionToIntersection<U> = (U extends any ? (k: U) => void : never) extends 
  (k: infer I) => void ? I : never;

// Conditional utility types  
export type IsEqual<T, U> = T extends U ? (U extends T ? true : false) : false;

export type NonNullable<T> = T extends null | undefined ? never : T;

export type DeepPartial<T> = T extends object ? {
  [P in keyof T]?: DeepPartial<T[P]>;
} : T;

export type DeepRequired<T> = T extends object ? {
  [P in keyof T]-?: DeepRequired<T[P]>;
} : T;

export type DeepReadonly<T> = T extends object ? {
  readonly [P in keyof T]: DeepReadonly<T[P]>;
} : T;

// Object manipulation types
export type PickByValue<T, V> = Pick<T, {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T]>;

export type OmitByValue<T, V> = Omit<T, {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T]>;

export type RequireOnly<T, K extends keyof T> = Partial<T> & Pick<T, K>;

export type OptionalBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Array and tuple utilities
export type Head<T extends readonly any[]> = T extends readonly [infer H, ...any[]] ? H : never;

export type Tail<T extends readonly any[]> = T extends readonly [any, ...infer R] ? R : never;

export type Last<T extends readonly any[]> = T extends readonly [...any[], infer L] ? L : never;

export type Length<T extends readonly any[]> = T['length'];

// String manipulation types
export type Split<S extends string, D extends string> = 
  S extends `${infer T}${D}${infer U}` ? [T, ...Split<U, D>] : [S];

export type Join<T extends readonly string[], D extends string> =
  T extends readonly [infer F, ...infer R]
    ? F extends string
      ? R extends readonly string[]
        ? R['length'] extends 0
          ? F
          : `${F}${D}${Join<R, D>}`
        : never
      : never
    : '';

export type Capitalize<S extends string> = S extends `${infer F}${infer R}` 
  ? `${Uppercase<F>}${R}` : S;

export type Uncapitalize<S extends string> = S extends `${infer F}${infer R}` 
  ? `${Lowercase<F>}${R}` : S;

// Function utilities
export type Parameters<T extends (...args: any) => any> = T extends (...args: infer P) => any ? P : never;

export type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any;

export type AsyncReturnType<T extends (...args: any) => Promise<any>> = 
  T extends (...args: any) => Promise<infer R> ? R : never;

export type Awaited<T> = T extends PromiseLike<infer U> ? Awaited<U> : T;

// Generic constraint utilities
export type StringKeys<T> = Extract<keyof T, string>;

export type NumberKeys<T> = Extract<keyof T, number>;

export type SymbolKeys<T> = Extract<keyof T, symbol>;

// Conditional type utilities
export type If<C extends boolean, T, F> = C extends true ? T : F;

export type Not<C extends boolean> = C extends true ? false : true;

export type And<A extends boolean, B extends boolean> = A extends true 
  ? B extends true ? true : false 
  : false;

export type Or<A extends boolean, B extends boolean> = A extends true 
  ? true 
  : B extends true ? true : false;

// Object path types
export type PathsToStringProps<T> = T extends string ? [] : {
  [K in Extract<keyof T, string>]: [K, ...PathsToStringProps<T[K]>];
}[Extract<keyof T, string>];

export type Join<K, P> = K extends string | number ?
  P extends string | number ?
    `${K}${"" extends P ? "" : "."}${P}`
    : never : never;

export type Paths<T, D extends number = 10> = [D] extends [never] ? never : T extends object ?
  { [K in keyof T]-?: K extends string | number ?
    `${K}` | Join<K, Paths<T[K], Prev[D]>>
    : never
  }[keyof T] : "";

export type Leaves<T, D extends number = 10> = [D] extends [never] ? never : T extends object ?
  { [K in keyof T]-?: Join<K, Leaves<T[K], Prev[D]>> }[keyof T] : "";

type Prev = [never, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
  11, 12, 13, 14, 15, 16, 17, 18, 19, 20, ...0[]];

// Event handler types
export type EventHandler<T = Event> = (event: T) => void;

export type AsyncEventHandler<T = Event> = (event: T) => Promise<void>;

// Component prop types
export type PropsWithChildren<P = Record<string, unknown>> = P & { 
  children?: React.ReactNode;
};

export type PropsWithoutRef<P> = P extends any ? ('ref' extends keyof P ? Pick<P, Exclude<keyof P, 'ref'>> : P) : P;

export type ComponentPropsWithoutRef<T extends keyof JSX.IntrinsicElements | React.JSXElementConstructor<any>> =
  T extends React.JSXElementConstructor<infer P>
    ? PropsWithoutRef<P>
    : T extends keyof JSX.IntrinsicElements
    ? PropsWithoutRef<JSX.IntrinsicElements[T]>
    : Record<string, unknown>;

// State management types
export type Action<T = any> = {
  type: string;
  payload?: T;
};

export type Reducer<S, A extends Action> = (state: S, action: A) => S;

export type AsyncAction<T = any> = (dispatch: Dispatch<Action>, getState: () => any) => Promise<T>;

export type Dispatch<A extends Action = Action> = (action: A) => void;

// API response types
export type ApiResponse<T = any> = {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
};

export type PaginatedResponse<T = any> = ApiResponse<T[]> & {
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
export type ValidationRule<T = any> = (value: T) => string | undefined;

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
  state?: any;
};

// WebSocket types
export type WebSocketEventType = 'open' | 'close' | 'error' | 'message';

export type WebSocketEventHandler<T = any> = (data: T) => void;

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

// Generic utility for branded types
export type Brand<K, T> = K & { __brand: T };

// Utility for creating nominal types
export type Nominal<T, K extends string> = T & { readonly [P in K]: unique symbol };

// Deep merge utility type
export type DeepMerge<T, U> = {
  [K in keyof T | keyof U]: K extends keyof U
    ? K extends keyof T
      ? T[K] extends object
        ? U[K] extends object
          ? DeepMerge<T[K], U[K]>
          : U[K]
        : U[K]
      : U[K]
    : K extends keyof T
    ? T[K]
    : never;
};

// Mutable utility type
export type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

// Type-safe object entries
export type Entries<T> = {
  [K in keyof T]: [K, T[K]];
}[keyof T][];

// Type-safe object keys
export type Keys<T> = (keyof T)[];

// Type-safe object values
export type Values<T> = T[keyof T][];

// Utility for strict object creation
export type StrictRecord<K extends keyof any, T> = Record<K, T>;

// Utility for extracting array element type
export type ArrayElement<A> = A extends readonly (infer T)[] ? T : never;

// Utility for tuple to union
export type TupleToUnion<T extends ReadonlyArray<any>> = T[number];

// Utility for union to tuple (limited)
export type UnionToTuple<T> = (
  T extends any ? (t: T) => T : never
) extends infer U
  ? (U extends any ? (u: U) => any : never) extends (v: infer V) => any
    ? V
    : never
  : never;

// Export commonly used type combinations
export type ID = string;
export type Timestamp = number;
export type ISO8601String = string;
export type JSONValue = string | number | boolean | null | JSONObject | JSONArray;
export type JSONObject = { [key: string]: JSONValue };
export type JSONArray = JSONValue[];

// Export utility functions for type checking
export const isString = (value: unknown): value is string => typeof value === 'string';
export const isNumber = (value: unknown): value is number => typeof value === 'number' && !isNaN(value);
export const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';
export const isObject = (value: unknown): value is Record<string, unknown> => 
  value !== null && typeof value === 'object' && !Array.isArray(value);
export const isArray = (value: unknown): value is unknown[] => Array.isArray(value);
export const isFunction = (value: unknown): value is Function => typeof value === 'function';
export const isDefined = <T>(value: T | undefined | null): value is T => value !== undefined && value !== null;
export const isEmpty = (value: unknown): boolean => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (isObject(value)) return Object.keys(value).length === 0;
  return false;
};

// Export type assertion utilities
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