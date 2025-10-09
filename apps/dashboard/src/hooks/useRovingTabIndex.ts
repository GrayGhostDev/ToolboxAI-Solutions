/**
 * Roving Tab Index Hook
 *
 * Implements WAI-ARIA roving tabindex pattern for keyboard navigation.
 * Only one item receives Tab focus, arrow keys navigate between items.
 *
 * @module useRovingTabIndex
 * @since 2025-10-01
 */

import { useState, useCallback, type KeyboardEvent } from 'react';

export interface RovingTabIndexOptions {
  /** Total number of items to navigate */
  itemsCount: number;
  /** Initial active index (default: 0) */
  initialIndex?: number;
  /** Loop back to start/end when reaching boundaries (default: true) */
  loop?: boolean;
  /** Orientation of navigation (default: 'horizontal') */
  orientation?: 'horizontal' | 'vertical' | 'both';
}

export interface RovingTabIndexReturn {
  /** Currently active index */
  activeIndex: number;
  /** Set active index manually */
  setActiveIndex: (index: number) => void;
  /** Keyboard event handler */
  handleKeyDown: (event: KeyboardEvent) => void;
  /** Get tab index for an item at given index */
  getTabIndex: (index: number) => number;
  /** Get ARIA attributes for an item */
  getItemProps: (index: number) => {
    tabIndex: number;
    'aria-selected'?: boolean;
  };
}

/**
 * Custom hook for implementing roving tabindex navigation pattern
 *
 * @example
 * ```typescript
 * const { activeIndex, handleKeyDown, getTabIndex } = useRovingTabIndex({
 *   itemsCount: items.length,
 *   orientation: 'horizontal'
 * });
 *
 * return (
 *   <nav onKeyDown={handleKeyDown}>
 *     {items.map((item, index) => (
 *       <button
 *         key={item.id}
 *         tabIndex={getTabIndex(index)}
 *         aria-selected={index === activeIndex}
 *       >
 *         {item.label}
 *       </button>
 *     ))}
 *   </nav>
 * );
 * ```
 */
export const useRovingTabIndex = ({
  itemsCount,
  initialIndex = 0,
  loop = true,
  orientation = 'horizontal',
}: RovingTabIndexOptions): RovingTabIndexReturn => {
  const [activeIndex, setActiveIndex] = useState(initialIndex);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const handleNext = () => {
        if (activeIndex < itemsCount - 1) {
          setActiveIndex(activeIndex + 1);
        } else if (loop) {
          setActiveIndex(0);
        }
      };

      const handlePrevious = () => {
        if (activeIndex > 0) {
          setActiveIndex(activeIndex - 1);
        } else if (loop) {
          setActiveIndex(itemsCount - 1);
        }
      };

      switch (event.key) {
        case 'ArrowRight':
          if (orientation === 'horizontal' || orientation === 'both') {
            event.preventDefault();
            handleNext();
          }
          break;

        case 'ArrowLeft':
          if (orientation === 'horizontal' || orientation === 'both') {
            event.preventDefault();
            handlePrevious();
          }
          break;

        case 'ArrowDown':
          if (orientation === 'vertical' || orientation === 'both') {
            event.preventDefault();
            handleNext();
          }
          break;

        case 'ArrowUp':
          if (orientation === 'vertical' || orientation === 'both') {
            event.preventDefault();
            handlePrevious();
          }
          break;

        case 'Home':
          event.preventDefault();
          setActiveIndex(0);
          break;

        case 'End':
          event.preventDefault();
          setActiveIndex(itemsCount - 1);
          break;

        default:
          break;
      }
    },
    [activeIndex, itemsCount, loop, orientation]
  );

  const getTabIndex = useCallback(
    (index: number): number => {
      return index === activeIndex ? 0 : -1;
    },
    [activeIndex]
  );

  const getItemProps = useCallback(
    (index: number) => ({
      tabIndex: getTabIndex(index),
      'aria-selected': index === activeIndex,
    }),
    [activeIndex, getTabIndex]
  );

  return {
    activeIndex,
    setActiveIndex,
    handleKeyDown,
    getTabIndex,
    getItemProps,
  };
};
