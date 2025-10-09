import { Box, Loader, Text, Title, Skeleton, Group } from '@mantine/core';
/**
 * Lazy loading wrapper for chart components
 *
 * Reduces initial bundle size by lazy loading charts when needed.
 * Supports both Recharts and Chart.js with unified interface.
 */

import React, { Suspense, lazy } from 'react';

// Lazy load chart components - these will be in separate chunks
const UserActivityChart = lazy(() => import('../analytics/UserActivityChart'));
const PerformanceIndicator = lazy(() => import('../analytics/PerformanceIndicator'));
const ContentMetrics = lazy(() => import('../analytics/ContentMetrics'));

// Chart skeleton component for better UX
const ChartSkeleton = ({
  height = 300,
  variant = 'line'
}: { height?: number; variant?: 'line' | 'bar' | 'pie' }) => (
  <Box
    style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      padding: 16,
      height,
      border: '1px solid var(--mantine-color-gray-3)',
      borderRadius: 'var(--mantine-radius-md)',
      backgroundColor: 'var(--mantine-color-gray-0)',
    }}
  >
    {/* Chart title skeleton */}
    <Skeleton height={24} width="60%" />

    {/* Chart area skeleton */}
    <Box style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: 8 }}>
      {variant === 'line' && (
        <>
          <Skeleton height="80%" width="100%" />
        </>
      )}
      {variant === 'bar' && (
        <>
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton
              key={i}
              height={`${Math.random() * 60 + 20}%`}
              width="10%"
            />
          ))}
        </>
      )}
      {variant === 'pie' && (
        <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          <Skeleton height={200} width={200} circle />
        </Box>
      )}
    </Box>

    {/* Legend skeleton */}
    <Group justify="center" spacing="md">
      {Array.from({ length: 3 }, (_, i) => (
        <Group key={i} spacing="xs" align="center">
          <Skeleton height={12} width={12} />
          <Skeleton height={16} width={60} />
        </Group>
      ))}
    </Group>
  </Box>
);

// Loading fallback component
const ChartLoadingFallback = ({
  message = 'Loading chart...',
  height = 300,
  variant = 'line'
}: {
  message?: string;
  height?: number;
  variant?: 'line' | 'bar' | 'pie';
}) => (
  <Box style={{ position: 'relative' }}>
    <ChartSkeleton height={height} variant={variant} />
    <Box
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(2px)',
      }}
    >
      <Box
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <Loader size="sm" />
        <Text size="xs" c="dimmed">
          {message}
        </Text>
      </Box>
    </Box>
  </Box>
);

// Error fallback component
const ChartErrorFallback = ({ error }: { error?: Error }) => (
  <Box
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 300,
      gap: 16,
      backgroundColor: 'var(--mantine-color-yellow-0)',
      borderRadius: 'var(--mantine-radius-md)',
      padding: 24,
      border: '1px solid var(--mantine-color-yellow-3)',
    }}
  >
    <Title order={6} c="orange">
      Chart Unavailable
    </Title>
    <Text size="sm" c="dimmed" ta="center">
      {error?.message || 'Unable to load chart. Please try refreshing the page.'}
    </Text>
  </Box>
);

// Error boundary for chart components
class ChartErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{ error?: Error }> },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('Chart component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || ChartErrorFallback;
      return <FallbackComponent error={this.state.error} />;
    }

    return this.props.children;
  }
}

// Props interfaces
interface LazyChartProps {
  fallback?: React.ComponentType;
  loadingMessage?: string;
  height?: number;
  variant?: 'line' | 'bar' | 'pie';
}

interface LazyUserActivityChartProps extends LazyChartProps {
  timeRange?: '30d' | '24h' | '7d' | '90d';
}

interface LazyPerformanceIndicatorProps extends LazyChartProps {
  showSystemHealth?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface LazyContentMetricsProps extends LazyChartProps {
  timeRange?: '24h' | '7d' | '30d' | '90d';
  autoRefresh?: boolean;
}

// Lazy UserActivityChart component
export const LazyUserActivityChart = ({
  timeRange,
  fallback,
  loadingMessage = 'Loading activity chart...',
  height = 300,
  variant = 'line'
}: LazyUserActivityChartProps) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        <UserActivityChart timeRange={timeRange as '30d' | '24h' | '7d' | '90d'} />
      </Suspense>
    </ChartErrorBoundary>
  );
};

// Lazy PerformanceIndicator component
export const LazyPerformanceIndicator = ({
  showSystemHealth,
  autoRefresh,
  refreshInterval,
  fallback,
  loadingMessage = 'Loading performance metrics...',
  height = 300,
  variant = 'bar'
}: LazyPerformanceIndicatorProps) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        <PerformanceIndicator
          showSystemHealth={showSystemHealth}
          autoRefresh={autoRefresh}
          refreshInterval={refreshInterval}
        />
      </Suspense>
    </ChartErrorBoundary>
  );
};

// Lazy ContentMetrics component
export const LazyContentMetrics = ({
  timeRange,
  autoRefresh,
  fallback,
  loadingMessage = 'Loading content metrics...',
  height = 300,
  variant = 'pie'
}: LazyContentMetricsProps) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        <ContentMetrics
          timeRange={timeRange}
          autoRefresh={autoRefresh}
        />
      </Suspense>
    </ChartErrorBoundary>
  );
};

// Preload chart components when user is likely to need them
export const preloadCharts = () => {
  // Preload the components without rendering them
  import('../analytics/UserActivityChart');
  import('../analytics/PerformanceIndicator');
  import('../analytics/ContentMetrics');
};

// Hook for conditional chart preloading
export const useChartsPreloader = (shouldPreload: boolean = false) => {
  React.useEffect(() => {
    if (shouldPreload) {
      // Preload on user interaction or route change
      const timeoutId = setTimeout(preloadCharts, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [shouldPreload]);
};

// Generic lazy chart wrapper for custom charts
export const LazyChart = ({
  children,
  fallback,
  loadingMessage = 'Loading chart...',
  height = 300,
  variant = 'line'
}: {
  children: React.ReactNode;
  fallback?: React.ComponentType;
  loadingMessage?: string;
  height?: number;
  variant?: 'line' | 'bar' | 'pie';
}) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        {children}
      </Suspense>
    </ChartErrorBoundary>
  );
};

export default LazyUserActivityChart;