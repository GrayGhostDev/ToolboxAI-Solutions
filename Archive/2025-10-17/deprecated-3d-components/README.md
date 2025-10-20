# Deprecated 3D Components Archive

**Date**: October 17, 2025
**Reason**: Three.js cleanup and consolidation

## Context

These Three.js components were deprecated as part of a comprehensive Three.js usage audit and cleanup effort. Most of these components were either:
1. **Unused** - No active imports in the codebase
2. **Redundant** - Duplicated functionality available elsewhere
3. **Incomplete** - Partially implemented or broken

## Deprecated Components

### Roblox 3D UI Components (Unused)
- `Roblox3DButton.tsx` + `Roblox3DButton.stories.tsx` + test
- `Roblox3DNavigation.tsx` + `Roblox3DNavigation.stories.tsx`
- `Roblox3DTabs.tsx`
- `Roblox3DMetricCard.tsx`
- `Roblox3DIcon.tsx`
- `Simple3DIcon.tsx`

### Icon Components (Redundant)
- `Procedural3DIconLite.tsx` - Replaced by `Procedural3DIcon.tsx`
- `Procedural3DCharacter.tsx` - Not actively used
- `Real3DIcon.tsx` - Wrapper for `Safe3DIcon.tsx`

### Scene Components (Unused)
- `Scene3D.tsx` + test - Generic 3D scene component
- `FloatingCharacters.tsx` - Old version (replaced by `FloatingCharactersV2.tsx`)
- `ParticleEffects.tsx` - Standalone particle system not integrated

## Active 3D Components (Kept in Codebase)

### ✅ Essential Components
1. **Procedural3DIcon** - Primary 3D icon renderer
2. **Safe3DIcon** - Error boundary wrapper with 2D fallback
3. **ThreeProvider** - Global WebGL context manager
4. **FloatingIslandNav** - 3D navigation component (fixed)
5. **FloatingCharactersV2** - Enhanced character animation system
6. **Roblox3DLoader** - Loading spinner with 3D elements

## Three.js Fixes Applied

All active components were updated to use proper Three.js methods:
- **Before**: `mesh.position.y = value` (direct assignment - causes errors)
- **After**: `mesh.position.setY(value)` (proper API - works correctly)

## Restoration

If any of these components need to be restored:
1. Copy the component back to `apps/dashboard/src/components/`
2. Verify Three.js API usage is correct (use `.set()` methods)
3. Add imports where needed
4. Test thoroughly with current React 19 + Three.js setup

## Related Changes

- **FloatingIslandNav**: Fixed property assignments, re-enabled 3D rendering
- **Roblox3DLoader**: Fixed property assignments in SpinningCube and LoadingRocket
- **Three.js Dependencies**: Kept in package.json (still needed for active components)

## Migration Notes

No migration needed for existing code - unused components were simply archived. All active 3D functionality remains intact and improved.

---

**Archive Location**: `/Archive/2025-10-17/deprecated-3d-components/`
**Created By**: Claude Code (Three.js Cleanup Task)
**Approved By**: User request to review and clean up Three.js usage
