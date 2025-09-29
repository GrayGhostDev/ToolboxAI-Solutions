import React from 'react';

export interface GridProps {
  columns?: number;
  gap?: number;
  children?: React.ReactNode;
}

const AtomicGrid = React.forwardRef<HTMLDivElement, GridProps>(({ columns = 1, gap = 16, children, ...props }, ref) => (
  <div 
    ref={ref} 
    style={{ 
      display: 'grid', 
      gridTemplateColumns: `repeat(${columns}, 1fr)`, 
      gap: `${gap}px` 
    }} 
    {...props}
  >
    {children}
  </div>
));

AtomicGrid.displayName = 'AtomicGrid';

export default AtomicGrid;