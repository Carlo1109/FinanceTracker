from __future__ import annotations

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
