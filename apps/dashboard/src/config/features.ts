/**
 * Feature Flags Configuration
 *
 * Centralized feature flag management for the dashboard application
 * Allows runtime control of features without code changes
 */

export interface FeatureFlags {
  // Performance Monitoring
  enablePerformanceMonitoring: boolean;
  performanceMonitoringLevel: 'off' | 'basic' | 'detailed' | 'verbose';
  performanceReportingInterval: number; // milliseconds

  // API Features
  enableSlowApiWarnings: boolean;
  apiTimeoutThreshold: number; // milliseconds

  // UI Features
  enableDarkMode: boolean;
  enableExperimentalFeatures: boolean;
  enableAdvancedAnalytics: boolean;

  // WebSocket/Realtime
  enableWebSocketReconnection: boolean;
  maxReconnectionAttempts: number;
  reconnectionBackoffMultiplier: number;

  // Security
  enableHttpOnlyCookies: boolean;
  enableCsrfProtection: boolean;
  sessionTimeout: number; // minutes

  // Developer Tools
  enableDebugMode: boolean;
  enableReduxDevTools: boolean;
  enableReactProfiler: boolean;
}

// Default feature flag values
const defaultFlags: FeatureFlags = {
  // Performance Monitoring
  enablePerformanceMonitoring: false,
  performanceMonitoringLevel: 'basic',
  performanceReportingInterval: 60000, // 1 minute

  // API Features
  enableSlowApiWarnings: true,
  apiTimeoutThreshold: 5000, // 5 seconds

  // UI Features
  enableDarkMode: true,
  enableExperimentalFeatures: false,
  enableAdvancedAnalytics: false,

  // WebSocket/Realtime
  enableWebSocketReconnection: true,
  maxReconnectionAttempts: 5,
  reconnectionBackoffMultiplier: 1.5,

  // Security
  enableHttpOnlyCookies: true,
  enableCsrfProtection: true,
  sessionTimeout: 30, // 30 minutes

  // Developer Tools
  enableDebugMode: import.meta.env.DEV,
  enableReduxDevTools: import.meta.env.DEV,
  enableReactProfiler: false,
};

/**
 * Feature Flag Manager
 *
 * Manages feature flags with support for:
 * - Environment variable overrides
 * - LocalStorage persistence
 * - Runtime updates
 */
class FeatureFlagManager {
  private flags: FeatureFlags;
  private listeners: Set<(flags: FeatureFlags) => void> = new Set();
  private storageKey = 'toolboxai_feature_flags';

