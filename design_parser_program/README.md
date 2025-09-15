# Design Parser Program

A complete, standalone design file parsing system that can extract and convert design files into readable, interpretable formats.

## Features

- **Complete Design File Support**: .fig, .sketch, .xd, .blend, .obj, .png, .jpg, .mp4, .txt
- **Structured Output**: All parsed data saved as organized JSON files
- **Standalone Operation**: No external dependencies on main application
- **Easy Integration**: Simple API for use in other projects
- **Comprehensive Parsing**: Extracts all design elements, properties, and relationships

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: Install system tools for full functionality
# macOS
brew install imagemagick ffmpeg

# Ubuntu/Debian
sudo apt-get install imagemagick ffmpeg

# For Blender files (optional)
# Download from https://www.blender.org/
```

### 2. Basic Usage

```python
import asyncio
from src.design_parser import DesignParser

async def main():
    # Initialize parser
    parser = DesignParser(output_dir="output")

    # Parse a design file
    result = await parser.parse_design_file("design_files/my_file.sketch")

    if result['success']:
        print(f"Parsed: {result['file_name']}")
        print(f"Output saved to: {result['output_file']}")
    else:
        print(f"Error: {result['error']}")

# Run the parser
asyncio.run(main())
```

### 3. Run Test Script

```bash
python test_parser.py
```

## File Structure

```
design_parser_program/
├── src/
│   └── design_parser.py          # Main parser module
├── design_files/                 # Source design files
│   ├── characters/               # Character designs
│   ├── dashcube_*/              # Dashboard designs
│   └── stuudy-3d-icons_*/       # 3D icon designs
├── output/                       # Parsed output files
├── examples/                     # Usage examples
├── docs/                         # Documentation
├── requirements.txt              # Python dependencies
├── test_parser.py               # Test script
└── README.md                    # This file
```

## Supported File Types

### Design Files
- **.fig** - Figma files (converted via fig2sketch)
- **.sketch** - Sketch files (native parsing)
- **.xd** - Adobe XD files (ZIP-based parsing)

### 3D Files
- **.blend** - Blender files (via Blender Python API)
- **.obj** - Wavefront OBJ files (complete geometry parsing)

### Media Files
- **.png, .jpg, .jpeg** - Image files (with EXIF and color analysis)
- **.mp4** - Video files (via ffprobe)

### Text Files
- **.txt** - Text files (content analysis)

## Output Format

Each parsed file generates a JSON file with this structure:

```json
{
  "success": true,
  "file_path": "/path/to/original/file.sketch",
  "file_name": "MyDesign.sketch",
  "file_type": ".sketch",
  "parsed_data": {
    "format": "sketch",
    "version": "95",
    "pages": [...],
    "artboards": [...],
    "symbols": [...],
    "colors": [...],
    "styles": [...]
  },
  "output_file": "/path/to/output/parsed_MyDesign_sketch.json"
}
```

## API Reference

### DesignParser Class

#### `__init__(output_dir="output")`
Initialize the parser with output directory.

#### `parse_design_file(file_path, save_output=True)`
Parse a design file and optionally save output.

**Parameters:**
- `file_path`: Path to design file (str or Path)
- `save_output`: Whether to save parsed data to file (bool)

**Returns:**
- Dictionary with parsing results

## Examples

### Parse Sketch File
```python
from src.design_parser import DesignParser

parser = DesignParser()
result = await parser.parse_design_file("design_files/Dashcube.sketch")

# Access parsed data
if result['success']:
    sketch_data = result['parsed_data']
    for page in sketch_data['pages']:
        print(f"Page: {page['name']}")
        for artboard in page['artboards']:
            print(f"  Artboard: {artboard['name']}")
```

### Parse OBJ File
```python
result = await parser.parse_design_file("design_files/model.obj")

if result['success']:
    obj_data = result['parsed_data']
    stats = obj_data['statistics']
    print(f"Vertices: {stats['vertex_count']}")
    print(f"Faces: {stats['face_count']}")
```

### Parse Image File
```python
result = await parser.parse_design_file("design_files/image.png")

if result['success']:
    image_data = result['parsed_data']
    size = image_data['size']
    print(f"Dimensions: {size['width']}x{size['height']}")
    print(f"Format: {image_data['file_format']}")
```

## Advanced Usage

### Batch Processing
```python
import asyncio
from pathlib import Path

async def batch_parse():
    parser = DesignParser()
    design_files = Path("design_files").rglob("*")

    tasks = []
    for file_path in design_files:
        if file_path.suffix.lower() in ['.sketch', '.fig', '.xd']:
            tasks.append(parser.parse_design_file(file_path))

    results = await asyncio.gather(*tasks)

    for result in results:
        if result['success']:
            print(f"✅ {result['file_name']}")
        else:
            print(f"❌ {result['error']}")

asyncio.run(batch_parse())
```

### Custom Output Directory
```python
parser = DesignParser(output_dir="my_custom_output")
result = await parser.parse_design_file("file.sketch")
```

## Dependencies

### Required
- Python 3.8+
- Pillow (for image processing)

### Optional (for full functionality)
- fig2sketch (for Figma files)
- sketch-tool (for Sketch files)
- ffmpeg (for video files)
- Blender (for .blend files)

## Troubleshooting

### Common Issues

1. **Module not found errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **fig2sketch not found**
   ```bash
   pip install fig2sketch[fast]
   ```

3. **ffprobe not found**
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

4. **Blender not found**
   - Download from https://www.blender.org/
   - Ensure `blender` command is in PATH

### Performance Tips

- Large files may take time to parse
- Image analysis can be memory-intensive
- Consider processing files individually for large batches

## Integration

This parser can be easily integrated into other projects:

1. **Copy the `src/` folder** to your project
2. **Install dependencies** from requirements.txt
3. **Import and use** the DesignParser class

## License

This design parser is part of the ToolBoxAI Solutions project.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the examples in the `examples/` folder
3. Check the parsed output files for debugging information

