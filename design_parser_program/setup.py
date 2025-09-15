#!/usr/bin/env python3
"""
Setup script for Design Parser Program

This script sets up the design parser program and runs initial tests.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")

    directories = [
        "output",
        "examples",
        "docs"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   Created: {directory}/")

    print("✅ Directories created")

def check_dependencies():
    """Check for optional dependencies"""
    print("🔍 Checking dependencies...")

    # Check for Pillow
    try:
        import PIL
        print("✅ Pillow (PIL) - Available")
    except ImportError:
        print("❌ Pillow (PIL) - Not available (required for image processing)")

    # Check for fig2sketch
    try:
        subprocess.run(["fig2sketch", "--help"], capture_output=True, check=True)
        print("✅ fig2sketch - Available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  fig2sketch - Not available (optional for Figma files)")

    # Check for sketch-tool
    try:
        subprocess.run(["sketch-tool", "--help"], capture_output=True, check=True)
        print("✅ sketch-tool - Available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  sketch-tool - Not available (optional for Sketch files)")

    # Check for ffprobe
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        print("✅ ffprobe - Available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ffprobe - Not available (optional for video files)")

    # Check for Blender
    try:
        subprocess.run(["blender", "--version"], capture_output=True, check=True)
        print("✅ Blender - Available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Blender - Not available (optional for .blend files)")

async def run_test():
    """Run a basic test"""
    print("\n🧪 Running basic test...")

    try:
        # Import the parser
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from design_parser import DesignParser

        # Initialize parser
        parser = DesignParser(output_dir="output")
        print("✅ Parser initialized successfully")

        # Test with a simple file if available
        test_files = [
            "design_files/dashcube_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/Dashcube.sketch",
            "design_files/characters/AstroClash - 3D Illustration Pack (Product).fig"
        ]

        for test_file in test_files:
            if Path(test_file).exists():
                print(f"🔍 Testing with: {test_file}")
                result = await parser.parse_design_file(test_file)

                if result['success']:
                    print(f"✅ Successfully parsed: {result['file_name']}")
                    if 'output_file' in result:
                        print(f"💾 Output saved to: {result['output_file']}")
                else:
                    print(f"❌ Error: {result['error']}")
                break
        else:
            print("⚠️  No test files found, skipping parsing test")

        print("✅ Basic test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def show_usage():
    """Show usage instructions"""
    print("\n📖 Usage Instructions:")
    print("=" * 50)
    print("1. Run the test script:")
    print("   python test_parser.py")
    print()
    print("2. Run the examples:")
    print("   python examples/basic_usage.py")
    print()
    print("3. Use in your own code:")
    print("   from src.design_parser import DesignParser")
    print("   parser = DesignParser()")
    print("   result = await parser.parse_design_file('your_file.sketch')")
    print()
    print("4. Check the output folder for parsed JSON files")

def main():
    """Main setup function"""
    print("🚀 Design Parser Program Setup")
    print("=" * 50)

    # Create directories
    create_directories()

    # Install requirements
    if not install_requirements():
        print("❌ Setup failed - could not install requirements")
        return

    # Check dependencies
    check_dependencies()

    # Run test
    asyncio.run(run_test())

    # Show usage
    show_usage()

    print("\n✅ Setup completed!")
    print("🎉 Design Parser Program is ready to use!")

if __name__ == "__main__":
    main()

