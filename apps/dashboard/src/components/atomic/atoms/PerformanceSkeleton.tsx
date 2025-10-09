import { Box, Skeleton, useMantineTheme } from '@mantine/core';
import React, { useEffect, useState } from 'react';

interface PerformanceSkeletonProps {
  variant: 'dashboard' | 'card' | 'list' | 'chart' | 'navigation' | 'form';
  height?: number;
  count?: number;
  animate?: boolean;
}

export const PerformanceSkeleton = ({
  variant,
  height = 200,
  count = 1,
  animate = true
}: PerformanceSkeletonProps) => {
  const theme = useMantineTheme();
  const [loaded, setLoaded] = useState(false);

  // Progressive enhancement - start showing content immediately
  useEffect(() => {
    const timer = setTimeout(() => setLoaded(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Optimized skeleton styles for faster rendering
  const skeletonStyles = {
    '--skeleton-animation-duration': animate ? '1.5s' : '0s',
    backgroundColor: theme.colorScheme === 'dark'
      ? 'rgba(255, 255, 255, 0.08)'
      : 'rgba(0, 0, 0, 0.06)',
    borderRadius: '6px',
    transform: loaded ? 'scale(1)' : 'scale(0.98)',
    transition: 'transform 0.2s ease',
  };

  const SkeletonComponent = ({ children, ...props }: any) => (
    <Skeleton animate={animate} style={skeletonStyles} {...props}>
      {children}
    </Skeleton>
  );

  const renderDashboardSkeleton = () => (
    <Box p="md" style={{ opacity: loaded ? 1 : 0.7, transition: 'opacity 0.3s ease' }}>
      {/* Header - faster loading with simplified structure */}
      <Box style={{ display: 'flex', justifyContent: 'space-between', marginBottom: theme.spacing.md }}>
        <SkeletonComponent width={200} height={32} />
        <SkeletonComponent width={100} height={32} />
      </Box>

      {/* Metrics cards - fewer items for faster perception */}
      <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonComponent key={i} height={80} />
        ))}
      </Box>

      {/* Main content - reduced height for faster perception */}
      <SkeletonComponent height={Math.min(height, 300)} />
    </Box>
  );

  const renderCardSkeleton = () => (
    <Box p="xs">
      <SkeletonComponent width="60%" height={24} style={{ marginBottom: theme.spacing.xs }} />
      <SkeletonComponent width="40%" height={16} style={{ marginBottom: theme.spacing.sm }} />
      <SkeletonComponent height={height - 80} />
    </Box>
  );

  const renderListSkeleton = () => (
    <Box>
      {Array.from({ length: count }).map((_, i) => (
        <Box key={i} style={{ display: 'flex', alignItems: 'center', padding: theme.spacing.sm, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
          <SkeletonComponent circle width={40} height={40} style={{ marginRight: theme.spacing.sm }} />
          <Box style={{ flex: 1 }}>
            <SkeletonComponent width="70%" height={20} />
            <SkeletonComponent width="50%" height={16} />
          </Box>
          <SkeletonComponent width={60} height={24} />
        </Box>
      ))}
    </Box>
  );

  const renderChartSkeleton = () => (
    <Box p="xs">
      <Box style={{ display: 'flex', justifyContent: 'space-between', marginBottom: theme.spacing.sm }}>
        <SkeletonComponent width={150} height={24} />
        <Box style={{ display: 'flex', gap: theme.spacing.xs }}>
          <SkeletonComponent width={80} height={32} />
          <SkeletonComponent width={80} height={32} />
        </Box>
      </Box>
      <SkeletonComponent height={height - 80} />
    </Box>
  );

  const renderNavigationSkeleton = () => (
    <Box p="xs">
      {Array.from({ length: count || 6 }).map((_, i) => (
        <Box key={i} style={{ display: 'flex', alignItems: 'center', padding: theme.spacing.xs, marginBottom: theme.spacing.xs }}>
          <SkeletonComponent width={20} height={20} style={{ marginRight: theme.spacing.sm }} />
          <SkeletonComponent width="80%" height={20} />
        </Box>
      ))}
    </Box>
  );

  const renderFormSkeleton = () => (
    <Box p="xs">
      {Array.from({ length: count || 4 }).map((_, i) => (
        <Box key={i} style={{ marginBottom: theme.spacing.md }}>
          <SkeletonComponent width="30%" height={20} style={{ marginBottom: theme.spacing.xs }} />
          <SkeletonComponent height={56} />
        </Box>
      ))}
      <Box style={{ display: 'flex', gap: theme.spacing.sm, marginTop: theme.spacing.md }}>
        <SkeletonComponent width={120} height={36} />
        <SkeletonComponent width={100} height={36} />
      </Box>
    </Box>
  );

  switch (variant) {
    case 'dashboard':
      return renderDashboardSkeleton();
    case 'card':
      return renderCardSkeleton();
    case 'list':
      return renderListSkeleton();
    case 'chart':
      return renderChartSkeleton();
    case 'navigation':
      return renderNavigationSkeleton();
    case 'form':
      return renderFormSkeleton();
    default:
      return <SkeletonComponent height={height} />;
  }
};

export default PerformanceSkeleton;