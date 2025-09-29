import React from 'react';

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
}

const AtomicDivider = (({ ...props, ref }: HTMLHRElement, DividerProps & { ref?: React.Ref<any> }) => (
  <hr ref={ref} {...props} />
));

AtomicDivider.displayName = 'AtomicDivider';

export default AtomicDivider;