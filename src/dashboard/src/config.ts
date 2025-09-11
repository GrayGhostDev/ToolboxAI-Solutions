/*
  NOTE: This file is deprecated. Use src/config/index.ts as the single source of truth.
  This wrapper re-exports from the directory module to maintain backward compatibility.
  Keep this file until all imports have been migrated from '../config' to '../config/index'.
*/
// Explicitly re-export from the directory index to avoid resolving this file again
export * from './config/index';
