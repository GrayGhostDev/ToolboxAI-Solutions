import React from 'react';
import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';
import { styled } from '@mui/material/styles';

// Optimized skeleton with reduced animation for better performance
const OptimizedSkeleton = styled(Skeleton)(({ theme }) => ({
  '&::after': {
    animationDuration: '2s', // Slower animation for better performance
  },
  backgroundColor: theme.palette.mode === 'dark'
    ? 'rgba(255, 255, 255, 0.08)'
    : 'rgba(0, 0, 0, 0.08)',
}));

interface PerformanceSkeletonProps {
  variant: 'dashboard' | 'card' | 'list' | 'chart' | 'navigation' | 'form';
  height?: number;
  count?: number;
  animate?: boolean;
}

export const PerformanceSkeleton: React.FC<PerformanceSkeletonProps> = ({
  variant,
  height = 200,
  count = 1,
  animate = true
}) => {
  const SkeletonComponent = animate ? OptimizedSkeleton : Skeleton;
  const animationProps = animate ? {} : { animation: false as const };

  const renderDashboardSkeleton = () => (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <SkeletonComponent variant="text" width={200} height={40} {...animationProps} />
        <SkeletonComponent variant="rectangular" width={120} height={36} {...animationProps} />
      </Box>

      {/* Metrics cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 3 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonComponent key={i} variant="rectangular" height={100} {...animationProps} />
        ))}
      </Box>

      {/* Main content */}
      <SkeletonComponent variant="rectangular" height={height} {...animationProps} />
    </Box>
  );

  const renderCardSkeleton = () => (
    <Box sx={{ p: 2 }}>
      <SkeletonComponent variant="text" width="60%" height={24} sx={{ mb: 1 }} {...animationProps} />
      <SkeletonComponent variant="text" width="40%" height={16} sx={{ mb: 2 }} {...animationProps} />
      <SkeletonComponent variant="rectangular" height={height - 80} {...animationProps} />
    </Box>
  );

  const renderListSkeleton = () => (
    <Box>
      {Array.from({ length: count }).map((_, i) => (
        <Box key={i} sx={{ display: 'flex', alignItems: 'center', p: 2, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
          <SkeletonComponent variant="circular" width={40} height={40} sx={{ mr: 2 }} {...animationProps} />
          <Box sx={{ flex: 1 }}>
            <SkeletonComponent variant="text" width="70%" height={20} {...animationProps} />
            <SkeletonComponent variant="text" width="50%" height={16} {...animationProps} />
          </Box>
          <SkeletonComponent variant="rectangular" width={60} height={24} {...animationProps} />
        </Box>
      ))}
    </Box>
  );

  const renderChartSkeleton = () => (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <SkeletonComponent variant="text" width={150} height={24} {...animationProps} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <SkeletonComponent variant="rectangular" width={80} height={32} {...animationProps} />
          <SkeletonComponent variant="rectangular" width={80} height={32} {...animationProps} />
        </Box>
      </Box>
      <SkeletonComponent variant="rectangular" height={height - 80} {...animationProps} />
    </Box>
  );

  const renderNavigationSkeleton = () => (
    <Box sx={{ p: 1 }}>
      {Array.from({ length: count || 6 }).map((_, i) => (
        <Box key={i} sx={{ display: 'flex', alignItems: 'center', p: 1.5, mb: 0.5 }}>
          <SkeletonComponent variant="rectangular" width={20} height={20} sx={{ mr: 2 }} {...animationProps} />
          <SkeletonComponent variant="text" width="80%" height={20} {...animationProps} />
        </Box>
      ))}
    </Box>
  );

  const renderFormSkeleton = () => (
    <Box sx={{ p: 2 }}>
      {Array.from({ length: count || 4 }).map((_, i) => (
        <Box key={i} sx={{ mb: 3 }}>
          <SkeletonComponent variant="text" width="30%" height={20} sx={{ mb: 1 }} {...animationProps} />
          <SkeletonComponent variant="rectangular" height={56} {...animationProps} />
        </Box>
      ))}
      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <SkeletonComponent variant="rectangular" width={120} height={36} {...animationProps} />
        <SkeletonComponent variant="rectangular" width={100} height={36} {...animationProps} />
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
      return <SkeletonComponent variant="rectangular" height={height} {...animationProps} />;
  }
};

export default PerformanceSkeleton;