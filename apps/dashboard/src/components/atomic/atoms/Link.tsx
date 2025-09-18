/**
 * Atomic Link Component - Placeholder
 */

import React from 'react';

export interface LinkProps {
  href?: string;
  children?: React.ReactNode;
}

const AtomicLink = React.forwardRef<HTMLAnchorElement, LinkProps>((props, ref) => (
  <a ref={ref} {...props} />
));

AtomicLink.displayName = 'AtomicLink';

export default AtomicLink;