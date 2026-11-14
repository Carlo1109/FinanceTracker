import html
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import streamlit as st


# HTML: entrate/uscite fissi (verde/rosso); accento per il resto dell’UI.
INCOME_COLOR = "var(--ft-income)"
EXPENSE_COLOR = "var(--ft-danger)"
INVESTMENT_COLOR = "var(--ft-investment)"
LIQUIDITY_COLOR = "var(--ft-income)"
BALANCE_COLOR = "var(--ft-income)"
TEXT_COLOR = "var(--ft-text)"
MUTED_COLOR = "var(--ft-muted)"
ACCENT_COLOR = "var(--ft-accent)"

CARD_RADIUS = "18px"
CARD_BORDER = "1px solid var(--ft-border)"
CARD_SHADOW = "var(--ft-shadow)"
CARD_BACKGROUND = "var(--ft-panel)"


def compact_html(value: str) -> str:
    """
    Compatta l'HTML su una singola riga.

    Streamlit può interpretare righe HTML indentate come blocchi Markdown
    di codice. La compattazione evita questo comportamento.
    """
    return " ".join(line.strip() for line in value.splitlines() if line.strip())


def render_html(value: str) -> None:
    st.markdown(compact_html(value), unsafe_allow_html=True)


def _amount_size_class(value: str) -> str:
    """Classi per importi lunghi: restano su una riga dentro la card."""
    length = len(str(value).replace("\u00a0", " "))
    if length >= 15:
        return "is-huge"
    if length >= 13:
        return "is-long"
    return ""


_TONE_BY_COLOR = {
    INCOME_COLOR: "good",
    EXPENSE_COLOR: "bad",
    "var(--ft-accent)": "info",
}


def _delta_chip(text: str | None, color: str) -> str:
    """Variazione rispetto al periodo precedente come piccola etichetta."""
    if not text:
        return ""
    tone = _TONE_BY_COLOR.get(color, "neutral")
    return (
        f'<span class="ft-delta is-{tone}">{html.escape(str(text))}</span>'
    )


def sparkline_svg(
    values: list[float],
    *,
    width: int = 260,
    height: int = 72,
    color: str = "var(--ft-accent)",
) -> str:
    """Piccola linea di tendenza in SVG (nessun JavaScript, nessuna libreria)."""
    points = [float(v or 0) for v in values]
    if len(points) < 2:
        return ""
    low, high = min(points + [0.0]), max(points + [0.0])
    span = (high - low) or 1.0
    pad = 6
    step = (width - pad * 2) / (len(points) - 1)

    def y_of(value: float) -> float:
        return pad + (height - pad * 2) * (1 - (value - low) / span)

    coords = [(pad + i * step, y_of(v)) for i, v in enumerate(points)]
    path = f"M {coords[0][0]:.1f} {coords[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
        mid = (x0 + x1) / 2
        path += f" C {mid:.1f} {y0:.1f} {mid:.1f} {y1:.1f} {x1:.1f} {y1:.1f}"
    zero = y_of(0.0)
    area = (
        path
        + f" L {coords[-1][0]:.1f} {zero:.1f} L {coords[0][0]:.1f} {zero:.1f} Z"
    )
    last_x, last_y = coords[-1]
    return f"""
        <svg class="ft-spark" viewBox="0 0 {width} {height}"
             preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id="ftSparkFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" style="stop-color:{color};stop-opacity:.30"/>
              <stop offset="100%" style="stop-color:{color};stop-opacity:0"/>
            </linearGradient>
          </defs>
          <line x1="{pad}" x2="{width - pad}" y1="{zero:.1f}" y2="{zero:.1f}"
                class="ft-spark-zero"/>
          <path d="{area}" style="fill:url(#ftSparkFill)"/>
          <path d="{path}" style="fill:none;stroke:{color};stroke-width:2.4;
                stroke-linecap:round;vector-effect:non-scaling-stroke"/>
          <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3.6"
                  style="fill:{color};vector-effect:non-scaling-stroke"/>
        </svg>
    """


