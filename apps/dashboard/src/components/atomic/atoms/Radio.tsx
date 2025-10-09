import React from 'react';

export interface RadioProps {
  checked?: boolean;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  value?: string;
}

const AtomicRadio = React.forwardRef<HTMLInputElement, RadioProps>((props, ref) => (
  <input ref={ref} type="radio" {...props} />
));

AtomicRadio.displayName = 'AtomicRadio';

export default AtomicRadio;