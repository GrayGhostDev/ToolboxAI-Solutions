/**
 * useKeyboardShortcut Hook
 *
 * Hook for handling keyboard shortcuts with support for key combinations,
 * modifiers, and conditional activation.
 */

import { useEffect, useCallback, useRef } from 'react';

export interface UseKeyboardShortcutOptions {
  enabled?: boolean;
  preventDefault?: boolean;
  stopPropagation?: boolean;
  target?: React.RefObject<HTMLElement> | HTMLElement | null;
}

type KeyboardEventHandler = (event: KeyboardEvent) => void;

/**
 * Custom hook for handling keyboard shortcuts
 *
 * @param keys - Array of key combinations or single key
 * @param callback - Function to call when shortcut is triggered
 * @param options - Configuration options
 *
 * @example
 * // Single key
 * useKeyboardShortcut(['Escape'], () => closeModal());
 *
 * // Key combination
 * useKeyboardShortcut(['Control', 's'], () => saveDocument(), {
 *   preventDefault: true
 * });
 *
 * // Multiple shortcuts
 * useKeyboardShortcut(
 *   [['Control', 'k'], ['Command', 'k']],
 *   () => openCommandPalette()
 * );
 */
const useKeyboardShortcut = (
  keys: string[] | string[][],
  callback: KeyboardEventHandler,
  options: UseKeyboardShortcutOptions = {}
): void => {
  const {
    enabled = true,
    preventDefault = false,
    stopPropagation = false,
    target
  } = options;

  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Normalize keys to array of arrays
      const normalizedKeys = Array.isArray(keys[0]) ? keys as string[][] : [keys as string[]];

      // Check if any key combination matches
      const matches = normalizedKeys.some(keyCombo => {
        return keyCombo.every(key => {
          const lowerKey = key.toLowerCase();

          // Handle modifiers
          if (lowerKey === 'control' || lowerKey === 'ctrl') {
            return event.ctrlKey;
          }
          if (lowerKey === 'shift') {
            return event.shiftKey;
          }
          if (lowerKey === 'alt') {
            return event.altKey;
          }
          if (lowerKey === 'meta' || lowerKey === 'command' || lowerKey === 'cmd') {
            return event.metaKey;
          }

          // Handle regular keys
          return event.key.toLowerCase() === lowerKey;
        });
      });

      if (matches) {
        if (preventDefault) {
          event.preventDefault();
        }
        if (stopPropagation) {
          event.stopPropagation();
        }

        callbackRef.current(event);
      }
    },
    [keys, enabled, preventDefault, stopPropagation]
  );

  useEffect(() => {
    if (!enabled) return;

    // Determine the target element
    let targetElement: HTMLElement | Document = document;

    if (target) {
      if ('current' in target) {
        // It's a ref object
        targetElement = target.current || document;
      } else {
        // It's a direct element
        targetElement = target;
      }
    }

    targetElement.addEventListener('keydown', handleKeyDown);

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, enabled, target]);
};

export type { UseKeyboardShortcutOptions };
export default useKeyboardShortcut;