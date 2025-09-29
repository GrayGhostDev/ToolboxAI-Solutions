/**
 * Atomic Hooks Library
 *
 * Custom hooks designed to work seamlessly with the atomic design system.
 * These hooks provide shared logic for common UI patterns and behaviors.
 */

// UI State Hooks
export { default as useToggle } from './useToggle';
export { default as useDisclosure } from './useDisclosure';
export { default as useLocalStorage } from './useLocalStorage';
export { default as useSessionStorage } from './useSessionStorage';
export { default as usePrevious } from './usePrevious';
export { default as useDebounce } from './useDebounce';
export { default as useThrottle } from './useThrottle';

// Component Behavior Hooks
export { default as useClickOutside } from './useClickOutside';
export { default as useKeyboardShortcut } from './useKeyboardShortcut';
export { default as useFocusTrap } from './useFocusTrap';
export { default as useScrollLock } from './useScrollLock';
export { default as useIntersectionObserver } from './useIntersectionObserver';
export { default as useResizeObserver } from './useResizeObserver';

// Form Hooks
export { default as useForm } from './useForm';
export { default as useFormField } from './useFormField';
export { default as useValidation } from './useValidation';

// Data Fetching Hooks
export { default as useAsyncData } from './useAsyncData';
export { default as usePagination } from './usePagination';
export { default as useInfiniteScroll } from './useInfiniteScroll';

// Gaming/Roblox Hooks
export { default as useXPCalculator } from './useXPCalculator';
export { default as useAchievements } from './useAchievements';
export { default as useGameStats } from './useGameStats';
export { default as usePlayerStatus } from './usePlayerStatus';

// Performance Hooks
export { default as useVirtualization } from './useVirtualization';
export { default as useMemo } from './useMemo';
export { default as useCallback } from './useCallback';

// Animation Hooks
export { default as useAnimation } from './useAnimation';
export { default as useSpring } from './useSpring';
export { default as useTransition } from './useTransition';

// Type exports
export type { ToggleState } from './useToggle';
export type { DisclosureState } from './useDisclosure';
export type { FormState, FormField, ValidationRule } from './useForm';
export type { PaginationState } from './usePagination';
export type { XPCalculation } from './useXPCalculator';
export type { Achievement } from './useAchievements';
export type { GameStats } from './useGameStats';
export type { PlayerStatus } from './usePlayerStatus';

// Grouped exports for convenience
export const uiHooks = {
  useToggle,
  useDisclosure,
  useLocalStorage,
  useSessionStorage,
  usePrevious,
  useDebounce,
  useThrottle
};

export const componentHooks = {
  useClickOutside,
  useKeyboardShortcut,
  useFocusTrap,
  useScrollLock,
  useIntersectionObserver,
  useResizeObserver
};

export const formHooks = {
  useForm,
  useFormField,
  useValidation
};

export const dataHooks = {
  useAsyncData,
  usePagination,
  useInfiniteScroll
};

export const gamingHooks = {
  useXPCalculator,
  useAchievements,
  useGameStats,
  usePlayerStatus
};

export const performanceHooks = {
  useVirtualization,
  useMemo,
  useCallback
};

export const animationHooks = {
  useAnimation,
  useSpring,
  useTransition
};