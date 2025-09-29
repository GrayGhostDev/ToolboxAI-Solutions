import { useMigration } from '../components/migration/MigrationWrapper';

// Re-export for convenience
export { useMigration } from '../components/migration/MigrationWrapper';

/**
 * Migration utilities and constants
 */

// Component priority list for migration
export const MIGRATION_PRIORITY = {
  HIGH: ['Button', 'TextInput', 'Card', 'Alert', 'Badge'],
  MEDIUM: ['Modal', 'Tabs', 'Paper', 'ActionIcon', 'Select'],
  LOW: ['Timeline', 'Progress', 'RingProgress', 'Tooltip', 'Menu'],
} as const;

// Migration phases
export type MigrationPhase = 'planning' | 'development' | 'testing' | 'rollout' | 'complete';

export interface MigrationComponent {
  id: string;
  name: string;
  priority: keyof typeof MIGRATION_PRIORITY;
  phase: MigrationPhase;
  sourcePath?: string;
  mantinePath?: string;
  notes?: string;
  testCoverage?: number;
  rolloutPercentage?: number;
}

// Default migration plan
export const DEFAULT_MIGRATION_PLAN: MigrationComponent[] = [
  {
    id: 'button',
    name: 'Button',
    priority: 'HIGH',
    phase: 'development',
    sourcePath: 'legacy/Button',
    mantinePath: '@mantine/core/Button',
    notes: 'Start with basic button migration',
  },
  {
    id: 'text-input',
    name: 'TextInput',
    priority: 'HIGH',
    phase: 'planning',
    sourcePath: 'legacy/TextField',
    mantinePath: '@mantine/core/TextInput',
    notes: 'Handle validation and error states',
  },
  {
    id: 'card',
    name: 'Card',
    priority: 'HIGH',
    phase: 'planning',
    sourcePath: 'legacy/Card',
    mantinePath: '@mantine/core/Card',
    notes: 'Migrate card layouts and content structure',
  },
  {
    id: 'alert',
    name: 'Alert',
    priority: 'HIGH',
    phase: 'planning',
    sourcePath: 'legacy/Alert',
    mantinePath: '@mantine/core/Alert',
    notes: 'Maintain severity levels and icons',
  },
  {
    id: 'badge',
    name: 'Badge',
    priority: 'HIGH',
    phase: 'planning',
    sourcePath: 'legacy/Badge',
    mantinePath: '@mantine/core/Badge',
    notes: 'Handle different badge variants',
  },
  {
    id: 'modal',
    name: 'Modal',
    priority: 'MEDIUM',
    phase: 'planning',
    sourcePath: 'legacy/Modal',
    mantinePath: '@mantine/core/Modal',
    notes: 'Focus trap and accessibility',
  },
  {
    id: 'tabs',
    name: 'Tabs',
    priority: 'MEDIUM',
    phase: 'planning',
    sourcePath: 'legacy/Tabs',
    mantinePath: '@mantine/core/Tabs',
    notes: 'Tab navigation and panels',
  },
];

/**
 * Extended hook with migration planning utilities
 */
export const useMigrationPlanner = () => {
  const migration = useMigration();

  const getMigrationPlan = () => {
    const saved = localStorage.getItem('migrationPlan');
    return saved ? JSON.parse(saved) : DEFAULT_MIGRATION_PLAN;
  };

  const updateMigrationPlan = (plan: MigrationComponent[]) => {
    localStorage.setItem('migrationPlan', JSON.stringify(plan));
  };

  const updateComponentPhase = (componentId: string, phase: MigrationPhase) => {
    const plan = getMigrationPlan();
    const updated = plan.map((comp: MigrationComponent) =>
      comp.id === componentId ? { ...comp, phase } : comp
    );
    updateMigrationPlan(updated);
  };

  const getComponentsByPhase = (phase: MigrationPhase) => {
    const plan = getMigrationPlan();
    return plan.filter((comp: MigrationComponent) => comp.phase === phase);
  };

  const getNextComponents = () => {
    const plan = getMigrationPlan();
    return plan
      .filter((comp: MigrationComponent) => comp.phase === 'planning')
      .sort((a, b) => {
        const priorityOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      })
      .slice(0, 3); // Next 3 components to work on
  };

  const getMigrationProgress = () => {
    const plan = getMigrationPlan();
    const total = plan.length;
    const completed = plan.filter((comp: MigrationComponent) => comp.phase === 'complete').length;
    const inProgress = plan.filter((comp: MigrationComponent) =>
      ['development', 'testing', 'rollout'].includes(comp.phase)
    ).length;

    return {
      total,
      completed,
      inProgress,
      remaining: total - completed - inProgress,
      completionPercentage: (completed / total) * 100,
      progressPercentage: ((completed + inProgress) / total) * 100,
    };
  };

  return {
    ...migration,
    getMigrationPlan,
    updateMigrationPlan,
    updateComponentPhase,
    getComponentsByPhase,
    getNextComponents,
    getMigrationProgress,
    MIGRATION_PRIORITY,
    DEFAULT_MIGRATION_PLAN,
  };
};

/**
 * Migration testing utilities
 */
export const useMigrationTesting = () => {
  const runComponentComparison = async (componentId: string) => {
    // This would integrate with your testing framework
    // For now, return mock data
    return {
      componentId,
      testsPassed: 12,
      testsFailed: 0,
      visualDifferences: [],
      performanceMetrics: {
        renderTime: 45,
        bundleSize: 2.3,
      },
      accessibilityScore: 98,
    };
  };

  const generateTestReport = async (componentIds: string[]) => {
    const results = await Promise.all(
      componentIds.map(id => runComponentComparison(id))
    );

    return {
      timestamp: new Date().toISOString(),
      results,
      summary: {
        totalComponents: results.length,
        passedComponents: results.filter(r => r.testsFailed === 0).length,
        averageAccessibilityScore: results.reduce((acc, r) => acc + r.accessibilityScore, 0) / results.length,
        totalBundleSizeReduction: results.reduce((acc, r) => acc + r.performanceMetrics.bundleSize, 0),
      },
    };
  };

  return {
    runComponentComparison,
    generateTestReport,
  };
};