"""Preferenze persistenti dell'app (tema, accento, …)."""

from __future__ import annotations

from src.database.db import database_version, get_connection

DEFAULT_THEME = "dark"
DEFAULT_ACCENT = "blue"

VALID_THEMES = ("dark", "light")
VALID_ACCENTS = ("blue", "green", "amber", "violet")


_settings_cache: tuple[object, dict[str, str]] | None = None


def _all_settings() -> dict[str, str]:
    """Tutte le preferenze, rilette solo quando il database cambia.

    Tema e accento si leggono più volte a ogni interazione: sul telefono
    ogni query costa, quindi si tiene una copia finché nessuno scrive.
    """
    global _settings_cache
    version = database_version()
    cached = _settings_cache
    if cached is not None and cached[0] == version:
        return cached[1]
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    values = {str(row["key"]): str(row["value"]) for row in rows}
    _settings_cache = (version, values)
    return values


def get_setting(key: str, default: str | None = None) -> str | None:
    value = _all_settings().get(key)
    return default if value is None else value


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        conn.commit()
    global _settings_cache
    _settings_cache = None


def get_theme_mode() -> str:
    value = get_setting("theme", DEFAULT_THEME) or DEFAULT_THEME
    return value if value in VALID_THEMES else DEFAULT_THEME


def get_accent() -> str:
    value = get_setting("accent", DEFAULT_ACCENT) or DEFAULT_ACCENT
    return value if value in VALID_ACCENTS else DEFAULT_ACCENT


def set_theme_preferences(*, theme: str, accent: str) -> None:
    if theme not in VALID_THEMES:
        raise ValueError(f"Tema non valido: {theme}")
    if accent not in VALID_ACCENTS:
        raise ValueError(f"Accento non valido: {accent}")
    set_setting("theme", theme)
    set_setting("accent", accent)
