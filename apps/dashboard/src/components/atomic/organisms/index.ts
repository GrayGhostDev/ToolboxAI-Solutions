/**
 * Organism Components - Level 3
 *
 * Complex UI components that combine molecules and atoms to form
 * distinct sections of an interface (headers, forms, lists, etc.).
 */

// Navigation Organisms
export { default as Header } from './Header';
export { default as Sidebar } from './Sidebar';
export { default as Navigation } from './Navigation';
export { default as Breadcrumbs } from './Breadcrumbs';

// Form Organisms
export { default as ContactForm } from './ContactForm';
export { default as LoginForm } from './LoginForm';
export { default as SearchForm } from './SearchForm';
export { default as FilterPanel } from './FilterPanel';

// Content Organisms
export { default as ArticleList } from './ArticleList';
export { default as ProductGrid } from './ProductGrid';
export { default as DataTable } from './DataTable';
export { default as CardGrid } from './CardGrid';

// Gaming Organisms (Roblox-specific)
export { default as PlayerDashboard } from './PlayerDashboard';
export { default as GameLobby } from './GameLobby';
export { default as AchievementPanel } from './AchievementPanel';
export { default as LeaderboardTable } from './LeaderboardTable';

// Layout Organisms
export { default as PageLayout } from './PageLayout';
export { default as DashboardLayout } from './DashboardLayout';
export { default as ContentLayout } from './ContentLayout';

// Interactive Organisms
export { default as ChatWidget } from './ChatWidget';
export { default as NotificationCenter } from './NotificationCenter';
export { default as HelpCenter } from './HelpCenter';

// Export type definitions
export type { HeaderProps } from './Header';
export type { SidebarProps } from './Sidebar';
export type { NavigationProps } from './Navigation';
export type { BreadcrumbsProps } from './Breadcrumbs';
export type { ContactFormProps } from './ContactForm';
export type { LoginFormProps } from './LoginForm';
export type { SearchFormProps } from './SearchForm';
export type { FilterPanelProps } from './FilterPanel';
export type { ArticleListProps } from './ArticleList';
export type { ProductGridProps } from './ProductGrid';
export type { DataTableProps } from './DataTable';
export type { CardGridProps } from './CardGrid';
export type { PlayerDashboardProps } from './PlayerDashboard';
export type { GameLobbyProps } from './GameLobby';
export type { AchievementPanelProps } from './AchievementPanel';
export type { LeaderboardTableProps } from './LeaderboardTable';
export type { PageLayoutProps } from './PageLayout';
export type { DashboardLayoutProps } from './DashboardLayout';
export type { ContentLayoutProps } from './ContentLayout';
export type { ChatWidgetProps } from './ChatWidget';
export type { NotificationCenterProps } from './NotificationCenter';
export type { HelpCenterProps } from './HelpCenter';

// Grouped exports for convenience
const organisms = {
  // Navigation
  Header,
  Sidebar,
  Navigation,
  Breadcrumbs,

  // Forms
  ContactForm,
  LoginForm,
  SearchForm,
  FilterPanel,

  // Content
  ArticleList,
  ProductGrid,
  DataTable,
  CardGrid,

  // Gaming
  PlayerDashboard,
  GameLobby,
  AchievementPanel,
  LeaderboardTable,

  // Layout
  PageLayout,
  DashboardLayout,
  ContentLayout,

  // Interactive
  ChatWidget,
  NotificationCenter,
  HelpCenter
} as const;

export default organisms;