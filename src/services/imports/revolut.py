from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.imports.base import BankImporterInfo
from src.services.imports.normalize import finalize_movements


class RevolutImporter:
    info = BankImporterInfo(
        id="revolut",
        label="Revolut CSV",
        account="Revolut",
        extensions=(".csv",),
        help_text=(
            "Export Revolut in CSV (header in riga 1). "
            "Se la cartella sembra vuota, passa a 'Tutti i file' "
            "nel dialog oppure trascina il file qui."
        ),
    )

    def parse(self, uploaded_file: Any) -> pd.DataFrame:
        df = pd.read_csv(uploaded_file)

        required = {
            "Data di inizio",
            "Data di completamento",
            "Descrizione",
            "Importo",
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                "CSV Revolut non valido. Colonne mancanti: "
                + ", ".join(sorted(missing))
            )

        mapped = pd.DataFrame(
            {
                "data_operazione": pd.to_datetime(
                    df["Data di inizio"],
                    errors="coerce",
                ),
                "data_valuta": pd.to_datetime(
                    df["Data di completamento"],
                    errors="coerce",
                ),
                "descrizione": df["Descrizione"].fillna("").astype(str),
                "descrizione_completa": "",
                "importo": pd.to_numeric(df["Importo"], errors="coerce").fillna(0),
                "stato": (
                    df["State"].fillna("").astype(str)
                    if "State" in df.columns
                    else ""
                ),
            }
        )

        mapped["data_valuta"] = mapped["data_valuta"].fillna(
            mapped["data_operazione"]
        )
        mapped["data_operazione"] = mapped["data_operazione"].fillna(
            mapped["data_valuta"]
        )

        return finalize_movements(mapped)
