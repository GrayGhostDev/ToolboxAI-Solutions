#!/usr/bin/env python3
"""
Design File Parsing Test with Images Folder Output

This script demonstrates the enhanced design file parsing system
with output saved to the images folder.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.backend.services.enhanced_design_parser import enhanced_design_parser

async def test_design_parsing_with_images():
    """Test design file parsing with output to images folder"""
    print("=== Enhanced Design File Parsing with Images Output ===\n")

    # Test files from your design folder
    test_files = [
        "design/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.fig",
        "design/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.sketch",
        "design/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/DashcubeXD.xd",
        "design/characters/AstroClash - 3D Illustration Pack (Product).fig",
        "design/characters/PNG/Aliens/back.png",
        "design/bored_loop.mp4",
        "design/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/BLEND/ABC_CUBE.blend",
        "design/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/OBJ/ABC_CUBE.obj"
    ]

    # Ensure images folder exists
    images_dir = project_root / "images"
    images_dir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {images_dir}")
    print(f"📁 Images folder exists: {images_dir.exists()}")
    print()

    for file_path in test_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"🔍 Parsing: {file_path}")
            print("-" * 60)

            result = await enhanced_design_parser.parse_design_file(full_path, save_output=True)

            if result['success']:
                print(f"✅ Successfully parsed: {result['file_name']}")
                print(f"📁 File type: {result['file_type']}")

                # Check if output was saved
                if 'output_file' in result and result['output_file']:
                    print(f"💾 Output saved to: {result['output_file']}")

                    # Verify the file was created
                    output_path = Path(result['output_file'])
                    if output_path.exists():
                        file_size = output_path.stat().st_size
                        print(f"📊 Output file size: {file_size:,} bytes")
                    else:
                        print("⚠️  Output file not found!")
                else:
                    print("⚠️  No output file saved")

                # Show a preview of the parsed data
                parsed_data = result['parsed_data']
                if isinstance(parsed_data, dict):
                    print(f"📋 Data structure keys: {list(parsed_data.keys())}")

                    # Show some sample data based on file type
                    if result['file_type'] == '.sketch':
                        pages = parsed_data.get('pages', [])
                        print(f"   Pages: {len(pages)}")
                        if pages:
                            print(f"   First page: {pages[0].get('name', 'Untitled')}")

                    elif result['file_type'] == '.obj':
                        stats = parsed_data.get('statistics', {})
                        print(f"   Vertices: {stats.get('vertex_count', 0)}")
                        print(f"   Faces: {stats.get('face_count', 0)}")

                    elif result['file_type'] in ['.png', '.jpg', '.jpeg']:
                        size = parsed_data.get('size', {})
                        print(f"   Dimensions: {size.get('width', 0)}x{size.get('height', 0)}")
                        print(f"   Format: {parsed_data.get('file_format', 'unknown')}")

            else:
                print(f"❌ Error: {result['error']}")

            print("\n" + "=" * 80 + "\n")
        else:
            print(f"⚠️  File not found: {file_path}\n")

    # List all files in images folder
    print("📁 Files in images folder:")
    if images_dir.exists():
        for file_path in images_dir.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                print(f"   {file_path.name} ({file_size:,} bytes)")
    else:
        print("   Images folder not found!")

async def main():
    """Run the design parsing test with images output"""
    print("🚀 Starting Design File Parsing Test with Images Output")
    print("This will parse design files and save outputs to the images folder")
    print("=" * 80)
    print()

    try:
        await test_design_parsing_with_images()

        print("✅ Design parsing test completed!")
        print("\n📁 Check the images folder for detailed JSON output files")
        print("   These contain the complete parsed data for each file type")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
