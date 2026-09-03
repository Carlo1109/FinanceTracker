import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

import re

from src.database.db import DATA_DIR, DB_PATH
from src.theme.colors import ensure_unique_category_colors


USER_CATEGORY_CONFIG_PATH = DATA_DIR / "categories.json"
DEFAULT_CATEGORY_ICON = "❓"

_category_definitions_cache: dict[str, dict[str, Any]] | None = None


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
    "Trasferimenti interni": "🔁",
    "Stipendio": "💼",
    "Rimborsi": "↩️",
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


def invalidate_category_cache() -> None:
    global _category_definitions_cache
    _category_definitions_cache = None


def _merge_new_bundled_categories(
    definitions: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], bool]:
    """
    Aggiunge categorie presenti nel JSON di default ma assenti
    nella copia utente, senza sovrascrivere quelle già personalizzate.
    """
    bundled_path = get_bundled_category_config_path()

    if not bundled_path.exists():
        return definitions, False

    try:
        with bundled_path.open("r", encoding="utf-8") as file:
            bundled_raw = json.load(file)
    except (json.JSONDecodeError, OSError):
        return definitions, False

    bundled_definitions, _ = _normalize_category_definitions(bundled_raw)
    changed = False

    for category_name, category_data in bundled_definitions.items():
        if category_name not in definitions:
            definitions[category_name] = category_data
            changed = True

    return definitions, changed


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
            color = None
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
            color = raw_value.get("color")

            if "keywords" not in raw_value or "icon" not in raw_value:
                changed = True
        else:
            keywords = []
            icon = DEFAULT_CATEGORY_ICONS.get(
                category_name,
                DEFAULT_CATEGORY_ICON,
            )
            color = None
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

        category_entry = {
            "icon": str(icon).strip() or DEFAULT_CATEGORY_ICON,
            "keywords": normalized_keywords,
        }

        if color:
            category_entry["color"] = str(color).strip()

        normalized[category_name] = category_entry

    if "Altro" not in normalized:
        normalized["Altro"] = {
            "icon": "❓",
            "keywords": [],
        }
        changed = True

    if "Trasferimenti interni" not in normalized:
        normalized["Trasferimenti interni"] = {
            "icon": "🔁",
            "keywords": [
                "GIROCONTO",
                "TRASFERIMENTO",
                "BONIFICO INTERNO",
                "TRA CONTI",
            ],
        }
        changed = True

    return normalized, changed


def _copy_category_data(
    data: dict[str, Any],
) -> dict[str, Any]:
    copied = {
        "icon": data["icon"],
        "keywords": list(data["keywords"]),
    }

    if data.get("color"):
        copied["color"] = str(data["color"])

    return copied


def load_category_definitions() -> dict[str, dict[str, Any]]:
    """
    Carica categorie, icone, keyword e colori.

    Se trova il vecchio formato JSON, lo migra automaticamente
    senza perdere categorie o parole chiave.

    Aggiunge anche eventuali nuove categorie del default bundled
    che non sono ancora nella copia utente.
    """
    global _category_definitions_cache

    if _category_definitions_cache is not None:
        return {
            category: _copy_category_data(data)
            for category, data in _category_definitions_cache.items()
        }

    config_path = ensure_category_config()

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (json.JSONDecodeError, OSError):
        raw_data = {}

    definitions, changed = _normalize_category_definitions(raw_data)
    definitions, merged = _merge_new_bundled_categories(definitions)
    definitions, colored = ensure_unique_category_colors(definitions)

    if changed or merged or colored:
        try:
            save_category_definitions(definitions)
        except OSError:
            # Se la copia utente non è scrivibile, usa comunque
            # le categorie unite per questa sessione.
            _category_definitions_cache = {
                category: _copy_category_data(data)
                for category, data in definitions.items()
            }
    else:
        _category_definitions_cache = {
            category: _copy_category_data(data)
            for category, data in definitions.items()
        }

    return {
        category: _copy_category_data(data)
        for category, data in definitions.items()
    }


