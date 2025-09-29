/**
 * useToggle Hook
 *
 * A simple hook for managing boolean state with toggle functionality.
 * Perfect for dropdowns, modals, sidebars, and other UI toggles.
 */

import { useState, useCallback } from 'react';

export interface ToggleState {
  value: boolean;
  toggle: () => void;
  setTrue: () => void;
  setFalse: () => void;
  setValue: (value: boolean) => void;
}

/**
 * Custom hook for managing toggle state
 *
 * @param initialValue - Initial boolean value (default: false)
 * @returns Object with current state and control methods
 *
 * @example
 * const modal = useToggle(false);
 *
 * // Usage in component
 * <Button onClick={modal.toggle}>Toggle Modal</Button>
 * <Modal isOpen={modal.value} onClose={modal.setFalse}>
 *   Content
 * </Modal>
 */
const useToggle = (initialValue: boolean = false): ToggleState => {
  const [value, setValue] = useState<boolean>(initialValue);

  const toggle = useCallback(() => {
    setValue(prev => !prev);
  }, []);

  const setTrue = useCallback(() => {
    setValue(true);
  }, []);

  const setFalse = useCallback(() => {
    setValue(false);
  }, []);

  const setValueCallback = useCallback((newValue: boolean) => {
    setValue(newValue);
  }, []);

  return {
    value,
    toggle,
    setTrue,
    setFalse,
    setValue: setValueCallback
  };
};

export type { ToggleState };
export default useToggle;