#!/bin/bash
set -e  # Exit immediately if any command fails

# ===== 1. INSTALL SYSTEM DEPENDENCIES =====
echo "📦 Installing critical system libraries..."
apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libtiff-dev \
    libqhull-dev

# ===== 2. CREATE VIRTUAL ENVIRONMENT =====
echo "🐍 Creating Python 3.11 virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# ===== 3. INSTALL REQUIREMENTS =====
echo "🚀 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt

# ===== 4. VERIFY INSTALLATIONS =====
echo "✅ Verifying installations..."
python -c "import PIL; print(f'✔ Pillow {PIL.__version__} working')"
python -c "import matplotlib; print('✔ Matplotlib imports successfully')"

echo "🎉 Build completed successfully!"