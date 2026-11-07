"""Rilevamento piattaforma: desktop (default) o app Android (stlite/Pyodide)."""

from __future__ import annotations

import os

# Impostata dal wrapper Android (android/web/index.html).
# Su desktop non esiste, quindi il comportamento resta quello di sempre.
IS_ANDROID = os.environ.get("FT_PLATFORM", "").strip().lower() == "android"

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ZIP_MIME = "application/zip"

# URL locale di plotly.js nell'app Android (vedi android/scripts/build-web.mjs).
# Vuoto su desktop: lì il grafico continua a includere la libreria come sempre.
PLOTLY_JS_URL = os.environ.get("FT_PLOTLY_JS_URL", "").strip() if IS_ANDROID else ""
