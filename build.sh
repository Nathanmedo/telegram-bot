#!/bin/bash
set -e  # Exit immediately if any command fails

# ===== 1. INSTALL PYTHON 3.11 (OVERRIDES RENDER'S 3.13) =====
echo "🔧 Forcing Python 3.11 installation..."
sudo apt-get update && sudo apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv

# ===== 2. INSTALL SYSTEM DEPENDENCIES =====
echo "📦 Installing critical system libraries..."
sudo apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libtiff-dev \
    libqhull-dev  # Required for matplotlib 3D

# ===== 3. CREATE VIRTUAL ENVIRONMENT =====
echo "🐍 Creating Python 3.11 virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# ===== 4. UPGRADE PIP AND INSTALL REQUIREMENTS =====
echo "🚀 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt

# ===== 5. VERIFY KEY PACKAGES =====
echo "✅ Verifying installations..."
python -c "import PIL; print(f'✔ Pillow {PIL.__version__} working')"
python -c "import matplotlib; print('✔ Matplotlib imports successfully')"
python -c "import numpy; print(f'✔ NumPy {numpy.__version__} installed')"

echo "🎉 Build completed successfully!"