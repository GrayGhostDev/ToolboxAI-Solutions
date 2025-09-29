/**
 * Atomic Components - Level 1
 *
 * Basic building blocks that cannot be broken down further.
 * These are the foundational elements of the design system.
 */

// Basic Elements
export { default as AtomicButton } from './Button';
export { default as AtomicInput } from './Input';
export { default as AtomicLabel } from './Label';
export { default as AtomicText } from './Text';
export { default as AtomicIcon } from './Icon';
export { default as AtomicImage } from './Image';
export { default as AtomicLink } from './Link';

// Form Elements
export { default as AtomicCheckbox } from './Checkbox';
export { default as AtomicRadio } from './Radio';
export { default as AtomicSwitch } from './Switch';
export { default as AtomicSlider } from './Slider';

// Visual Elements
export { default as AtomicBadge } from './Badge';
export { default as AtomicChip } from './Chip';
export { default as AtomicAvatar } from './Avatar';
export { default as AtomicDivider } from './Divider';
export { default as AtomicSkeleton } from './Skeleton';
export { default as AtomicSpinner } from './Spinner';

// Layout Elements
export { default as AtomicBox } from './Box';
export { default as AtomicStack } from './Stack';
export { default as AtomicGrid } from './Grid';

// Export type definitions
export type { ButtonProps } from './Button';
export type { InputProps } from './Input';
export type { LabelProps } from './Label';
export type { TextProps } from './Text';
export type { IconProps } from './Icon';
export type { ImageProps } from './Image';
export type { LinkProps } from './Link';
export type { CheckboxProps } from './Checkbox';
export type { RadioProps } from './Radio';
export type { SwitchProps } from './Switch';
export type { SliderProps } from './Slider';
export type { BadgeProps } from './Badge';
export type { ChipProps } from './Chip';
export type { AvatarProps } from './Avatar';
export type { DividerProps } from './Divider';
export type { SkeletonProps } from './Skeleton';
export type { SpinnerProps } from './Spinner';
export type { BoxProps } from './Box';
export type { StackProps } from './Stack';
export type { GridProps } from './Grid';

// Import components for grouped export
import ButtonDefault from './Button';
import InputDefault from './Input';
import LabelDefault from './Label';
import TextDefault from './Text';
import IconDefault from './Icon';
import ImageDefault from './Image';
import LinkDefault from './Link';
import CheckboxDefault from './Checkbox';
import RadioDefault from './Radio';
import SwitchDefault from './Switch';
import SliderDefault from './Slider';
import BadgeDefault from './Badge';
import ChipDefault from './Chip';
import AvatarDefault from './Avatar';
import DividerDefault from './Divider';
import SkeletonDefault from './Skeleton';
import SpinnerDefault from './Spinner';
import BoxDefault from './Box';
import StackDefault from './Stack';
import GridDefault from './Grid';

// Grouped exports for convenience
const atoms = {
  // Basic Elements
  Button: ButtonDefault,
  Input: InputDefault,
  Label: LabelDefault,
  Text: TextDefault,
  Icon: IconDefault,
  Image: ImageDefault,
  Link: LinkDefault,

  // Form Elements
  Checkbox: CheckboxDefault,
  Radio: RadioDefault,
  Switch: SwitchDefault,
  Slider: SliderDefault,

  // Visual Elements
  Badge: BadgeDefault,
  Chip: ChipDefault,
  Avatar: AvatarDefault,
  Divider: DividerDefault,
  Skeleton: SkeletonDefault,
  Spinner: SpinnerDefault,

  // Layout Elements
  Box: BoxDefault,
  Stack: StackDefault,
  Grid: GridDefault
} as const;

export default atoms;