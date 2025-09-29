/**
 * SearchBar Molecule - Placeholder
 */

import React from 'react';

export interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
}

const SearchBar = (({ ...props, ref }: HTMLDivElement, SearchBarProps & { ref?: React.Ref<any> }) => (
  <div ref={ref} {...props}>SearchBar Component</div>
));

SearchBar.displayName = 'SearchBar';

export default SearchBar;