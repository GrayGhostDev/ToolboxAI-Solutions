/**
 * Lazy loading wrapper for chart components
 *
 * Reduces initial bundle size by lazy loading charts when needed.
 * Supports both Recharts and Chart.js with unified interface.
 */

import React, { Suspense, lazy } from 'react';
import { Box, CircularProgress, Typography, Skeleton } from '@mui/material';

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
    display="flex"
    flexDirection="column"
    gap={1}
    p={2}
    height={height}
    border="1px solid"
    borderColor="divider"
    borderRadius={1}
    bgcolor="background.paper"
  >
    {/* Chart title skeleton */}
    <Skeleton variant="text" width="60%" height={24} />

    {/* Chart area skeleton */}
    <Box flex={1} display="flex" alignItems="flex-end" gap={1}>
      {variant === 'line' && (
        <>
          <Skeleton variant="rectangular" width="100%" height="80%" />
        </>
      )}
      {variant === 'bar' && (
        <>
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton
              key={i}
              variant="rectangular"
              width="10%"
              height={`${Math.random() * 60 + 20}%`}
            />
          ))}
        </>
      )}
      {variant === 'pie' && (
        <Box display="flex" alignItems="center" justifyContent="center" width="100%">
          <Skeleton variant="circular" width={200} height={200} />
        </Box>
      )}
    </Box>

    {/* Legend skeleton */}
    <Box display="flex" gap={2} justifyContent="center">
      {Array.from({ length: 3 }, (_, i) => (
        <Box key={i} display="flex" alignItems="center" gap={1}>
          <Skeleton variant="rectangular" width={12} height={12} />
          <Skeleton variant="text" width={60} />
        </Box>
      ))}
    </Box>
  </Box>
);

// Loading fallback component
const ChartLoadingFallback = ({
  message = "Loading chart...",
  height = 300,
  variant = 'line'
}: {
  message?: string;
  height?: number;
  variant?: 'line' | 'bar' | 'pie';
}) => (
  <Box position="relative">
    <ChartSkeleton height={height} variant={variant} />
    <Box
      position="absolute"
      top={0}
      left={0}
      right={0}
      bottom={0}
      display="flex"
      alignItems="center"
      justifyContent="center"
      bgcolor="rgba(255, 255, 255, 0.8)"
      backdropFilter="blur(2px)"
    >
      <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
        <CircularProgress size={24} />
        <Typography variant="caption" color="text.secondary">
          {message}
        </Typography>
      </Box>
    </Box>
  </Box>
);

// Error fallback component
const ChartErrorFallback = ({ error }: { error?: Error }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    minHeight={300}
    gap={2}
    bgcolor="warning.light"
    borderRadius={1}
    p={3}
    border="1px solid"
    borderColor="warning.main"
  >
    <Typography variant="h6" color="warning.dark">
      Chart Unavailable
    </Typography>
    <Typography variant="body2" color="text.secondary" textAlign="center">
      {error?.message || "Unable to load chart. Please try refreshing the page."}
    </Typography>
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
  data?: any[];
  timeRange?: string;
}

interface LazyPerformanceIndicatorProps extends LazyChartProps {
  metrics?: any;
}

interface LazyContentMetricsProps extends LazyChartProps {
  contentType?: string;
  dateRange?: { start: Date; end: Date };
}

// Lazy UserActivityChart component
export const LazyUserActivityChart = ({
  data,
  timeRange,
  fallback,
  loadingMessage = "Loading activity chart...",
  height = 300,
  variant = 'line'
}: LazyUserActivityChartProps) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        <UserActivityChart data={data} timeRange={timeRange} />
      </Suspense>
    </ChartErrorBoundary>
  );
};

// Lazy PerformanceIndicator component
export const LazyPerformanceIndicator = ({
  metrics,
  fallback,
  loadingMessage = "Loading performance metrics...",
  height = 300,
  variant = 'bar'
}: LazyPerformanceIndicatorProps) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        <PerformanceIndicator metrics={metrics} />
      </Suspense>
    </ChartErrorBoundary>
  );
};

// Lazy ContentMetrics component
export const LazyContentMetrics = ({
  contentType,
  dateRange,
  fallback,
  loadingMessage = "Loading content metrics...",
  height = 300,
  variant = 'pie'
}: LazyContentMetricsProps) => {
  return (
    <ChartErrorBoundary fallback={fallback}>
      <Suspense fallback={<ChartLoadingFallback message={loadingMessage} height={height} variant={variant} />}>
        <ContentMetrics contentType={contentType} dateRange={dateRange} />
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
  loadingMessage = "Loading chart...",
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