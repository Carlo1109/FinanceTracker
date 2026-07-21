from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.imports.base import BankImporterInfo
from src.services.imports.normalize import finalize_movements


class PayPalImporter:
    info = BankImporterInfo(
        id="paypal",
        label="PayPal CSV",
        account="PayPal",
        extensions=(".csv",),
        help_text=(
            "Export attività PayPal in CSV (header in riga 1). "
            "Importi con virgola decimale supportati. "
            "Se la cartella sembra vuota, passa a 'Tutti i file' "
            "oppure trascina il file qui."
        ),
    )

    def parse(self, uploaded_file: Any) -> pd.DataFrame:
        df = self._read_csv(uploaded_file)

        date_col = self._find_column(
            df.columns,
            candidates=("Data", "Date"),
            contains=("data", "date"),
        )
        name_col = self._find_column(
            df.columns,
            candidates=("Nome", "Name"),
            contains=("nome", "name"),
        )
        type_col = self._find_column(
            df.columns,
            candidates=("Tipo", "Type"),
            contains=("tipo", "type"),
        )
        status_col = self._find_column(
            df.columns,
            candidates=("Stato", "Status"),
            contains=("stato", "status"),
        )
        amount_col = self._find_column(
            df.columns,
            candidates=("Netto", "Net", "Lordo", "Gross"),
            contains=("netto", "net", "lordo", "gross"),
        )
        notes_col = self._find_column(
            df.columns,
            candidates=("Nota", "Note", "Notes", "Oggetto", "Subject"),
            contains=("nota", "note", "oggetto", "subject"),
        )

        if date_col is None or amount_col is None:
            raise ValueError(
                "CSV PayPal non valido: servono almeno le colonne "
                "Data/Date e Netto/Lordo (o Net/Gross)."
            )

        if status_col is not None:
            status_normalized = df[status_col].fillna("").astype(str).str.strip().str.lower()
            completed = status_normalized.isin(
                {"completato", "completed", "completo"}
            )
            # Se nessuna riga matcha, non filtrare (header diversi)
            if completed.any():
                df = df.loc[completed].copy()

        names = self._series_or_empty(df, name_col)
        types = self._series_or_empty(df, type_col)
        notes = self._series_or_empty(df, notes_col)

        description = (
            names.str.strip()
            + " "
            + types.str.strip()
            + " "
            + notes.str.strip()
        ).str.replace(r"\s+", " ", regex=True).str.strip()

        full_description = description

        amounts = df[amount_col].map(self._parse_amount)

        mapped = pd.DataFrame(
            {
                "data_operazione": pd.to_datetime(
                    df[date_col],
                    dayfirst=True,
                    errors="coerce",
                ),
                "data_valuta": pd.to_datetime(
                    df[date_col],
                    dayfirst=True,
                    errors="coerce",
                ),
                "descrizione": description,
                "descrizione_completa": full_description.fillna("").astype(str),
                "importo": amounts,
                "stato": (
                    df[status_col].fillna("").astype(str)
                    if status_col is not None
                    else ""
                ),
            }
        )

        return finalize_movements(mapped)

    @staticmethod
    def _series_or_empty(df: pd.DataFrame, column: str | None) -> pd.Series:
        if column is None:
            return pd.Series([""] * len(df), index=df.index, dtype=str)
        return df[column].fillna("").astype(str)

    @staticmethod
    def _read_csv(uploaded_file: Any) -> pd.DataFrame:
        last_error: Exception | None = None

        for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                uploaded_file.seek(0)
            except Exception:  # noqa: BLE001
                pass

            try:
                return pd.read_csv(uploaded_file, encoding=encoding)
            except Exception as error:  # noqa: BLE001
                last_error = error

        raise ValueError(
            f"Impossibile leggere il CSV PayPal: {last_error}"
        )

    @staticmethod
    def _parse_amount(value: Any) -> float:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0

        text = str(value).strip()
        if not text:
            return 0.0

        # Formato IT: -10,99  /  EN: -10.99  /  con migliaia 1.234,56
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            text = text.replace(".", "").replace(",", ".")

        text = text.replace(" ", "").replace("€", "")
        try:
            return float(text)
        except ValueError:
            return 0.0

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
            if any(token == label or token in label for token in contains):
                # Evita match troppo larghi tipo "Transaction ID"
                if "id" in label and "netto" not in contains and "net" not in contains:
                    continue
                return col

        return None
