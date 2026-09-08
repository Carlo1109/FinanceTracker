"""Salvataggio in Download, uguale su tutti i sistemi."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _get_downloads_dir() -> Path:
    if sys.platform == "win32":
        known = _windows_known_downloads()
        if known is not None:
            return known

    xdg = os.environ.get("XDG_DOWNLOAD_DIR", "").strip()
    if xdg:
        path = Path(xdg).expanduser()
        if path.is_dir():
            return path

    if sys.platform != "win32":
        try:
            output = subprocess.check_output(
                ["xdg-user-dir", "DOWNLOAD"],
                text=True,
                timeout=2,
            ).strip()
            if output:
                path = Path(output)
                if path.is_dir():
                    return path
        except (OSError, subprocess.SubprocessError):
            pass

    for name in ("Downloads", "Scaricati", "Download"):
        path = Path.home() / name
        if path.is_dir():
            return path

    fallback = Path.home() / "Downloads"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _windows_known_downloads() -> Path | None:
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8),
        ]

    folder_id = GUID(
        0x374DE290,
        0x123F,
        0x4565,
        (wintypes.BYTE * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B),
    )
    path_ptr = ctypes.c_wchar_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(
        ctypes.byref(folder_id),
        0,
        None,
        ctypes.byref(path_ptr),
    )
    if result != 0 or not path_ptr.value:
        return None
    path = Path(path_ptr.value)
    ctypes.windll.ole32.CoTaskMemFree(path_ptr)
    return path if path.is_dir() else None


def _unique_path(directory: Path, file_name: str) -> Path:
    target = directory / file_name
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _save_bytes_to_downloads(data: bytes, file_name: str) -> Path:
    directory = _get_downloads_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = _unique_path(directory, file_name)
    path.write_bytes(data)
    return path


def _reveal_in_file_manager(path: Path) -> None:
    resolved = str(path.resolve())
    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", f"/select,{resolved}"])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", resolved])
        else:
            subprocess.Popen(["xdg-open", str(path.parent)])
    except OSError:
        return


def save_and_reveal(data: bytes, file_name: str) -> Path:
    path = _save_bytes_to_downloads(data, file_name)
    _reveal_in_file_manager(path)
    return path
