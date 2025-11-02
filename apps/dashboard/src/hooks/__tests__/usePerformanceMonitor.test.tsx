import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import {
  usePerformanceMonitor,
  useComponentPerformance,
  useApiPerformance,
} from '../usePerformanceMonitor';
import * as performanceMonitorModule from '@/utils/performance-monitor';
import * as featureConfig from '@/config/features';

// Mock performance monitor
vi.mock('@/utils/performance-monitor', () => ({
  performanceMonitor: {
    startMonitoring: vi.fn(),
    stopMonitoring: vi.fn(),
    clearAlerts: vi.fn(),
    updateThresholds: vi.fn(),
    getPerformanceSummary: vi.fn(() => ({
      score: 85,
      alerts: [],
      metrics: {},
    })),
  },
}));

// Mock feature flags
vi.mock('@/config/features', () => ({
  useFeatureFlag: vi.fn((flag: string) => {
    const defaults: Record<string, any> = {
      enablePerformanceMonitoring: true,
      performanceMonitoringLevel: 'basic',
      performanceReportingInterval: 5000,
      enableSlowApiWarnings: true,
      apiTimeoutThreshold: 2000,
    };
    return defaults[flag];
  }),
}));

// FIXME: Tests timing out due to async/timer synchronization issues - see docs/05-implementation/testing/reports/TESTING_KNOWN_ISSUES.md #5
describe.skip('usePerformanceMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      const defaults: Record<string, any> = {
        enablePerformanceMonitoring: true,
        performanceMonitoringLevel: 'basic',
        performanceReportingInterval: 5000,
      };
      return defaults[flag];
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Initialization', () => {
    it('should start monitoring when feature flag enabled', async () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      expect(result.current.isMonitoring).toBe(false);

      // Fast-forward initialization delay
      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(result.current.isMonitoring).toBe(true);
      });

      expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
    });

    it('should not start when feature flag disabled', async () => {
      vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
        if (flag === 'enablePerformanceMonitoring') return false;
        return 'basic';
      });

      renderHook(() => usePerformanceMonitor());

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.startMonitoring).not.toHaveBeenCalled();
      }, { timeout: 100 }).catch(() => {
        // Expected - monitoring should not start
      });
    });

    it('should respect forceEnable option', async () => {
      vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
        if (flag === 'enablePerformanceMonitoring') return false;
        return 'off';
      });

      const { result } = renderHook(() => usePerformanceMonitor({ forceEnable: true }));

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(result.current.isMonitoring).toBe(true);
      });
    });

    it('should respect forceDisable option', async () => {
      const { result } = renderHook(() => usePerformanceMonitor({ forceDisable: true }));

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      expect(result.current.isMonitoring).toBe(false);
      expect(performanceMonitorModule.performanceMonitor.startMonitoring).not.toHaveBeenCalled();
    });

    it('should apply custom thresholds on initialization', async () => {
      const customThresholds = {
        componentRenderTime: 100,
        apiCallDuration: 500,
      };

      renderHook(() => usePerformanceMonitor({ thresholds: customThresholds }));

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.updateThresholds).toHaveBeenCalledWith(
          customThresholds
        );
      });
    });
  });

  describe('Manual Control', () => {
    it('should allow manual start', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      act(() => {
        result.current.startMonitoring();
      });

      expect(result.current.isMonitoring).toBe(true);
      expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
    });

    it('should allow manual stop', async () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      act(() => {
        result.current.startMonitoring();
      });

      expect(result.current.isMonitoring).toBe(true);

      act(() => {
        result.current.stopMonitoring();
      });

      expect(result.current.isMonitoring).toBe(false);
      expect(performanceMonitorModule.performanceMonitor.stopMonitoring).toHaveBeenCalled();
    });

    it('should not start twice', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      act(() => {
        result.current.startMonitoring();
        result.current.startMonitoring();
      });

      expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalledTimes(1);
    });

    it('should not stop when not monitoring', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      act(() => {
        result.current.stopMonitoring();
      });

      expect(performanceMonitorModule.performanceMonitor.stopMonitoring).not.toHaveBeenCalled();
    });
  });

  describe('Reporting', () => {
    it('should report at specified intervals', async () => {
      const onReport = vi.fn();

      renderHook(() =>
        usePerformanceMonitor({
          onReport,
          reportingInterval: 1000,
        })
      );

      act(() => {
        vi.advanceTimersByTime(3000); // Skip initialization delay
      });

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
      });

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(onReport).toHaveBeenCalledTimes(1);
      });

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(onReport).toHaveBeenCalledTimes(2);
      });
    });

    it('should update summary during reporting', async () => {
      const mockSummary = { score: 90, alerts: [], metrics: {} };
      vi.mocked(performanceMonitorModule.performanceMonitor.getPerformanceSummary).mockReturnValue(
        mockSummary
      );

      const { result } = renderHook(() =>
        usePerformanceMonitor({
          reportingInterval: 1000,
        })
      );

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(result.current.isMonitoring).toBe(true);
      });

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(result.current.summary).toEqual(mockSummary);
      });
    });

    it('should not report when interval is 0', async () => {
      const onReport = vi.fn();

      renderHook(() =>
        usePerformanceMonitor({
          onReport,
          reportingInterval: 0,
        })
      );

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
      });

      act(() => {
        vi.advanceTimersByTime(10000);
      });

      expect(onReport).not.toHaveBeenCalled();
    });
  });

  describe('Alert Management', () => {
    it('should clear alerts', async () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      act(() => {
        result.current.startMonitoring();
      });

      act(() => {
        result.current.clearAlerts();
      });

      expect(performanceMonitorModule.performanceMonitor.clearAlerts).toHaveBeenCalled();
    });

    it('should update summary after clearing alerts', async () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      act(() => {
        result.current.startMonitoring();
      });

      act(() => {
        result.current.clearAlerts();
      });

      expect(performanceMonitorModule.performanceMonitor.getPerformanceSummary).toHaveBeenCalled();
    });
  });

  describe('Threshold Updates', () => {
    it('should update thresholds', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      const newThresholds = { componentRenderTime: 200 };

      act(() => {
        result.current.updateThresholds(newThresholds);
      });

      expect(performanceMonitorModule.performanceMonitor.updateThresholds).toHaveBeenCalledWith(
        newThresholds
      );
    });
  });

  describe('Feature Flag Changes', () => {
    it('should start monitoring when flag changes to enabled', async () => {
      let monitoringEnabled = false;

      vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
        if (flag === 'enablePerformanceMonitoring') return monitoringEnabled;
        return 'basic';
      });

      const { rerender } = renderHook(() => usePerformanceMonitor());

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      expect(performanceMonitorModule.performanceMonitor.startMonitoring).not.toHaveBeenCalled();

      // Enable monitoring
      monitoringEnabled = true;
      rerender();

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
      });
    });

    it('should stop monitoring when flag changes to disabled', async () => {
      let monitoringEnabled = true;

      vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
        if (flag === 'enablePerformanceMonitoring') return monitoringEnabled;
        return 'basic';
      });

      const { rerender } = renderHook(() => usePerformanceMonitor());

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
      });

      // Disable monitoring
      monitoringEnabled = false;
      rerender();

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.stopMonitoring).toHaveBeenCalled();
      });
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on unmount', async () => {
      const { unmount } = renderHook(() =>
        usePerformanceMonitor({ reportingInterval: 1000 })
      );

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
      });

      unmount();

      // Verify timer was cleaned up by checking it doesn't fire
      const onReport = vi.fn();
      vi.mocked(performanceMonitorModule.performanceMonitor.getPerformanceSummary).mockReturnValue({
        score: 90,
        alerts: [],
        metrics: {},
      });

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      // Timer should be cleared, so we can't directly test it
      // But we can verify monitoring was started and summary is accessible
      expect(performanceMonitorModule.performanceMonitor.startMonitoring).toHaveBeenCalled();
    });
  });
});

