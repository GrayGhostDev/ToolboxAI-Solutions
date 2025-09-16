# Design Assets

This directory contains optimized design assets for the dashboard.

## Structure

- `images/` - Optimized image files (PNG, JPG, SVG)
- `icons/` - Icon files
- `logos/` - Logo files

## Important Notes

1. **File Size Limits**: Keep all files under 50MB
2. **Optimization**: Use image optimization tools before committing
3. **Format Guidelines**:
   - Use SVG for icons and logos when possible
   - Use WebP or optimized PNG/JPG for images
   - Keep JSON files minimal and compressed

## Git LFS (if needed)

For files larger than 10MB but smaller than 50MB, consider using Git LFS:

```bash
git lfs track "*.png"
git lfs track "*.jpg"
git add .gitattributes
```

## Excluded Files

The original `design_files/` directory has been excluded from version control due to file size constraints. Only essential, optimized assets should be placed here.