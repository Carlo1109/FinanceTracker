import json
from pathlib import Path

import pandas as pd


CATEGORY_CONFIG_PATH = Path("config/categories.json")


def load_category_rules() -> dict[str, list[str]]:
    if not CATEGORY_CONFIG_PATH.exists():
        return {}

    with CATEGORY_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)
    
def save_category_rules(rules: dict[str, list[str]]) -> None:
    CATEGORY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CATEGORY_CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            rules,
            file,
            indent=2,
            ensure_ascii=False,
        )


def add_category(category_name: str) -> bool:
    category_name = category_name.strip()

    if not category_name:
        return False

    rules = load_category_rules()

    existing_names = {name.casefold() for name in rules}

    if category_name.casefold() in existing_names:
        return False

    rules[category_name] = []
    save_category_rules(rules)

    return True


def add_keyword_to_category(category: str, keyword: str) -> bool:
    keyword = keyword.strip().upper()

    if not keyword:
        return False

    rules = load_category_rules()

    if category not in rules:
        return False

    existing_keywords = {
        current_keyword.strip().upper()
        for current_keyword in rules[category]
    }

    if keyword in existing_keywords:
        return False

    rules[category].append(keyword)
    save_category_rules(rules)

    return True

def remove_keyword_from_category(category: str, keyword: str) -> bool:
    rules = load_category_rules()

    if category not in rules:
        return False

    normalized_keyword = keyword.strip().upper()

    updated_keywords = [
        current_keyword
        for current_keyword in rules[category]
        if current_keyword.strip().upper() != normalized_keyword
    ]

    if len(updated_keywords) == len(rules[category]):
        return False

    rules[category] = updated_keywords
    save_category_rules(rules)

    return True


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