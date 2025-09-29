/**
 * Branded Types for Type Safety
 *
 * Branded types prevent accidental mixing of different ID types
 * and provide compile-time type safety for primitive values.
 */

// Base branded type utility
declare const __brand: unique symbol;
type Brand<T, B> = T & { readonly [__brand]: B };

// ID Branded Types
export type UserId = Brand<string, 'UserId'>;
export type ClassId = Brand<string, 'ClassId'>;
export type LessonId = Brand<string, 'LessonId'>;
export type AssessmentId = Brand<string, 'AssessmentId'>;
export type MessageId = Brand<string, 'MessageId'>;
export type BadgeId = Brand<string, 'BadgeId'>;
export type SchoolId = Brand<string, 'SchoolId'>;
export type MissionId = Brand<string, 'MissionId'>;
export type ChallengeId = Brand<string, 'ChallengeId'>;
export type RewardId = Brand<string, 'RewardId'>;
export type NotificationId = Brand<string, 'NotificationId'>;
export type RobloxWorldId = Brand<string, 'RobloxWorldId'>;
export type PlaceId = Brand<string, 'PlaceId'>;
export type UniverseId = Brand<string, 'UniverseId'>;

// Score and Progress Types
export type XPPoints = Brand<number, 'XPPoints'>;
export type Level = Brand<number, 'Level'>;
export type ProgressPercentage = Brand<number, 'ProgressPercentage'>;
export type Score = Brand<number, 'Score'>;
export type Rank = Brand<number, 'Rank'>;

// Temporal Types
export type Timestamp = Brand<string, 'Timestamp'>;
export type Duration = Brand<number, 'Duration'>;

// URL Types
export type ImageUrl = Brand<string, 'ImageUrl'>;
export type AvatarUrl = Brand<string, 'AvatarUrl'>;
export type JoinUrl = Brand<string, 'JoinUrl'>;
export type PreviewUrl = Brand<string, 'PreviewUrl'>;
export type DownloadUrl = Brand<string, 'DownloadUrl'>;

// Email and Username Types
export type Email = Brand<string, 'Email'>;
export type Username = Brand<string, 'Username'>;
export type DisplayName = Brand<string, 'DisplayName'>;

// Type Guards and Constructors
export const createUserId = (value: string): UserId => value as UserId;
export const createClassId = (value: string): ClassId => value as ClassId;
export const createLessonId = (value: string): LessonId => value as LessonId;
export const createAssessmentId = (value: string): AssessmentId => value as AssessmentId;
export const createMessageId = (value: string): MessageId => value as MessageId;
export const createBadgeId = (value: string): BadgeId => value as BadgeId;
export const createSchoolId = (value: string): SchoolId => value as SchoolId;
export const createMissionId = (value: string): MissionId => value as MissionId;
export const createChallengeId = (value: string): ChallengeId => value as ChallengeId;
export const createRewardId = (value: string): RewardId => value as RewardId;
export const createNotificationId = (value: string): NotificationId => value as NotificationId;
export const createRobloxWorldId = (value: string): RobloxWorldId => value as RobloxWorldId;
export const createPlaceId = (value: string): PlaceId => value as PlaceId;
export const createUniverseId = (value: string): UniverseId => value as UniverseId;

export const createXPPoints = (value: number): XPPoints => {
  if (value < 0) throw new Error('XP points cannot be negative');
  return value as XPPoints;
};

export const createLevel = (value: number): Level => {
  if (value < 1) throw new Error('Level must be at least 1');
  return value as Level;
};

export const createProgressPercentage = (value: number): ProgressPercentage => {
  if (value < 0 || value > 100) throw new Error('Progress percentage must be between 0 and 100');
  return value as ProgressPercentage;
};

export const createScore = (value: number): Score => {
  if (value < 0) throw new Error('Score cannot be negative');
  return value as Score;
};

export const createRank = (value: number): Rank => {
  if (value < 1) throw new Error('Rank must be at least 1');
  return value as Rank;
};

