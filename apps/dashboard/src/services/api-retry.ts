/**
 * API Retry Service
 *
 * Provides retry logic with exponential backoff for failed API calls
 * Includes circuit breaker pattern and request deduplication
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Retry configuration options
 */
export interface RetryConfig {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryCondition?: (error: AxiosError) => boolean;
  onRetry?: (retryCount: number, error: AxiosError) => void;
  shouldResetTimeout?: boolean;
}

/**
 * Circuit breaker configuration
 */
export interface CircuitBreakerConfig {
  enabled?: boolean;
  failureThreshold?: number;
  resetTimeout?: number;
  halfOpenRequests?: number;
}

/**
 * Request deduplication configuration
 */
export interface DeduplicationConfig {
  enabled?: boolean;
  ttl?: number;
  keyGenerator?: (config: AxiosRequestConfig) => string;
}

/**
 * Default retry configuration
 */
const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
  retryCondition: (error: AxiosError) => {
    // Retry on network errors and 5xx status codes
    if (!error.response) return true;
    const status = error.response.status;
    return status >= 500 && status <= 599;
  },
  onRetry: (retryCount: number, error: AxiosError) => {
    console.log(`Retry attempt ${retryCount} for ${error.config?.url}`);
  },
  shouldResetTimeout: true,
};

/**
 * Default circuit breaker configuration
 */
const DEFAULT_CIRCUIT_BREAKER_CONFIG: Required<CircuitBreakerConfig> = {
  enabled: true,
  failureThreshold: 5,
  resetTimeout: 60000, // 1 minute
  halfOpenRequests: 3,
};

/**
 * Circuit breaker states
 */
enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN',
}

/**
 * Circuit breaker implementation
 */
class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private halfOpenRequestCount: number = 0;
  private config: Required<CircuitBreakerConfig>;

  constructor(config: CircuitBreakerConfig = {}) {
    this.config = { ...DEFAULT_CIRCUIT_BREAKER_CONFIG, ...config };
  }

  /**
   * Check if request should be allowed
   */
  public shouldAllowRequest(): boolean {
    if (!this.config.enabled) return true;

    switch (this.state) {
      case CircuitState.CLOSED:
        return true;

      case CircuitState.OPEN:
        // Check if enough time has passed to try again
        if (Date.now() - this.lastFailureTime >= this.config.resetTimeout) {
          this.state = CircuitState.HALF_OPEN;
          this.halfOpenRequestCount = 0;
          return true;
        }
        return false;

      case CircuitState.HALF_OPEN:
        // Allow limited requests in half-open state
        return this.halfOpenRequestCount < this.config.halfOpenRequests;
    }
  }

  /**
   * Record successful request
   */
  public recordSuccess(): void {
    if (!this.config.enabled) return;

    if (this.state === CircuitState.HALF_OPEN) {
      this.halfOpenRequestCount++;
      if (this.halfOpenRequestCount >= this.config.halfOpenRequests) {
        // All test requests succeeded, close the circuit
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
      }
    }
  }

  /**
   * Record failed request
   */
  public recordFailure(): void {
    if (!this.config.enabled) return;

    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      // Failed in half-open state, reopen circuit
      this.state = CircuitState.OPEN;
    } else if (this.failureCount >= this.config.failureThreshold) {
      // Too many failures, open circuit
      this.state = CircuitState.OPEN;
    }
  }

  /**
   * Get current circuit state
   */
  public getState(): CircuitState {
    return this.state;
  }

  /**
   * Reset circuit breaker
   */
  public reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.lastFailureTime = 0;
    this.halfOpenRequestCount = 0;
  }
}

/**
 * Request deduplication cache
 */
class RequestCache {
  private cache: Map<string, Promise<AxiosResponse>> = new Map();
  private timestamps: Map<string, number> = new Map();
  private config: Required<DeduplicationConfig>;

  constructor(config: DeduplicationConfig = {}) {
    this.config = {
      enabled: true,
      ttl: 5000, // 5 seconds
      keyGenerator: (config: AxiosRequestConfig) => {
        return `${config.method}:${config.url}:${JSON.stringify(config.params)}`;
      },
      ...config,
    };
  }

  /**
   * Get cached request if available
   */
  public get(config: AxiosRequestConfig): Promise<AxiosResponse> | null {
    if (!this.config.enabled) return null;

    const key = this.config.keyGenerator(config);
    const cached = this.cache.get(key);
    const timestamp = this.timestamps.get(key);

    if (cached && timestamp && Date.now() - timestamp < this.config.ttl) {
      return cached;
    }

    // Clean up expired entry
    if (cached) {
      this.cache.delete(key);
      this.timestamps.delete(key);
    }

    return null;
  }

