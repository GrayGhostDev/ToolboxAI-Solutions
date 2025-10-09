import { Box, Alert, Skeleton } from '@mantine/core';
import React, { Suspense, lazy } from 'react';

// Lazy load chart components
const UserActivityChart = lazy(() => import('../analytics/UserActivityChart'));

interface LazyChartProps {
  type: 'user-activity';
  height?: number;
  timeRange?: '24h' | '7d' | '30d' | '90d';
  autoRefresh?: boolean;
  fallbackHeight?: number;
}

// Enhanced loading skeleton for charts
const ChartSkeleton = ({ height }: { height: number }) => (
  <Box p="md">
    <Skeleton height={32} width={200} mb="md" />
    <Box style={{ display: 'flex', justifyContent: 'space-between' }} mb="md">
      <Skeleton height={40} width={120} />
      <Skeleton height={40} width={100} />
    </Box>
    <Skeleton height={height - 120} width="100%" />
  </Box>
);

// Error boundary for chart loading
class ChartErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Chart loading error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

export const LazyChart = ({
  type,
  height = 350,
  timeRange,
  autoRefresh,
  fallbackHeight = 350
}: LazyChartProps) => {
  const errorFallback = (
    <Alert color="yellow" variant="light" style={{ height: fallbackHeight, display: 'flex', alignItems: 'center' }}>
      Chart temporarily unavailable. Please refresh the page.
    </Alert>
  );

  const loadingFallback = <ChartSkeleton height={fallbackHeight} />;

  if (type === 'user-activity') {
    return (
      <ChartErrorBoundary fallback={errorFallback}>
        <Suspense fallback={loadingFallback}>
          <UserActivityChart
            height={height}
            timeRange={timeRange}
            autoRefresh={autoRefresh}
          />
        </Suspense>
      </ChartErrorBoundary>
    );
  }

  return errorFallback;
};

export default LazyChart;