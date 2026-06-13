#!/usr/bin/env bash
set -e

echo "=== GymOS Enterprise — Build Script ==="
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
ELECTRON_DIR="$ROOT/electron"

echo "1. Building frontend..."
cd "$ROOT/frontend"
npm install
npm run build
echo "   ✓ Frontend built to frontend/dist"

echo "2. Installing Electron deps..."
cd "$ELECTRON_DIR"
npm install
echo "   ✓ Dependencies installed"

echo "3. Building installers..."
# Detect platform
case "$(uname -s)" in
  Darwin) npm run build:mac ;;
  Linux)  npm run build:linux ;;
  MINGW*|MSYS*|CYGWIN*) npm run build:win ;;
  *) npm run build:all ;;
esac

echo ""
echo "=== Build complete ==="
echo "Installers in: $ELECTRON_DIR/dist/"
ls -lh "$ELECTRON_DIR/dist/" 2>/dev/null || true
