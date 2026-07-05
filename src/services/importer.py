import json
from pathlib import Path

import pandas as pd


CATEGORY_CONFIG_PATH = Path("config/categories.json")


def load_category_rules() -> dict[str, list[str]]:
    if not CATEGORY_CONFIG_PATH.exists():
        return {}

    with CATEGORY_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def categorize(text: str) -> str:
    text = str(text).upper()
    rules = load_category_rules()

    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword.upper() in text:
                return category

    return "Altro"


def get_transaction_date(row) -> pd.Timestamp:
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


def import_fineco_excel(uploaded_file) -> pd.DataFrame:
    df = pd.read_excel(uploaded_file, sheet_name="Movimenti", header=12)

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

    df["entrate"] = df["entrate"].fillna(0)
    df["uscite"] = df["uscite"].fillna(0)
    df["importo"] = df["entrate"] + df["uscite"]

    df["testo"] = (
        df["descrizione"].fillna("")
        + " "
        + df["descrizione_completa"].fillna("")
    )

    df["data"] = df.apply(get_transaction_date, axis=1)
    df["mese"] = df["data"].dt.to_period("M").astype(str)

    df["categoria"] = df["testo"].apply(categorize)
    df["tipo"] = df["importo"].apply(lambda x: "Entrata" if x > 0 else "Uscita")
    df["category_source"] = "automatic"

    return df[
        [
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
    ].sort_values("data", ascending=False)