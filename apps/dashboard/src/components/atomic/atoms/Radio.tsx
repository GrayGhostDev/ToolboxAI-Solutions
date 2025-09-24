import React from 'react';

export interface RadioProps {
  checked?: boolean;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  value?: string;
}

const AtomicRadio = (({ ...props, ref }: HTMLInputElement, RadioProps & { ref?: React.Ref<any> }) => (
  <input ref={ref} type="radio" {...props} />
));

AtomicRadio.displayName = 'AtomicRadio';

export default AtomicRadio;