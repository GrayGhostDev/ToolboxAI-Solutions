/**
 * Event Handler Type Definitions
 * Fixes WebSocket and React event handler type errors
 */

// WebSocket Event Handlers
export type WebSocketEventHandler = (data: unknown) => void;

export interface WebSocketEventHandlers {
  onMessage?: WebSocketEventHandler;
  onError?: WebSocketEventHandler;
  onOpen?: WebSocketEventHandler;
  onClose?: WebSocketEventHandler;
}

// React Event Handlers
export type ReactEventHandler<T = Element> = (event: React.SyntheticEvent<T>) => void;
export type ReactClickHandler<T = Element> = (event: React.MouseEvent<T>) => void;
export type ReactChangeHandler<T = Element> = (event: React.ChangeEvent<T>) => void;
export type ReactSubmitHandler<T = HTMLFormElement> = (event: React.FormEvent<T>) => void;
export type ReactKeyboardHandler<T = Element> = (event: React.KeyboardEvent<T>) => void;

// Generic form handlers
export interface FormHandlers {
  onSubmit?: ReactSubmitHandler;
  onChange?: ReactChangeHandler<HTMLInputElement>;
  onFocus?: ReactEventHandler<HTMLInputElement>;
  onBlur?: ReactEventHandler<HTMLInputElement>;
}

// WebSocket specific types
export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: number;
  id?: string;
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error?: string;
  lastMessage?: WebSocketMessage;
  reconnectAttempts?: number;
}

export interface WebSocketChannel {
  name: string;
  handlers: Map<string, WebSocketEventHandler>;
  subscribed: boolean;
}

// Pusher channel types
export interface PusherChannel {
  bind: (event: string, handler: WebSocketEventHandler) => void;
  unbind: (event: string, handler?: WebSocketEventHandler) => void;
  trigger: (event: string, data: unknown) => void;
}

export interface PresenceChannel extends PusherChannel {
  members: {
    count: number;
    each: (callback: (member: unknown) => void) => void;
  };
}