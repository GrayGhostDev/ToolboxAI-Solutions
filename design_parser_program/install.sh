#!/bin/bash
# Design Parser Program Installation Script

echo "🚀 Design Parser Program Setup"
echo "=================================================="

# Create directories
echo "📁 Creating directories..."
mkdir -p output examples docs
echo "✅ Directories created"

# Install Python requirements (optional)
echo "📦 Installing Python requirements (optional)..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt --user
    echo "✅ Requirements installed with --user flag"
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt --user
    echo "✅ Requirements installed with --user flag"
else
    echo "⚠️  pip not found, skipping requirements installation"
    echo "   You can install manually later with: pip install -r requirements.txt"
fi

# Check dependencies
echo "🔍 Checking dependencies..."

# Check for Pillow
if python3 -c "import PIL" 2>/dev/null; then
    echo "✅ Pillow (PIL) - Available"
else
    echo "❌ Pillow (PIL) - Not available (required for image processing)"
fi

# Check for fig2sketch
if command -v fig2sketch &> /dev/null; then
    echo "✅ fig2sketch - Available"
else
    echo "⚠️  fig2sketch - Not available (optional for Figma files)"
fi

# Check for sketch-tool
if command -v sketch-tool &> /dev/null; then
    echo "✅ sketch-tool - Available"
else
    echo "⚠️  sketch-tool - Not available (optional for Sketch files)"
fi

# Check for ffprobe
if command -v ffprobe &> /dev/null; then
    echo "✅ ffprobe - Available"
else
    echo "⚠️  ffprobe - Not available (optional for video files)"
fi

# Check for Blender
if command -v blender &> /dev/null; then
    echo "✅ Blender - Available"
else
    echo "⚠️  Blender - Not available (optional for .blend files)"
fi

echo ""
echo "📖 Usage Instructions:"
echo "=================================================="
echo "1. Run the test script:"
echo "   python3 test_parser.py"
echo ""
echo "2. Run the examples:"
echo "   python3 examples/basic_usage.py"
echo ""
echo "3. Use in your own code:"
echo "   from src.design_parser import DesignParser"
echo "   parser = DesignParser()"
echo "   result = await parser.parse_design_file('your_file.sketch')"
echo ""
echo "4. Check the output folder for parsed JSON files"
echo ""
echo "✅ Setup completed!"
echo "🎉 Design Parser Program is ready to use!"

