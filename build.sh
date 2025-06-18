#!/bin/bash
set -e  # Exit on error

# ===== 1. USE RENDER'S PYTHON (NO VENV) =====
echo "🐍 Using Render's Python environment directly"

# ===== 2. INSTALL BINARY WHEELS =====
echo "📦 Installing Python packages (binary wheels only)..."
pip install --upgrade pip setuptools wheel
pip install \
    --no-deps \
    --only-binary=:all: \
    --no-cache-dir \
    -r requirements.txt

# ===== 3. VERIFY INSTALLS =====
echo "✅ Verifying critical packages..."
python -c "import PIL; print(f'✔ Pillow {PIL.__version__} working')"
python -c "import numpy; print(f'✔ NumPy {numpy.__version__}')"
python -c "import matplotlib; print('✔ Matplotlib imports OK')"

echo "🎉 Build completed successfully!"