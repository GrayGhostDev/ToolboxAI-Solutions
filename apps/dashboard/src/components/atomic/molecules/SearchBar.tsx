/**
 * SearchBar Molecule - Placeholder
 */

import React from 'react';

export interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
}

const AtomicSearchBar = React.forwardRef<HTMLDivElement, SearchBarProps>((props, ref) => (
  <div ref={ref} {...props}>SearchBar Component</div>
));

AtomicSearchBar.displayName = 'AtomicSearchBar';

export default AtomicSearchBar;