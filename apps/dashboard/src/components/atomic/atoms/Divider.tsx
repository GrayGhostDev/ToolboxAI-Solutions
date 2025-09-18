import React from 'react';

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
}

const AtomicDivider = React.forwardRef<HTMLHRElement, DividerProps>((props, ref) => (
  <hr ref={ref} {...props} />
));

AtomicDivider.displayName = 'AtomicDivider';

export default AtomicDivider;