import React from 'react';

export interface SwitchProps {
  checked?: boolean;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const AtomicSwitch = (({ ...props, ref }: HTMLInputElement, SwitchProps & { ref?: React.Ref<any> }) => (
  <input ref={ref} type="checkbox" role="switch" {...props} />
));

AtomicSwitch.displayName = 'AtomicSwitch';

export default AtomicSwitch;