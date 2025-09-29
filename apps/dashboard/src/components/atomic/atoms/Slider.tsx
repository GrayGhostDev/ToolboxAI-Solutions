import React from 'react';

export interface SliderProps {
  value?: number;
  onChange?: (event: Event, value: number | number[]) => void;
  min?: number;
  max?: number;
}

const AtomicSlider = (({ ...props, ref }: HTMLInputElement, SliderProps & { ref?: React.Ref<any> }) => (
  <input ref={ref} type="range" {...props} />
));

AtomicSlider.displayName = 'AtomicSlider';

export default AtomicSlider;