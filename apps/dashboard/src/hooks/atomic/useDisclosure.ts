/**
 * useDisclosure Hook
 *
 * Extended toggle hook specifically designed for disclosure patterns
 * like modals, dropdowns, accordions, and other show/hide interfaces.
 */

import { useState, useCallback } from 'react';
import { useKeyboardShortcut } from './useKeyboardShortcut';

export interface DisclosureState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface UseDisclosureOptions {
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  closeOnEscape?: boolean;
  id?: string;
}

/**
 * Custom hook for managing disclosure state with enhanced features
 *
 * @param options - Configuration options
 * @returns Object with disclosure state and control methods
 *
 * @example
 * const modal = useDisclosure({
 *   onClose: () => console.log('Modal closed'),
 *   closeOnEscape: true
 * });
 *
 * // Usage in component
 * <Button onClick={modal.open}>Open Modal</Button>
 * <Modal isOpen={modal.isOpen} onClose={modal.close}>
 *   Content
 * </Modal>
 */
const useDisclosure = (options: UseDisclosureOptions = {}): DisclosureState => {
  const {
    defaultIsOpen = false,
    onOpen,
    onClose,
    closeOnEscape = true,
    id
  } = options;

  const [isOpen, setIsOpen] = useState<boolean>(defaultIsOpen);

  const open = useCallback(() => {
    setIsOpen(true);
    onOpen?.();
  }, [onOpen]);

  const close = useCallback(() => {
    setIsOpen(false);
    onClose?.();
  }, [onClose]);

  const toggle = useCallback(() => {
    if (isOpen) {
      close();
    } else {
      open();
    }
  }, [isOpen, open, close]);

  // Close on Escape key if enabled
  useKeyboardShortcut(
    ['Escape'],
    () => {
      if (isOpen && closeOnEscape) {
        close();
      }
    },
    {
      enabled: closeOnEscape && isOpen
    }
  );

  return {
    isOpen,
    open,
    close,
    toggle,
    onOpen,
    onClose
  };
};

export type { DisclosureState, UseDisclosureOptions };
export default useDisclosure;