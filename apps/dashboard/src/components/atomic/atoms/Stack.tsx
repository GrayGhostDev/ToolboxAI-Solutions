import React from 'react';

export interface StackProps {
  direction?: 'row' | 'column';
  spacing?: number;
  children?: React.ReactNode;
}

const AtomicStack = React.forwardRef<HTMLDivElement, StackProps>(({ direction = 'column', spacing = 8, children, ...props }, ref) => (
  <div 
    ref={ref} 
    style={{ 
      display: 'flex', 
      flexDirection: direction, 
      gap: `${spacing}px` 
    }} 
    {...props}
  >
    {children}
  </div>
));

AtomicStack.displayName = 'AtomicStack';

export default AtomicStack;