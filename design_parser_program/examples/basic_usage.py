#!/usr/bin/env python3
"""
Basic Usage Example

Demonstrates how to use the Design Parser for common tasks.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from design_parser import DesignParser

async def parse_single_file():
    """Parse a single design file"""
    print("=== Parse Single File ===")

    parser = DesignParser(output_dir="output")

    # Parse a Sketch file
    result = await parser.parse_design_file("design_files/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.sketch")

    if result['success']:
        print(f"✅ Successfully parsed: {result['file_name']}")
        print(f"📁 File type: {result['file_type']}")
        print(f"💾 Output saved to: {result['output_file']}")

        # Show some data
        parsed_data = result['parsed_data']
        if 'pages' in parsed_data:
            print(f"📄 Pages: {len(parsed_data['pages'])}")
        if 'artboards' in parsed_data:
            print(f"🎨 Artboards: {len(parsed_data['artboards'])}")
    else:
        print(f"❌ Error: {result['error']}")

async def parse_all_design_files():
    """Parse all design files in the design_files directory"""
    print("\n=== Parse All Design Files ===")

    parser = DesignParser(output_dir="output")
    design_files_dir = Path("design_files")

    # Find all supported files
    supported_extensions = ['.sketch', '.fig', '.xd', '.blend', '.obj', '.png', '.jpg', '.mp4', '.txt']
    design_files = []

    for ext in supported_extensions:
        design_files.extend(design_files_dir.rglob(f"*{ext}"))

    print(f"Found {len(design_files)} design files to parse")

    success_count = 0
    error_count = 0

    for file_path in design_files:
        print(f"\n🔍 Parsing: {file_path}")

        result = await parser.parse_design_file(file_path)

        if result['success']:
            print(f"✅ {result['file_name']} ({result['file_type']})")
            success_count += 1
        else:
            print(f"❌ {result['error']}")
            error_count += 1

    print(f"\n📊 Results: {success_count} successful, {error_count} errors")

async def extract_design_elements():
    """Extract specific design elements from parsed files"""
    print("\n=== Extract Design Elements ===")

    parser = DesignParser(output_dir="output")

    # Parse a Sketch file
    result = await parser.parse_design_file("design_files/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.sketch")

    if result['success']:
        parsed_data = result['parsed_data']

        # Extract all text layers
        text_layers = []
        for page in parsed_data.get('pages', []):
            for artboard in page.get('artboards', []):
                for layer in artboard.get('layers', []):
                    if layer.get('class') == 'text':
                        text_layers.append({
                            'name': layer.get('name'),
                            'text': layer.get('text', ''),
                            'position': layer.get('frame', {})
                        })

        print(f"📝 Found {len(text_layers)} text layers:")
        for layer in text_layers[:5]:  # Show first 5
            print(f"   - {layer['name']}: {layer['text'][:50]}...")

        # Extract all rectangles
        rectangles = []
        for page in parsed_data.get('pages', []):
            for artboard in page.get('artboards', []):
                for layer in artboard.get('layers', []):
                    if layer.get('class') == 'rectangle':
                        rectangles.append({
                            'name': layer.get('name'),
                            'frame': layer.get('frame', {})
                        })

        print(f"📦 Found {len(rectangles)} rectangles:")
        for rect in rectangles[:5]:  # Show first 5
            frame = rect['frame']
            print(f"   - {rect['name']}: {frame.get('width', 0)}x{frame.get('height', 0)}")

async def analyze_image_colors():
    """Analyze colors in image files"""
    print("\n=== Analyze Image Colors ===")

    parser = DesignParser(output_dir="output")

    # Find image files
    image_files = list(Path("design_files").rglob("*.png"))[:3]  # First 3 PNG files

    for image_file in image_files:
        print(f"\n🖼️  Analyzing: {image_file.name}")

        result = await parser.parse_design_file(image_file)

        if result['success']:
            parsed_data = result['parsed_data']

            # Show basic info
            size = parsed_data.get('size', {})
            print(f"   Dimensions: {size.get('width', 0)}x{size.get('height', 0)}")
            print(f"   Format: {parsed_data.get('file_format', 'unknown')}")
            print(f"   Mode: {parsed_data.get('mode', 'unknown')}")

            # Show dominant colors
            dominant_colors = parsed_data.get('dominant_colors', [])
            if dominant_colors:
                print(f"   Dominant colors:")
                for color_info in dominant_colors[:3]:
                    color = color_info.get('color', [])
                    frequency = color_info.get('frequency', 0)
                    print(f"     RGB{color} (frequency: {frequency})")

async def main():
    """Run all examples"""
    print("🚀 Design Parser - Basic Usage Examples")
    print("=" * 50)

    try:
        await parse_single_file()
        await parse_all_design_files()
        await extract_design_elements()
        await analyze_image_colors()

        print("\n✅ All examples completed!")
        print("\n📁 Check the output folder for parsed JSON files")

    except Exception as e:
        print(f"❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

