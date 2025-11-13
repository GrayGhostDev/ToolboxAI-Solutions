#!/usr/bin/env bash
# Render Build Script for ToolBoxAI Backend
# Handles scipy and scientific Python packages without requiring Fortran compiler

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

echo "========================================="
echo "ToolBoxAI Backend Build Script"
echo "========================================="

# Upgrade pip, setuptools, wheel
echo "📦 Upgrading pip, setuptools, and wheel..."
python -m pip install --upgrade pip setuptools wheel

# Install packages that have binary wheels for most platforms
echo "📦 Installing packages with binary wheels..."
pip install --only-binary=:all: \
    numpy==1.26.4 \
    pandas==2.2.3 \
    || echo "⚠️  Some packages don't have binary wheels, will try with --prefer-binary"

# Install critical database drivers with binary wheels
echo "📦 Installing critical database drivers..."
pip install --prefer-binary asyncpg==0.29.0 || exit 1  # Critical - must succeed

# Install scipy and scikit-learn with fallback to older versions if needed
echo "📦 Installing scipy and scikit-learn (optional)..."
pip install --prefer-binary scipy==1.13.1 scikit-learn==1.5.2 \
    || pip install --prefer-binary scipy==1.11.4 scikit-learn==1.3.2 \
    || echo "⚠️  scipy/scikit-learn installation failed, continuing without them"

# Install pyarrow (optional - for columnar data)
echo "📦 Installing pyarrow (optional)..."
pip install --prefer-binary pyarrow==14.0.2 \
    || echo "⚠️  pyarrow installation failed, continuing without it"

# Install all other requirements (skip packages already installed)
echo "📦 Installing remaining requirements..."
pip install -r requirements.txt --no-deps || true  # Install without dependencies
pip install -r requirements.txt  # Then install with dependencies (will skip already installed)

# Verify critical packages
echo "✅ Verifying installation..."
python -c "import fastapi; print(f'✓ FastAPI {fastapi.__version__}')" || exit 1
python -c "import redis; print(f'✓ Redis {redis.__version__}')" || exit 1
python -c "import sqlalchemy; print(f'✓ SQLAlchemy {sqlalchemy.__version__}')" || exit 1
python -c "import pydantic; print(f'✓ Pydantic {pydantic.__version__}')" || exit 1
python -c "import asyncpg; print(f'✓ asyncpg {asyncpg.__version__}')" || exit 1

# Verify optional scientific packages (don't fail if missing)
python -c "import numpy; print(f'✓ NumPy {numpy.__version__}')" || echo "⚠️  NumPy not installed"
python -c "import pandas; print(f'✓ Pandas {pandas.__version__}')" || echo "⚠️  Pandas not installed"
python -c "import scipy; print(f'✓ SciPy {scipy.__version__}')" || echo "⚠️  SciPy not installed"
python -c "import sklearn; print(f'✓ scikit-learn {sklearn.__version__}')" || echo "⚠️  scikit-learn not installed"
python -c "import pyarrow; print(f'✓ pyarrow {pyarrow.__version__}')" || echo "⚠️  pyarrow not installed"

echo "========================================="
echo "✅ Build completed successfully!"
echo "========================================="
