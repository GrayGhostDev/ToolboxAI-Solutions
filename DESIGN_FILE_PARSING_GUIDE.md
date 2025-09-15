# Design File Parsing Guide

This guide explains how to use the enhanced design file parsing system to extract complete, interpretable data from design files for development and manipulation.

## Overview

The enhanced design file parsing system provides complete extraction and interpretation of design files, converting them into structured data that can be understood and manipulated programmatically.

## Supported File Types

### Design Files
- **`.fig`** - Figma files (converted via fig2sketch)
- **`.sketch`** - Sketch files (native parsing)
- **`.xd`** - Adobe XD files (ZIP-based parsing)

### 3D Files
- **`.blend`** - Blender files (via Blender Python API)
- **`.obj`** - Wavefront OBJ files (complete geometry parsing)

### Media Files
- **`.png`, `.jpg`, `.jpeg`** - Image files (with EXIF and color analysis)
- **`.mp4`** - Video files (via ffprobe)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements_design_parsing.txt
```

2. Install system dependencies:

**macOS:**
```bash
brew install imagemagick ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install imagemagick ffmpeg
```

**Windows:**
- Download ImageMagick from https://imagemagick.org/
- Download FFmpeg from https://ffmpeg.org/

3. For Blender file parsing (optional):
- Install Blender from https://www.blender.org/
- Ensure `blender` command is available in PATH

## Usage Examples

### Basic File Parsing

```python
from apps.backend.services.enhanced_design_parser import enhanced_design_parser

# Parse a single design file
result = await enhanced_design_parser.parse_design_file("design/my_file.sketch")

if result['success']:
    parsed_data = result['parsed_data']
    print(f"File: {result['file_name']}")
    print(f"Type: {result['file_type']}")
    # Use parsed_data for development/manipulation
else:
    print(f"Error: {result['error']}")
```

### Sketch File Parsing

```python
# Parse Sketch file
result = await enhanced_design_parser.parse_design_file("design/Dashcube.sketch")

if result['success']:
    data = result['parsed_data']

    # Access pages and artboards
    for page in data['pages']:
        print(f"Page: {page['name']}")
        for artboard in page['artboards']:
            print(f"  Artboard: {artboard['name']}")
            print(f"  Size: {artboard['frame']['width']}x{artboard['frame']['height']}")

            # Access layers
            for layer in artboard['layers']:
                print(f"    Layer: {layer['name']} ({layer['class']})")
                if layer['style']:
                    print(f"      Style: {layer['style']}")

    # Access symbols
    for symbol in data['symbols']:
        print(f"Symbol: {symbol['name']}")

    # Access colors and styles
    print(f"Colors: {len(data['colors'])}")
    print(f"Styles: {len(data['styles'])}")
```

### Figma File Parsing

```python
# Parse Figma file (converts to Sketch format)
result = await enhanced_design_parser.parse_design_file("design/Dashcube.fig")

if result['success']:
    data = result['parsed_data']

    if 'sketch_data' in data:
        # Use the converted Sketch data
        sketch_data = data['sketch_data']
        # Same structure as Sketch files
    else:
        # Basic Figma metadata
        figma_data = data['figma_data']
        print(f"Figma file size: {figma_data['file_size']} bytes")
```

### Adobe XD File Parsing

```python
# Parse Adobe XD file
result = await enhanced_design_parser.parse_design_file("design/DashcubeXD.xd")

if result['success']:
    data = result['parsed_data']

    # Access artboards
    for artboard in data['artboards']:
        print(f"Artboard: {artboard['name']}")
        bounds = artboard['bounds']
        print(f"  Size: {bounds['width']}x{bounds['height']}")

        # Access children elements
        for child in artboard['children']:
            print(f"    Element: {child['name']} ({child['type']})")

    # Access components
    for component in data['components']:
        print(f"Component: {component['name']}")

    # Access interactions and prototypes
    print(f"Interactions: {len(data['interactions'])}")
    print(f"Prototypes: {len(data['prototypes'])}")
```

### 3D File Parsing

#### Blender Files
```python
# Parse Blender file
result = await enhanced_design_parser.parse_design_file("design/model.blend")

