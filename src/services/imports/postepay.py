from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.imports.base import BankImporterInfo
from src.services.imports.normalize import finalize_movements


# Header Excel PostePay in riga 3 (1-based) → header=2 in pandas.
POSTEPAY_HEADER_ROW = 2


class PostePayImporter:
    info = BankImporterInfo(
        id="postepay",
        label="PostePay Excel",
        account="PostePay",
        extensions=(".xlsx", ".xls"),
        help_text=(
            "Export movimenti PostePay in Excel (.xlsx / .xls). "
            "Il logo sopra le colonne viene ignorato. "
            "Se la cartella sembra vuota, passa a 'Tutti i file' "
            "oppure trascina il file qui."
        ),
    )

    def parse(self, uploaded_file: Any) -> pd.DataFrame:
        df = pd.read_excel(
            uploaded_file,
            header=POSTEPAY_HEADER_ROW,
        )

        # Normalizza nomi colonne (spazi / casing)
        renamed = {
            str(col).strip(): str(col).strip()
            for col in df.columns
        }
        df = df.rename(columns=renamed)

        amount_col = self._find_column(
            df.columns,
            candidates=("Importo (euro)", "Importo", "Importo euro"),
            contains=("importo",),
        )
        description_col = self._find_column(
            df.columns,
            candidates=("Descrizione operazioni", "Descrizione"),
            contains=("descrizione",),
        )

        date_cols = [
            col
            for col in df.columns
            if "data" in str(col).strip().lower()
        ]

        # Se i nomi sotto il logo sono vuoti/Unnamed, usa posizioni A/B/C/D
        if amount_col is None or description_col is None or len(date_cols) < 1:
            cols = list(df.columns)
            if len(cols) < 4:
                raise ValueError(
                    "File PostePay non valido: attese almeno 4 colonne "
                    "(date, importo, descrizione)."
                )
            date_op_col = cols[0]
            date_val_col = cols[1]
            amount_col = cols[2]
            description_col = cols[3]
        else:
            if len(date_cols) >= 2:
                date_op_col, date_val_col = date_cols[0], date_cols[1]
            else:
                date_op_col = date_val_col = date_cols[0]

        mapped = pd.DataFrame(
            {
                "data_operazione": df[date_op_col],
                "data_valuta": df[date_val_col],
                "descrizione": df[description_col].fillna("").astype(str),
                "descrizione_completa": "",
                "importo": pd.to_numeric(df[amount_col], errors="coerce").fillna(0),
                "stato": "",
            }
        )

        mapped["data_valuta"] = mapped["data_valuta"].fillna(
            mapped["data_operazione"]
        )
        mapped["data_operazione"] = mapped["data_operazione"].fillna(
            mapped["data_valuta"]
        )

        return finalize_movements(mapped)

    @staticmethod
    def _find_column(
        columns,
        *,
        candidates: tuple[str, ...],
        contains: tuple[str, ...],
    ) -> str | None:
        normalized = {str(col).strip().lower(): col for col in columns}

        for candidate in candidates:
            key = candidate.strip().lower()
            if key in normalized:
                return normalized[key]

        for col in columns:
            label = str(col).strip().lower()
            if any(token in label for token in contains):
                return col

        return None
