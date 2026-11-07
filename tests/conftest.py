"""
Configurazione comune dei test.

I test usano una cartella dati temporanea (mai i tuoi dati veri):
FT_DATA_DIR va impostata PRIMA di importare src, perché il percorso
del database viene calcolato all'import.
"""

import os
import sys
import tempfile
from pathlib import Path

_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="financetracker-tests-"))
os.environ["FT_DATA_DIR"] = str(_TEST_DATA_DIR)
os.environ.pop("FT_PLATFORM", None)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from src.database import db  # noqa: E402
from src.services import categories  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    """Ogni test parte da un database e da categorie nuovi."""
    for name in ("finance_tracker.db", "categories.json"):
        (_TEST_DATA_DIR / name).unlink(missing_ok=True)
    categories.invalidate_category_cache()
    db.init_db()
    yield
    categories.invalidate_category_cache()


class UploadedFile:
    """Imita il file caricato da st.file_uploader (getvalue/read/seek/name)."""

    def __init__(self, name: str, data: bytes):
        import io

        self.name = name
        self._buffer = io.BytesIO(data)

    def getvalue(self) -> bytes:
        return self._buffer.getvalue()

    def read(self, *args):
        return self._buffer.read(*args)

    def seek(self, *args):
        return self._buffer.seek(*args)

    def tell(self):
        return self._buffer.tell()

    def readable(self):
        return True

    def seekable(self):
        return True


@pytest.fixture
def uploaded_file():
    return UploadedFile
