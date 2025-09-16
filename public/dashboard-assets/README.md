# Dashboard Assets Directory

This directory contains optimized assets for the dashboard that are safe to include in git.

## Size Constraints
- Individual files should be < 100KB
- Total directory size should be < 10MB
- Use WebP format where possible for better compression

## Directory Structure
- `icons/` - Small icon files for UI elements
- `characters/` - Optimized character sprites
- `backgrounds/` - Compressed background images

## Important Notes
- Original high-resolution assets are stored locally in `design_files/` (not in git)
- Use image optimization tools before adding new assets
- Consider using CDN for production deployments