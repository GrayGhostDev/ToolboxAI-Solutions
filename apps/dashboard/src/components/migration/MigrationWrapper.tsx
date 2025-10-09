import React, { type ReactNode } from 'react';

interface MigrationWrapperProps {
  children?: ReactNode;
  /** Component ID for tracking migration */
  componentId: string;
  /** MUI component version */
  muiComponent: ReactNode;
  /** Mantine component version */
  mantineComponent: ReactNode;
  /** Force use of specific version */
  forcedVersion?: 'mui' | 'mantine';
  /** Migration status - determines which version to render */
  migrationStatus?: 'mui' | 'mantine' | 'both';
  /** Enable A/B testing */
  enableABTesting?: boolean;
  /** A/B test percentage for Mantine (0-100) */
  mantineTestPercentage?: number;
}

/**
 * MigrationWrapper - Component that helps with gradual migration from MUI to Mantine
 *
 * This wrapper allows for:
 * - Side-by-side comparison of MUI and Mantine versions
 * - Gradual rollout of Mantine components
 * - A/B testing between versions
 * - Easy rollback if needed
 */
export const MigrationWrapper: React.FC<MigrationWrapperProps> = ({
  componentId,
  muiComponent,
  mantineComponent,
  forcedVersion,
  migrationStatus = 'mui',
  enableABTesting = false,
  mantineTestPercentage = 0,
}) => {
  // Check for feature flag or environment variable
  const isMantineEnabled = React.useMemo(() => {
    // Check localStorage for component-specific override
    const localOverride = localStorage.getItem(`migration-${componentId}`);
    if (localOverride) {
      return localOverride === 'mantine';
    }

    // Check global migration flag
    const globalFlag = localStorage.getItem('enableMantineMigration');
    if (globalFlag === 'true') {
      return true;
    }

    // Check environment variable
    if (import.meta.env.VITE_ENABLE_MANTINE_MIGRATION === 'true') {
      return true;
    }

    return false;
  }, [componentId]);

  // A/B testing logic
  const shouldUseMantine = React.useMemo(() => {
    if (forcedVersion) {
      return forcedVersion === 'mantine';
    }

    if (migrationStatus === 'mantine') {
      return true;
    }

    if (migrationStatus === 'mui') {
      return false;
    }

    if (enableABTesting && mantineTestPercentage > 0) {
      // Use component ID to create consistent hash for user
      const hash = componentId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const userBucket = hash % 100;
      return userBucket < mantineTestPercentage;
    }

    return isMantineEnabled;
  }, [componentId, forcedVersion, migrationStatus, enableABTesting, mantineTestPercentage, isMantineEnabled]);

  // Log migration events for analytics
  React.useEffect(() => {
    if (import.meta.env.DEV) {
      console.log(`Migration: ${componentId} using ${shouldUseMantine ? 'Mantine' : 'MUI'}`);
    }

    // In production, you might want to send this to analytics
    if (import.meta.env.PROD) {
      // Example: analytics.track('component_migration', { componentId, version: shouldUseMantine ? 'mantine' : 'mui' });
    }
  }, [componentId, shouldUseMantine]);

  // Render side-by-side comparison in development
  if (import.meta.env.DEV && migrationStatus === 'both') {
    return (
      <div style={{ display: 'flex', gap: '20px', padding: '10px', border: '2px dashed #ccc', borderRadius: '8px' }}>
        <div style={{ flex: 1, border: '1px solid #1976d2', borderRadius: '4px', padding: '10px' }}>
          <div style={{ fontSize: '12px', color: '#1976d2', fontWeight: 'bold', marginBottom: '5px' }}>
            MUI Version
          </div>
          {muiComponent}
        </div>
        <div style={{ flex: 1, border: '1px solid #15aabf', borderRadius: '4px', padding: '10px' }}>
          <div style={{ fontSize: '12px', color: '#15aabf', fontWeight: 'bold', marginBottom: '5px' }}>
            Mantine Version
          </div>
          {mantineComponent}
        </div>
      </div>
    );
  }

  return shouldUseMantine ? <>{mantineComponent}</> : <>{muiComponent}</>;
};

