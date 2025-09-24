// Global Type Definitions
declare global {
  // WebSocket types
  interface WebSocketEventHandler {
    (event: MessageEvent): void;
  }

  interface WebSocketErrorHandler {
    (error: Event): void;
  }

  // API types
  interface APIResponse<T = any> {
    data?: T;
    error?: string;
    status: number;
    message?: string;
  }

  // User types
  interface User {
    id: string;
    username: string;
    email: string;
    role: 'admin' | 'teacher' | 'student';
    createdAt?: string;
    updatedAt?: string;
  }

  // Auth types
  interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    token: string | null;
    loading: boolean;
    error: string | null;
  }

  // Module declarations
  declare module '*.svg' {
    const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
    export default content;
  }

  declare module '*.png' {
    const value: string;
    export default value;
  }

  declare module '*.jpg' {
    const value: string;
    export default value;
  }

  declare module '*.json' {
    const value: any;
    export default value;
  }

  declare module '*.css' {
    const classes: { [key: string]: string };
    export default classes;
  }

  declare module '*.scss' {
    const classes: { [key: string]: string };
    export default classes;
  }
}

// Component Props types
export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

// Form types
export interface FormFieldProps<T = any> {
  name: string;
  label?: string;
  value?: T;
  onChange?: (value: T) => void;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

// Table types
export interface TableColumn<T = any> {
  key: string;
  label: string;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
}

// Pagination types
export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  id?: string;
}

// Hook return types
export interface UseWebSocketReturn {
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  readyState: number;
  connect: () => void;
  disconnect: () => void;
}

export interface UseAPIReturn<T = any> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

// Event handlers
export type ClickHandler = (event: React.MouseEvent<HTMLElement>) => void;
export type ChangeHandler<T = string> = (value: T) => void;
export type SubmitHandler = (event: React.FormEvent<HTMLFormElement>) => void;

// Utility types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type AsyncFunction<T = void> = () => Promise<T>;

export {};