def render_hero_card(
    title: str,
    main_value: str,
    main_color: str,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
    *,
    context: str | None = None,
    spark_values: list[float] | None = None,
    spark_caption: str | None = None,
    stats: list[tuple[str, str, str]] | None = None,
) -> None:
    """
    Card principale: valore grande, variazione, contesto e mini andamento.

    stats: piccole cifre sotto il valore [(etichetta, valore, colore)].
    """
    context_html = (
        f'<div class="ft-hero-context">{html.escape(context)}</div>'
        if context
        else ""
    )
    spark = sparkline_svg(spark_values or [], color=main_color)
    spark_html = ""
    if spark:
        caption = (
            f'<div class="ft-hero-spark-caption">{html.escape(spark_caption)}</div>'
            if spark_caption
            else ""
        )
        spark_html = f'<div class="ft-hero-spark">{caption}{spark}</div>'
    stats_html = ""
    if stats:
        stats_html = '<div class="ft-hero-stats">' + "".join(
            f"""<div class="ft-hero-stat">
                  <span>{html.escape(label)}</span>
                  <strong style="color:{color}">{html.escape(value)}</strong>
                </div>"""
            for label, value, color in stats
        ) + "</div>"

    render_html(
        f"""
        <div class="ft-hero">
          <div class="ft-hero-main">
            <div class="ft-kicker">{html.escape(title)}</div>
            <div class="ft-hero-value {_amount_size_class(main_value)}"
                 style="color:{main_color}">{html.escape(main_value)}</div>
            <div class="ft-hero-row">
              {_delta_chip(subtitle, subtitle_color)}
              {context_html}
            </div>
            {stats_html}
          </div>
          {spark_html}
        </div>
        """
    )


# Icone delle card KPI (emoji: nessun font di icone da caricare).
KPI_ICONS = {
    "Entrate": "↘",
    "Uscite": "↗",
    "Investimenti": "◆",
    "Liquidità": "◉",
    "Bilancio": "±",
    "Prestati": "↗",
    "Rientrati": "↘",
    "Netto": "±",
}

_KPI_TONES = {
    INCOME_COLOR: "income",
    EXPENSE_COLOR: "expense",
    INVESTMENT_COLOR: "investment",
}


def render_kpi_card(
    title: str,
    value: str,
    icon: str = "",
    value_color: str = TEXT_COLOR,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
    *,
    tone: str | None = None,
) -> None:
    tone = tone or _KPI_TONES.get(value_color, "accent")
    glyph = icon or KPI_ICONS.get(title, "•")
    size_class = _amount_size_class(value)
    render_html(
        f"""
        <div class="ft-kpi-card ft-kpi is-{tone}">
          <div class="ft-kpi-head">
            <span class="ft-kpi-icon">{html.escape(glyph)}</span>
            <span class="ft-kicker">{html.escape(title)}</span>
          </div>
          <div class="ft-kpi-value {size_class}" style="color:{value_color}">
            {html.escape(value)}
          </div>
          <div class="ft-kpi-foot">{_delta_chip(subtitle, subtitle_color)}</div>
        </div>
        """
    )


def _info_card_body_html(
    title: str,
    value: str,
    secondary_value: str | None = None,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
    footer: str | None = None,
) -> str:
    secondary_value_html = ""
    if secondary_value:
        secondary_value_html = f"""
            <div class="ft-info-card-amount">
                {html.escape(str(secondary_value))}
            </div>
        """

    subtitle_html = ""
    if subtitle:
        subtitle_html = (
            f'<div class="ft-info-card-sub">'
            f"{_delta_chip(subtitle, subtitle_color)}</div>"
        )

    footer_html = ""
    if footer:
        footer_html = f"""
            <div class="ft-info-card-footer">
                {html.escape(str(footer))}
            </div>
        """

    return f"""
        <div class="ft-info-card-kicker ft-kicker">
            {html.escape(str(title))}
        </div>
        <div class="ft-info-card-value">
            {html.escape(str(value))}
        </div>
        {secondary_value_html}
        {subtitle_html}
        {footer_html}
    """


