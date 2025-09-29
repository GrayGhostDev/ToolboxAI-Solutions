/**
 * Atomic Image Component - Placeholder
 */

import React from 'react';

export interface ImageProps {
  src?: string;
  alt?: string;
}

const AtomicImage = (({ ...props, ref }: HTMLImageElement, ImageProps & { ref?: React.Ref<any> }) => (
  <img ref={ref} {...props} />
));

AtomicImage.displayName = 'AtomicImage';

export default AtomicImage;