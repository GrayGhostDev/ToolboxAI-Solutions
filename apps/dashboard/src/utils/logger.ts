/**
 * Production-ready logger utility
 *
 * Features:
 * - Environment-aware logging (only in development by default)
 * - Multiple log levels (debug, info, warn, error)
 * - Structured logging with timestamps
 * - Performance-optimized (no-op in production)
 * - Optional context/metadata support
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  module?: string;
  component?: string;
  action?: string;
  userId?: string;
  [key: string]: any;
}

class Logger {
  private isDevelopment: boolean;
  private isEnabled: boolean;
  private logLevel: LogLevel;

  constructor() {
    this.isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';
    this.isEnabled = this.isDevelopment || import.meta.env.VITE_ENABLE_LOGGING === 'true';
    this.logLevel = (import.meta.env.VITE_LOG_LEVEL as LogLevel) || 'warn';
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.isEnabled) return false;

    const levels: Record<LogLevel, number> = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3
    };

    return levels[level] >= levels[this.logLevel];
  }

  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;

    if (context) {
      const { module, component, action, ...rest } = context;
      let contextStr = '';
      if (module) contextStr += `[${module}]`;
      if (component) contextStr += `[${component}]`;
      if (action) contextStr += `[${action}]`;

      return `${prefix}${contextStr} ${message}`;
    }

    return `${prefix} ${message}`;
  }

  debug(message: string, data?: any, context?: LogContext): void {
    if (!this.shouldLog('debug')) return;

    const formattedMessage = this.formatMessage('debug', message, context);
    if (data !== undefined) {
      console.debug(formattedMessage, data);
    } else {
      console.debug(formattedMessage);
    }
  }

  info(message: string, data?: any, context?: LogContext): void {
    if (!this.shouldLog('info')) return;

    const formattedMessage = this.formatMessage('info', message, context);
    if (data !== undefined) {
      console.info(formattedMessage, data);
    } else {
      console.info(formattedMessage);
    }
  }

  warn(message: string, data?: any, context?: LogContext): void {
    if (!this.shouldLog('warn')) return;

    const formattedMessage = this.formatMessage('warn', message, context);
    if (data !== undefined) {
      console.warn(formattedMessage, data);
    } else {
      console.warn(formattedMessage);
    }
  }

  error(message: string, error?: Error | any, context?: LogContext): void {
    if (!this.shouldLog('error')) return;

    const formattedMessage = this.formatMessage('error', message, context);

    if (error instanceof Error) {
      console.error(formattedMessage, {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
    } else if (error !== undefined) {
      console.error(formattedMessage, error);
    } else {
      console.error(formattedMessage);
    }

    // In production, you might want to send errors to a service like Sentry
    if (!this.isDevelopment && error) {
      this.reportToErrorService(message, error, context);
    }
  }

  /**
   * Group related logs together
   */
  group(label: string): void {
    if (!this.isEnabled) return;
    console.group(label);
  }

  groupEnd(): void {
    if (!this.isEnabled) return;
    console.groupEnd();
  }

  /**
   * Performance timing helper
   */
  time(label: string): void {
    if (!this.shouldLog('debug')) return;
    console.time(label);
  }

  timeEnd(label: string): void {
    if (!this.shouldLog('debug')) return;
    console.timeEnd(label);
  }

  /**
   * Table display for structured data
   */
  table(data: any): void {
    if (!this.shouldLog('debug')) return;
    console.table(data);
  }

  /**
   * Clear the console (development only)
   */
  clear(): void {
    if (!this.isDevelopment) return;
    console.clear();
  }

  /**
   * Report errors to external service (Sentry, etc.)
   */
  private reportToErrorService(message: string, error: any, context?: LogContext): void {
    // This is where you'd integrate with Sentry or another error tracking service
    // For now, we'll just store in sessionStorage for debugging
    try {
      const errors = JSON.parse(sessionStorage.getItem('app_errors') || '[]');
      errors.push({
        timestamp: new Date().toISOString(),
        message,
        error: error instanceof Error ? {
          message: error.message,
          stack: error.stack
        } : error,
        context
      });
      // Keep only last 50 errors
      if (errors.length > 50) {
        errors.splice(0, errors.length - 50);
      }
      sessionStorage.setItem('app_errors', JSON.stringify(errors));
    } catch {
      // Fail silently if storage is full or unavailable
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export convenient shortcuts
export const { debug, info, warn, error, group, groupEnd, time, timeEnd, table, clear } = logger;

// Development-only helper for debugging
if (import.meta.env.DEV) {
  (window as any).__logger = logger;
  (window as any).__getErrors = () => {
    const errors = sessionStorage.getItem('app_errors');
    return errors ? JSON.parse(errors) : [];
  };
}