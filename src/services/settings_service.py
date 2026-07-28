"""Preferenze persistenti dell'app (tema, accento, …)."""

from __future__ import annotations

from src.database.db import get_connection

DEFAULT_THEME = "dark"
DEFAULT_ACCENT = "blue"

VALID_THEMES = ("dark", "light")
VALID_ACCENTS = ("blue", "green", "amber", "violet")


def get_setting(key: str, default: str | None = None) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return default
    return str(row["value"])


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
