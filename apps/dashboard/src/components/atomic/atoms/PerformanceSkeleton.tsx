import { Skeleton } from '@mantine/core';
import React from 'react';

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
  // Use Mantine's Skeleton directly - no need for styled components
  const animationProps = animate ? {} : { animate: false };

  const renderDashboardSkeleton = () => (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Skeleton height={40} width={200} {...animationProps} />
        <Skeleton height={36} width={120} {...animationProps} />
      </div>

      {/* Metrics cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} height={100} {...animationProps} />
        ))}
      </div>

      {/* Main content */}
      <Skeleton height={height} {...animationProps} />
    </div>
  );

  const renderCardSkeleton = () => (
    <div style={{ padding: 16 }}>
      <Skeleton height={24} width="60%" style={{ marginBottom: 8 }} {...animationProps} />
      <Skeleton height={16} width="40%" style={{ marginBottom: 16 }} {...animationProps} />
      <Skeleton height={height - 80} {...animationProps} />
    </div>
  );

  const renderListSkeleton = () => (
    <div>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', padding: 16, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
          <Skeleton height={40} circle style={{ marginRight: 16 }} {...animationProps} />
          <div style={{ flex: 1 }}>
            <Skeleton height={20} width="70%" {...animationProps} />
            <Skeleton height={16} width="50%" {...animationProps} />
          </div>
          <Skeleton height={24} width={60} {...animationProps} />
        </div>
      ))}
    </div>
  );

  const renderChartSkeleton = () => (
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Skeleton height={24} width={150} {...animationProps} />
        <div style={{ display: 'flex', gap: 8 }}>
          <Skeleton height={32} width={80} {...animationProps} />
          <Skeleton height={32} width={80} {...animationProps} />
        </div>
      </div>
      <Skeleton height={height - 80} {...animationProps} />
    </div>
  );

  const renderNavigationSkeleton = () => (
    <div style={{ padding: 8 }}>
      {Array.from({ length: count || 6 }).map((_, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', padding: 12, marginBottom: 4 }}>
          <Skeleton height={20} width={20} style={{ marginRight: 16 }} {...animationProps} />
          <Skeleton height={20} width="80%" {...animationProps} />
        </div>
      ))}
    </div>
  );

  const renderFormSkeleton = () => (
    <div style={{ padding: 16 }}>
      {Array.from({ length: count || 4 }).map((_, i) => (
        <div key={i} style={{ marginBottom: 24 }}>
          <Skeleton height={20} width="30%" style={{ marginBottom: 8 }} {...animationProps} />
          <Skeleton height={40} {...animationProps} />
        </div>
      ))}
    </div>
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
      return <Skeleton height={height} {...animationProps} />;
  }
};

export default PerformanceSkeleton;