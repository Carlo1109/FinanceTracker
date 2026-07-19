import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pandas as pd

import re

from src.database.db import DATA_DIR, DB_PATH


USER_CATEGORY_CONFIG_PATH = DATA_DIR / "categories.json"
DEFAULT_CATEGORY_ICON = "❓"

DEFAULT_CATEGORY_ICONS = {
    "Alimentari": "🛒",
    "Trasporti": "🚆",
    "Auto": "🚗",
    "Gestione Conti": "💳",
    "Bar & Ristoranti": "🍺",
    "Shopping": "🛍️",
    "Casa & Utenze": "🏠",
    "Salute & Benessere": "❤️",
    "Investimenti": "📈",
    "Stipendio": "💼",
    "Viaggi & Vacanze": "🏖️",
    "Svago & Tempo libero": "🎮",
    "Abbonamenti": "📺",
    "Regali & Donazioni": "🎁",
    "Altro": "❓",
}


def get_bundled_category_config_path() -> Path:
    """Restituisce il file categorie predefinito incluso nell'app."""
    if getattr(sys, "frozen", False):
        bundle_dir = Path(sys._MEIPASS)
    else:
        bundle_dir = Path(__file__).resolve().parents[2]

    return bundle_dir / "config" / "categories.json"


def ensure_category_config() -> Path:
    """Crea il file categorie personale dell'utente al primo avvio."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if USER_CATEGORY_CONFIG_PATH.exists():
        return USER_CATEGORY_CONFIG_PATH

    default_path = get_bundled_category_config_path()

    if default_path.exists():
        shutil.copy2(default_path, USER_CATEGORY_CONFIG_PATH)
    else:
        USER_CATEGORY_CONFIG_PATH.write_text(
            json.dumps(
                {
                    "Altro": {
                        "icon": "❓",
                        "keywords": [],
                    }
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return USER_CATEGORY_CONFIG_PATH


def _normalize_category_definitions(
    raw_data: Any,
) -> tuple[dict[str, dict[str, Any]], bool]:
    """
    Migra automaticamente il vecchio formato:

        "Categoria": ["KEYWORD"]

    nel nuovo formato:

        "Categoria": {
            "icon": "🛒",
            "keywords": ["KEYWORD"]
        }
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    normalized: dict[str, dict[str, Any]] = {}
    changed = False

    for raw_name, raw_value in raw_data.items():
        category_name = str(raw_name).strip()

        if not category_name:
            changed = True
            continue

        if isinstance(raw_value, list):
            keywords = raw_value
            icon = DEFAULT_CATEGORY_ICONS.get(
                category_name,
                DEFAULT_CATEGORY_ICON,
            )
            changed = True

        elif isinstance(raw_value, dict):
            keywords = raw_value.get("keywords", [])
            icon = raw_value.get(
                "icon",
                DEFAULT_CATEGORY_ICONS.get(
                    category_name,
                    DEFAULT_CATEGORY_ICON,
                ),
            )

            if "keywords" not in raw_value or "icon" not in raw_value:
                changed = True
        else:
            keywords = []
            icon = DEFAULT_CATEGORY_ICONS.get(
                category_name,
                DEFAULT_CATEGORY_ICON,
            )
            changed = True

        if not isinstance(keywords, list):
            keywords = []
            changed = True

        normalized_keywords: list[str] = []

        for keyword in keywords:
            normalized_keyword = str(keyword).strip().upper()

            if (
                normalized_keyword
                and normalized_keyword not in normalized_keywords
            ):
                normalized_keywords.append(normalized_keyword)

        normalized[category_name] = {
            "icon": str(icon).strip() or DEFAULT_CATEGORY_ICON,
            "keywords": normalized_keywords,
        }

    if "Altro" not in normalized:
        normalized["Altro"] = {
            "icon": "❓",
            "keywords": [],
        }
        changed = True

    return normalized, changed


def load_category_definitions() -> dict[str, dict[str, Any]]:
    """
    Carica categorie, icone e keyword.

    Se trova il vecchio formato JSON, lo migra automaticamente
    senza perdere categorie o parole chiave.
    """
    config_path = ensure_category_config()

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (json.JSONDecodeError, OSError):
        raw_data = {}

    definitions, changed = _normalize_category_definitions(raw_data)

    if changed:
        save_category_definitions(definitions)

    return definitions


