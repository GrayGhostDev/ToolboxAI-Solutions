/**
 * Utility Types for Common Patterns
 *
 * These utility types provide common patterns used throughout the application
 * for better type safety and developer experience.
 */

// Make certain properties required
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Make certain properties optional
export type OptionalBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Deep partial (makes all nested properties optional)
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends Array<infer U>
    ? Array<DeepPartial<U>>
    : T[P] extends object
      ? DeepPartial<T[P]>
      : T[P];
};

// Deep required (makes all nested properties required)
export type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object
    ? DeepRequired<T[P]>
    : T[P];
};

// Extract keys of a certain type
export type KeysOfType<T, U> = {
  [K in keyof T]: T[K] extends U ? K : never;
}[keyof T];

// Exclude keys of a certain type
export type ExcludeKeysOfType<T, U> = {
  [K in keyof T]: T[K] extends U ? never : K;
}[keyof T];

// Create a type with only properties of a certain type
export type PickByType<T, U> = Pick<T, KeysOfType<T, U>>;

// Create a type excluding properties of a certain type
export type OmitByType<T, U> = Pick<T, ExcludeKeysOfType<T, U>>;

// Nullable utility
export type Nullable<T> = T | null;

// Optional nullable
export type OptionalNullable<T> = T | null | undefined;

// Non-nullable
export type NonNullable<T> = T extends null | undefined ? never : T;

// Array element type
export type ElementType<T> = T extends readonly (infer U)[] ? U : never;

// Function parameter types
export type Parameters<T> = T extends (...args: infer P) => any ? P : never;

// Function return type
export type ReturnType<T> = T extends (...args: any[]) => infer R ? R : any;

// Promise resolution type
export type Awaited<T> = T extends Promise<infer U> ? U : T;

// Mutable version of readonly type
export type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

// Create object type from union
export type UnionToIntersection<U> = (U extends any ? (k: U) => void : never) extends (k: infer I) => void ? I : never;

// Extract property paths (dot notation)
export type PropertyPath<T, K extends keyof T = keyof T> = K extends string | number
  ? T[K] extends object
    ? T[K] extends any[]
      ? `${K}` | `${K}.${PropertyPath<T[K][number]>}`
      : `${K}` | `${K}.${PropertyPath<T[K]>}`
    : `${K}`
  : never;

// Get property type by path
export type PropertyType<T, P extends PropertyPath<T>> = P extends `${infer K}.${infer Rest}`
  ? K extends keyof T
    ? Rest extends PropertyPath<T[K]>
      ? PropertyType<T[K], Rest>
      : never
    : never
  : P extends keyof T
  ? T[P]
  : never;

// Create event handler type
export type EventHandler<T = unknown> = (event: T) => void;

// Async event handler
export type AsyncEventHandler<T = unknown> = (event: T) => Promise<void>;

// Optional event handler
export type OptionalEventHandler<T = unknown> = EventHandler<T> | undefined;

// Component props with children
export type WithChildren<T = {}> = T & {
  children?: React.ReactNode;
};

// Component props with optional children
export type MaybeWithChildren<T = {}> = T & {
  children?: React.ReactNode;
};

// Component props with required children
export type WithRequiredChildren<T = {}> = T & {
  children: React.ReactNode;
};

// Component props with className
export type WithClassName<T = {}> = T & {
  className?: string;
};

// Component props with style
export type WithStyle<T = {}> = T & {
  style?: React.CSSProperties;
};

// Component props with common HTML attributes
export type WithCommonProps<T = {}> = T & {
  id?: string;
  className?: string;
  style?: React.CSSProperties;
  'data-testid'?: string;
};

// API response envelope
export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  pagination?: {
    page: number;
    perPage: number;
    total: number;
    pages: number;
  };
  metadata?: {
    timestamp: string;
    version: string;
    [key: string]: unknown;
  };
};

// Paginated response
export type PaginatedResponse<T> = {
  items: T[];
  pagination: {
    page: number;
    perPage: number;
    total: number;
    pages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
};

// Error response
export type ErrorResponse = {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
    stack?: string;
  };
  timestamp: string;
};

// Success response
export type SuccessResponse<T> = {
  success: true;
  data: T;
  timestamp: string;
};

// Form field error
export type FieldError = {
  message: string;
  type: 'required' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  details?: unknown;
};

// Form errors
export type FormErrors<T> = {
  [K in keyof T]?: FieldError;
};

// Validation result
export type ValidationResult<T> = {
  isValid: boolean;
  errors: FormErrors<T>;
  warnings?: FormErrors<T>;
};

// Sort direction
export type SortDirection = 'asc' | 'desc';

// Sort configuration
export type SortConfig<T> = {
  key: keyof T;
  direction: SortDirection;
};

// Filter configuration
export type FilterConfig<T> = {
  [K in keyof T]?: T[K] | T[K][] | { min?: T[K]; max?: T[K] };
};

