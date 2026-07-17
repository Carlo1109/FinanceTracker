#!/usr/bin/env bash
# Build FinanceTracker .deb for Debian/Ubuntu (amd64).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

VERSION="$(tr -d '[:space:]' < VERSION)"
ARCH="amd64"
PKG_NAME="financetracker"
DEB_ROOT="$SCRIPT_DIR/deb_root"
OUT_DIR="$ROOT/installer_output"
DIST_APP="$ROOT/dist/FinanceTracker"
SPEC="$ROOT/packaging/FinanceTracker.spec"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Questo script va eseguito su Linux."
  exit 1
fi

if [[ ! -x "$ROOT/.venv/bin/pyinstaller" ]]; then
  echo "Manca PyInstaller nel venv. Attiva .venv e: pip install -r requirements.txt"
  exit 1
fi

# pywebview su Linux richiede PyGObject (gi) + WebKitGTK di sistema.
export PYTHONPATH="/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"

if ! "$ROOT/.venv/bin/python" -c "import gi" 2>/dev/null; then
  cat <<'EOF'
Errore: non trovo il modulo 'gi' (PyGObject).

Su Ubuntu/Debian:
  sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
EOF
  exit 1
fi

echo "==> PyInstaller (onedir)"
rm -rf "$ROOT/build" "$ROOT/dist"
"$ROOT/.venv/bin/pyinstaller" \
  --noconfirm \
  --distpath "$ROOT/dist" \
  --workpath "$ROOT/build" \
  "$SPEC"

if [[ ! -x "$DIST_APP/FinanceTracker" ]]; then
  echo "Build PyInstaller fallita: non trovo $DIST_APP/FinanceTracker"
  exit 1
fi

echo "==> Staging pacchetto .deb"
rm -rf "$DEB_ROOT"
mkdir -p \
  "$DEB_ROOT/DEBIAN" \
  "$DEB_ROOT/opt/$PKG_NAME" \
  "$DEB_ROOT/usr/bin" \
  "$DEB_ROOT/usr/share/applications" \
  "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps" \
  "$DEB_ROOT/usr/share/doc/$PKG_NAME"

cp -a "$DIST_APP/." "$DEB_ROOT/opt/$PKG_NAME/"

cat > "$DEB_ROOT/usr/bin/financetracker" <<'EOF'
#!/bin/bash
exec /opt/financetracker/FinanceTracker "$@"
EOF
chmod 755 "$DEB_ROOT/usr/bin/financetracker"
chmod 755 "$DEB_ROOT/opt/$PKG_NAME/FinanceTracker"

cp "$SCRIPT_DIR/financetracker.desktop" \
  "$DEB_ROOT/usr/share/applications/financetracker.desktop"

cp "$ROOT/assets/icons/ft_logo.png" \
  "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps/financetracker.png"

cp "$ROOT/LICENSE" "$DEB_ROOT/usr/share/doc/$PKG_NAME/copyright"
gzip -9 -c "$ROOT/CHANGELOG.md" > "$DEB_ROOT/usr/share/doc/$PKG_NAME/changelog.gz"

sed "s/__VERSION__/${VERSION}/" "$SCRIPT_DIR/control.in" \
  > "$DEB_ROOT/DEBIAN/control"

INSTALLED_SIZE="$(du -sk "$DEB_ROOT/opt" "$DEB_ROOT/usr" | awk '{s+=$1} END {print s}')"
echo "Installed-Size: $INSTALLED_SIZE" >> "$DEB_ROOT/DEBIAN/control"

mkdir -p "$OUT_DIR"
DEB_FILE="$OUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "==> dpkg-deb"
fakeroot dpkg-deb --build "$DEB_ROOT" "$DEB_FILE"

echo
echo "Pacchetto pronto: $DEB_FILE"
echo "Installazione:"
echo "  sudo apt install ./$(basename "$DEB_FILE")"
echo "(oppure: sudo dpkg -i \"$DEB_FILE\" && sudo apt-get install -f)"
