#!/usr/bin/env bash
# Build FinanceTracker.app for macOS (doppio click).
# Lo zip serve solo per caricare l'artefatto su GitHub Releases.
# Nessuna firma/notarizzazione: Gatekeeper mostrerà un warning.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

VERSION="$(tr -d '[:space:]' < VERSION)"
SPEC="$ROOT/packaging/FinanceTracker.spec"
OUT_DIR="$ROOT/installer_output"
APP_PATH="$ROOT/dist/FinanceTracker.app"
ICNS_PATH="$ROOT/assets/icons/ft_logo.icns"
PNG_PATH="$ROOT/assets/icons/ft_logo.png"
ICONSET_DIR="$SCRIPT_DIR/ft_logo.iconset"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Questo script va eseguito su macOS."
  exit 1
fi

if [[ ! -x "$ROOT/.venv/bin/pyinstaller" ]]; then
  echo "Manca PyInstaller nel venv. Attiva .venv e: pip install -r requirements.txt"
  exit 1
fi

echo "==> Icona .icns"
rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$PNG_PATH" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$PNG_PATH" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET_DIR" -o "$ICNS_PATH"
rm -rf "$ICONSET_DIR"

echo "==> PyInstaller (.app)"
rm -rf "$ROOT/build" "$ROOT/dist"
"$ROOT/.venv/bin/pyinstaller" \
  --noconfirm \
  --distpath "$ROOT/dist" \
  --workpath "$ROOT/build" \
  "$SPEC"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Build PyInstaller fallita: non trovo $APP_PATH"
  exit 1
fi

ARCH="$(uname -m)"
mkdir -p "$OUT_DIR"
ZIP_FILE="$OUT_DIR/FinanceTracker_${VERSION}_macos_${ARCH}.zip"

echo "==> Zip per GitHub Release (contiene FinanceTracker.app)"
rm -f "$ZIP_FILE"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_FILE"

echo
echo "App pronta: $APP_PATH"
echo "Pacchetto Release: $ZIP_FILE"
echo "Uso: scompatta lo zip → doppio click su FinanceTracker.app"
echo "Nota: senza notarizzazione macOS mostrerà un warning al primo avvio."
