"""Colori stabili e univoci per categoria (torta e UI)."""

from __future__ import annotations

from typing import Any


# Palette ampia: default + categorie custom senza collisioni.
CATEGORY_PALETTE = [
    "#34d399",
    "#60a5fa",
    "#38bdf8",
    "#818cf8",
    "#fbbf24",
    "#e879f9",
    "#2dd4bf",
    "#5eead4",
    "#fb7185",
    "#f59e0b",
    "#4ade80",
    "#22d3ee",
    "#a78bfa",
    "#93c5fd",
    "#fdba74",
    "#94a3b8",
    "#f87171",
    "#c084fc",
    "#86efac",
    "#f9a8d4",
    "#67e8f9",
    "#fcd34d",
    "#6ee7b7",
    "#7dd3fc",
    "#d8b4fe",
    "#fda4af",
    "#bbf7d0",
    "#a5b4fc",
    "#fde68a",
    "#99f6e4",
    "#fecdd3",
    "#bfdbfe",
    "#d9f99d",
    "#c4b5fd",
    "#fed7aa",
    "#a7f3d0",
    "#bae6fd",
    "#fbcfe8",
    "#e2e8f0",
    "#80e848",
]

# Preferenza iniziale per le categorie di default.
CATEGORY_COLORS: dict[str, str] = {
    "Alimentari": "#34d399",
    "Trasporti": "#60a5fa",
    "Auto": "#38bdf8",
    "Gestione Conti": "#818cf8",
    "Bar & Ristoranti": "#fbbf24",
    "Shopping": "#e879f9",
    "Casa & Utenze": "#2dd4bf",
    "Casa": "#14b8a6",
    "Utenze": "#5eead4",
    "Salute & Benessere": "#fb7185",
    "Investimenti": "#f59e0b",
    "Stipendio": "#4ade80",
    "Viaggi & Vacanze": "#22d3ee",
    "Svago & Tempo libero": "#a78bfa",
    "Abbonamenti": "#93c5fd",
    "Regali & Donazioni": "#fdba74",
    "Altro": "#94a3b8",
}


def _normalize_hex(color: str) -> str:
    return str(color).strip().casefold()


def _pick_unused_color(used: set[str]) -> str:
    for color in CATEGORY_PALETTE:
        if _normalize_hex(color) not in used:
            return color

    # Esaurita la palette: genera toni distinti in HSL.
    index = len(used)
    hue = (index * 47) % 360
    return f"hsl({hue} 72% 62%)"


def ensure_unique_category_colors(
    definitions: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], bool]:
    """
    Garantisce un colore per ogni categoria, senza duplicati.

    Priorità:
    1. colore già salvato nella categoria
    2. colore preferito di default (se libero)
    3. primo colore libero della palette
    """
    changed = False
    used: set[str] = set()
    updated: dict[str, dict[str, Any]] = {}

    # Prima passata: mantieni colori già validi e non in conflitto.
    pending: list[str] = []

    for category_name, data in definitions.items():
        category_data = dict(data)
        raw_color = str(category_data.get("color", "")).strip()

        if raw_color:
            normalized = _normalize_hex(raw_color)

            if normalized not in used:
                used.add(normalized)
                category_data["color"] = raw_color
                updated[category_name] = category_data
                continue

            # Conflitto: andrà riassegnato.
            changed = True
            pending.append(category_name)
            updated[category_name] = category_data
            continue

        preferred = CATEGORY_COLORS.get(category_name)

        if preferred and _normalize_hex(preferred) not in used:
            used.add(_normalize_hex(preferred))
            category_data["color"] = preferred
            updated[category_name] = category_data
            changed = True
            continue

        pending.append(category_name)
        updated[category_name] = category_data
        changed = True

    for category_name in pending:
        color = _pick_unused_color(used)
        used.add(_normalize_hex(color))
        updated[category_name]["color"] = color

    return updated, changed


def get_category_color(
    category: str,
    definitions: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Restituisce il colore della categoria (salvato o di default)."""
    name = str(category).strip()

    if definitions and name in definitions:
        stored = str(definitions[name].get("color", "")).strip()

        if stored:
            return stored

    if name in CATEGORY_COLORS:
        return CATEGORY_COLORS[name]

    return _pick_unused_color(set())


def get_category_colors(
    categories: list[str],
    definitions: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Elenco colori allineato all'ordine delle categorie passate."""
    return [
        get_category_color(category, definitions)
        for category in categories
    ]