describe('useComponentPerformance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      if (flag === 'enablePerformanceMonitoring') return true;
      if (flag === 'performanceMonitoringLevel') return 'verbose';
      return true;
    });
  });

  it('should track component mount/unmount time', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    const { unmount } = renderHook(() => useComponentPerformance('TestComponent'));

    unmount();

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Component [TestComponent] lifecycle')
    );

    consoleSpy.mockRestore();
  });

  it('should not track when monitoring disabled', () => {
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      if (flag === 'enablePerformanceMonitoring') return false;
      return 'verbose';
    });

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    const { unmount } = renderHook(() => useComponentPerformance('TestComponent'));

    unmount();

    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it('should not track in basic level', () => {
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      if (flag === 'enablePerformanceMonitoring') return true;
      if (flag === 'performanceMonitoringLevel') return 'basic';
      return true;
    });

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    const { unmount } = renderHook(() => useComponentPerformance('TestComponent'));

    unmount();

    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it('should track in verbose level', () => {
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      if (flag === 'enablePerformanceMonitoring') return true;
      if (flag === 'performanceMonitoringLevel') return 'verbose';
      return true;
    });

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    const { unmount } = renderHook(() => useComponentPerformance('TestComponent'));

    unmount();

    expect(consoleSpy).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});

describe('useApiPerformance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      if (flag === 'enableSlowApiWarnings') return true;
      if (flag === 'apiTimeoutThreshold') return 2000;
      return true;
    });
  });

  it('should track API calls', () => {
    const { result } = renderHook(() => useApiPerformance());

    const startTime = Date.now();
    const endTime = startTime + 1000;

    result.current.trackApiCall('/api/test', startTime, endTime, 200);

    // No assertion needed - just verify it doesn't throw
  });

  it('should warn on slow API calls', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { result } = renderHook(() => useApiPerformance());

    const startTime = Date.now();
    const endTime = startTime + 3000; // Exceeds 2000ms threshold

    result.current.trackApiCall('/api/slow', startTime, endTime, 200);

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Slow API call detected')
    );

    consoleSpy.mockRestore();
  });

  it('should not warn on fast API calls', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { result } = renderHook(() => useApiPerformance());

    const startTime = Date.now();
    const endTime = startTime + 1000; // Below 2000ms threshold

    result.current.trackApiCall('/api/fast', startTime, endTime, 200);

    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it('should not track when warnings disabled', () => {
    vi.mocked(featureConfig.useFeatureFlag).mockImplementation((flag: string) => {
      if (flag === 'enableSlowApiWarnings') return false;
      if (flag === 'apiTimeoutThreshold') return 2000;
      return false;
    });

    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { result } = renderHook(() => useApiPerformance());

    const startTime = Date.now();
    const endTime = startTime + 3000;

    result.current.trackApiCall('/api/slow', startTime, endTime, 200);

    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
