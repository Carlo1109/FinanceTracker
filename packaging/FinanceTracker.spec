# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_all,
    copy_metadata,
)


# packaging/FinanceTracker.spec → root del progetto
PROJECT_ROOT = Path(SPECPATH).resolve().parent
VERSION = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()


streamlit_datas, streamlit_binaries, streamlit_hidden = collect_all(
    "streamlit"
)

webview_datas, webview_binaries, webview_hidden = collect_all(
    "webview"
)

datas = [
    (str(PROJECT_ROOT / "app.py"), "."),
    (str(PROJECT_ROOT / "VERSION"), "."),
    (str(PROJECT_ROOT / "config" / "categories.json"), "config"),
    (str(PROJECT_ROOT / "assets"), "assets"),
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
    "src.components.cards",
    "src.components.navigation",
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
    "src.theme.colors",
    "src.utils",
    "src.utils.formatting",
    "src.utils.version",
]

hiddenimports += streamlit_hidden
hiddenimports += webview_hidden

# Su Linux pywebview usa GTK/WebKit via PyGObject.
if sys.platform.startswith("linux"):
    hiddenimports += [
        "gi",
        "gi.repository.Gtk",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "gi.repository.Gdk",
        "gi.repository.Pango",
        "gi.repository.WebKit2",
    ]

if sys.platform == "win32":
    icon_file = str(PROJECT_ROOT / "assets" / "icons" / "ft_logo.ico")
elif sys.platform == "darwin":
    icns = PROJECT_ROOT / "assets" / "icons" / "ft_logo.icns"
    icon_file = str(icns) if icns.exists() else None
else:
    icon_file = str(PROJECT_ROOT / "assets" / "icons" / "ft_logo.png")

analysis = Analysis(
    [str(PROJECT_ROOT / "launcher.py")],
    pathex=[str(PROJECT_ROOT)],
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

if sys.platform == "win32":
    # Windows: onefile (compatibile con installer.iss).
    exe = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        name="FinanceTracker",
        icon=icon_file,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
    )
elif sys.platform == "darwin":
    # macOS: onedir + .app (doppio click).
    exe = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name="FinanceTracker",
        icon=icon_file,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
    )

    coll = COLLECT(
        exe,
        analysis.binaries,
        analysis.datas,
        name="FinanceTracker",
    )

    app = BUNDLE(
        coll,
        name="FinanceTracker.app",
        icon=icon_file,
        bundle_identifier="com.financetracker.app",
        info_plist={
            "CFBundleName": "FinanceTracker",
            "CFBundleDisplayName": "FinanceTracker",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSPrincipalClass": "NSApplication",
        },
    )
else:
    # Linux: onedir (per .deb).
    exe = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name="FinanceTracker",
        icon=icon_file,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
    )

    coll = COLLECT(
        exe,
        analysis.binaries,
        analysis.datas,
        name="FinanceTracker",
    )
