/**
 * SearchBar Molecule - Placeholder
 */

import React from 'react';

export interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
}

const SearchBar = React.forwardRef<HTMLDivElement, SearchBarProps>((props, ref) => (
  <div ref={ref} {...props}>SearchBar Component</div>
));

SearchBar.displayName = 'SearchBar';

export default SearchBar;