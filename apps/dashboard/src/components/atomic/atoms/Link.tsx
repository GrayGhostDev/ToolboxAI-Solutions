/**
 * Atomic Link Component - Placeholder
 */

import React from 'react';

export interface LinkProps {
  href?: string;
  children?: React.ReactNode;
}

const AtomicLink = (({ ...props, ref }: HTMLAnchorElement, LinkProps & { ref?: React.Ref<any> }) => (
  <a ref={ref} {...props} />
));

AtomicLink.displayName = 'AtomicLink';

export default AtomicLink;