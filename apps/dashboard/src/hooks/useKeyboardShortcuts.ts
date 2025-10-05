/**
 * Keyboard Shortcuts Hook
 *
 * Provides global keyboard shortcut functionality for the dashboard.
 *
 * @module useKeyboardShortcuts
 * @since 2025-10-01
 */

import { useEffect } from 'react';

export interface KeyboardShortcut {
  /** The key to listen for (e.g., 'h', '/', 'Escape') */
  key: string;
  /** Optional modifier keys required */
  modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[];
  /** Function to execute when shortcut is triggered */
  action: () => void;
  /** Human-readable description of the shortcut */
  description: string;
  /** Optional condition to enable/disable the shortcut */
  enabled?: boolean;
}

/**
 * Custom hook for managing keyboard shortcuts
 *
 * @example
 * ```typescript
 * const shortcuts: KeyboardShortcut[] = [
 *   { key: 'h', modifiers: ['alt'], action: () => navigate('/'), description: 'Go to Home' },
 *   { key: '/', action: () => searchRef.current?.focus(), description: 'Focus search' },
 * ];
 *
 * useKeyboardShortcuts(shortcuts);
 * ```
 */
export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      shortcuts.forEach((shortcut) => {
        // Skip if shortcut is disabled
        if (shortcut.enabled === false) return;

        // Check if modifier keys match
        const modifiersMatch =
          (!shortcut.modifiers || shortcut.modifiers.length === 0) ||
          shortcut.modifiers.every((mod) => {
            switch (mod) {
              case 'ctrl':
                return event.ctrlKey;
              case 'alt':
                return event.altKey;
              case 'shift':
                return event.shiftKey;
              case 'meta':
                return event.metaKey;
              default:
                return false;
            }
          });

        // Execute action if key and modifiers match
        if (modifiersMatch && event.key === shortcut.key) {
          event.preventDefault();
          shortcut.action();
        }
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};

/**
 * Default dashboard keyboard shortcuts
 */
export const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  {
    key: 'h',
    modifiers: ['alt'],
    description: 'Go to Home',
    action: () => {}, // Override with navigation
  },
  {
    key: 'c',
    modifiers: ['alt'],
    description: 'Go to Courses',
    action: () => {},
  },
  {
    key: 'a',
    modifiers: ['alt'],
    description: 'Go to Achievements',
    action: () => {},
  },
  {
    key: 'p',
    modifiers: ['alt'],
    description: 'Go to Profile',
    action: () => {},
  },
  {
    key: '/',
    description: 'Focus search input',
    action: () => {},
  },
  {
    key: '?',
    modifiers: ['shift'],
    description: 'Show keyboard shortcuts',
    action: () => {},
  },
  {
    key: 'Escape',
    description: 'Close modal or cancel action',
    action: () => {},
  },
];

/**
 * Format shortcut keys for display
 *
 * @example
 * ```typescript
 * formatShortcut({ key: 'h', modifiers: ['alt'] })
 * // Returns: "Alt+H"
 * ```
 */
export const formatShortcut = (shortcut: KeyboardShortcut): string => {
  const parts: string[] = [];

  if (shortcut.modifiers) {
    shortcut.modifiers.forEach((mod) => {
      switch (mod) {
        case 'ctrl':
          parts.push('Ctrl');
          break;
        case 'alt':
          parts.push('Alt');
          break;
        case 'shift':
          parts.push('Shift');
          break;
        case 'meta':
          parts.push('⌘'); // Mac command key
          break;
      }
    });
  }

  // Format key display
  const keyDisplay = shortcut.key === ' '
    ? 'Space'
    : shortcut.key.length === 1
    ? shortcut.key.toUpperCase()
    : shortcut.key;

  parts.push(keyDisplay);

  return parts.join('+');
};