  /**
   * Store request in cache
   */
  public set(config: AxiosRequestConfig, promise: Promise<AxiosResponse>): void {
    if (!this.config.enabled) return;

    const key = this.config.keyGenerator(config);
    this.cache.set(key, promise);
    this.timestamps.set(key, Date.now());

    // Clean up on completion (success or failure)
    promise.finally(() => {
      setTimeout(() => {
        this.cache.delete(key);
        this.timestamps.delete(key);
      }, this.config.ttl);
    });
  }

  /**
   * Clear cache
   */
  public clear(): void {
    this.cache.clear();
    this.timestamps.clear();
  }
}

/**
 * Enhanced Axios client with retry logic
 */
export class RetryableApiClient {
  private axiosInstance: AxiosInstance;
  private retryConfig: Required<RetryConfig>;
  private circuitBreaker: CircuitBreaker;
  private requestCache: RequestCache;

  constructor(
    axiosConfig: AxiosRequestConfig = {},
    retryConfig: RetryConfig = {},
    circuitBreakerConfig: CircuitBreakerConfig = {},
    deduplicationConfig: DeduplicationConfig = {}
  ) {
    this.axiosInstance = axios.create(axiosConfig);
    this.retryConfig = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
    this.circuitBreaker = new CircuitBreaker(circuitBreakerConfig);
    this.requestCache = new RequestCache(deduplicationConfig);

    this.setupInterceptors();
  }

  /**
   * Setup axios interceptors for retry logic
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Check circuit breaker
        if (!this.circuitBreaker.shouldAllowRequest()) {
          return Promise.reject(new Error('Circuit breaker is open'));
        }

        // Check for cached request
        const cached = this.requestCache.get(config);
        if (cached) {
          return Promise.reject({ __cached: true, promise: cached });
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      (response) => {
        this.circuitBreaker.recordSuccess();
        return response;
      },
      async (error) => {
        // Handle cached response
        if (error.__cached) {
          return error.promise;
        }

        const config = error.config;

        // Initialize retry count if not present
        if (!config.__retryCount) {
          config.__retryCount = 0;
        }

        // Check if we should retry
        if (
          config.__retryCount < this.retryConfig.maxRetries &&
          this.retryConfig.retryCondition(error)
        ) {
          config.__retryCount++;

          // Calculate delay with exponential backoff
          const delay = Math.min(
            this.retryConfig.initialDelay * Math.pow(this.retryConfig.backoffMultiplier, config.__retryCount - 1),
            this.retryConfig.maxDelay
          );

          // Call retry callback
          this.retryConfig.onRetry(config.__retryCount, error);

          // Wait before retrying
          await this.sleep(delay);

          // Reset timeout if needed
          if (this.retryConfig.shouldResetTimeout && config.timeout) {
            config.timeout = config.__originalTimeout || config.timeout;
          }

          // Retry the request
          return this.axiosInstance(config);
        }

        // Record failure in circuit breaker
        this.circuitBreaker.recordFailure();

        return Promise.reject(error);
      }
    );
  }

  /**
   * Sleep helper for delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Make GET request with retry
   */
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    const promise = this.axiosInstance.get<T>(url, config);
    this.requestCache.set({ ...config, method: 'GET', url }, promise);
    return promise;
  }

  /**
   * Make POST request with retry
   */
  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.post<T>(url, data, config);
  }

  /**
   * Make PUT request with retry
   */
  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.put<T>(url, data, config);
  }

  /**
   * Make DELETE request with retry
   */
  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.delete<T>(url, config);
  }

  /**
   * Make PATCH request with retry
   */
  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.patch<T>(url, data, config);
  }

  /**
   * Get circuit breaker state
   */
  public getCircuitState(): string {
    return this.circuitBreaker.getState();
  }

  /**
   * Reset circuit breaker
   */
  public resetCircuit(): void {
    this.circuitBreaker.reset();
  }

  /**
   * Clear request cache
   */
  public clearCache(): void {
    this.requestCache.clear();
  }

  /**
   * Update retry configuration
   */
  public updateRetryConfig(config: RetryConfig): void {
    this.retryConfig = { ...this.retryConfig, ...config };
  }

  /**
   * Get axios instance
   */
  public getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

/**
 * Create a singleton instance with default configuration
 */
export const retryableApi = new RetryableApiClient(
  {
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8009',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  },
  {
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
    retryCondition: (error) => {
      // Don't retry on 4xx errors (client errors)
      if (error.response && error.response.status >= 400 && error.response.status < 500) {
        return false;
      }
      return true;
    },
    onRetry: (retryCount, error) => {
      console.log(`API retry attempt ${retryCount} for ${error.config?.url}`);
    },
  },
  {
    enabled: true,
    failureThreshold: 5,
    resetTimeout: 60000,
    halfOpenRequests: 3,
  },
  {
    enabled: true,
    ttl: 5000,
  }
);

export default retryableApi;