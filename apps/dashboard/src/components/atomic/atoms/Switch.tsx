import React from 'react';

export interface SwitchProps {
  checked?: boolean;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const AtomicSwitch = React.forwardRef<HTMLInputElement, SwitchProps>((props, ref) => (
  <input ref={ref} type="checkbox" role="switch" {...props} />
));

AtomicSwitch.displayName = 'AtomicSwitch';

export default AtomicSwitch;