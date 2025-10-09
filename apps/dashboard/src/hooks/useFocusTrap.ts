/**
 * Focus Trap Hook
 *
 * Traps keyboard focus within a container (useful for modals, dialogs).
 * Implements WAI-ARIA focus management pattern.
 *
 * @module useFocusTrap
 * @since 2025-10-01
 */

import { useEffect, useRef, type RefObject } from 'react';

export interface FocusTrapOptions {
  /** Whether the focus trap is active */
  isActive: boolean;
  /** Element to focus when trap activates (default: first focusable) */
  initialFocus?: HTMLElement | null;
  /** Element to focus when trap deactivates */
  returnFocus?: HTMLElement | null;
}

/**
 * Custom hook for trapping focus within a container
 *
 * @example
 * ```typescript
 * const MyModal = ({ isOpen, onClose }) => {
 *   const trapRef = useFocusTrap({ isActive: isOpen });
 *
 *   return (
 *     <Modal opened={isOpen} onClose={onClose}>
 *       <div ref={trapRef}>
 *         <button>First</button>
 *         <input />
 *         <button>Last</button>
 *       </div>
 *     </Modal>
 *   );
 * };
 * ```
 */
export const useFocusTrap = <T extends HTMLElement = HTMLDivElement>({
  isActive,
  initialFocus,
  returnFocus,
}: FocusTrapOptions): RefObject<T> => {
  const containerRef = useRef<T>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) {
      // Restore focus when trap deactivates
      if (!isActive && returnFocus) {
        returnFocus.focus();
      } else if (!isActive && previousFocus.current) {
        previousFocus.current.focus();
      }
      return;
    }

    const container = containerRef.current;

    // Save currently focused element
    previousFocus.current = document.activeElement as HTMLElement;

    // Get all focusable elements within container
    const getFocusableElements = (): HTMLElement[] => {
      const selector = [
        'button:not([disabled])',
        '[href]',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
      ].join(', ');

      return Array.from(container.querySelectorAll<HTMLElement>(selector)).filter(
        (element) => {
          // Ensure element is visible and not hidden
          return (
            element.offsetParent !== null &&
            !element.hasAttribute('disabled') &&
            !element.getAttribute('aria-hidden')
          );
        }
      );
    };

    const focusableElements = getFocusableElements();
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus initial element
    if (initialFocus) {
      initialFocus.focus();
    } else if (firstElement) {
      firstElement.focus();
    }

    // Handle Tab key navigation
    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      const currentFocusableElements = getFocusableElements();
      const currentFirst = currentFocusableElements[0];
      const currentLast = currentFocusableElements[currentFocusableElements.length - 1];

      if (event.shiftKey) {
        // Shift+Tab: moving backwards
        if (document.activeElement === currentFirst) {
          event.preventDefault();
          currentLast?.focus();
        }
      } else {
        // Tab: moving forwards
        if (document.activeElement === currentLast) {
          event.preventDefault();
          currentFirst?.focus();
        }
      }
    };

    // Prevent focus from leaving container
    const handleFocusOut = (event: FocusEvent) => {
      if (!container.contains(event.relatedTarget as Node)) {
        event.preventDefault();
        firstElement?.focus();
      }
    };

    container.addEventListener('keydown', handleTabKey);
    container.addEventListener('focusout', handleFocusOut);

    return () => {
      container.removeEventListener('keydown', handleTabKey);
      container.removeEventListener('focusout', handleFocusOut);
    };
  }, [isActive, initialFocus, returnFocus]);

  return containerRef;
};

/**
 * Alternative focus trap using IntersectionObserver for dynamic content
 */
export const useAdvancedFocusTrap = <T extends HTMLElement = HTMLDivElement>({
  isActive,
  initialFocus,
  returnFocus,
}: FocusTrapOptions): RefObject<T> => {
  const containerRef = useRef<T>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const observerRef = useRef<MutationObserver | null>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) {
      if (!isActive && (returnFocus || previousFocus.current)) {
        (returnFocus || previousFocus.current)?.focus();
      }
      return;
    }

    const container = containerRef.current;
    previousFocus.current = document.activeElement as HTMLElement;

    const getFocusableElements = (): HTMLElement[] => {
      const selector = [
        'button:not([disabled])',
        '[href]',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
      ].join(', ');

      return Array.from(container.querySelectorAll<HTMLElement>(selector)).filter(
        (element) =>
          element.offsetParent !== null &&
          !element.hasAttribute('disabled') &&
          !element.getAttribute('aria-hidden')
      );
    };

    let focusableElements = getFocusableElements();

    // Watch for DOM changes and update focusable elements
    observerRef.current = new MutationObserver(() => {
      focusableElements = getFocusableElements();
    });

    observerRef.current.observe(container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['disabled', 'aria-hidden', 'tabindex'],
    });

    // Focus initial element
    if (initialFocus) {
      initialFocus.focus();
    } else if (focusableElements[0]) {
      focusableElements[0].focus();
    }

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      const current = getFocusableElements();
      const first = current[0];
      const last = current[current.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };

    container.addEventListener('keydown', handleTabKey);

    return () => {
      container.removeEventListener('keydown', handleTabKey);
      observerRef.current?.disconnect();
    };
  }, [isActive, initialFocus, returnFocus]);

  return containerRef;
};