/**
 * Hook to manage migration state across components
 */
export const useMigration = () => {
  const [migrationFlags, setMigrationFlags] = React.useState<Record<string, 'mui' | 'mantine'>>(() => {
    const saved = localStorage.getItem('migrationFlags');
    return saved ? JSON.parse(saved) : {};
  });

  const setComponentMigration = React.useCallback((componentId: string, version: 'mui' | 'mantine') => {
    setMigrationFlags(prev => {
      const updated = { ...prev, [componentId]: version };
      localStorage.setItem('migrationFlags', JSON.stringify(updated));
      localStorage.setItem(`migration-${componentId}`, version);
      return updated;
    });
  }, []);

  const toggleGlobalMigration = React.useCallback((enabled: boolean) => {
    localStorage.setItem('enableMantineMigration', enabled.toString());
    window.location.reload(); // Force refresh to apply changes
  }, []);

  const resetMigrationFlags = React.useCallback(() => {
    setMigrationFlags({});
    localStorage.removeItem('migrationFlags');
    localStorage.removeItem('enableMantineMigration');
    // Clear all component-specific flags
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('migration-')) {
        localStorage.removeItem(key);
      }
    });
  }, []);

  const getMigrationStats = React.useCallback(() => {
    const total = Object.keys(migrationFlags).length;
    const migrated = Object.values(migrationFlags).filter(v => v === 'mantine').length;
    return {
      total,
      migrated,
      percentage: total > 0 ? (migrated / total) * 100 : 0,
      components: migrationFlags,
    };
  }, [migrationFlags]);

  return {
    migrationFlags,
    setComponentMigration,
    toggleGlobalMigration,
    resetMigrationFlags,
    getMigrationStats,
    isGlobalMigrationEnabled: localStorage.getItem('enableMantineMigration') === 'true',
  };
};

/**
 * Migration Control Panel component for development
 */
export const MigrationControlPanel: React.FC = () => {
  const {
    migrationFlags,
    setComponentMigration,
    toggleGlobalMigration,
    resetMigrationFlags,
    getMigrationStats,
    isGlobalMigrationEnabled
  } = useMigration();

  const stats = getMigrationStats();

  if (import.meta.env.PROD) {
    return null; // Don't show in production
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      background: 'white',
      border: '2px solid #ccc',
      borderRadius: '8px',
      padding: '15px',
      maxWidth: '300px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      fontSize: '12px',
      zIndex: 9999,
    }}>
      <h4 style={{ margin: '0 0 10px 0' }}>Migration Control</h4>

      <div style={{ marginBottom: '10px' }}>
        <strong>Stats:</strong> {stats.migrated}/{stats.total} components migrated ({stats.percentage.toFixed(1)}%)
      </div>

      <label style={{ display: 'block', marginBottom: '10px' }}>
        <input
          type="checkbox"
          checked={isGlobalMigrationEnabled}
          onChange={(e) => toggleGlobalMigration(e.target.checked)}
        />
        Enable Global Mantine Migration
      </label>

      <div style={{ marginBottom: '10px' }}>
        <strong>Component Status:</strong>
        {Object.entries(migrationFlags).map(([componentId, version]) => (
          <div key={componentId} style={{ marginLeft: '10px', fontSize: '10px' }}>
            <label>
              {componentId}:
              <select
                value={version}
                onChange={(e) => setComponentMigration(componentId, e.target.value as 'mui' | 'mantine')}
                style={{ marginLeft: '5px', fontSize: '10px' }}
              >
                <option value="mui">MUI</option>
                <option value="mantine">Mantine</option>
              </select>
            </label>
          </div>
        ))}
      </div>

      <button
        onClick={resetMigrationFlags}
        style={{
          background: '#f44336',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          padding: '5px 10px',
          fontSize: '10px',
          cursor: 'pointer',
        }}
      >
        Reset All
      </button>
    </div>
  );
};