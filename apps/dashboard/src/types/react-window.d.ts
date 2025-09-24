declare module 'react-window' {
  import * as React from 'react';

  export interface FixedSizeListProps {
    children: React.ComponentType<any>;
    height: number;
    itemCount: number;
    itemSize: number;
    width?: number | string;
    overscanCount?: number;
    direction?: 'ltr' | 'rtl';
    layout?: 'vertical' | 'horizontal';
    onItemsRendered?: (params: {
      overscanStartIndex: number;
      overscanStopIndex: number;
      visibleStartIndex: number;
      visibleStopIndex: number;
    }) => void;
    onScroll?: (params: {
      scrollDirection: 'forward' | 'backward';
      scrollOffset: number;
      scrollUpdateWasRequested: boolean;
    }) => void;
    ref?: React.Ref<any>;
    style?: React.CSSProperties;
    className?: string;
    useIsScrolling?: boolean;
    initialScrollOffset?: number;
    itemData?: any;
    outerRef?: React.Ref<any>;
    innerRef?: React.Ref<any>;
    outerElementType?: React.ElementType;
    innerElementType?: React.ElementType;
    itemKey?: (index: number, data: any) => any;
  }

  export class FixedSizeList extends React.Component<FixedSizeListProps> {
    scrollTo(scrollOffset: number): void;
    scrollToItem(index: number, align?: 'auto' | 'smart' | 'center' | 'start' | 'end'): void;
  }

  export interface VariableSizeListProps {
    children: React.ComponentType<any>;
    height: number;
    itemCount: number;
    itemSize: (index: number) => number;
    width?: number | string;
    overscanCount?: number;
    direction?: 'ltr' | 'rtl';
    layout?: 'vertical' | 'horizontal';
    onItemsRendered?: (params: {
      overscanStartIndex: number;
      overscanStopIndex: number;
      visibleStartIndex: number;
      visibleStopIndex: number;
    }) => void;
    onScroll?: (params: {
      scrollDirection: 'forward' | 'backward';
      scrollOffset: number;
      scrollUpdateWasRequested: boolean;
    }) => void;
    ref?: React.Ref<any>;
    style?: React.CSSProperties;
    className?: string;
    useIsScrolling?: boolean;
    initialScrollOffset?: number;
    itemData?: any;
    outerRef?: React.Ref<any>;
    innerRef?: React.Ref<any>;
    outerElementType?: React.ElementType;
    innerElementType?: React.ElementType;
    itemKey?: (index: number, data: any) => any;
    estimatedItemSize?: number;
  }

  export class VariableSizeList extends React.Component<VariableSizeListProps> {
    scrollTo(scrollOffset: number): void;
    scrollToItem(index: number, align?: 'auto' | 'smart' | 'center' | 'start' | 'end'): void;
    resetAfterIndex(index: number, shouldForceUpdate?: boolean): void;
  }

  // Grid components
  export interface FixedSizeGridProps {
    children: React.ComponentType<any>;
    columnCount: number;
    columnWidth: number;
    height: number;
    rowCount: number;
    rowHeight: number;
    width?: number | string;
    overscanColumnCount?: number;
    overscanRowCount?: number;
    direction?: 'ltr' | 'rtl';
    onItemsRendered?: (params: {
      overscanColumnStartIndex: number;
      overscanColumnStopIndex: number;
      overscanRowStartIndex: number;
      overscanRowStopIndex: number;
      visibleColumnStartIndex: number;
      visibleColumnStopIndex: number;
      visibleRowStartIndex: number;
      visibleRowStopIndex: number;
    }) => void;
    onScroll?: (params: {
      horizontalScrollDirection: 'forward' | 'backward';
      scrollLeft: number;
      scrollTop: number;
      scrollUpdateWasRequested: boolean;
      verticalScrollDirection: 'forward' | 'backward';
    }) => void;
    ref?: React.Ref<any>;
    style?: React.CSSProperties;
    className?: string;
    useIsScrolling?: boolean;
    initialScrollLeft?: number;
    initialScrollTop?: number;
    itemData?: any;
    outerRef?: React.Ref<any>;
    innerRef?: React.Ref<any>;
    outerElementType?: React.ElementType;
    innerElementType?: React.ElementType;
    itemKey?: (params: { columnIndex: number; rowIndex: number; data: any }) => any;
  }

  export class FixedSizeGrid extends React.Component<FixedSizeGridProps> {
    scrollTo(params: { scrollLeft: number; scrollTop: number }): void;
    scrollToItem(params: {
      columnIndex?: number;
      rowIndex?: number;
      align?: 'auto' | 'smart' | 'center' | 'start' | 'end';
    }): void;
  }
}