import React, { Suspense, lazy } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Skeleton from '@mui/material/Skeleton';
import Alert from '@mui/material/Alert';

// Lazy load chart components
const UserActivityChart = lazy(() => import('../analytics/UserActivityChart'));

interface LazyChartProps {
  type: 'user-activity';
  height?: number;
  timeRange?: "24h" | "7d" | "30d" | "90d";
  autoRefresh?: boolean;
  fallbackHeight?: number;
}

// Enhanced loading skeleton for charts
const ChartSkeleton: React.FC<{ height: number }> = ({ height }) => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="text" width={200} height={32} sx={{ mb: 2 }} />
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
      <Skeleton variant="rectangular" width={120} height={40} />
      <Skeleton variant="rectangular" width={100} height={40} />
    </Box>
    <Skeleton variant="rectangular" width="100%" height={height - 120} />
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

export const LazyChart: React.FC<LazyChartProps> = ({
  type,
  height = 350,
  timeRange,
  autoRefresh,
  fallbackHeight = 350
}) => {
  const errorFallback = (
    <Alert severity="warning" sx={{ height: fallbackHeight, display: 'flex', alignItems: 'center' }}>
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