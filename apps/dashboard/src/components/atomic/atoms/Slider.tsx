import React from 'react';

export interface SliderProps {
  value?: number;
  onChange?: (event: Event, value: number | number[]) => void;
  min?: number;
  max?: number;
}

const AtomicSlider = React.forwardRef<HTMLInputElement, SliderProps>((props, ref) => (
  <input ref={ref} type="range" {...props} />
));

AtomicSlider.displayName = 'AtomicSlider';

export default AtomicSlider;