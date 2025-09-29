# Images Folder Setup for Design File Parsing

This document explains the setup and usage of the `images` folder for design file parsing outputs.

## Overview

The design file parsing system now outputs parsed data to the `images` folder instead of being ignored. This allows you to:

- Store parsed design file data in a structured location
- Track the outputs in version control
- Access parsed data for further processing
- Share parsed results with team members

## Folder Structure

```
ToolBoxAI-Solutions/
├── images/                          # Main output directory
│   ├── .gitkeep                    # Ensures folder is tracked by Git
│   ├── parsed_Dashcube_fig.json    # Parsed Figma file
│   ├── parsed_Dashcube_sketch.json # Parsed Sketch file
│   ├── parsed_DashcubeXD_xd.json   # Parsed Adobe XD file
│   └── ...                         # Other parsed files
├── design/                         # Source design files (ignored)
└── ...
```

## What Gets Saved

### File Naming Convention
- Original: `Dashcube.fig`
- Parsed: `parsed_Dashcube_fig.json`

### Content Structure
Each parsed file contains:
```json
{
  "success": true,
  "file_path": "/path/to/original/file.fig",
  "file_name": "Dashcube.fig",
  "file_type": ".fig",
  "parsed_data": {
    // Complete parsed structure
  },
  "output_file": "/path/to/images/parsed_Dashcube_fig.json"
}
```

## Usage Examples

### 1. Parse a Single File
```python
from apps.backend.services.enhanced_design_parser import enhanced_design_parser

# Parse and save to images folder
result = await enhanced_design_parser.parse_design_file(
    "design/Dashcube.sketch",
    save_output=True
)

print(f"Output saved to: {result['output_file']}")
```

### 2. Parse Without Saving
```python
# Parse without saving to images folder
result = await enhanced_design_parser.parse_design_file(
    "design/Dashcube.sketch",
    save_output=False
)
```

### 3. API Usage
```bash
# Process file via API (automatically saves to images folder)
curl -X POST "http://localhost:8000/api/v1/design/process-file" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "design/Dashcube.sketch"}'
```

### 4. WebSocket Usage
```javascript
// Send via WebSocket (automatically saves to images folder)
websocket.send(JSON.stringify({
    type: 'design_file_process',
    payload: {
        file_path: 'design/Dashcube.sketch',
        include_content: true
    }
}));
```

## File Types Supported

### Design Files
- `.fig` - Figma files
- `.sketch` - Sketch files
- `.xd` - Adobe XD files

### 3D Files
- `.blend` - Blender files
- `.obj` - Wavefront OBJ files

### Media Files
- `.png`, `.jpg`, `.jpeg` - Image files
- `.mp4` - Video files

## Ignore File Configuration

The `images` folder is **NOT ignored** by Git, allowing you to track parsed outputs:

```gitignore
# Design file parsing outputs (allow images folder)
parsed_*.json
**/parsed_*.json
design_parsing_output/
**/design_parsing_output/
!images/                    # Allow images folder
!**/images/                 # Allow images folder anywhere
!images/**/*                # Allow all contents of images folder
!**/images/**/*             # Allow all contents of images folder anywhere
```

## Benefits

1. **Version Control**: Parsed outputs can be tracked and shared
2. **Structured Storage**: All outputs in one organized location
3. **Easy Access**: Simple path to find parsed data
4. **Team Collaboration**: Team members can access parsed results
5. **Backup**: Parsed data is included in repository backups

## Testing

Run the test script to see the images folder in action:

```bash
python test_design_parsing_images.py
```

This will:
- Parse all design files in your design folder
- Save outputs to the images folder
- Show file sizes and locations
- List all files in the images folder

## File Management

### Automatic Cleanup
The system automatically:
- Creates the images folder if it doesn't exist
- Generates safe filenames (replaces spaces and special characters)
- Overwrites existing files with the same name

### Manual Cleanup
You can manually clean the images folder:
```bash
# Remove all parsed files
rm images/parsed_*.json

# Remove specific file types
rm images/parsed_*_fig.json
rm images/parsed_*_sketch.json
```

## Integration with Chat System

The parsed data in the images folder can be used by your chat system:

1. **File References**: Chat can reference specific parsed files
2. **Data Access**: Chat can read and analyze parsed data
3. **Visualization**: Chat can use parsed data for visual representations
4. **Manipulation**: Chat can modify and regenerate parsed data

## Troubleshooting

### Images Folder Not Created
- Ensure the path is correct in the parser configuration
- Check file permissions for the project directory

### Files Not Saving
- Check if the images folder exists and is writable
- Verify the file path is valid
- Check logs for error messages

### Large File Sizes
- Parsed JSON files can be large for complex designs
- Consider implementing compression if needed
- Monitor disk space usage

## Future Enhancements

Potential improvements:
- Compression for large parsed files
- Caching mechanism for frequently accessed files
- Automatic cleanup of old parsed files
- Batch processing capabilities
- File format conversion utilities
