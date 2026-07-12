# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import (
    collect_all,
    copy_metadata,
)


streamlit_datas, streamlit_binaries, streamlit_hidden = collect_all(
    "streamlit"
)

webview_datas, webview_binaries, webview_hidden = collect_all(
    "webview"
)

datas = [
    ("app.py", "."),
    ("config/categories.json", "config"),
    ("assets", "assets"),
]

datas += streamlit_datas
datas += webview_datas
datas += copy_metadata("streamlit")
datas += copy_metadata("pandas")
datas += copy_metadata("plotly")
datas += copy_metadata("pywebview")

binaries = streamlit_binaries + webview_binaries

hiddenimports = [
    "streamlit.web.cli",
    "src.database.db",
    "src.pages.dashboard",
    "src.pages.import_data",
    "src.pages.manual_entry",
    "src.pages.movements",
    "src.pages.settings",
    "src.services.backup_service",
    "src.services.importer",
    "src.services.movement_service",
    "src.theme.style",
]

hiddenimports += streamlit_hidden
hiddenimports += webview_hidden


analysis = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="FinanceTracker",
    icon="assets/icons/ft_logo.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)