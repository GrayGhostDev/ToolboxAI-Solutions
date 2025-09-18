/**
 * Atomic Image Component - Placeholder
 */

import React from 'react';

export interface ImageProps {
  src?: string;
  alt?: string;
}

const AtomicImage = React.forwardRef<HTMLImageElement, ImageProps>((props, ref) => (
  <img ref={ref} {...props} />
));

AtomicImage.displayName = 'AtomicImage';

export default AtomicImage;