if result['success']:
    data = result['parsed_data']

    # Access objects
    for obj in data['data']['objects']:
        print(f"Object: {obj['name']} ({obj['type']})")
        print(f"  Location: {obj['location']}")
        print(f"  Rotation: {obj['rotation']}")
        print(f"  Scale: {obj['scale']}")

        if obj['type'] == 'MESH':
            mesh = obj['mesh']
            print(f"  Vertices: {mesh['vertices']}")
            print(f"  Faces: {mesh['faces']}")
            print(f"  Materials: {mesh['materials']}")

    # Access materials
    for mat in data['data']['materials']:
        print(f"Material: {mat['name']}")
        print(f"  Color: {mat['diffuse_color']}")
        print(f"  Metallic: {mat['metallic']}")
        print(f"  Roughness: {mat['roughness']}")
```

#### OBJ Files
```python
# Parse OBJ file
result = await enhanced_design_parser.parse_design_file("design/model.obj")

if result['success']:
    data = result['parsed_data']

    # Access geometry
    stats = data['statistics']
    print(f"Vertices: {stats['vertex_count']}")
    print(f"Faces: {stats['face_count']}")
    print(f"Normals: {stats['normal_count']}")
    print(f"Texture Coordinates: {stats['texture_coord_count']}")

    # Access faces with material and group info
    for face in data['faces'][:5]:  # First 5 faces
        print(f"Face: {face['vertices']}")
        print(f"  Material: {face['material']}")
        print(f"  Group: {face['group']}")
        print(f"  Object: {face['object']}")

    # Access materials
    print(f"Material Libraries: {data['materials']}")
    print(f"Objects: {data['objects']}")
```

### Image File Parsing

```python
# Parse image file
result = await enhanced_design_parser.parse_design_file("design/image.png")

if result['success']:
    data = result['parsed_data']

    # Basic image info
    print(f"Format: {data['file_format']}")
    print(f"Mode: {data['mode']}")
    print(f"Size: {data['size']['width']}x{data['size']['height']}")
    print(f"Total Pixels: {data['size']['total_pixels']:,}")
    print(f"Has Transparency: {data['has_transparency']}")
    print(f"Color Channels: {data['color_channels']}")

    # EXIF data
    if data['exif_data']:
        print("EXIF Data:")
        for key, value in data['exif_data'].items():
            print(f"  {key}: {value}")

    # Color analysis
    if data['dominant_colors']:
        print("Dominant Colors:")
        for color_info in data['dominant_colors']:
            color = color_info['color']
            frequency = color_info['frequency']
            print(f"  RGB{color} (frequency: {frequency})")
```

### Video File Parsing

```python
# Parse video file
result = await enhanced_design_parser.parse_design_file("design/video.mp4")

if result['success']:
    data = result['parsed_data']

    # Basic video info
    print(f"Format: {data['file_format']}")
    print(f"Duration: {data['duration']:.2f} seconds")
    print(f"File Size: {data['size']:,} bytes")
    print(f"Bitrate: {data['bitrate']:,} bps")

    # Stream information
    for stream in data['streams']:
        print(f"Stream: {stream['codec_type']}")
        print(f"  Codec: {stream['codec_name']}")

        if stream['codec_type'] == 'video':
            print(f"  Resolution: {stream['width']}x{stream['height']}")
            print(f"  Frame Rate: {stream['frame_rate']}")
            print(f"  Pixel Format: {stream['pixel_format']}")
        elif stream['codec_type'] == 'audio':
            print(f"  Sample Rate: {stream['sample_rate']} Hz")
            print(f"  Channels: {stream['channels']}")

    # Metadata
    if data['metadata']:
        print("Metadata:")
        for key, value in data['metadata'].items():
            print(f"  {key}: {value}")
```

## WebSocket Integration

The system integrates with WebSocket handlers for real-time processing:

```javascript
// Send design file processing request
websocket.send(JSON.stringify({
    type: 'design_file_process',
    payload: {
        file_path: 'design/my_file.sketch',
        include_content: true
    }
}));

// Listen for response
websocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'design_file_processed') {
        const result = message.payload.result;
        if (result.success) {
            console.log('Parsed data:', result.parsed_data);
        } else {
            console.error('Error:', result.error);
        }
    }
};
```

## API Endpoints

REST API endpoints are available for design file processing:

```bash
# Process a single file
POST /api/v1/design/process-file
{
    "file_path": "design/my_file.sketch",
    "include_content": true
}