  constructor() {
    // Start with defaults
    this.flags = { ...defaultFlags };

    // Load from environment variables
    this.loadFromEnvironment();

    // Load from localStorage (overrides environment)
    this.loadFromStorage();

    // Listen for storage changes (for cross-tab sync)
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', this.handleStorageChange);
    }
  }

  /**
   * Load feature flags from environment variables
   * Environment variables should be prefixed with VITE_FEATURE_
   */
  private loadFromEnvironment(): void {
    if (typeof import.meta.env === 'undefined') return;

    // Performance monitoring from env
    if (import.meta.env.VITE_FEATURE_PERFORMANCE_MONITORING !== undefined) {
      this.flags.enablePerformanceMonitoring =
        import.meta.env.VITE_FEATURE_PERFORMANCE_MONITORING === 'true';
    }

    if (import.meta.env.VITE_FEATURE_PERFORMANCE_LEVEL !== undefined) {
      this.flags.performanceMonitoringLevel =
        import.meta.env.VITE_FEATURE_PERFORMANCE_LEVEL as any;
    }

    // API features from env
    if (import.meta.env.VITE_FEATURE_SLOW_API_WARNINGS !== undefined) {
      this.flags.enableSlowApiWarnings =
        import.meta.env.VITE_FEATURE_SLOW_API_WARNINGS === 'true';
    }

    // UI features from env
    if (import.meta.env.VITE_FEATURE_DARK_MODE !== undefined) {
      this.flags.enableDarkMode =
        import.meta.env.VITE_FEATURE_DARK_MODE === 'true';
    }

    if (import.meta.env.VITE_FEATURE_EXPERIMENTAL !== undefined) {
      this.flags.enableExperimentalFeatures =
        import.meta.env.VITE_FEATURE_EXPERIMENTAL === 'true';
    }
  }

  /**
   * Load feature flags from localStorage
   */
  private loadFromStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Only override specific flags, not all
        Object.keys(parsed).forEach(key => {
          if (key in this.flags) {
            (this.flags as any)[key] = parsed[key];
          }
        });
      }
    } catch (error) {
      console.warn('Failed to load feature flags from storage:', error);
    }
  }

  /**
   * Save current flags to localStorage
   */
  private saveToStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      // Only save flags that differ from defaults
      const toSave: Partial<FeatureFlags> = {};
      Object.keys(this.flags).forEach(key => {
        if ((this.flags as any)[key] !== (defaultFlags as any)[key]) {
          (toSave as any)[key] = (this.flags as any)[key];
        }
      });

      if (Object.keys(toSave).length > 0) {
        localStorage.setItem(this.storageKey, JSON.stringify(toSave));
      } else {
        localStorage.removeItem(this.storageKey);
      }
    } catch (error) {
      console.warn('Failed to save feature flags to storage:', error);
    }
  }

  /**
   * Handle storage changes from other tabs
   */
  private handleStorageChange = (event: StorageEvent): void => {
    if (event.key === this.storageKey && event.newValue) {
      try {
        const parsed = JSON.parse(event.newValue);
        Object.keys(parsed).forEach(key => {
          if (key in this.flags) {
            (this.flags as any)[key] = parsed[key];
          }
        });
        this.notifyListeners();
      } catch (error) {
        console.warn('Failed to parse storage change:', error);
      }
    }
  };

  /**
   * Get current feature flags
   */
  public getFlags(): Readonly<FeatureFlags> {
    return { ...this.flags };
  }

  /**
   * Get a specific feature flag
   */
  public getFlag<K extends keyof FeatureFlags>(key: K): FeatureFlags[K] {
    return this.flags[key];
  }

  /**
   * Update feature flags
   */
  public updateFlags(updates: Partial<FeatureFlags>): void {
    const changed = Object.keys(updates).some(
      key => (this.flags as any)[key] !== (updates as any)[key]
    );

    if (changed) {
      Object.assign(this.flags, updates);
      this.saveToStorage();
      this.notifyListeners();

      console.log('🚩 Feature flags updated:', updates);
    }
  }

  /**
   * Reset flags to defaults
   */
  public resetToDefaults(): void {
    this.flags = { ...defaultFlags };
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.storageKey);
    }
    this.notifyListeners();
    console.log('🔄 Feature flags reset to defaults');
  }

  /**
   * Subscribe to flag changes
   */
  public subscribe(listener: (flags: FeatureFlags) => void): () => void {
    this.listeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of flag changes
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.getFlags());
      } catch (error) {
        console.error('Feature flag listener error:', error);
      }
    });
  }

  /**
   * Check if performance monitoring should be enabled
   * Considers multiple factors
   */
  public shouldEnablePerformanceMonitoring(): boolean {
    // Never enable if explicitly disabled
    if (!this.flags.enablePerformanceMonitoring) {
      return false;
    }

    // Check if level is not 'off'
    if (this.flags.performanceMonitoringLevel === 'off') {
      return false;
    }

    // Additional checks could be added here
    // e.g., browser compatibility, user preferences, etc.

    return true;
  }

  /**
   * Get performance monitoring configuration
   */
  public getPerformanceConfig(): {
    enabled: boolean;
    level: string;
    reportingInterval: number;
    includeApiMetrics: boolean;
    includeComponentMetrics: boolean;
    includeSystemMetrics: boolean;
  } {
    const enabled = this.shouldEnablePerformanceMonitoring();
    const level = this.flags.performanceMonitoringLevel;

    return {
      enabled,
      level,
      reportingInterval: this.flags.performanceReportingInterval,
      includeApiMetrics: level !== 'off',
      includeComponentMetrics: level === 'detailed' || level === 'verbose',
      includeSystemMetrics: level === 'verbose',
    };
  }

  /**
   * Cleanup
   */
  public destroy(): void {
    if (typeof window !== 'undefined') {
      window.removeEventListener('storage', this.handleStorageChange);
    }
    this.listeners.clear();
  }
}

// Create singleton instance
export const featureFlags = new FeatureFlagManager();

// Export hooks for React components
export function useFeatureFlag<K extends keyof FeatureFlags>(key: K): FeatureFlags[K] {
  const [value, setValue] = React.useState(() => featureFlags.getFlag(key));

  React.useEffect(() => {
    const unsubscribe = featureFlags.subscribe((flags) => {
      setValue(flags[key]);
    });

    return unsubscribe;
  }, [key]);

  return value;
}

export function useFeatureFlags(): Readonly<FeatureFlags> {
  const [flags, setFlags] = React.useState(() => featureFlags.getFlags());

  React.useEffect(() => {
    const unsubscribe = featureFlags.subscribe(setFlags);
    return unsubscribe;
  }, []);

  return flags;
}

// Expose to window for debugging in development
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  (window as any).__FEATURE_FLAGS__ = featureFlags;
}