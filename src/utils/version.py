import sys
from functools import lru_cache
from pathlib import Path


def _version_candidates() -> list[Path]:
    if getattr(sys, "frozen", False):
        return [
            Path(sys._MEIPASS) / "VERSION",
            Path(sys.executable).resolve().parent / "VERSION",
        ]

    return [Path(__file__).resolve().parents[2] / "VERSION"]


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """
    Legge la versione dal file VERSION in root.

    Restituisce sempre il formato visualizzato in UI, es. "v1.0.1".
    """
    for path in _version_candidates():
        if not path.exists():
            continue

        version = path.read_text(encoding="utf-8").strip()

        if not version:
            continue

        return version if version.startswith("v") else f"v{version}"

    return "v0.0.0"