// Search configuration
export type SearchConfig = {
  query: string;
  fields?: string[];
  fuzzy?: boolean;
  caseSensitive?: boolean;
};

// Table column definition
export type ColumnDef<T> = {
  key: keyof T;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  render?: (value: T[keyof T], item: T, index: number) => React.ReactNode;
};

// Theme configuration
export type ThemeMode = 'light' | 'dark' | 'auto';

// Breakpoint names
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Responsive value
export type ResponsiveValue<T> = T | Partial<Record<Breakpoint, T>>;

// Color palette
export type ColorPalette = {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  text: {
    primary: string;
    secondary: string;
    disabled: string;
  };
  background: {
    default: string;
    paper: string;
  };
  border: string;
  divider: string;
};

// Loading state with error
export type AsyncState<T, E = string> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: E };

// RTK Query hook return type helper
export type QueryHookResult<T, E = string> = {
  data: T | undefined;
  error: E | undefined;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
  refetch: () => void;
};

// Mutation hook return type helper
export type MutationHookResult<T, V, E = string> = [
  (variables: V) => Promise<{ data: T } | { error: E }>,
  {
    data: T | undefined;
    error: E | undefined;
    isLoading: boolean;
    isSuccess: boolean;
    isError: boolean;
    reset: () => void;
  }
];

// Route parameter types
export type RouteParams<T extends string> = T extends `${string}:${infer Param}/${infer Rest}`
  ? { [K in Param]: string } & RouteParams<Rest>
  : T extends `${string}:${infer Param}`
  ? { [K in Param]: string }
  : {};

// URL search params
export type SearchParams = Record<string, string | string[] | undefined>;

// Navigation state
export type NavigationState = {
  pathname: string;
  search: string;
  hash: string;
  state?: unknown;
};

// Component ref types
export type ComponentRef<T extends React.ElementType> = React.ComponentRef<T>;

// Element type from component
export type ElementTypeFromComponent<T extends React.ElementType> = React.ComponentProps<T>;

// Polymorphic component props
export type PolymorphicProps<T extends React.ElementType, P = {}> = P &
  Omit<React.ComponentProps<T>, keyof P> & {
    as?: T;
  };

// Forward ref component type
export type ForwardRefComponent<T, P = {}> = React.ForwardRefExoticComponent<
  React.PropsWithoutRef<P> & React.RefAttributes<T>
>;

// Context value type
export type ContextValue<T> = T | undefined;

// Provider props
export type ProviderProps<T> = {
  value: T;
  children: React.ReactNode;
};

// Hook return type
export type UseStateReturn<T> = [T, React.Dispatch<React.SetStateAction<T>>];

// Effect cleanup function
export type EffectCleanup = () => void;

// Effect callback
export type EffectCallback = () => void | EffectCleanup;

// Reducer action
export type ReducerAction<T extends string = string, P = unknown> = {
  type: T;
  payload?: P;
};

// Reducer function
export type ReducerFunction<S, A extends ReducerAction> = (state: S, action: A) => S;

// Immutable update helpers
export type ImmutableUpdate<T> = T | ((draft: T) => void | T);

// Type-safe object keys
export const typedKeys = <T extends Record<string, unknown>>(obj: T): (keyof T)[] => {
  return Object.keys(obj) as (keyof T)[];
};

// Type-safe object entries
export const typedEntries = <T extends Record<string, unknown>>(obj: T): [keyof T, T[keyof T]][] => {
  return Object.entries(obj) as [keyof T, T[keyof T]][];
};

// Exhaustive switch check
export const assertNever = (value: never): never => {
  throw new Error(`Unexpected value: ${value}`);
};

// Type predicate for non-null values
export const isNotNull = <T>(value: T | null | undefined): value is T => {
  return value !== null && value !== undefined;
};

// Type predicate for defined values
export const isDefined = <T>(value: T | undefined): value is T => {
  return value !== undefined;
};

// Array type guards
export const isNonEmptyArray = <T>(array: T[]): array is [T, ...T[]] => {
  return array.length > 0;
};

// String type guards
export const isNonEmptyString = (value: string): value is string => {
  return value.length > 0;
};

// Number type guards
export const isPositiveNumber = (value: number): value is number => {
  return value > 0;
};

export const isNonNegativeNumber = (value: number): value is number => {
  return value >= 0;
};

// Object type guards
export const hasProperty = <T, K extends string>(
  obj: T,
  prop: K
): obj is T & Record<K, unknown> => {
  return typeof obj === 'object' && obj !== null && prop in obj;
};

// Deep clone utility type
export type DeepClone<T> = T extends Date
  ? Date
  : T extends RegExp
  ? RegExp
  : T extends (infer U)[]
  ? DeepClone<U>[]
  : T extends object
  ? { [K in keyof T]: DeepClone<T[K]> }
  : T;
