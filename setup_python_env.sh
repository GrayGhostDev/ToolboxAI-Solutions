#!/bin/bash

# Setup Python Environment for ToolBoxAI-Solutions
# This script properly configures the Python environment and paths

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export the project root to PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Path to the virtual environment
VENV_PATH="${SCRIPT_DIR}/ToolboxAI-Roblox-Environment/venv_clean"

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please create it first with: python -m venv $VENV_PATH"
    exit 1
fi

# Activate the virtual environment
source "${VENV_PATH}/bin/activate"

echo "✅ Python environment configured"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   Python: $(which python)"
echo "   Version: $(python --version)"

# Export for other scripts
export PROJECT_ROOT="${SCRIPT_DIR}"
export PYTHON_BIN="${VENV_PATH}/bin/python"

# Alias for running Python with correct path
alias pyrun="${PYTHON_BIN} -B"

echo ""
echo "📝 Usage:"
echo "   - Run Python scripts: pyrun script.py"
echo "   - Test imports: python -c 'from database.models import EducationalContent'"
echo "   - Run tests: pytest"