# Scan entire design folder
GET /api/v1/design/scan-folder?include_content=true

# Search for files
POST /api/v1/design/search
{
    "query": "dashcube",
    "category": "design_files"
}

# Get folder contents
GET /api/v1/design/folder/characters

# Health check
GET /api/v1/design/health
```

## Data Structure Examples

### Sketch File Structure
```json
{
    "format": "sketch",
    "version": "95",
    "pages": [
        {
            "name": "Page 1",
            "artboards": [
                {
                    "name": "Artboard 1",
                    "frame": {
                        "x": 0,
                        "y": 0,
                        "width": 375,
                        "height": 812
                    },
                    "layers": [
                        {
                            "name": "Rectangle",
                            "class": "rectangle",
                            "frame": {...},
                            "style": {...}
                        }
                    ]
                }
            ]
        }
    ],
    "symbols": [...],
    "colors": [...],
    "styles": [...]
}
```

### OBJ File Structure
```json
{
    "format": "wavefront_obj",
    "vertices": [
        {"x": 1.0, "y": 0.0, "z": 0.0, "w": 1.0}
    ],
    "faces": [
        {
            "vertices": [0, 1, 2],
            "texture_coords": [0, 1, 2],
            "normals": [0, 1, 2],
            "material": "Material1",
            "group": "Group1",
            "object": "Object1"
        }
    ],
    "statistics": {
        "vertex_count": 1000,
        "face_count": 500,
        "normal_count": 1000,
        "texture_coord_count": 1000,
        "material_count": 5,
        "object_count": 10
    }
}
```

## Development and Manipulation

The parsed data structures are designed for easy programmatic manipulation:

```python
# Example: Extract all text layers from a Sketch file
def extract_text_layers(sketch_data):
    text_layers = []

    for page in sketch_data['pages']:
        for artboard in page['artboards']:
            for layer in artboard['layers']:
                if layer['class'] == 'text':
                    text_layers.append({
                        'name': layer['name'],
                        'text': layer.get('text', ''),
                        'position': layer['frame'],
                        'style': layer['style']
                    })

    return text_layers

# Example: Calculate total area of all rectangles
def calculate_total_rectangle_area(sketch_data):
    total_area = 0

    for page in sketch_data['pages']:
        for artboard in page['artboards']:
            for layer in artboard['layers']:
                if layer['class'] == 'rectangle':
                    frame = layer['frame']
                    area = frame['width'] * frame['height']
                    total_area += area

    return total_area

# Example: Extract color palette
def extract_color_palette(sketch_data):
    colors = set()

    for page in sketch_data['pages']:
        for artboard in page['artboards']:
            for layer in artboard['layers']:
                style = layer.get('style', {})
                fills = style.get('fills', [])
                for fill in fills:
                    if 'color' in fill:
                        colors.add(tuple(fill['color']))

    return list(colors)
```

## Error Handling

The system provides comprehensive error handling:

```python
result = await enhanced_design_parser.parse_design_file("design/file.sketch")

if not result['success']:
    error = result['error']
    if 'File not found' in error:
        print("File doesn't exist")
    elif 'Unsupported format' in error:
        print("File type not supported")
    elif 'fig2sketch conversion failed' in error:
        print("Figma conversion failed - install fig2sketch")
    elif 'Blender export failed' in error:
        print("Blender parsing failed - install Blender")
    else:
        print(f"Parsing error: {error}")
```

## Performance Considerations

- Large files may take time to parse
- Image analysis can be memory-intensive
- Video parsing requires ffprobe
- Blender parsing requires Blender installation
- Consider caching parsed results for frequently accessed files

## Troubleshooting

1. **fig2sketch not found**: Install with `pip install fig2sketch[fast]`
2. **ffprobe not found**: Install FFmpeg
3. **Blender not found**: Install Blender and ensure it's in PATH
4. **PIL import error**: Install Pillow with `pip install Pillow`
5. **Memory issues**: Process files individually or increase system memory

## Testing

Run the test script to verify functionality:

```bash
python test_enhanced_parsing.py
```

This will parse all design files in your design folder and save detailed JSON output for inspection.