def save_category_definitions(
    definitions: dict[str, dict[str, Any]],
) -> None:
    """Salva il nuovo formato delle categorie."""
    config_path = ensure_category_config()
    normalized, _ = _normalize_category_definitions(definitions)

    with config_path.open("w", encoding="utf-8") as file:
        json.dump(
            normalized,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_category_rules() -> dict[str, list[str]]:
    """
    Compatibilità con il codice esistente:
    restituisce soltanto le keyword per categoria.
    """
    definitions = load_category_definitions()

    return {
        category: list(data["keywords"])
        for category, data in definitions.items()
    }


def save_category_rules(rules: dict[str, list[str]]) -> None:
    """
    Compatibilità con il codice esistente:
    aggiorna le keyword conservando le icone già assegnate.
    """
    definitions = load_category_definitions()

    for category, keywords in rules.items():
        if category not in definitions:
            definitions[category] = {
                "icon": DEFAULT_CATEGORY_ICONS.get(
                    category,
                    DEFAULT_CATEGORY_ICON,
                ),
                "keywords": [],
            }

        definitions[category]["keywords"] = keywords

    save_category_definitions(definitions)


def get_category_names() -> list[str]:
    """Restituisce i nomi delle categorie nell'ordine del JSON."""
    return list(load_category_definitions().keys())


def get_category_icon(category: str) -> str:
    """Restituisce l'icona associata a una categoria."""
    definitions = load_category_definitions()

    category_data = definitions.get(category)

    if not category_data:
        return DEFAULT_CATEGORY_ICON

    return str(category_data.get("icon", DEFAULT_CATEGORY_ICON))


def add_category(
    category_name: str,
    icon: str = DEFAULT_CATEGORY_ICON,
) -> bool:
    """Crea una categoria con icona e nessuna keyword iniziale."""
    category_name = category_name.strip()
    icon = icon.strip() or DEFAULT_CATEGORY_ICON

    if not category_name:
        return False

    definitions = load_category_definitions()

    existing_names = {
        current_name.casefold()
        for current_name in definitions
    }

    if category_name.casefold() in existing_names:
        return False

    definitions[category_name] = {
        "icon": icon,
        "keywords": [],
    }

    save_category_definitions(definitions)
    return True


def update_category_icon(category: str, icon: str) -> bool:
    """Aggiorna l'icona di una categoria esistente."""
    definitions = load_category_definitions()

    if category not in definitions:
        return False

    normalized_icon = icon.strip() or DEFAULT_CATEGORY_ICON

    if definitions[category]["icon"] == normalized_icon:
        return False

    definitions[category]["icon"] = normalized_icon
    save_category_definitions(definitions)

    return True


def add_keyword_to_category(category: str, keyword: str) -> bool:
    """Aggiunge una parola chiave a una categoria."""
    keyword = keyword.strip().upper()

    if not keyword:
        return False

    definitions = load_category_definitions()

    if category not in definitions:
        return False

    keywords = definitions[category]["keywords"]

    existing_keywords = {
        str(current_keyword).strip().upper()
        for current_keyword in keywords
    }

    if keyword in existing_keywords:
        return False

    keywords.append(keyword)
    save_category_definitions(definitions)

    return True


def remove_keyword_from_category(category: str, keyword: str) -> bool:
    """Rimuove una parola chiave da una categoria."""
    definitions = load_category_definitions()

    if category not in definitions:
        return False

    normalized_keyword = keyword.strip().upper()
    keywords = definitions[category]["keywords"]

    updated_keywords = [
        current_keyword
        for current_keyword in keywords
        if str(current_keyword).strip().upper() != normalized_keyword
    ]

    if len(updated_keywords) == len(keywords):
        return False

    definitions[category]["keywords"] = updated_keywords
    save_category_definitions(definitions)

    return True


def delete_category(category: str) -> tuple[bool, int]:
    """
    Elimina una categoria.

    I movimenti che la utilizzavano vengono spostati automaticamente
    nella categoria "Altro".

    Compatibile sia con database che usano nomi italiani
    sia con database che usano nomi inglesi.
    """
    if category == "Altro":
        return False, 0

    definitions = load_category_definitions()

    if category not in definitions:
        return False, 0

    reassigned_movements = 0

    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as connection:
            columns = connection.execute(
                "PRAGMA table_info(movements)"
            ).fetchall()

            column_names = {
                column[1]
                for column in columns
            }

            if "categoria" in column_names:
                category_column = "categoria"
            elif "category" in column_names:
                category_column = "category"
            else:
                raise RuntimeError(
                    "Nel database non è stata trovata una colonna "
                    "per la categoria dei movimenti."
                )

            if "category_source" in column_names:
                cursor = connection.execute(
                    f"""
                    UPDATE movements
                    SET {category_column} = ?,
                        category_source = ?
                    WHERE {category_column} = ?
                    """,
                    ("Altro", "manual", category),
                )
            else:
                cursor = connection.execute(
                    f"""
                    UPDATE movements
                    SET {category_column} = ?
                    WHERE {category_column} = ?
                    """,
                    ("Altro", category),
                )

            reassigned_movements = max(
                cursor.rowcount,
                0,
            )

            connection.commit()

    del definitions[category]
    save_category_definitions(definitions)

    return True, reassigned_movements


def categorize(text: str) -> str:
    normalized_text = str(text).upper()
    definitions = load_category_definitions()

    best_category = "Altro"
    best_keyword_length = -1

    for category, data in definitions.items():
        for keyword in data["keywords"]:
            normalized_keyword = str(keyword).strip().upper()

            if not normalized_keyword:
                continue

            matched = False

            if len(normalized_keyword) <= 3:
                pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"
                matched = re.search(pattern, normalized_text) is not None
            else:
                matched = normalized_keyword in normalized_text

            if matched and len(normalized_keyword) > best_keyword_length:
                best_category = category
                best_keyword_length = len(normalized_keyword)

    return best_category


def get_transaction_date(row) -> pd.Timestamp:
    description = str(row.get("descrizione", "")).upper()
    full_description = str(
        row.get("descrizione_completa", "")
    ).upper()

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

    df["tipo"] = df["importo"].apply(
        lambda value: "Entrata" if value > 0 else "Uscita"
    )

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
