"""Palette temi e accenti FinanceTracker."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccentPalette:
    id: str
    label: str
    accent: str
    accent_strong: str
    accent_rgb: str  # "r, g, b" per rgba(var(--ft-accent-rgb), a)


@dataclass(frozen=True)
class ThemePalette:
    id: str
    label: str
    bg_0: str
    bg_1: str
    bg_2: str
    panel: str
    panel_soft: str
    border: str
    text: str
    muted: str
    nav_text: str
    shadow: str
    glow_alpha: str
    scrollbar: str
    input_bg: str
    danger: str = "#f87171"
    investment: str = "#fbbf24"


@dataclass(frozen=True)
class SemanticColors:
    """Colori semantici in hex (Plotly) + CSS vars (HTML)."""

    income: str
    expense: str
    investment: str
    muted: str
    text: str
    info: str
    pie_outline: str
    hover_bg: str


ACCENTS: dict[str, AccentPalette] = {
    "blue": AccentPalette(
        id="blue",
        label="Blu",
        accent="#60a5fa",
        accent_strong="#3b82f6",
        accent_rgb="96, 165, 250",
    ),
    "green": AccentPalette(
        id="green",
        label="Verde",
        accent="#34d399",
        accent_strong="#10b981",
        accent_rgb="52, 211, 153",
    ),
    "amber": AccentPalette(
        id="amber",
        label="Ambra",
        accent="#fbbf24",
        accent_strong="#f59e0b",
        accent_rgb="251, 191, 36",
    ),
    "violet": AccentPalette(
        id="violet",
        label="Viola",
        accent="#a78bfa",
        accent_strong="#8b5cf6",
        accent_rgb="167, 139, 250",
    ),
}

# Sul chiaro: toni medi (leggibili, meno cupi del testo scuro).
ACCENTS_LIGHT: dict[str, AccentPalette] = {
    "blue": AccentPalette(
        id="blue",
        label="Blu",
        accent="#3b82f6",
        accent_strong="#2563eb",
        accent_rgb="59, 130, 246",
    ),
    "green": AccentPalette(
        id="green",
        label="Verde",
        accent="#10b981",
        accent_strong="#059669",
        accent_rgb="16, 185, 129",
    ),
    "amber": AccentPalette(
        id="amber",
        label="Ambra",
        accent="#d97706",
        accent_strong="#b45309",
        accent_rgb="217, 119, 6",
    ),
    "violet": AccentPalette(
        id="violet",
        label="Viola",
        accent="#8b5cf6",
        accent_strong="#7c3aed",
        accent_rgb="139, 92, 246",
    ),
}

THEMES: dict[str, ThemePalette] = {
    "dark": ThemePalette(
        id="dark",
        label="Scuro",
        bg_0="#070b14",
        bg_1="#0b1220",
        bg_2="#111a2e",
        panel="rgba(11, 18, 32, 0.90)",
        panel_soft="rgba(17, 26, 46, 0.74)",
        border="rgba(148, 163, 184, 0.16)",
        text="#eef3ff",
        muted="#94a3b8",
        nav_text="#c5d5cc",
        shadow="0 16px 36px rgba(0, 0, 0, 0.28)",
        glow_alpha="0.16",
        scrollbar="#243044",
        input_bg="rgba(11, 18, 32, 0.55)",
    ),
    "light": ThemePalette(
        id="light",
        label="Chiaro",
        bg_0="#f3f6fb",
        bg_1="#e9eef6",
        bg_2="#e2e9f3",
        panel="rgba(255, 255, 255, 0.94)",
        panel_soft="rgba(255, 255, 255, 0.82)",
        border="rgba(15, 23, 42, 0.10)",
        text="#0f172a",
        muted="#64748b",
        nav_text="#334155",
        shadow="0 14px 32px rgba(15, 23, 42, 0.10)",
        glow_alpha="0.22",
        scrollbar="#cbd5e1",
        input_bg="#ffffff",
    ),
}


def resolve_palette(
    theme_id: str,
    accent_id: str,
) -> tuple[ThemePalette, AccentPalette]:
    theme = THEMES.get(theme_id) or THEMES["dark"]
    if theme_id == "light":
        accent = ACCENTS_LIGHT.get(accent_id) or ACCENTS_LIGHT["blue"]
    else:
        accent = ACCENTS.get(accent_id) or ACCENTS["blue"]
    return theme, accent


def resolve_semantic(
    theme_id: str | None = None,
    accent_id: str | None = None,
) -> SemanticColors:
    """Colori per KPI/grafici: entrate verdi, uscite rosse (non seguono l’accento)."""
    from src.services.settings_service import get_accent, get_theme_mode

    theme_id = theme_id or get_theme_mode()
    accent_id = accent_id or get_accent()
    theme, accent = resolve_palette(theme_id, accent_id)

    income = "#34d399"
    pie_outline = (
        "rgba(255, 255, 255, 0.92)"
        if theme_id == "light"
        else "rgba(7, 11, 20, 0.95)"
    )
    hover_bg = (
        "rgba(255, 255, 255, 0.96)"
        if theme_id == "light"
        else "rgba(11, 18, 32, 0.96)"
    )

    return SemanticColors(
        income=income,
        expense=theme.danger,
        investment=theme.investment,
        muted=theme.muted,
        text=theme.text,
        info=accent.accent,
        pie_outline=pie_outline,
        hover_bg=hover_bg,
    )
