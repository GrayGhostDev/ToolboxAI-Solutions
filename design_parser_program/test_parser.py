#!/usr/bin/env python3
"""
Design Parser Test Script

Simple test script to parse design files and save outputs to the output folder.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from design_parser import DesignParser

async def test_parser():
    """Test the design parser with sample files"""
    print("=== Design Parser Test ===\n")

    # Initialize parser
    parser = DesignParser(output_dir="output")

    # Test files from the copied design folder
    test_files = [
        "design_files/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.sketch",
        "design_files/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.fig",
        "design_files/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/DashcubeXD.xd",
        "design_files/characters/AstroClash - 3D Illustration Pack (Product).fig",
        "design_files/characters/PNG/Aliens/back.png",
        "design_files/bored_loop.mp4",
        "design_files/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/BLEND/ABC_CUBE.blend",
        "design_files/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/OBJ/ABC_CUBE.obj"
    ]

    print(f"Output directory: {parser.output_dir}")
    print(f"Output directory exists: {parser.output_dir.exists()}")
    print()

    for file_path in test_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"🔍 Parsing: {file_path}")
            print("-" * 60)

            result = await parser.parse_design_file(full_path, save_output=True)

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

            else:
                print(f"❌ Error: {result['error']}")

            print("\n" + "=" * 80 + "\n")
        else:
            print(f"⚠️  File not found: {file_path}\n")

    # List all files in output folder
    print("📁 Files in output folder:")
    if parser.output_dir.exists():
        for file_path in parser.output_dir.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                print(f"   {file_path.name} ({file_size:,} bytes)")
    else:
        print("   Output folder not found!")

async def main():
    """Run the parser test"""
    print("🚀 Starting Design Parser Test")
    print("This will parse design files and save outputs to the output folder")
    print("=" * 80)
    print()

    try:
        await test_parser()

        print("✅ Design parser test completed!")
        print("\n📁 Check the output folder for detailed JSON output files")
        print("   These contain the complete parsed data for each file type")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
