from __future__ import annotations

import pandas as pd

from src.services.categories import categorize, load_category_definitions
from src.services.imports.base import OUTPUT_COLUMNS
from src.utils.formatting import movement_type_from_amount


def get_transaction_date(row: pd.Series) -> pd.Timestamp:
    description = str(row.get("descrizione", "")).upper()
    full_description = str(row.get("descrizione_completa", "")).upper()
    text = f"{description} {full_description}"

    is_debit_card = (
        "VISA DEBIT" in text
        or "PAGAMENTO VISA" in text
        or "PAGAMENTO POS" in text
        or "CARTA DI DEBITO" in text
    )

    if is_debit_card and pd.notna(row.get("data_valuta")):
        return row["data_valuta"]

    if pd.notna(row.get("data_operazione")):
        return row["data_operazione"]

    return row["data_valuta"]


def _to_datetime_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, dayfirst=True, errors="coerce")


def finalize_movements(df: pd.DataFrame) -> pd.DataFrame:
    """
    Completa lo schema interno: date, mese, categoria, tipo.
    Richiede colonne: data_operazione, data_valuta, descrizione,
    descrizione_completa, importo, stato.
    """
    result = df.copy()

    result["data_operazione"] = _to_datetime_series(result["data_operazione"])
    result["data_valuta"] = _to_datetime_series(result["data_valuta"])

    result["descrizione"] = result["descrizione"].fillna("").astype(str)
    result["descrizione_completa"] = (
        result["descrizione_completa"].fillna("").astype(str)
    )
    result["stato"] = result["stato"].fillna("").astype(str)
    result["importo"] = pd.to_numeric(result["importo"], errors="coerce").fillna(0.0)

    result["testo"] = (
        result["descrizione"] + " " + result["descrizione_completa"]
    )

    result["data"] = result.apply(get_transaction_date, axis=1)

    # Scarta righe senza data utilizzabile
    result = result[result["data"].notna()].copy()

    result["mese"] = result["data"].dt.to_period("M").astype(str)

    category_definitions = load_category_definitions()
    result["categoria"] = result["testo"].apply(
        lambda text: categorize(text, category_definitions)
    )
    result["tipo"] = result["importo"].apply(movement_type_from_amount)
    result["category_source"] = "automatic"

    return (
        result[OUTPUT_COLUMNS]
        .sort_values("data", ascending=False)
        .reset_index(drop=True)
    )