export const createTimestamp = (value: string): Timestamp => {
  const date = new Date(value);
  if (isNaN(date.getTime())) throw new Error('Invalid timestamp format');
  return value as Timestamp;
};

export const createDuration = (value: number): Duration => {
  if (value < 0) throw new Error('Duration cannot be negative');
  return value as Duration;
};

export const createImageUrl = (value: string): ImageUrl => {
  if (!value.startsWith('http') && !value.startsWith('/')) {
    throw new Error('Invalid image URL format');
  }
  return value as ImageUrl;
};

export const createAvatarUrl = (value: string): AvatarUrl => {
  if (!value.startsWith('http') && !value.startsWith('/')) {
    throw new Error('Invalid avatar URL format');
  }
  return value as AvatarUrl;
};

export const createJoinUrl = (value: string): JoinUrl => {
  if (!value.startsWith('http')) {
    throw new Error('Join URL must be a valid HTTP URL');
  }
  return value as JoinUrl;
};

export const createPreviewUrl = (value: string): PreviewUrl => {
  if (!value.startsWith('http') && !value.startsWith('/')) {
    throw new Error('Invalid preview URL format');
  }
  return value as PreviewUrl;
};

export const createDownloadUrl = (value: string): DownloadUrl => {
  if (!value.startsWith('http') && !value.startsWith('/')) {
    throw new Error('Invalid download URL format');
  }
  return value as DownloadUrl;
};

export const createEmail = (value: string): Email => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    throw new Error('Invalid email format');
  }
  return value as Email;
};

export const createUsername = (value: string): Username => {
  if (value.length < 3 || value.length > 30) {
    throw new Error('Username must be between 3 and 30 characters');
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
    throw new Error('Username can only contain letters, numbers, underscores, and dashes');
  }
  return value as Username;
};

export const createDisplayName = (value: string): DisplayName => {
  if (value.length < 1 || value.length > 50) {
    throw new Error('Display name must be between 1 and 50 characters');
  }
  return value as DisplayName;
};

// Type guards
export const isUserId = (value: unknown): value is UserId =>
  typeof value === 'string' && value.length > 0;

export const isClassId = (value: unknown): value is ClassId =>
  typeof value === 'string' && value.length > 0;

export const isLessonId = (value: unknown): value is LessonId =>
  typeof value === 'string' && value.length > 0;

export const isAssessmentId = (value: unknown): value is AssessmentId =>
  typeof value === 'string' && value.length > 0;

export const isXPPoints = (value: unknown): value is XPPoints =>
  typeof value === 'number' && value >= 0;

export const isLevel = (value: unknown): value is Level =>
  typeof value === 'number' && value >= 1;

export const isProgressPercentage = (value: unknown): value is ProgressPercentage =>
  typeof value === 'number' && value >= 0 && value <= 100;

export const isScore = (value: unknown): value is Score =>
  typeof value === 'number' && value >= 0;

export const isRank = (value: unknown): value is Rank =>
  typeof value === 'number' && value >= 1;

export const isTimestamp = (value: unknown): value is Timestamp =>
  typeof value === 'string' && !isNaN(new Date(value).getTime());

export const isDuration = (value: unknown): value is Duration =>
  typeof value === 'number' && value >= 0;

export const isEmail = (value: unknown): value is Email =>
  typeof value === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

export const isUsername = (value: unknown): value is Username =>
  typeof value === 'string' &&
  value.length >= 3 &&
  value.length <= 30 &&
  /^[a-zA-Z0-9_-]+$/.test(value);

export const isDisplayName = (value: unknown): value is DisplayName =>
  typeof value === 'string' && value.length >= 1 && value.length <= 50;

// Utility type for extracting the underlying type from a branded type
export type UnbrandedType<T> = T extends Brand<infer U, any> ? U : never;

// Helper for converting arrays of branded types
export type BrandedArray<T extends Brand<any, any>> = readonly T[];

// Helper for mapping branded types in objects
export type BrandedRecord<K extends string | number | symbol, V extends Brand<any, any>> = Record<K, V>;