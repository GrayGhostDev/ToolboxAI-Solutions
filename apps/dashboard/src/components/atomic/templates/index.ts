/**
 * Template Components - Level 4
 *
 * Page-level objects that place components into a layout and
 * articulate the design's underlying content structure.
 */

// Layout Templates
export { default as DashboardTemplate } from './DashboardTemplate';
export { default as AuthTemplate } from './AuthTemplate';
export { default as ContentTemplate } from './ContentTemplate';
export { default as LandingTemplate } from './LandingTemplate';

// Gaming Templates (Roblox-specific)
export { default as GameTemplate } from './GameTemplate';
export { default as PlayerTemplate } from './PlayerTemplate';
export { default as LeaderboardTemplate } from './LeaderboardTemplate';

// Specialized Templates
export { default as FormTemplate } from './FormTemplate';
export { default as ListTemplate } from './ListTemplate';
export { default as DetailTemplate } from './DetailTemplate';
export { default as ErrorTemplate } from './ErrorTemplate';

// Export type definitions
export type { DashboardTemplateProps } from './DashboardTemplate';
export type { AuthTemplateProps } from './AuthTemplate';
export type { ContentTemplateProps } from './ContentTemplate';
export type { LandingTemplateProps } from './LandingTemplate';
export type { GameTemplateProps } from './GameTemplate';
export type { PlayerTemplateProps } from './PlayerTemplate';
export type { LeaderboardTemplateProps } from './LeaderboardTemplate';
export type { FormTemplateProps } from './FormTemplate';
export type { ListTemplateProps } from './ListTemplate';
export type { DetailTemplateProps } from './DetailTemplate';
export type { ErrorTemplateProps } from './ErrorTemplate';

// Grouped exports for convenience
const templates = {
  // Layout
  DashboardTemplate,
  AuthTemplate,
  ContentTemplate,
  LandingTemplate,

  // Gaming
  GameTemplate,
  PlayerTemplate,
  LeaderboardTemplate,

  // Specialized
  FormTemplate,
  ListTemplate,
  DetailTemplate,
  ErrorTemplate
} as const;

export default templates;