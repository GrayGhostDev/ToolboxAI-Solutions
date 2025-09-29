/**
 * Compound Components
 *
 * Advanced component patterns that use context and composition
 * to create flexible, reusable component APIs.
 */

// Table compound component
export { default as Table } from './Table';
export type { TableProps } from './Table';

// Form compound component
export { default as Form } from './Form';
export type { FormProps } from './Form';

// Dialog compound component
export { default as Dialog } from './Dialog';
export type { DialogProps } from './Dialog';

// Accordion compound component
export { default as Accordion } from './Accordion';
export type { AccordionProps } from './Accordion';

// Tabs compound component
export { default as Tabs } from './Tabs';
export type { TabsProps } from './Tabs';

// Select compound component
export { default as Select } from './Select';
export type { SelectProps } from './Select';

// Dropdown compound component
export { default as Dropdown } from './Dropdown';
export type { DropdownProps } from './Dropdown';

// Navigation compound component
export { default as Navigation } from './Navigation';
export type { NavigationProps } from './Navigation';

// Grouped exports for convenience
const compoundComponents = {
  Table,
  Form,
  Dialog,
  Accordion,
  Tabs,
  Select,
  Dropdown,
  Navigation
} as const;

export default compoundComponents;