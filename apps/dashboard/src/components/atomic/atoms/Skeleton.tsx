import React from 'react';

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'rectangular' | 'circular';
}

const AtomicSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(({ width, height, variant = 'text', ...props }, ref) => (
  <div ref={ref} style={{ width, height, backgroundColor: '#e0e0e0', borderRadius: variant === 'circular' ? '50%' : '4px' }} {...props} />
));

AtomicSkeleton.displayName = 'AtomicSkeleton';

export default AtomicSkeleton;