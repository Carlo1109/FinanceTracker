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
    panel_solid: str  # superfici piene (menu, dialog, barra in basso)
    raised: str  # elementi sopra le card (chip, campi, righe al passaggio)
    border: str
    border_strong: str
    text: str
    muted: str
    subtle: str  # testo terziario (date, didascalie)
    nav_text: str
    shadow: str
    shadow_soft: str
    glow_alpha: str
    scrollbar: str
    input_bg: str
    menu_bg: str
    field_border: str
    income: str
    income_rgb: str
    danger: str
    danger_rgb: str
    investment: str
    investment_rgb: str


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
        bg_0="#060912",
        bg_1="#0a0f1c",
        bg_2="#0d1424",
        panel="rgba(17, 24, 41, 0.78)",
        panel_soft="rgba(22, 31, 52, 0.62)",
        panel_solid="#111829",
        raised="rgba(148, 163, 184, 0.08)",
        border="rgba(148, 163, 184, 0.12)",
        border_strong="rgba(148, 163, 184, 0.22)",
        text="#eef2fb",
        muted="#93a1b8",
        subtle="#66758e",
        nav_text="#c3cde0",
        shadow="0 1px 0 rgba(255, 255, 255, 0.04) inset, 0 18px 40px -18px rgba(0, 0, 0, 0.65)",
        shadow_soft="0 10px 24px -14px rgba(0, 0, 0, 0.55)",
        glow_alpha="0.14",
        scrollbar="#243046",
        input_bg="rgba(9, 14, 26, 0.72)",
        menu_bg="#121a2c",
        field_border="rgba(148, 163, 184, 0.22)",
        income="#34d399",
        income_rgb="52, 211, 153",
        danger="#fb7185",
        danger_rgb="251, 113, 133",
        investment="#a78bfa",
        investment_rgb="167, 139, 250",
    ),
    "light": ThemePalette(
        id="light",
        label="Chiaro",
        bg_0="#f7f9fc",
        bg_1="#f1f4f9",
        bg_2="#eaeff6",
        panel="rgba(255, 255, 255, 0.92)",
        panel_soft="rgba(255, 255, 255, 0.76)",
        panel_solid="#ffffff",
        raised="rgba(15, 23, 42, 0.04)",
        border="rgba(15, 23, 42, 0.08)",
        border_strong="rgba(15, 23, 42, 0.14)",
        text="#0b1324",
        muted="#5b6b84",
        subtle="#8593a8",
        nav_text="#334155",
        shadow="0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 32px -16px rgba(15, 23, 42, 0.16)",
        shadow_soft="0 8px 20px -14px rgba(15, 23, 42, 0.22)",
        glow_alpha="0.16",
        scrollbar="#cbd5e1",
        input_bg="#ffffff",
        menu_bg="#ffffff",
        field_border="#dbe2ec",
        income="#059669",
        income_rgb="5, 150, 105",
        danger="#e11d48",
        danger_rgb="225, 29, 72",
        investment="#7c3aed",
        investment_rgb="124, 58, 237",
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

    income = theme.income
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
