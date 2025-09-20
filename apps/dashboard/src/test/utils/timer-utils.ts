/**
 * Timer Utilities for Test Environment
 * Provides centralized timer mock management to prevent conflicts
 */

import { vi } from 'vitest';

/**
 * Configuration options for timer mocking
 */
export interface TimerConfig {
  /** Whether to include performance.now() in mocks */
  includePerformance?: boolean;
  /** Whether time should automatically advance */
  shouldAdvanceTime?: boolean;
  /** Custom list of timer methods to fake */
  toFake?: string[];
}

/**
 * Default timer configuration for most tests
 */
const DEFAULT_CONFIG: TimerConfig = {
  includePerformance: false,
  shouldAdvanceTime: true,
  toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date']
};

/**
 * Performance test timer configuration
 */
const PERFORMANCE_CONFIG: TimerConfig = {
  includePerformance: true,
  shouldAdvanceTime: false,
  toFake: [
    'setTimeout',
    'clearTimeout',
    'setInterval',
    'clearInterval',
    'Date',
    'performance'
  ]
};

/**
 * Track current timer state to prevent conflicts
 */
let currentTimerState: 'real' | 'fake' | 'uninitialized' = 'uninitialized';

/**
 * Setup fake timers with proper configuration
 */
export function setupFakeTimers(config: TimerConfig = {}): void {
  // If timers are already fake, restore them first to prevent conflicts
  if (currentTimerState === 'fake') {
    vi.useRealTimers();
  }

  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  vi.useFakeTimers({
    shouldAdvanceTime: finalConfig.shouldAdvanceTime,
    toFake: finalConfig.toFake as any
  });

  currentTimerState = 'fake';
}

/**
 * Setup fake timers specifically for performance tests
 */
export function setupPerformanceTimers(): void {
  setupFakeTimers(PERFORMANCE_CONFIG);
}

/**
 * Restore real timers
 */
export function restoreRealTimers(): void {
  if (currentTimerState === 'fake') {
    vi.useRealTimers();
    currentTimerState = 'real';
  }
}

/**
 * Run all pending timers and clear them
 */
export function cleanupTimers(): void {
  if (currentTimerState === 'fake') {
    vi.runOnlyPendingTimers();
    vi.clearAllTimers();
  }
}

/**
 * Advance timers by a specific amount
 */
export function advanceTimersByTime(ms: number): void {
  if (currentTimerState === 'fake') {
    vi.advanceTimersByTime(ms);
  }
}

/**
 * Run all timers until there are none left
 */
export function runAllTimers(): void {
  if (currentTimerState === 'fake') {
    vi.runAllTimers();
  }
}

/**
 * Get current timer state
 */
export function getTimerState(): 'real' | 'fake' | 'uninitialized' {
  return currentTimerState;
}

/**
 * Helper to run async code with fake timers
 */
export async function withFakeTimers<T>(
  fn: () => Promise<T>,
  config?: TimerConfig
): Promise<T> {
  setupFakeTimers(config);
  try {
    const result = await fn();
    return result;
  } finally {
    restoreRealTimers();
  }
}

/**
 * Helper to run performance tests with proper timer setup
 */
export async function withPerformanceTimers<T>(
  fn: () => Promise<T>
): Promise<T> {
  return withFakeTimers(fn, PERFORMANCE_CONFIG);
}

/**
 * Reset timer state (for use in global setup/teardown)
 */
export function resetTimerState(): void {
  currentTimerState = 'uninitialized';
}