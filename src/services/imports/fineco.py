from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.imports.base import BankImporterInfo
from src.services.imports.normalize import finalize_movements


class FinecoImporter:
    info = BankImporterInfo(
        id="fineco",
        label="Fineco Excel",
        account="Fineco",
        extensions=(".xlsx", ".xls"),
        help_text=(
            "Export movimenti Fineco in Excel (.xlsx / .xls). "
            "Se la cartella sembra vuota, passa a 'Tutti i file' "
            "nel dialog oppure trascina il file qui."
        ),
    )

    def parse(self, uploaded_file: Any) -> pd.DataFrame:
        df = pd.read_excel(
            uploaded_file,
            sheet_name="Movimenti",
            header=12,
        )

        df = df.rename(
            columns={
                "Data_Operazione": "data_operazione",
                "Data_Valuta": "data_valuta",
                "Entrate": "entrate",
                "Uscite": "uscite",
                "Descrizione": "descrizione",
                "Descrizione_Completa": "descrizione_completa",
                "Stato": "stato",
            }
        )

        df["entrate"] = pd.to_numeric(df["entrate"], errors="coerce").fillna(0)
        df["uscite"] = pd.to_numeric(df["uscite"], errors="coerce").fillna(0)
        df["importo"] = df["entrate"] + df["uscite"]
        df["descrizione"] = df["descrizione"].fillna("")
        df["descrizione_completa"] = df["descrizione_completa"].fillna("")
        df["stato"] = df["stato"].fillna("")

        return finalize_movements(
            df[
                [
                    "data_operazione",
                    "data_valuta",
                    "descrizione",
                    "descrizione_completa",
                    "importo",
                    "stato",
                ]
            ]
        )
