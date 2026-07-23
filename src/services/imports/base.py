from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd

OUTPUT_COLUMNS = [
    "data",
    "data_operazione",
    "data_valuta",
    "mese",
    "descrizione",
    "descrizione_completa",
    "categoria",
    "category_source",
    "tipo",
    "importo",
    "stato",
]


@dataclass(frozen=True)
class BankImporterInfo:
    id: str
    label: str
    account: str
    extensions: tuple[str, ...]
    help_text: str


class BankImporter(Protocol):
    info: BankImporterInfo

    def parse(self, uploaded_file: Any) -> pd.DataFrame:
        """Legge il file banca e restituisce lo schema interno standard."""


def read_bank_excel(uploaded_file: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Legge un Excel banca.

    openpyxl avvisa spesso su export senza stile default: è innocuo.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Workbook contains no default style",
            category=UserWarning,
            module=r"openpyxl\.styles\.stylesheet",
        )
        return pd.read_excel(uploaded_file, **kwargs)
