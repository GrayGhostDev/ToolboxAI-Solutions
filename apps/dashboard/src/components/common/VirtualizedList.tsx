import React, { memo, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import Box, { BoxProps } from '@mui/material/Box';

export interface VirtualizedListItem {
  id: string | number;
  [key: string]: any;
}

export interface VirtualizedListProps extends BoxProps {
  items: VirtualizedListItem[];
  itemHeight: number;
  height: number;
  renderItem: (item: VirtualizedListItem, index: number) => React.ReactNode;
  overscanCount?: number;
  width?: string | number;
}

const VirtualizedListItemWrapper = memo<{
  index: number;
  style: React.CSSProperties;
  data: {
    items: VirtualizedListItem[];
    renderItem: (item: VirtualizedListItem, index: number) => React.ReactNode;
  };
}>(({ index, style, data }) => {
  const { items, renderItem } = data;
  const item = items[index];

  return (
    <div style={style}>
      {renderItem(item, index)}
    </div>
  );
});

VirtualizedListItemWrapper.displayName = 'VirtualizedListItemWrapper';

/**
 * A performant virtualized list component using react-window
 * Only renders visible items for optimal performance with large datasets
 */
export const VirtualizedList = memo<VirtualizedListProps>(({
  items,
  itemHeight,
  height,
  renderItem,
  overscanCount = 5,
  width = '100%',
  ...boxProps
}) => {
  const itemData = useMemo(() => ({
    items,
    renderItem,
  }), [items, renderItem]);

  if (!items.length) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height={height}
        color="text.secondary"
        {...boxProps}
      >
        No items to display
      </Box>
    );
  }

  return (
    <Box {...boxProps}>
      <List
        height={height}
        itemCount={items.length}
        itemSize={itemHeight}
        itemData={itemData}
        overscanCount={overscanCount}
        width={width}
      >
        {VirtualizedListItemWrapper}
      </List>
    </Box>
  );
});

VirtualizedList.displayName = 'VirtualizedList';

export default VirtualizedList;