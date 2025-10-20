/**
 * Barrel export for all Roblox components
 *
 * Provides centralized exports for easier imports throughout the application
 */

// Export legacy components
export { RobloxControlPanel } from './RobloxControlPanel';
export { ContentGenerationMonitor } from './ContentGenerationMonitor';
export { StudentProgressDashboard } from './StudentProgressDashboard';
export { RobloxSessionManager } from './RobloxSessionManager';
export { QuizResultsAnalytics } from './QuizResultsAnalytics';
export { default as RobloxEnvironmentPreview } from './RobloxEnvironmentPreview';

// Export new 3D components
export { Roblox3DButton } from './Roblox3DButton';
export { Roblox3DNavigation } from './Roblox3DNavigation';
export { Roblox3DTabs } from './Roblox3DTabs';
export { Roblox3DMetricCard } from './Roblox3DMetricCard';
export { Roblox3DLoader } from './Roblox3DLoader';
export { Roblox3DIcon } from './Roblox3DIcon';

// Export gamification components
export { RobloxProgressBar } from './RobloxProgressBar';
export { RobloxAchievementBadge } from './RobloxAchievementBadge';
export { RobloxCharacterAvatar } from './RobloxCharacterAvatar';

// Export dashboard components
export { RobloxDashboardGrid } from './RobloxDashboardGrid';
export { RobloxDashboardHeader } from './RobloxDashboardHeader';

// Export animation/effect components
export { ParticleEffects } from './ParticleEffects';
export { AnimatedLeaderboard } from './AnimatedLeaderboard';
export { FloatingIslandNav } from './FloatingIslandNav';

// Export AI/chat components
export { RobloxAIAssistant } from './RobloxAIAssistant';
export { default as RobloxAIAssistantEnhanced } from './RobloxAIAssistantEnhanced';
export { RobloxAIChat } from './RobloxAIChat';
export { default as RobloxConversationFlow } from './RobloxConversationFlow';

// Export notification and UI components
export { RobloxNotificationSystem } from './RobloxNotificationSystem';
export { RobloxKeyboardShortcutsModal } from './RobloxKeyboardShortcutsModal';

// Export 3D and procedural components
export { Procedural3DIcon } from './Procedural3DIcon';
export { Procedural3DIconLite } from './Procedural3DIconLite';
export { Procedural3DCharacter } from './Procedural3DCharacter';
export { Safe3DIcon } from './Safe3DIcon';
export { Simple3DIcon } from './Simple3DIcon';
export { SafeFade } from './SafeFade';

// Re-export types if needed (optional - only if you want to expose them)
// export type { SessionSettings, ContentRequest } from './types';