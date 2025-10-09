/**
 * Atomic Checkbox Component - Placeholder
 */

import React from 'react';

export interface CheckboxProps {
  checked?: boolean;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const AtomicCheckbox = React.forwardRef<HTMLInputElement, CheckboxProps>((props, ref) => (
  <input ref={ref} type="checkbox" {...props} />
));

AtomicCheckbox.displayName = 'AtomicCheckbox';

export default AtomicCheckbox;