/**
 * Molecular Components - Level 2
 *
 * Combinations of atoms that form simple functional units.
 * These are small groups of UI elements functioning as a unit.
 */

// Form Molecules
export { default as FormField } from './FormField';
export { default as SearchBar } from './SearchBar';
export { default as ToggleGroup } from './ToggleGroup';
export { default as InputGroup } from './InputGroup';

// Display Molecules
export { default as Card } from './Card';
export { default as UserCard } from './UserCard';
export { default as StatCard } from './StatCard';
export { default as AlertMessage } from './AlertMessage';
export { default as ProgressCard } from './ProgressCard';

// Navigation Molecules
export { default as Breadcrumb } from './Breadcrumb';
export { default as Pagination } from './Pagination';
export { default as NavItem } from './NavItem';
export { default as TabGroup } from './TabGroup';

// Interactive Molecules
export { default as ButtonGroup } from './ButtonGroup';
export { default as DropdownMenu } from './DropdownMenu';
export { default as Modal } from './Modal';
export { default as Tooltip } from './Tooltip';

// Media Molecules
export { default as ImageCard } from './ImageCard';
export { default as VideoPlayer } from './VideoPlayer';
export { default as FileUpload } from './FileUpload';

// Gaming Molecules (Roblox-specific)
export { default as XPBar } from './XPBar';
export { default as AchievementCard } from './AchievementCard';
export { default as PlayerCard } from './PlayerCard';
export { default as GameCard } from './GameCard';

// Export type definitions
export type { FormFieldProps } from './FormField';
export type { SearchBarProps } from './SearchBar';
export type { ToggleGroupProps } from './ToggleGroup';
export type { InputGroupProps } from './InputGroup';
export type { CardProps } from './Card';
export type { UserCardProps } from './UserCard';
export type { StatCardProps } from './StatCard';
export type { AlertMessageProps } from './AlertMessage';
export type { ProgressCardProps } from './ProgressCard';
export type { BreadcrumbProps } from './Breadcrumb';
export type { PaginationProps } from './Pagination';
export type { NavItemProps } from './NavItem';
export type { TabGroupProps } from './TabGroup';
export type { ButtonGroupProps } from './ButtonGroup';
export type { DropdownMenuProps } from './DropdownMenu';
export type { ModalProps } from './Modal';
export type { TooltipProps } from './Tooltip';
export type { ImageCardProps } from './ImageCard';
export type { VideoPlayerProps } from './VideoPlayer';
export type { FileUploadProps } from './FileUpload';
export type { XPBarProps } from './XPBar';
export type { AchievementCardProps } from './AchievementCard';
export type { PlayerCardProps } from './PlayerCard';
export type { GameCardProps } from './GameCard';

// Grouped exports for convenience
const molecules = {
  // Form Molecules
  FormField,
  SearchBar,
  ToggleGroup,
  InputGroup,

  // Display Molecules
  Card,
  UserCard,
  StatCard,
  AlertMessage,
  ProgressCard,

  // Navigation Molecules
  Breadcrumb,
  Pagination,
  NavItem,
  TabGroup,

  // Interactive Molecules
  ButtonGroup,
  DropdownMenu,
  Modal,
  Tooltip,

  // Media Molecules
  ImageCard,
  VideoPlayer,
  FileUpload,

  // Gaming Molecules
  XPBar,
  AchievementCard,
  PlayerCard,
  GameCard
} as const;

export default molecules;