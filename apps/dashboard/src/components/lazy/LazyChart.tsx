import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import React, { Suspense, lazy } from 'react';

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
const ChartSkeleton = ({ height }: { height: number }) => (
  <Box style={{ p: 2 }}>
    <Skeleton variant="text" width={200} height={32} style={{ mb: 2 }} />
    <Box style={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
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

export const LazyChart = ({
  type,
  height = 350,
  timeRange,
  autoRefresh,
  fallbackHeight = 350
}: LazyChartProps) => {
  const errorFallback = (
    <Alert severity="warning" style={{ height: fallbackHeight, display: 'flex', alignItems: 'center' }}>
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