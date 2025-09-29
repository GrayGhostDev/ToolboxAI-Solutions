/**
 * Atomic Design Component System
 *
 * This file exports all atomic design components organized by level:
 * - Atoms: Basic building blocks (buttons, inputs, labels)
 * - Molecules: Combinations of atoms (form fields, search bars)
 * - Organisms: Groups of molecules (headers, forms, sections)
 * - Templates: Wireframes/layouts
 * - Pages: Complete page compositions
 */

// Atoms - Basic building blocks
export * from './atoms';

// Molecules - Simple combinations of atoms
export * from './molecules';

// Organisms - Complex UI components
export * from './organisms';

// Templates - Page layouts and wireframes
export * from './templates';

// Compound Components - Advanced patterns
export * from './compound';

// Higher-Order Components
export * from './hoc';

// Re-export for convenience
export { default as atomicComponents } from './atoms';
export { default as molecularComponents } from './molecules';
export { default as organismComponents } from './organisms';
export { default as templateComponents } from './templates';
export { default as compoundComponents } from './compound';