def save_category_definitions(
    definitions: dict[str, dict[str, Any]],
) -> None:
    """Salva il nuovo formato delle categorie."""
    global _category_definitions_cache

    config_path = ensure_category_config()
    normalized, _ = _normalize_category_definitions(definitions)
    normalized, _ = ensure_unique_category_colors(normalized)

    with config_path.open("w", encoding="utf-8") as file:
        json.dump(
            normalized,
            file,
            indent=2,
            ensure_ascii=False,
        )

    _category_definitions_cache = {
        category: _copy_category_data(data)
        for category, data in normalized.items()
    }


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


_KEYWORD_NOISE = {
    "SUMUP",
    "PAGAMENTO",
    "PAGAMENTI",
    "TRAMITE",
    "POS",
    "CARTA",
    "CARTE",
    "ADDEBITO",
    "ACCREDITO",
    "BONIFICO",
    "SEPA",
    "SCT",
    "SDD",
    "TRN",
    "OPERAZIONE",
    "PRELIEVO",
    "BANCOMAT",
    "CONTANTE",
    "EURO",
    "EUR",
    "IMPORTO",
    "PAYPAL",
    "VOSTRO",
    "FAVORE",
    "PRESSO",
    "NOSTRO",
    "DEBITO",
    "CREDITO",
    "CASH",
    "CARD",
    "PAYMENT",
    "TRANSFER",
    "TRANSACTION",
    "DA",
    "DI",
    "DEL",
    "DELLA",
    "DELLO",
    "DEI",
    "DELLE",
    "IL",
    "LO",
    "LA",
    "UN",
    "UNA",
    "THE",
    "AND",
    "PER",
    "CON",
    "SUL",
    "SULLA",
    "VIA",
    "PIAZZA",
    "VS",
    "NS",
    "CC",
    "NR",
    "NUM",
    "N",
}


def _keyword_tokens(text: str) -> list[str]:
    normalized = re.sub(r"[^0-9A-ZÀ-Ü]+", " ", str(text).upper())
    tokens: list[str] = []
    for raw in normalized.split():
        token = raw.strip()
        if len(token) < 4:
            continue
        if token in _KEYWORD_NOISE:
            continue
        if token.isdigit():
            continue
        if sum(ch.isdigit() for ch in token) > len(token) / 2:
            continue
        tokens.append(token)
    return tokens


def suggest_keyword_from_text(
    text: str,
    category: str,
    definitions: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    """
    Propone una keyword da una descrizione ricategorizzata.

    Evita Altro, keyword già presenti e token generici da estratto conto.
    Se un token singolo è già di un'altra categoria, prova una frase
    più specifica (es. AMAZON EU invece di AMAZON).
    """
    category = str(category).strip()
    if not category or category == "Altro":
        return None

    if definitions is None:
        definitions = load_category_definitions()

    if category not in definitions:
        return None

    if categorize(text, definitions) == category:
        return None

    tokens = _keyword_tokens(text)
    if not tokens:
        return None

    target_keywords = {
        str(keyword).strip().upper()
        for keyword in definitions[category]["keywords"]
    }
    other_keywords = {
        str(keyword).strip().upper()
        for name, data in definitions.items()
        if name != category
        for keyword in data.get("keywords", [])
    }

    first = tokens[0]
    phrases: list[str] = []
    if len(tokens) >= 3:
        phrases.append(" ".join(tokens[:3]))
    if len(tokens) >= 2:
        phrases.append(" ".join(tokens[:2]))

    if first in other_keywords:
        candidates = phrases + [first]
    else:
        candidates = [first] + phrases

    longest = max(tokens, key=len)
    if longest not in candidates:
        candidates.append(longest)

    fallback: str | None = None
    for candidate in candidates:
        if len(candidate) > 40:
            continue
        if candidate in target_keywords:
            continue
        if candidate in other_keywords and " " not in candidate:
            if fallback is None:
                fallback = candidate
            continue
        return candidate

    return fallback


def categorize(
    text: str,
    definitions: dict[str, dict[str, Any]] | None = None,
) -> str:
    normalized_text = str(text).upper()

    if definitions is None:
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
