#!/bin/bash
# ============================================================
# AI Newsletter Bot — Setup Script
# ============================================================
# This script sets up the AI Newsletter Bot on your system.
# Run: chmod +x setup.sh && ./setup.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
VENV_DIR="$SCRIPT_DIR/venv"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║     🤖 AI Newsletter Bot — Setup             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check Python
echo "🔍 Checking Python installation..."
if ! command -v $PYTHON &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "   ✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
    echo "   ✅ Virtual environment created"
else
    echo "   ✅ Virtual environment already exists"
fi

# Activate
source "$VENV_DIR/bin/activate"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q 2>/dev/null || {
    echo "   ⚠️  Some optional packages failed. Installing core dependencies..."
    pip install pyyaml requests beautifulsoup4 lxml jinja2 schedule python-dateutil colorama -q
}
echo "   ✅ Dependencies installed"

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p "$SCRIPT_DIR/history" "$SCRIPT_DIR/logs"
echo "   ✅ Directories ready"

# Verify
echo ""
echo "🧪 Running quick verification..."
cd "$SCRIPT_DIR"
$PYTHON -c "
from src.config_loader import load_config
config = load_config()
print('   ✅ Configuration loaded successfully')
print(f'   📋 Tracking {len(config.get(\"accounts\", []))} X accounts')
print(f'   🔑 {len(config.get(\"keywords\", []))} AI keywords configured')
"

echo ""
echo "════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml with your Gmail credentials"
echo "  2. Run demo:       python main.py --demo"
echo "  3. Send test:      python main.py --test-email"
echo "  4. Run once:       python main.py"
echo "  5. Start daily:    python main.py --schedule"
echo "  6. Setup cron:     ./setup_cron.sh"
echo "════════════════════════════════════════════════"
echo ""