def render_info_card(
    title: str,
    value: str,
    secondary_value: str | None = None,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
    footer: str | None = None,
    value_color: str = TEXT_COLOR,
    extra_class: str = "",
) -> None:
    body = _info_card_body_html(
        title,
        value,
        secondary_value=secondary_value,
        subtitle=subtitle,
        subtitle_color=subtitle_color,
        footer=footer,
    )
    classes = " ".join(
        part for part in ("ft-info-card", extra_class) if part
    )
    render_html(
        f"""
        <div class="{classes}" style="--ft-info-value:{value_color};">
            {body}
        </div>
        """
    )


def _section_label(text: str) -> None:
    render_html(f'<div class="ft-kicker ft-card-label">{html.escape(text)}</div>')


def category_rows_html(rows: list[dict]) -> str:
    """Righe categoria: icona, nome, importo, percentuale e barra."""
    items: list[str] = []
    for row in rows:
        percent = max(0.0, min(100.0, float(row.get("percent", 0))))
        color = html.escape(str(row.get("color") or "var(--ft-accent)"))
        extra = row.get("extra") or ""
        items.append(
            f"""
            <div class="ft-cat-row" style="--c:{color}">
              <span class="ft-cat-icon">{html.escape(str(row.get("icon", "")))}</span>
              <div class="ft-cat-body">
                <div class="ft-cat-line">
                  <span class="ft-cat-name">{html.escape(str(row.get("name", "")))}</span>
                  <span class="ft-cat-amount">{html.escape(str(row.get("amount", "")))}</span>
                </div>
                <div class="ft-cat-line is-sub">
                  <div class="ft-cat-track"><div style="width:{percent:.2f}%"></div></div>
                  <span class="ft-cat-pct">{f"{percent:.1f}".replace(".", ",")}%</span>
                </div>
                {extra}
              </div>
            </div>
            """
        )
    return "".join(items)


_category_rows_html = category_rows_html


def render_expense_distribution_card(
    rows: list[dict],
    *,
    total_label: str,
    render_pie: Callable[[], None],
    list_max_height: int = 360,
    key: str = "ft_dashboard_distribution_card",
) -> None:
    """
    Card unica con ciambella a sinistra e lista scorrevole a destra.

    ``render_pie`` è una callback senza argomenti.
    """
    with st.container(border=True, key=key):
        render_html(
            '<span class="ft-distribution-anchor" aria-hidden="true"></span>'
        )
        left_col, right_col = st.columns([1, 1.15], gap="large")

        with left_col:
            render_pie()

        with right_col:
            render_html(
                f"""
                <div class="ft-category-scroll" style="max-height:{list_max_height}px;">
                    {category_rows_html(rows)}
                </div>
                <div class="ft-cat-total">
                    <span class="ft-kicker">Totale</span>
                    <strong>{html.escape(total_label)}</strong>
                </div>
                """
            )


def render_chart_card(render_chart: Callable[[], None]) -> None:
    """Card semplice che avvolge un grafico (callback senza argomenti)."""
    with st.container(border=True, key="ft_dashboard_chart_card"):
        render_html(
            '<span class="ft-chart-card-anchor" aria-hidden="true"></span>'
        )
        render_chart()


def render_section_title(text: str, subtitle: str | None = None) -> None:
    sub = (
        f'<div class="ft-section-sub">{html.escape(subtitle)}</div>'
        if subtitle
        else ""
    )
    render_html(
        f'<div class="ft-section-title">{html.escape(text)}</div>{sub}'
    )


@contextmanager
def styled_panel(*, kind: str = "panel") -> Any:
    """
    Pannello con lo stesso look delle card Dashboard.

    kind: panel | movement
    """
    with st.container(border=True):
        render_html(
            f'<span class="ft-{html.escape(kind)}-anchor" '
            'aria-hidden="true"></span>'
        )
        yield
